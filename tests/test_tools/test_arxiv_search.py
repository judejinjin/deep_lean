"""Tests for arXiv search (mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.arxiv_search import search_arxiv


@pytest.mark.asyncio
async def test_search_returns_list():
    """Should return a list of dicts on success."""
    mock_paper = MagicMock()
    mock_paper.title = "Test Paper"
    mock_paper.authors = [MagicMock(name="Author A")]
    mock_paper.summary = "Abstract text"
    mock_paper.entry_id = "http://arxiv.org/abs/1234.5678"
    mock_paper.pdf_url = "http://arxiv.org/pdf/1234.5678"
    mock_paper.published = MagicMock(year=2023)
    mock_paper.categories = ["math.AG"]

    mock_client = MagicMock()
    mock_client.results.return_value = [mock_paper]

    # The import happens inside _search_sync, so we patch at the module level
    with patch.dict("sys.modules", {"arxiv": MagicMock()}) as _:
        import arxiv as mock_arxiv

        mock_arxiv.Client.return_value = mock_client
        mock_arxiv.Search.return_value = MagicMock()
        mock_arxiv.SortCriterion.Relevance = "relevance"
        results = await search_arxiv("test query", max_results=5)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["title"] == "Test Paper"
    assert results[0]["year"] == 2023


@pytest.mark.asyncio
async def test_search_handles_error():
    """Should return empty list on error."""
    # Patch _search_sync to raise an exception
    with patch(
        "src.tools.arxiv_search._search_sync",
        side_effect=Exception("search failed"),
    ):
        results = await search_arxiv("test query")
    assert isinstance(results, list)
    assert len(results) == 0
