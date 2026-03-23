"""
Minimal single-agent proof loop — validates the full LLM → Lean stack.

Usage:
    uv run python -m src.agents.single_loop "Prove that 1 + 1 = 2"
"""

from __future__ import annotations

import asyncio
import re
import sys

from src.config import settings
from src.llm import call_llm, get_session_stats
from src.models import LeanCode, ProofAttempt, ResearchOutput, ResearchQuestion
from src.tools.lean_executor import LeanExecutor
from src.utils.lean_parser import format_for_llm, parse_lean_output
from src.utils.logging import log


def _extract_lean_code(text: str) -> str:
    """Extract Lean source from LLM response (strip markdown fences)."""
    # Try to find ```lean ... ``` block
    m = re.search(r"```lean4?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try generic code fence
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Return raw text (might be plain Lean)
    return text.strip()


SYSTEM_PROMPT = """\
You are a Lean 4 expert using Mathlib4. Generate ONLY Lean 4 code (not Lean 3).
Rules:
- Use `import Mathlib` at the top for broad Mathlib access, or specific imports.
- Add `set_option linter.unusedVariables false` after imports.
- Use `theorem`, `lemma`, or `example` declarations.
- Use tactic mode (`by`) for proofs.
- Common tactics: `simp`, `ring`, `omega`, `exact`, `apply`, `intro`, `cases`, `induction`, `norm_num`, `linarith`, `decide`.
- Use `positivity` to prove goals like `0 < expr` — NEVER use manual chains of `apply mul_pos`/`apply div_pos`.
- Use `field_simp` to simplify fractions/divisions — it often closes goals on its own (don't follow with `ring` unless needed).
- Use `nlinarith` for nonlinear arithmetic with hint terms.
- Do NOT use `#check`, `#eval` or `#print` at top-level in the proof file.
- Return ONLY the Lean code inside a ```lean code fence.
"""


async def single_agent_prove(question: str) -> ResearchOutput:
    """Simplest proof pipeline: one LLM, iterative Lean verification."""
    output = ResearchOutput(question=ResearchQuestion(question=question))
    executor = LeanExecutor()
    lean_available = await executor.check_available()

    # Step 1: Ask LLM to generate Lean 4 code directly
    log.info("step", phase="generate_lean", question=question)
    lean_response = await call_llm(
        settings.formalization_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Write a Lean 4 proof for:\n\n{question}\n\n"
                    "Use Mathlib if needed. Return ONLY the Lean code."
                ),
            },
        ],
        max_tokens=4096,
    )
    lean_source = _extract_lean_code(lean_response)

    # Step 2: Iterative verification
    for attempt_num in range(1, settings.lean_max_retries + 1):
        code = LeanCode(filename="Proof.lean", source=lean_source)
        log.info("step", phase="verify", attempt=attempt_num)

        if lean_available:
            result = await executor.verify(code)
        else:
            # If Lean is not installed, do a syntax-level check only
            log.warning("lean_not_available", msg="Skipping actual build; marking as unverified")
            from src.models import LeanResult

            result = LeanResult(success=False, stderr="Lean/lake not installed on this system")

        output.proof_attempts.append(
            ProofAttempt(attempt_number=attempt_num, lean_code=code, result=result)
        )

        if result.success:
            log.info("proof_verified", attempts=attempt_num)
            output.verified = True
            output.final_lean_code = code
            break

        if attempt_num == settings.lean_max_retries:
            log.warning("max_retries_reached", attempts=attempt_num)
            output.final_lean_code = code
            break

        # Feed errors back to LLM for repair
        error_feedback = format_for_llm(parse_lean_output(result.stderr))
        log.info("step", phase="repair", errors=error_feedback[:200])

        repair_response = await call_llm(
            settings.formalization_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"This Lean 4 code failed to compile:\n\n```lean\n{lean_source}\n```\n\n"
                        f"Errors:\n{error_feedback}\n\n"
                        "Fix the code. Return ONLY the corrected Lean code."
                    ),
                },
            ],
            max_tokens=4096,
        )
        lean_source = _extract_lean_code(repair_response)

    # Finalise
    stats = get_session_stats()
    output.total_llm_calls = stats["total_calls"]
    output.total_cost_usd = stats["total_cost_usd"]
    return output


async def main() -> None:
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Prove that 1 + 1 = 2"
    log.info("single_loop_start", question=question)

    result = await single_agent_prove(question)

    print(f"\n{'='*60}")
    print(f"Question: {result.question.question}")
    print(f"Verified: {result.verified}")
    print(f"Attempts: {len(result.proof_attempts)}")
    print(f"LLM calls: {result.total_llm_calls}")
    print(f"Cost: ${result.total_cost_usd:.4f}")
    if result.final_lean_code:
        print(f"\nFinal Lean code:\n{result.final_lean_code.source}")


if __name__ == "__main__":
    asyncio.run(main())
