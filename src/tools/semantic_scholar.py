"""
Semantic Scholar API wrapper using httpx (more reliable than the package).
"""

from __future__ import annotations

from typing import Any

import httpx

from src.utils.logging import log

BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,authors,abstract,url,year,citationCount,externalIds"


async def search_semantic_scholar(
    query: str, max_results: int = 10
) -> list[dict[str, Any]]:
    """Search Semantic Scholar for papers matching `query`."""
    log.info("semantic_scholar_search", query=query, max_results=max_results)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{BASE_URL}/paper/search",
                params={
                    "query": query,
                    "limit": min(max_results, 100),
                    "fields": FIELDS,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        papers: list[dict[str, Any]] = []
        for item in data.get("data", []):
            papers.append(
                {
                    "title": item.get("title", ""),
                    "authors": [
                        a.get("name", "") for a in (item.get("authors") or [])
                    ],
                    "abstract": item.get("abstract", ""),
                    "url": item.get("url", ""),
                    "year": item.get("year"),
                    "citation_count": item.get("citationCount", 0),
                    "external_ids": item.get("externalIds", {}),
                }
            )
        log.info("semantic_scholar_results", count=len(papers))
        return papers
    except Exception as e:
        log.warning("semantic_scholar_search_failed", error=str(e))
        return []
