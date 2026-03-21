"""
Research Agent — literature search and context synthesis.
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.config import settings
from src.tools.arxiv_search import search_arxiv
from src.tools.pdf_reader import extract_text
from src.tools.semantic_scholar import search_semantic_scholar
from src.utils.logging import log


class ResearcherAgent(BaseAgent):
    name = "researcher"
    model = settings.research_model

    async def run(self, state: dict) -> dict:
        """Search literature, extract PDF content, synthesise context."""
        question = state.get("question", "")
        log.info("researcher_start", question=question[:100])

        # 1. Search arXiv + Semantic Scholar in parallel
        arxiv_papers = await search_arxiv(question, max_results=5)
        ss_papers = await search_semantic_scholar(question, max_results=5)

        # 2. Extract text from provided PDFs
        pdf_texts: list[str] = []
        for pdf_path in state.get("source_pdfs", []):
            text = await extract_text(pdf_path)
            if text:
                pdf_texts.append(f"--- {pdf_path} ---\n{text[:5000]}")

        # 3. Build context for synthesis
        papers_text = self._format_papers(arxiv_papers + ss_papers)
        pdfs_text = "\n\n".join(pdf_texts) if pdf_texts else "(No PDFs provided)"

        # 4. Synthesise with LLM
        context = await self.llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Research question: {question}\n\n"
                        f"## Papers Found\n{papers_text}\n\n"
                        f"## Source PDFs\n{pdfs_text}\n\n"
                        f"Synthesise a comprehensive literature review with key theorems, "
                        f"definitions, and relevant Mathlib formalizations."
                    ),
                }
            ],
            max_tokens=4096,
        )

        log.info("researcher_done", context_length=len(context))

        return {
            "research_context": context,
            "papers": arxiv_papers + ss_papers,
        }

    @staticmethod
    def _format_papers(papers: list[dict]) -> str:
        """Format papers for the LLM prompt."""
        if not papers:
            return "(No papers found)"
        lines: list[str] = []
        for i, p in enumerate(papers, 1):
            authors = ", ".join(p.get("authors", [])[:3])
            abstract = (p.get("abstract") or "")[:300]
            lines.append(
                f"{i}. **{p.get('title', 'Untitled')}** ({p.get('year', '?')})\n"
                f"   Authors: {authors}\n"
                f"   Abstract: {abstract}...\n"
            )
        return "\n".join(lines)
