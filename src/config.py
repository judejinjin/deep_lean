"""
DeepLean configuration — loads .env, remaps keys for litellm, exposes typed settings.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env before anything else
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Remap our key names → litellm-expected env vars
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_KEY", "")
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_KEY", "")
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("CLAUDE_KEY", "")
os.environ["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_KEY", "")


class Settings(BaseSettings):
    """Typed, validated project settings."""

    # ── Model routing ───────────────────────────────────────────────
    orchestration_model: str = "anthropic/claude-sonnet-4-6"
    reasoning_model: str = "anthropic/claude-sonnet-4-6"
    formalization_model: str = "anthropic/claude-sonnet-4-6"
    research_model: str = "anthropic/claude-sonnet-4-6"
    notebook_code_model: str = "anthropic/claude-sonnet-4-6"
    notebook_narrative_model: str = "anthropic/claude-sonnet-4-6"
    multimodal_model: str = "anthropic/claude-sonnet-4-6"
    report_model: str = "anthropic/claude-sonnet-4-6"
    fast_model: str = "anthropic/claude-sonnet-4-6"
    error_analysis_model: str = "anthropic/claude-sonnet-4-6"
    fallback_coding_model: str = "anthropic/claude-sonnet-4-6"
    cheap_model: str = "anthropic/claude-sonnet-4-6"

    # ── Lean ────────────────────────────────────────────────────────
    lean_project_dir: str = "lean_project"
    lean_max_retries: int = 8
    lean_timeout: int = 180  # seconds per build

    # ── Paths ───────────────────────────────────────────────────────
    output_dir: str = "output"
    reports_dir: str = "output/reports"
    notebooks_dir: str = "output/notebooks"
    prompts_dir: str = "src/prompts"

    # ── Embeddings ──────────────────────────────────────────────────
    embedding_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = ".chromadb"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
