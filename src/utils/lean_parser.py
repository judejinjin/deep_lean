"""
Parse Lean 4 compiler output into structured, LLM-friendly feedback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class LeanError:
    """A single parsed Lean compiler diagnostic."""

    file: str = ""
    line: int = 0
    column: int = 0
    severity: str = "error"  # error | warning | info
    message: str = ""
    category: str = "unknown"
    suggestion: str = ""


# ── Error category patterns ─────────────────────────────────────
ERROR_PATTERNS: dict[str, re.Pattern[str]] = {
    "type_mismatch": re.compile(r"type mismatch", re.IGNORECASE),
    "unknown_identifier": re.compile(r"unknown identifier '(.+?)'"),
    "unknown_constant": re.compile(r"unknown constant '(.+?)'"),
    "tactic_failed": re.compile(r"tactic '(.+?)' failed"),
    "declaration_uses_sorry": re.compile(r"declaration uses 'sorry'"),
    "missing_import": re.compile(r"unknown namespace '(.+?)'"),
    "expected_token": re.compile(r"expected '(.+?)'"),
    "function_expected": re.compile(r"function expected"),
    "application_type_mismatch": re.compile(r"application type mismatch"),
    "unused_variable": re.compile(r"unused variable"),
}

# Pattern: file:line:col: severity: message
_DIAG_RE = re.compile(
    r"^(.+?):(\d+):(\d+):\s*(error|warning|info):\s*(.*)", re.MULTILINE
)


def _classify(message: str) -> str:
    """Classify an error message into a category."""
    for cat, pat in ERROR_PATTERNS.items():
        if pat.search(message):
            return cat
    return "unknown"


def _suggest(category: str, message: str) -> str:
    """Generate a brief repair hint based on category."""
    hints = {
        "type_mismatch": "Check the expected vs. actual types. You may need a coercion or different lemma.",
        "unknown_identifier": "The identifier is not in scope. Check spelling or add the correct import.",
        "unknown_constant": "This constant is not defined. Check Mathlib imports.",
        "tactic_failed": "The tactic could not close the goal. Try a different tactic or simplify the goal first.",
        "declaration_uses_sorry": "Replace 'sorry' with an actual proof term or tactic.",
        "missing_import": "Add the missing import at the top of the file.",
        "expected_token": "Syntax error. Check for missing parentheses, commas, or keywords.",
        "function_expected": "You're applying something that isn't a function. Check the expression type.",
        "application_type_mismatch": "The arguments don't match the function's type signature.",
        "unused_variable": "Remove or use the unused binding (this is a warning).",
    }
    return hints.get(category, "Review the error message and adjust the code accordingly.")


def parse_lean_output(stderr: str) -> list[LeanError]:
    """Parse raw Lean stderr into a list of structured errors."""
    errors: list[LeanError] = []
    # Try structured pattern first
    for m in _DIAG_RE.finditer(stderr):
        msg = m.group(5).strip()
        cat = _classify(msg)
        errors.append(
            LeanError(
                file=m.group(1),
                line=int(m.group(2)),
                column=int(m.group(3)),
                severity=m.group(4),
                message=msg,
                category=cat,
                suggestion=_suggest(cat, msg),
            )
        )

    # If no structured matches but stderr has content, treat whole thing as one error
    if not errors and stderr.strip():
        cat = _classify(stderr)
        errors.append(
            LeanError(
                message=stderr.strip(),
                category=cat,
                suggestion=_suggest(cat, stderr),
            )
        )

    return errors


def format_for_llm(errors: list[LeanError]) -> str:
    """Format errors as a clear text section for the Formalization Agent to consume."""
    if not errors:
        return "No errors."

    lines = [f"Found {len(errors)} error(s):\n"]
    for i, e in enumerate(errors, 1):
        loc = f"{e.file}:{e.line}:{e.column}" if e.file else "unknown location"
        lines.append(f"  Error {i} [{e.category}] at {loc}")
        lines.append(f"    Message: {e.message}")
        lines.append(f"    Hint: {e.suggestion}")
        lines.append("")
    return "\n".join(lines)
