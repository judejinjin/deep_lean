"""
Reporter Agent — generates polished Markdown research reports.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from src.agents.base import BaseAgent
from src.config import settings
from src.utils.logging import log


class ReporterAgent(BaseAgent):
    name = "reporter"
    model = settings.report_model

    async def run(self, state: dict) -> dict:
        """Assemble the final research report."""
        log.info("reporter_start")

        prompt = self._build_prompt(state)
        report = await self.llm(
            [{"role": "user", "content": prompt}],
            max_tokens=8192,
        )

        # Save to file
        session_id = state.get("session_id", uuid.uuid4().hex[:8])
        report_path = Path(settings.reports_dir) / f"report_{session_id}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

        log.info("reporter_done", path=str(report_path), length=len(report))

        return {
            "report_md": report,
            "report_path": str(report_path),
            "lean_verified": state.get("lean_verified"),
            "attempt_count": state.get("attempt_count"),
        }

    @staticmethod
    def _build_prompt(state: dict) -> str:
        """Build the report generation prompt from agent state."""
        question = state.get("question", "")
        context = state.get("research_context", "")
        lean_code = state.get("lean_code", "")
        verified = state.get("lean_verified", False)
        attempts = state.get("attempt_count", 0)
        errors = state.get("lean_errors", "")
        plan = state.get("research_plan", "")

        verification_status = "✅ Verified" if verified else "⚠️ Unverified"
        error_section = f"\n\n### Last Errors\n{errors}" if errors and not verified else ""

        return (
            f"Generate a comprehensive research report for the following:\n\n"
            f"## Research Question\n{question}\n\n"
            f"## Research Plan\n{plan[:2000]}\n\n"
            f"## Literature Review\n{context[:3000]}\n\n"
            f"## Lean 4 Code ({verification_status}, {attempts} attempts)\n"
            f"```lean\n{lean_code}\n```\n"
            f"{error_section}\n\n"
            f"Write a publication-quality Markdown report with all sections: "
            f"title, abstract, problem statement, literature review, informal proof, "
            f"formal Lean 4 proof, verification status, discussion, references."
        )
