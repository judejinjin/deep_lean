"""Tests for configuration module."""

from src.config import Settings, settings


def test_settings_loads():
    """Settings object should instantiate with defaults."""
    assert isinstance(settings, Settings)


def test_model_fields_are_strings():
    """All model routing fields should be non-empty strings."""
    model_fields = [
        "orchestration_model",
        "reasoning_model",
        "formalization_model",
        "research_model",
        "notebook_code_model",
        "notebook_narrative_model",
        "report_model",
        "fast_model",
        "error_analysis_model",
        "fallback_coding_model",
        "cheap_model",
    ]
    for field in model_fields:
        value = getattr(settings, field)
        assert isinstance(value, str), f"{field} should be str, got {type(value)}"
        assert len(value) > 0, f"{field} should not be empty"


def test_lean_settings():
    """Lean-related settings should have sensible defaults."""
    assert settings.lean_max_retries >= 1
    assert settings.lean_timeout > 0
    assert isinstance(settings.lean_project_dir, str)


def test_path_settings():
    """Path settings should be non-empty strings."""
    assert settings.output_dir
    assert settings.reports_dir
    assert settings.notebooks_dir
    assert settings.prompts_dir
