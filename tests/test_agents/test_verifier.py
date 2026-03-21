"""Tests for the Verifier Agent (mocked Lean executor)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.verifier import VerifierAgent
from src.models import LeanResult


@pytest.mark.asyncio
async def test_verifier_success():
    """Should return verified=True on successful build."""
    agent = VerifierAgent()

    state = {"lean_code": "theorem t : True := trivial", "attempt_count": 0}

    with patch.object(
        agent.executor, "check_available", new_callable=AsyncMock, return_value=True
    ):
        with patch.object(
            agent.executor,
            "verify",
            new_callable=AsyncMock,
            return_value=LeanResult(success=True, stdout="Build OK"),
        ):
            result = await agent.run(state)

    assert result["lean_verified"] is True
    assert result["lean_errors"] == ""
    assert result["attempt_count"] == 1


@pytest.mark.asyncio
async def test_verifier_failure():
    """Should return verified=False with error analysis on failure."""
    agent = VerifierAgent()

    state = {"lean_code": "theorem t : 1 = 2 := by norm_num", "attempt_count": 0}

    with patch.object(
        agent.executor, "check_available", new_callable=AsyncMock, return_value=True
    ):
        with patch.object(
            agent.executor,
            "verify",
            new_callable=AsyncMock,
            return_value=LeanResult(
                success=False,
                stderr="Proof.lean:1:0: error: tactic 'norm_num' failed",
            ),
        ):
            with patch.object(
                agent, "_analyse_errors", new_callable=AsyncMock, return_value="Fix: use sorry"
            ):
                result = await agent.run(state)

    assert result["lean_verified"] is False
    assert result["attempt_count"] == 1


@pytest.mark.asyncio
async def test_verifier_empty_code():
    """Should handle empty Lean code gracefully."""
    agent = VerifierAgent()
    state = {"lean_code": "", "attempt_count": 0}
    result = await agent.run(state)
    assert result["lean_verified"] is False
    assert "No Lean code" in result["lean_errors"]


@pytest.mark.asyncio
async def test_verifier_lean_not_available():
    """Should handle Lean not being installed."""
    agent = VerifierAgent()
    state = {"lean_code": "theorem t : True := trivial", "attempt_count": 0}

    with patch.object(
        agent.executor, "check_available", new_callable=AsyncMock, return_value=False
    ):
        with patch.object(
            agent, "_analyse_errors", new_callable=AsyncMock, return_value="Lean not installed"
        ):
            result = await agent.run(state)

    assert result["lean_verified"] is False
