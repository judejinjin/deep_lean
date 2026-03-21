"""Tests for the Lean error parser."""

from src.utils.lean_parser import LeanError, format_for_llm, parse_lean_output


def test_parse_type_mismatch():
    stderr = """\
Proof.lean:5:4: error: type mismatch
  expected Nat
  got Int
"""
    errors = parse_lean_output(stderr)
    assert len(errors) >= 1
    assert errors[0].severity == "error"
    assert "type mismatch" in errors[0].message.lower() or errors[0].category == "type_mismatch"


def test_parse_unknown_identifier():
    stderr = """\
Proof.lean:3:8: error: unknown identifier 'foo_bar'
"""
    errors = parse_lean_output(stderr)
    assert len(errors) >= 1
    assert "unknown" in errors[0].message.lower() or errors[0].category == "unknown_identifier"


def test_parse_tactic_failed():
    stderr = """\
Proof.lean:10:2: error: tactic 'simp' failed, nested error:
  simp made no progress
"""
    errors = parse_lean_output(stderr)
    assert len(errors) >= 1


def test_parse_sorry():
    stderr = """\
Proof.lean:7:0: warning: declaration uses 'sorry'
"""
    errors = parse_lean_output(stderr)
    assert len(errors) >= 1
    sorry_errors = [e for e in errors if "sorry" in e.message.lower() or e.category == "declaration_uses_sorry"]
    assert len(sorry_errors) >= 1


def test_parse_empty_input():
    errors = parse_lean_output("")
    assert errors == []


def test_format_for_llm_empty():
    result = format_for_llm([])
    assert isinstance(result, str)


def test_format_for_llm_with_errors():
    errors = [
        LeanError(
            file="Test.lean",
            line=5,
            column=4,
            severity="error",
            message="type mismatch\n  expected Nat\n  got Int",
            category="type_mismatch",
            suggestion="Check that the expression has the correct type",
        )
    ]
    result = format_for_llm(errors)
    assert "type mismatch" in result.lower()
    assert "Test.lean" in result


def test_parse_multiple_errors():
    stderr = """\
Proof.lean:3:0: error: unknown identifier 'natPrime'
Proof.lean:5:4: error: type mismatch
  expected Bool
  got Prop
Proof.lean:8:2: error: tactic 'omega' failed
"""
    errors = parse_lean_output(stderr)
    assert len(errors) >= 2  # Should find at least 2 distinct errors
