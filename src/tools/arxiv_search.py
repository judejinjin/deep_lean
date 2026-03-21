"""
arXiv API wrapper for literature search.
"""

from __future__ import annotations

import asyncio
from typing import Any

from src.utils.logging import log


def _search_sync(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Synchronous arXiv search using the arxiv package."""
    import arxiv

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results: list[dict[str, Any]] = []
    for paper in client.results(search):
        results.append(
            {
                "title": paper.title,
                "authors": [a.name for a in paper.authors],
                "abstract": paper.summary,
                "url": paper.entry_id,
                "pdf_url": paper.pdf_url,
                "year": paper.published.year if paper.published else None,
                "categories": paper.categories,
            }
        )
    return results


async def search_arxiv(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Async wrapper around arXiv search."""
    log.info("arxiv_search", query=query, max_results=max_results)
    try:
        results = await asyncio.to_thread(_search_sync, query, max_results)
        log.info("arxiv_results", count=len(results))
        return results
    except Exception as e:
        log.warning("arxiv_search_failed", error=str(e))
        return []
