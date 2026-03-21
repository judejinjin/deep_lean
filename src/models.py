"""
Pydantic data models for all data flowing through the DeepLean system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class ResearchQuestion(BaseModel):
    """The user's input query."""

    question: str
    context: str = ""
    source_pdfs: list[str] = Field(default_factory=list)


class LiteratureResult(BaseModel):
    """Output from the Research Agent."""

    query: str
    papers: list[dict] = Field(default_factory=list)
    key_theorems: list[str] = Field(default_factory=list)
    summary: str = ""


class InformalProof(BaseModel):
    """A natural-language mathematical argument."""

    steps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    conclusion: str = ""


class LeanCode(BaseModel):
    """Generated Lean 4 source code."""

    filename: str
    source: str
    imports: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)


class LeanResult(BaseModel):
    """Output from running lake build."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    errors: list[dict] = Field(default_factory=list)
    build_time_seconds: float = 0.0


class ProofAttempt(BaseModel):
    """One cycle of formalize → verify."""

    attempt_number: int
    lean_code: LeanCode
    result: LeanResult
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotebookPlan(BaseModel):
    """Structure plan for a generated notebook."""

    title: str
    sections: list[dict] = Field(default_factory=list)
    visualization_specs: list[dict] = Field(default_factory=list)


class ResearchOutput(BaseModel):
    """The complete output of a research session."""

    question: ResearchQuestion
    literature: LiteratureResult | None = None
    informal_proof: InformalProof | None = None
    proof_attempts: list[ProofAttempt] = Field(default_factory=list)
    final_lean_code: LeanCode | None = None
    verified: bool = False
    report_path: str | None = None
    notebook_path: str | None = None
    total_llm_calls: int = 0
    total_cost_usd: float = 0.0
