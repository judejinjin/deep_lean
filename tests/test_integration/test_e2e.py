"""
End-to-end integration test using the full multi-agent pipeline.

Requires: live API keys.
Mark: pytest -m integration
"""

import os

import pytest

pytestmark = pytest.mark.integration


def _has_api_key() -> bool:
    return bool(os.environ.get("CLAUDE_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


@pytest.mark.skipif(not _has_api_key(), reason="No API key available")
@pytest.mark.asyncio
async def test_simple_proof_pipeline():
    """Run the full pipeline on a trivial problem."""
    from src.agents.graph import build_graph, create_initial_state

    graph = build_graph()
    state = create_initial_state("Prove that 1 + 1 = 2")

    result = await graph.ainvoke(state)

    # Should complete without crashing
    assert "report_md" in result or "report_path" in result
    assert isinstance(result.get("lean_code", ""), str)
    assert isinstance(result.get("attempt_count", 0), int)


@pytest.mark.skipif(not _has_api_key(), reason="No API key available")
@pytest.mark.asyncio
async def test_single_loop_trivial():
    """Run the single-agent loop on a trivial problem."""
    from src.agents.single_loop import single_agent_prove

    result = await single_agent_prove("Prove that 1 + 1 = 2")
    assert result.question.question == "Prove that 1 + 1 = 2"
    assert result.total_llm_calls >= 1
