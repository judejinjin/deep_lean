"""Tests for Pydantic data models."""

from datetime import datetime, timezone

from src.models import (
    InformalProof,
    LeanCode,
    LeanResult,
    NotebookPlan,
    ProofAttempt,
    ResearchOutput,
    ResearchQuestion,
    TaskStatus,
    LiteratureResult,
)


def test_task_status_enum():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.SUCCESS == "success"


def test_research_question_defaults():
    q = ResearchQuestion(question="Test question")
    assert q.question == "Test question"
    assert q.context == ""
    assert q.source_pdfs == []


def test_lean_code_serialization():
    code = LeanCode(filename="Test.lean", source="theorem t : True := trivial")
    d = code.model_dump()
    assert d["filename"] == "Test.lean"
    assert "theorem" in d["source"]
    # Round-trip
    code2 = LeanCode(**d)
    assert code2 == code


def test_lean_result_success():
    result = LeanResult(success=True, stdout="Build successful")
    assert result.success
    assert result.errors == []


def test_lean_result_failure():
    result = LeanResult(
        success=False,
        stderr="error: type mismatch",
        errors=[{"line": 5, "message": "type mismatch"}],
    )
    assert not result.success
    assert len(result.errors) == 1


def test_proof_attempt_timestamp():
    code = LeanCode(filename="t.lean", source="sorry")
    result = LeanResult(success=False, stderr="error")
    attempt = ProofAttempt(attempt_number=1, lean_code=code, result=result)
    assert isinstance(attempt.timestamp, datetime)


def test_research_output_defaults():
    q = ResearchQuestion(question="test")
    out = ResearchOutput(question=q)
    assert not out.verified
    assert out.proof_attempts == []
    assert out.total_llm_calls == 0
    assert out.total_cost_usd == 0.0


def test_literature_result():
    lit = LiteratureResult(query="test", summary="Summary text")
    assert lit.query == "test"
    assert lit.papers == []
    assert lit.key_theorems == []


def test_informal_proof():
    proof = InformalProof(
        steps=["Step 1", "Step 2"],
        assumptions=["A1"],
        conclusion="Therefore Q.E.D.",
    )
    assert len(proof.steps) == 2
    assert proof.conclusion == "Therefore Q.E.D."


def test_notebook_plan():
    plan = NotebookPlan(
        title="Test Notebook",
        sections=[{"heading": "Intro", "type": "markdown"}],
    )
    assert plan.title == "Test Notebook"
    assert len(plan.sections) == 1
