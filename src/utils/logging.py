"""
Structured logging setup using structlog.
"""

from __future__ import annotations

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog with timestamp + console rendering."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )


# Initialise with defaults on import
setup_logging()

log = structlog.get_logger()
