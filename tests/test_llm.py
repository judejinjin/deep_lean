"""Tests for the LLM client wrapper (mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm import call_llm, get_session_stats, reset_session_stats


@pytest.fixture(autouse=True)
def _reset_stats():
    """Reset session stats before each test."""
    reset_session_stats()
    yield
    reset_session_stats()


@pytest.mark.asyncio
async def test_call_llm_success():
    """call_llm should return content on success."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello, world!"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    with patch("src.llm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        with patch("src.llm.litellm.completion_cost", return_value=0.001):
            result = await call_llm(
                "anthropic/claude-sonnet-4-6",
                [{"role": "user", "content": "Hello"}],
            )
    assert result == "Hello, world!"


@pytest.mark.asyncio
async def test_call_llm_tracks_cost():
    """Session cost should accumulate across calls."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "response"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    with patch("src.llm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        with patch("src.llm.litellm.completion_cost", return_value=0.005):
            await call_llm("test-model", [{"role": "user", "content": "Hi"}])
            await call_llm("test-model", [{"role": "user", "content": "Hi"}])

    stats = get_session_stats()
    assert stats["total_calls"] == 2
    assert stats["total_cost_usd"] == pytest.approx(0.01, abs=0.001)


@pytest.mark.asyncio
async def test_call_llm_fallback():
    """Should fall back to secondary model on primary failure."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "fallback response"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Primary model failed")
        return mock_response

    with patch("src.llm.acompletion", side_effect=mock_acompletion):
        with patch("src.llm.litellm.completion_cost", return_value=0.0):
            result = await call_llm(
                "anthropic/claude-sonnet-4-6",
                [{"role": "user", "content": "test"}],
            )
    assert result == "fallback response"


@pytest.mark.asyncio
async def test_call_llm_all_fail():
    """Should raise RuntimeError when all models fail."""

    async def mock_fail(**kwargs):
        raise Exception("Model unavailable")

    with patch("src.llm.acompletion", side_effect=mock_fail):
        with pytest.raises(RuntimeError, match="All models failed"):
            await call_llm(
                "nonexistent/model",
                [{"role": "user", "content": "test"}],
            )


def test_session_stats_reset():
    """Stats should be zeroed after reset."""
    reset_session_stats()
    stats = get_session_stats()
    assert stats["total_calls"] == 0
    assert stats["total_cost_usd"] == 0.0
