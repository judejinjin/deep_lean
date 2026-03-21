"""Tests for the Notebook builder."""

import json
from pathlib import Path

import nbformat
import pytest

from src.tools.notebook_builder import NotebookBuilder


@pytest.fixture
def builder():
    return NotebookBuilder(title="Test Notebook")


def test_initial_state(builder):
    """New notebook should have title cell."""
    assert builder.cell_count == 1  # Title markdown cell
    assert builder.nb.cells[0].cell_type == "markdown"
    assert "Test Notebook" in builder.nb.cells[0].source


def test_add_markdown(builder):
    builder.add_markdown("## Section")
    assert builder.cell_count == 2
    assert builder.nb.cells[1].cell_type == "markdown"


def test_add_code(builder):
    builder.add_code("print('hello')")
    assert builder.cell_count == 2
    assert builder.nb.cells[1].cell_type == "code"
    assert builder.nb.cells[1].source == "print('hello')"


def test_add_lean_block_verified(builder):
    builder.add_lean_block("theorem t : True := trivial", verified=True)
    assert builder.cell_count == 2
    cell = builder.nb.cells[1]
    assert cell.cell_type == "markdown"
    assert "✅ Verified" in cell.source
    assert "```lean" in cell.source


def test_add_lean_block_unverified(builder):
    builder.add_lean_block("sorry", verified=False)
    cell = builder.nb.cells[1]
    assert "⚠️ Unverified" in cell.source


def test_fluent_api(builder):
    """Builder methods should return self for chaining."""
    result = builder.add_markdown("md").add_code("code").add_section("H", "B")
    assert result is builder


def test_save(builder, tmp_path):
    builder.add_code("x = 1")
    path = builder.save(tmp_path / "test.ipynb")
    assert path.exists()

    # Should be valid nbformat
    with open(path) as f:
        nb = nbformat.read(f, as_version=4)
    assert len(nb.cells) == 2


def test_save_creates_directories(builder, tmp_path):
    path = builder.save(tmp_path / "deep" / "dir" / "test.ipynb")
    assert path.exists()


def test_verification_summary(builder):
    steps = [
        {"step": "Search", "verified": True},
        {"step": "Lean build", "verified": False},
    ]
    builder.add_verification_summary(steps)
    cell = builder.nb.cells[-1]
    assert "✅" in cell.source
    assert "⚠️" in cell.source
    assert "Search" in cell.source
