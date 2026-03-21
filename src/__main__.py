"""
DeepLean — CLI entry point.

Usage:
    uv run python -m src "Prove that 1 + 1 = 2"
    uv run python -m src --pdfs file1.pdf file2.pdf "Research question here"
    uv run python -m src --single "Prove that 1 + 1 = 2"   # single-agent loop only
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from src.agents.graph import build_graph, create_initial_state
from src.llm import get_session_stats, reset_session_stats
from src.utils.logging import log


async def run_pipeline(question: str, source_pdfs: list[str] | None = None) -> dict:
    """Run the full multi-agent LangGraph pipeline."""
    reset_session_stats()
    t0 = time.monotonic()

    graph = build_graph()
    state = create_initial_state(question, source_pdfs)

    log.info("pipeline_start", question=question[:100])
    result = await graph.ainvoke(state)
    elapsed = time.monotonic() - t0
    stats = get_session_stats()

    log.info(
        "pipeline_done",
        verified=result.get("lean_verified"),
        attempts=result.get("attempt_count"),
        cost_usd=stats["total_cost_usd"],
        elapsed_s=round(elapsed, 1),
    )

    return result


async def run_single(question: str) -> None:
    """Run the simpler single-agent proof loop."""
    from src.agents.single_loop import single_agent_prove

    result = await single_agent_prove(question)

    print(f"\n{'='*60}")
    print(f"Question: {result.question.question}")
    print(f"Verified: {result.verified}")
    print(f"Attempts: {len(result.proof_attempts)}")
    print(f"LLM calls: {result.total_llm_calls}")
    print(f"Cost: ${result.total_cost_usd:.4f}")
    if result.final_lean_code:
        print(f"\nFinal Lean code:\n{result.final_lean_code.source}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeepLean — Agentic Deep Researcher for Lean 4",
        prog="python -m src",
    )
    parser.add_argument("question", nargs="*", help="Research question to investigate")
    parser.add_argument("--pdfs", nargs="*", default=[], help="Paths to source PDFs")
    parser.add_argument(
        "--single", action="store_true", help="Use single-agent loop instead of full pipeline"
    )

    args = parser.parse_args()
    question = " ".join(args.question) if args.question else ""

    if not question:
        parser.print_help()
        sys.exit(1)

    if args.single:
        asyncio.run(run_single(question))
    else:
        result = asyncio.run(run_pipeline(question, args.pdfs))
        print(f"\n{'='*60}")
        print(f"Verified: {result.get('lean_verified', False)}")
        print(f"Attempts: {result.get('attempt_count', 0)}")
        print(f"Report: {result.get('report_path', 'N/A')}")
        print(f"Notebook: {result.get('notebook_path', 'N/A')}")
        stats = get_session_stats()
        print(f"LLM calls: {stats['total_calls']}")
        print(f"Cost: ${stats['total_cost_usd']:.4f}")


if __name__ == "__main__":
    main()
