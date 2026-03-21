"""
Orchestrator Agent — plans research strategy and decomposes questions.
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.config import settings
from src.utils.logging import log


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"
    model = settings.orchestration_model

    async def run(self, state: dict) -> dict:
        """Decompose the question into a research plan."""
        question = state.get("question", "")
        log.info("orchestrator_start", question=question[:100])

        plan = await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Decompose this research question into a structured plan:\n\n"
                        f"{question}\n\n"
                        f"Source PDFs provided: {state.get('source_pdfs', [])}\n"
                    ),
                }
            ],
            max_tokens=4096,
        )

        log.info("orchestrator_done", plan_length=len(plan))

        return {
            "research_plan": plan,
            "research_context": "",
            "informal_proof": "",
            "lean_code": "",
            "lean_errors": "",
            "lean_verified": False,
            "attempt_count": 0,
        }
