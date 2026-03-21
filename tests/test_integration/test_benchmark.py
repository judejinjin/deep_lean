"""
Benchmark test suite — measures system performance on graded problems.

Requires: live API keys + Lean 4.
Mark: pytest -m benchmark
"""

import os

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.benchmark]


BENCHMARK_PROBLEMS = [
    {
        "name": "trivial_arithmetic",
        "question": "Prove that 1 + 1 = 2",
        "difficulty": "trivial",
        "max_retries": 1,
    },
    {
        "name": "nat_nonneg",
        "question": "Prove that for all natural numbers n, 0 ≤ n",
        "difficulty": "easy",
        "max_retries": 2,
    },
    {
        "name": "sqrt2_irrational",
        "question": "Prove that the square root of 2 is irrational",
        "difficulty": "medium",
        "max_retries": 5,
    },
    {
        "name": "primes_infinite",
        "question": "Prove that there are infinitely many prime numbers",
        "difficulty": "medium",
        "max_retries": 5,
    },
]


def _has_api_key() -> bool:
    return bool(os.environ.get("CLAUDE_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


@pytest.mark.skipif(not _has_api_key(), reason="No API key available")
@pytest.mark.parametrize(
    "problem",
    BENCHMARK_PROBLEMS,
    ids=[p["name"] for p in BENCHMARK_PROBLEMS],
)
@pytest.mark.asyncio
async def test_benchmark(problem):
    """Run a benchmark problem through the single-agent loop."""
    from src.agents.single_loop import single_agent_prove

    result = await single_agent_prove(problem["question"])

    # Record results (for manual review)
    print(f"\n--- {problem['name']} ({problem['difficulty']}) ---")
    print(f"  Verified: {result.verified}")
    print(f"  Attempts: {len(result.proof_attempts)}")
    print(f"  LLM calls: {result.total_llm_calls}")
    print(f"  Cost: ${result.total_cost_usd:.4f}")

    # Soft assertion: we expect to at least get LLM responses
    assert result.total_llm_calls >= 1
