"""
Base class for all DeepLean agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.config import settings
from src.llm import call_llm
from src.utils.logging import log


class BaseAgent(ABC):
    """Abstract base for every agent in the LangGraph pipeline."""

    name: str = "base"
    model: str = ""
    system_prompt: str = ""

    def __init__(self) -> None:
        if not self.model:
            self.model = settings.fast_model
        # Try to load system prompt from file
        prompt_path = Path(settings.prompts_dir) / f"{self.name}.md"
        if prompt_path.exists():
            self.system_prompt = prompt_path.read_text(encoding="utf-8")

    @abstractmethod
    async def run(self, state: dict) -> dict:
        """Execute the agent's logic, reading/writing the shared state."""
        ...

    async def llm(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        **kwargs,
    ) -> str:
        """Call this agent's assigned model (or an override)."""
        m = model or self.model
        # Prepend the system prompt if any
        if self.system_prompt:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *messages,
            ]
        log.info("agent_llm_call", agent=self.name, model=m)
        return await call_llm(m, messages, **kwargs)
