"""
LangGraph state definition and graph builder for the DeepLean multi-agent pipeline.

Pipeline: orchestrator → researcher → formalizer → verifier → (retry?) → reporter → notebook
"""

from __future__ import annotations

import operator
import uuid
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from src.config import settings
from src.utils.logging import log


# ── State definition ────────────────────────────────────────────────
class AgentState(TypedDict, total=False):
    """Shared state flowing through the LangGraph.

    All fields use the last-writer-wins merge strategy (operator.or_
    is not needed — LangGraph merges TypedDict keys by default).
    """

    question: str
    source_pdfs: list[str]
    session_id: str
    research_plan: str
    research_context: str
    papers: list[dict]
    informal_proof: str
    lean_code: str
    lean_errors: str
    lean_verified: bool
    lean_result: dict
    attempt_count: int
    report_md: str
    report_path: str
    notebook_path: str


# ── Node functions ──────────────────────────────────────────────────
async def orchestrator_node(state: dict) -> dict:
    from src.agents.orchestrator import OrchestratorAgent

    agent = OrchestratorAgent()
    return await agent.run(state)


async def researcher_node(state: dict) -> dict:
    from src.agents.researcher import ResearcherAgent

    agent = ResearcherAgent()
    return await agent.run(state)


async def formalizer_node(state: dict) -> dict:
    from src.agents.formalizer import FormalizerAgent

    agent = FormalizerAgent()
    return await agent.run(state)


async def verifier_node(state: dict) -> dict:
    from src.agents.verifier import VerifierAgent

    agent = VerifierAgent()
    return await agent.run(state)


async def reporter_node(state: dict) -> dict:
    from src.agents.reporter import ReporterAgent

    agent = ReporterAgent()
    return await agent.run(state)


async def notebook_node(state: dict) -> dict:
    from src.agents.notebook_agent import NotebookAgent

    agent = NotebookAgent()
    return await agent.run(state)


# ── Routing logic ───────────────────────────────────────────────────
def route_after_verification(state: dict) -> str:
    """Decide what happens after verification."""
    if state.get("lean_verified"):
        log.info("route", decision="accept")
        return "accept"
    if state.get("attempt_count", 0) >= settings.lean_max_retries:
        log.info("route", decision="give_up", attempts=state.get("attempt_count"))
        return "give_up"
    log.info("route", decision="retry", attempts=state.get("attempt_count"))
    return "retry"


# ── Graph builder ───────────────────────────────────────────────────
def build_graph() -> Any:
    """Build and compile the LangGraph multi-agent pipeline."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("formalizer", formalizer_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("reporter", reporter_node)
    graph.add_node("notebook_gen", notebook_node)

    # Define edges
    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "researcher")
    graph.add_edge("researcher", "formalizer")
    graph.add_edge("formalizer", "verifier")

    # Conditional routing after verification
    graph.add_conditional_edges(
        "verifier",
        route_after_verification,
        {
            "retry": "formalizer",
            "accept": "reporter",
            "give_up": "reporter",
        },
    )

    graph.add_edge("reporter", "notebook_gen")
    graph.add_edge("notebook_gen", END)

    return graph.compile()


def create_initial_state(
    question: str,
    source_pdfs: list[str] | None = None,
    session_id: str | None = None,
) -> dict:
    """Create a fresh agent state dict for a new research session."""
    return {
        "question": question,
        "source_pdfs": source_pdfs or [],
        "session_id": session_id or uuid.uuid4().hex[:8],
        "research_plan": "",
        "research_context": "",
        "papers": [],
        "informal_proof": "",
        "lean_code": "",
        "lean_errors": "",
        "lean_verified": False,
        "lean_result": {},
        "attempt_count": 0,
        "report_md": "",
        "report_path": "",
        "notebook_path": "",
    }
