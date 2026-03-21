"""Tests for the Formalization Agent (mocked LLM)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.formalizer import FormalizerAgent, extract_lean_code


def test_extract_lean_code_fenced():
    """Should extract Lean code from markdown fence."""
    text = "Here's the proof:\n```lean\ntheorem t : True := trivial\n```\nDone."
    assert extract_lean_code(text) == "theorem t : True := trivial"


def test_extract_lean_code_lean4_fence():
    text = "```lean4\nimport Mathlib\ntheorem t : True := trivial\n```"
    assert "import Mathlib" in extract_lean_code(text)


def test_extract_lean_code_generic_fence():
    text = "```\ntheorem t : True := trivial\n```"
    assert extract_lean_code(text) == "theorem t : True := trivial"


def test_extract_lean_code_no_fence():
    text = "theorem t : True := trivial"
    assert extract_lean_code(text) == "theorem t : True := trivial"


@pytest.mark.asyncio
async def test_formalizer_initial():
    """Should generate Lean code on first run (no errors)."""
    agent = FormalizerAgent()
    state = {
        "question": "Prove 1 + 1 = 2",
        "research_context": "Basic arithmetic.",
        "lean_code": "",
        "lean_errors": "",
    }

    with patch.object(
        agent,
        "llm",
        new_callable=AsyncMock,
        return_value="```lean\ntheorem t : 1 + 1 = 2 := by norm_num\n```",
    ):
        result = await agent.run(state)

    assert "lean_code" in result
    assert "theorem" in result["lean_code"]


@pytest.mark.asyncio
async def test_formalizer_repair():
    """Should repair code when errors are present."""
    agent = FormalizerAgent()
    state = {
        "question": "Prove 1 + 1 = 2",
        "research_context": "",
        "lean_code": "theorem t : 1 + 1 = 3 := by norm_num",
        "lean_errors": "type mismatch: expected 3 = 2",
        "attempt_count": 1,
    }

    with patch.object(
        agent,
        "llm",
        new_callable=AsyncMock,
        return_value="```lean\ntheorem t : 1 + 1 = 2 := by norm_num\n```",
    ):
        result = await agent.run(state)

    assert "1 + 1 = 2" in result["lean_code"]
