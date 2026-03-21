"""
Notebook Generator Agent — builds interactive Jupyter notebooks from research outputs.

Uses a two-phase approach:
1. Plan the notebook structure (narrative model)
2. Generate code cells (code model)
"""

from __future__ import annotations

import uuid
from pathlib import Path

from src.agents.base import BaseAgent
from src.config import settings
from src.llm import call_llm
from src.tools.notebook_builder import NotebookBuilder
from src.utils.logging import log


class NotebookAgent(BaseAgent):
    name = "notebook_agent"
    model = settings.notebook_narrative_model

    async def run(self, state: dict) -> dict:
        """Generate a complete Jupyter notebook from the research state."""
        question = state.get("question", "")
        log.info("notebook_agent_start", question=question[:80])

        session_id = state.get("session_id", uuid.uuid4().hex[:8])

        # Phase 1: Plan notebook structure
        plan = await self._plan_notebook(state)

        # Phase 2: Build the notebook
        nb = NotebookBuilder(title=f"DeepLean: {question[:60]}")

        # Overview section
        nb.add_section("Overview", self._build_overview(state))

        # Literature review section
        if state.get("research_context"):
            nb.add_section("Literature Review", state["research_context"][:3000])

        # Generate and add code cells for symbolic computation
        code_cells = await self._generate_code_cells(state)
        if code_cells:
            nb.add_markdown("## Symbolic Computations")
            for cell in code_cells:
                if cell.get("explanation"):
                    nb.add_markdown(cell["explanation"])
                nb.add_code(cell["code"])

        # Add Lean proof block
        lean_code = state.get("lean_code", "")
        if lean_code:
            nb.add_lean_block(lean_code, verified=state.get("lean_verified", False))

        # Add verification summary
        attempts = state.get("attempt_count", 0)
        verified = state.get("lean_verified", False)
        nb.add_verification_summary(
            [
                {"step": "Literature search", "verified": bool(state.get("research_context"))},
                {"step": "Lean formalization", "verified": bool(lean_code)},
                {"step": "Lean compilation", "verified": verified},
                {"step": f"Attempts used: {attempts}/{settings.lean_max_retries}", "verified": verified},
            ]
        )

        # Conclusion
        nb.add_section("Conclusion", self._build_conclusion(state))

        # Save
        path = Path(settings.notebooks_dir) / f"notebook_{session_id}.ipynb"
        nb.save(path)

        log.info("notebook_agent_done", path=str(path), cells=nb.cell_count)

        return {"notebook_path": str(path)}

    async def _plan_notebook(self, state: dict) -> dict:
        """Plan the notebook structure using the narrative model."""
        plan_text = await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Plan a Jupyter notebook structure for this research:\n\n"
                        f"**Question:** {state.get('question', '')}\n\n"
                        f"**Verified:** {state.get('lean_verified', False)}\n\n"
                        f"List the sections with: heading, type (markdown/code/lean), "
                        f"and brief description of content."
                    ),
                }
            ],
            max_tokens=2048,
        )
        return {"plan_text": plan_text}

    async def _generate_code_cells(self, state: dict) -> list[dict[str, str]]:
        """Generate Python code cells for symbolic computation and visualization."""
        question = state.get("question", "")
        context = state.get("research_context", "")[:2000]

        response = await call_llm(
            settings.notebook_code_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python code generator for Jupyter notebooks. "
                        "Generate self-contained code cells that use SymPy, NumPy, and Matplotlib. "
                        "Each cell should be independently runnable. "
                        "Return a JSON array of objects with 'explanation' and 'code' keys. "
                        "Keep code cells focused and short (under 30 lines each)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate 2-4 Python code cells for this research topic:\n\n"
                        f"**Question:** {question}\n\n"
                        f"**Context:** {context}\n\n"
                        f"Include: imports, symbolic derivation with SymPy, and a visualization."
                    ),
                },
            ],
            max_tokens=4096,
        )

        return self._parse_code_cells(response)

    @staticmethod
    def _parse_code_cells(response: str) -> list[dict[str, str]]:
        """Parse LLM response into code cell dicts."""
        import json
        import re

        # Try direct JSON parse
        try:
            cells = json.loads(response)
            if isinstance(cells, list):
                return [
                    {"explanation": c.get("explanation", ""), "code": c.get("code", "")}
                    for c in cells
                    if c.get("code")
                ]
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown fence
        m = re.search(r"```(?:json)?\s*\n(\[.*?\])\s*\n```", response, re.DOTALL)
        if m:
            try:
                cells = json.loads(m.group(1))
                if isinstance(cells, list):
                    return [
                        {"explanation": c.get("explanation", ""), "code": c.get("code", "")}
                        for c in cells
                        if c.get("code")
                    ]
            except json.JSONDecodeError:
                pass

        # Fallback: extract python code blocks
        code_blocks = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
        return [{"explanation": "", "code": block.strip()} for block in code_blocks if block.strip()]

    @staticmethod
    def _build_overview(state: dict) -> str:
        """Build the overview section text."""
        question = state.get("question", "")
        verified = state.get("lean_verified", False)
        status = "✅ Verified" if verified else "⚠️ Not fully verified"
        return (
            f"**Research Question:** {question}\n\n"
            f"**Verification Status:** {status}\n\n"
            f"This notebook presents the automated research output from the DeepLean system, "
            f"including literature review, symbolic computations, and formal Lean 4 proofs."
        )

    @staticmethod
    def _build_conclusion(state: dict) -> str:
        """Build the conclusion section text."""
        verified = state.get("lean_verified", False)
        attempts = state.get("attempt_count", 0)

        if verified:
            return (
                f"The proof was successfully verified by the Lean 4 compiler after "
                f"{attempts} attempt(s). The formalization confirms the mathematical "
                f"correctness of the result."
            )
        return (
            f"The proof could not be fully verified after {attempts} attempt(s). "
            f"Further work may be needed to complete the formalization, possibly "
            f"by decomposing the proof into smaller lemmas or consulting Mathlib documentation."
        )
