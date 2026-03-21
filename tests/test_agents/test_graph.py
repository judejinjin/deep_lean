"""Tests for the LangGraph agent graph."""

import pytest

from src.agents.graph import build_graph, create_initial_state, route_after_verification
from src.config import settings


def test_create_initial_state():
    """Should create a state dict with all required keys."""
    state = create_initial_state("Test question")
    assert state["question"] == "Test question"
    assert state["lean_verified"] is False
    assert state["attempt_count"] == 0
    assert isinstance(state["session_id"], str)


def test_create_initial_state_with_pdfs():
    """Should include source PDFs if provided."""
    state = create_initial_state("Q", source_pdfs=["a.pdf", "b.pdf"])
    assert state["source_pdfs"] == ["a.pdf", "b.pdf"]


def test_route_accept():
    """Should route to 'accept' when verified."""
    state = {"lean_verified": True, "attempt_count": 1}
    assert route_after_verification(state) == "accept"


def test_route_retry():
    """Should route to 'retry' when not verified and under limit."""
    state = {"lean_verified": False, "attempt_count": 1}
    assert route_after_verification(state) == "retry"


def test_route_give_up():
    """Should route to 'give_up' when at max retries."""
    state = {"lean_verified": False, "attempt_count": settings.lean_max_retries}
    assert route_after_verification(state) == "give_up"


def test_build_graph():
    """Should compile the graph without error."""
    graph = build_graph()
    assert graph is not None
