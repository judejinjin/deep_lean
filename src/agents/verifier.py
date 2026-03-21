"""
Verifier Agent — runs Lean 4 compiler and analyses errors.
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.config import settings
from src.models import LeanCode, LeanResult
from src.tools.lean_executor import LeanExecutor
from src.utils.lean_parser import format_for_llm, parse_lean_output
from src.utils.logging import log


class VerifierAgent(BaseAgent):
    name = "verifier"
    model = settings.error_analysis_model

    def __init__(self) -> None:
        super().__init__()
        self.executor = LeanExecutor()

    async def run(self, state: dict) -> dict:
        """Verify Lean code and return structured error analysis."""
        lean_source = state.get("lean_code", "")
        attempt = state.get("attempt_count", 0) + 1
        log.info("verifier_start", attempt=attempt)

        if not lean_source.strip():
            return {
                "lean_verified": False,
                "lean_errors": "No Lean code to verify.",
                "attempt_count": attempt,
            }

        code = LeanCode(filename="Proof.lean", source=lean_source)
        lean_available = await self.executor.check_available()

        if lean_available:
            result = await self.executor.verify(code)
        else:
            log.warning("lean_not_available", msg="Lean/lake not installed")
            result = LeanResult(
                success=False,
                stderr="Lean/lake not available on this system. Cannot verify.",
            )

        if result.success:
            log.info("verifier_success", attempt=attempt)
            return {
                "lean_verified": True,
                "lean_errors": "",
                "attempt_count": attempt,
                "lean_result": result.model_dump(),
            }

        # Parse and analyse errors
        parsed_errors = parse_lean_output(result.stderr)
        error_summary = format_for_llm(parsed_errors)

        # If we have complex errors, use LLM to produce deeper analysis
        if parsed_errors:
            analysis = await self._analyse_errors(lean_source, error_summary)
        else:
            analysis = f"Build failed with output:\n{result.stderr[:2000]}"

        log.info("verifier_failed", attempt=attempt, errors=len(parsed_errors))

        return {
            "lean_verified": False,
            "lean_errors": analysis,
            "attempt_count": attempt,
            "lean_result": result.model_dump(),
        }

    async def _analyse_errors(self, code: str, error_summary: str) -> str:
        """Use LLM to provide detailed error analysis and fix suggestions."""
        return await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Analyse these Lean 4 compiler errors and suggest fixes:\n\n"
                        f"**Code:**\n```lean\n{code}\n```\n\n"
                        f"**Errors:**\n{error_summary}\n\n"
                        f"Provide a clear, actionable error analysis."
                    ),
                }
            ],
            max_tokens=2048,
        )
