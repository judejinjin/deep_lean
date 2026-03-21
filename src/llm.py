"""
Unified LLM interface via litellm.

- Model routing (pick model by task role)
- Automatic fallback on failure / rate-limit
- Cost tracking per session
- Structured output via Pydantic
"""

from __future__ import annotations

import json
import time
from typing import Any

import litellm
from litellm import acompletion

from src.config import settings
from src.utils.logging import log

# Suppress litellm's verbose logging
litellm.suppress_debug_info = True
litellm.set_verbose = False

# ── Fallback chains ─────────────────────────────────────────────────
FALLBACK_CHAINS: dict[str, list[str]] = {
    settings.orchestration_model: [settings.fast_model],
    settings.reasoning_model: [settings.research_model],
    settings.formalization_model: [settings.fallback_coding_model],
    settings.research_model: [settings.multimodal_model],
    settings.notebook_code_model: [settings.fallback_coding_model],
    settings.report_model: [settings.multimodal_model],
}

# ── Session-level cost tracker ──────────────────────────────────────
_session_cost: float = 0.0
_session_calls: int = 0


def get_session_stats() -> dict[str, Any]:
    return {"total_calls": _session_calls, "total_cost_usd": round(_session_cost, 6)}


def reset_session_stats() -> None:
    global _session_cost, _session_calls
    _session_cost = 0.0
    _session_calls = 0


# ── Core call function ──────────────────────────────────────────────
async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    response_format: type | None = None,
    **kwargs: Any,
) -> str:
    """
    Call an LLM with automatic fallback on error.

    Parameters
    ----------
    model : litellm model string, e.g. "anthropic/claude-sonnet-4-6"
    messages : OpenAI-style message list
    response_format : optional Pydantic model → request JSON and validate
    """
    global _session_cost, _session_calls

    models_to_try = [model, *FALLBACK_CHAINS.get(model, [])]

    last_error: Exception | None = None
    for m in models_to_try:
        try:
            t0 = time.monotonic()
            resp = await acompletion(
                model=m,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            elapsed = time.monotonic() - t0

            content: str = resp.choices[0].message.content or ""
            _session_calls += 1

            # Cost tracking
            try:
                cost = litellm.completion_cost(completion_response=resp)
                _session_cost += cost
            except Exception:
                cost = 0.0

            log.info(
                "llm_call",
                model=m,
                tokens_in=resp.usage.prompt_tokens if resp.usage else 0,
                tokens_out=resp.usage.completion_tokens if resp.usage else 0,
                cost_usd=round(cost, 6),
                elapsed_s=round(elapsed, 2),
            )

            # Structured output: parse JSON → validate with Pydantic
            if response_format is not None:
                try:
                    data = json.loads(content)
                    return response_format(**data).model_dump()  # type: ignore[return-value]
                except (json.JSONDecodeError, Exception) as e:
                    log.warning("structured_output_parse_failed", error=str(e))
                    return content

            return content

        except Exception as e:
            last_error = e
            log.warning("llm_call_failed", model=m, error=str(e))
            continue

    raise RuntimeError(
        f"All models failed for {model}: {last_error}"
    )


def call_llm_sync(
    model: str,
    messages: list[dict[str, str]],
    **kwargs: Any,
) -> str:
    """Synchronous wrapper around call_llm."""
    import asyncio

    return asyncio.run(call_llm(model, messages, **kwargs))
