"""Tests for the Mathlib index (mocked ChromaDB)."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.mathlib_index import MathlibIndex


@pytest.fixture
def index(tmp_path):
    """Create a MathlibIndex with a temp directory."""
    return MathlibIndex(persist_dir=str(tmp_path / "chromadb"))


def test_index_initializes(index):
    """Should create a MathlibIndex without error."""
    assert index.count == 0


@pytest.mark.asyncio
async def test_search_empty_index(index):
    """Search on empty index should return empty list."""
    results = await index.search("continuous function")
    assert results == []


def test_extract_declarations(index, tmp_path):
    """Should extract theorem/lemma declarations from .lean files."""
    lean_dir = tmp_path / "mathlib"
    lean_dir.mkdir()
    (lean_dir / "Test.lean").write_text(
        """\
/-- A test theorem about naturals. -/
theorem test_theorem (n : ℕ) : 0 ≤ n := by omega

lemma helper_lemma : True := trivial

def some_function (x : ℕ) : ℕ := x + 1
"""
    )
    decls = index._extract_declarations(lean_dir)
    assert len(decls) == 3
    names = [d["name"] for d in decls]
    assert "test_theorem" in names
    assert "helper_lemma" in names
    assert "some_function" in names
