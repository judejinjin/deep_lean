"""
Proof Decomposition Agent — breaks complex proofs into independently verifiable lemmas.
"""

from __future__ import annotations

import re

from src.agents.base import BaseAgent
from src.config import settings
from src.llm import call_llm
from src.utils.logging import log


class DecomposerAgent(BaseAgent):
    name = "decomposer"
    model = settings.reasoning_model

    async def run(self, state: dict) -> dict:
        """Decompose a proof goal into sub-lemmas."""
        question = state.get("question", "")
        context = state.get("research_context", "")

        log.info("decomposer_start", question=question[:100])
        lemmas = await self.decompose(question, context)
        log.info("decomposer_done", num_lemmas=len(lemmas))

        return {"sub_lemmas": lemmas}

    async def decompose(self, question: str, context: str) -> list[dict[str, str]]:
        """Break a proof into independent lemmas."""
        response = await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Break this proof into independent, individually verifiable lemmas.\n\n"
                        f"**Proof goal:** {question}\n\n"
                        f"**Context:** {context[:2000]}\n\n"
                        f"For each lemma, provide:\n"
                        f"1. A name (valid Lean identifier)\n"
                        f"2. An informal statement\n"
                        f"3. Dependencies (which other lemmas it uses)\n\n"
                        f"Format each lemma as:\n"
                        f"### LEMMA: <name>\n"
                        f"Statement: <informal statement>\n"
                        f"Depends on: <comma-separated names or 'none'>\n"
                    ),
                }
            ],
            max_tokens=4096,
        )

        return self._parse_lemmas(response)

    @staticmethod
    def _parse_lemmas(text: str) -> list[dict[str, str]]:
        """Parse LLM response into structured lemma list."""
        lemmas: list[dict[str, str]] = []
        # Match "### LEMMA: name" sections
        pattern = re.compile(
            r"###\s*LEMMA:\s*(\S+)\s*\n"
            r"(?:Statement:\s*(.*?)\n)?"
            r"(?:Depends on:\s*(.*?)(?:\n|$))?",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            name = match.group(1).strip()
            statement = (match.group(2) or "").strip()
            deps_str = (match.group(3) or "none").strip()
            deps = (
                []
                if deps_str.lower() == "none"
                else [d.strip() for d in deps_str.split(",") if d.strip()]
            )
            lemmas.append(
                {
                    "name": name,
                    "statement": statement,
                    "depends_on": deps,
                }
            )

        # Fallback: if parsing found nothing, return the whole text as one item
        if not lemmas and text.strip():
            lemmas.append(
                {
                    "name": "main_lemma",
                    "statement": text.strip()[:500],
                    "depends_on": [],
                }
            )

        return lemmas


async def sorry_driven_verify(lean_code: str) -> tuple[str, list[str]]:
    """Replace tactic blocks with sorry, verify structure, identify gaps.

    Returns (modified_code, list_of_sorry_locations).
    """
    sorry_pattern = re.compile(r"(by\s*\n\s*)((?:(?!\ntheorem|\nlemma|\ndef|\n\n)[\s\S])*)")

    sorry_locations: list[str] = []
    sorry_count = 0

    def replacer(match: re.Match) -> str:
        nonlocal sorry_count
        sorry_count += 1
        sorry_locations.append(f"gap_{sorry_count}")
        return f"{match.group(1)}sorry -- gap_{sorry_count}\n"

    modified = sorry_pattern.sub(replacer, lean_code)

    return modified, sorry_locations
