"""
Programmatic Jupyter notebook construction using nbformat.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


class NotebookBuilder:
    """Fluent builder for .ipynb files."""

    def __init__(self, title: str):
        self.nb = new_notebook()
        self.nb.metadata["kernelspec"] = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        }
        self.nb.metadata["language_info"] = {"name": "python", "version": "3.12"}
        self.add_markdown(f"# {title}")

    # ── Cell adders ─────────────────────────────────────────────
    def add_markdown(self, content: str) -> "NotebookBuilder":
        self.nb.cells.append(new_markdown_cell(content))
        return self

    def add_code(self, source: str) -> "NotebookBuilder":
        self.nb.cells.append(new_code_cell(source))
        return self

    def add_lean_block(self, lean_source: str, verified: bool = False) -> "NotebookBuilder":
        badge = "✅ Verified" if verified else "⚠️ Unverified"
        md = f"### Lean 4 Proof {badge}\n\n```lean\n{lean_source}\n```"
        self.nb.cells.append(new_markdown_cell(md))
        return self

    def add_section(self, heading: str, body: str) -> "NotebookBuilder":
        self.add_markdown(f"## {heading}\n\n{body}")
        return self

    def add_verification_summary(
        self, steps: list[dict[str, bool | str]]
    ) -> "NotebookBuilder":
        """Add a verification badge table.

        steps: list of {"step": str, "verified": bool}
        """
        lines = ["## Verification Summary\n", "| Step | Status |", "|---|---|"]
        for s in steps:
            icon = "✅" if s.get("verified") else "⚠️"
            lines.append(f"| {s.get('step', '?')} | {icon} |")
        self.add_markdown("\n".join(lines))
        return self

    # ── Save ────────────────────────────────────────────────────
    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            nbformat.write(self.nb, f)
        return path

    @property
    def cell_count(self) -> int:
        return len(self.nb.cells)
