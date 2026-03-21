"""
Append-only JSONL provenance log for full auditability.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class ProvenanceTracker:
    """Records every LLM call, tool invocation, and decision to a JSONL file."""

    def __init__(self, session_id: str, base_dir: str = "output/provenance"):
        self.log_path = Path(base_dir) / f"{session_id}.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, data: dict) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **data,
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def read_all(self) -> list[dict]:
        """Read all entries (for testing / inspection)."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
