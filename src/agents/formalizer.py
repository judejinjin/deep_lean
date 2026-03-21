"""
Formalization Agent — translates informal math into Lean 4 code.
"""

from __future__ import annotations

import re

from src.agents.base import BaseAgent
from src.config import settings
from src.utils.logging import log


def extract_lean_code(text: str) -> str:
    """Extract Lean source from LLM response (strip markdown fences)."""
    m = re.search(r"```lean4?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


class FormalizerAgent(BaseAgent):
    name = "formalizer"
    model = settings.formalization_model

    async def run(self, state: dict) -> dict:
        """Generate or repair Lean 4 code."""
        question = state.get("question", "")
        context = state.get("research_context", "")
        existing_code = state.get("lean_code", "")
        errors = state.get("lean_errors", "")

        if existing_code and errors:
            log.info("formalizer_repair", attempt=state.get("attempt_count", 0))
            lean_code = await self._repair(existing_code, errors, context)
        else:
            log.info("formalizer_initial", question=question[:100])
            lean_code = await self._formalize(question, context)

        return {"lean_code": lean_code}

    async def _formalize(self, question: str, context: str) -> str:
        """Initial formalization from question + research context."""
        response = await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Formalize the following in Lean 4 using Mathlib:\n\n"
                        f"**Question:** {question}\n\n"
                        f"**Research Context:**\n{context[:3000]}\n\n"
                        f"Return ONLY the Lean 4 code in a ```lean code fence."
                    ),
                }
            ],
            max_tokens=4096,
        )
        return extract_lean_code(response)

    async def _repair(self, code: str, errors: str, context: str) -> str:
        """Repair failed Lean code based on compiler errors."""
        response = await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"This Lean 4 code failed to compile:\n\n"
                        f"```lean\n{code}\n```\n\n"
                        f"**Errors:**\n{errors}\n\n"
                        f"**Context:**\n{context[:2000]}\n\n"
                        f"Fix the code. Return ONLY the corrected Lean 4 code "
                        f"in a ```lean code fence."
                    ),
                }
            ],
            max_tokens=4096,
        )
        return extract_lean_code(response)
