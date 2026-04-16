"""
Structured logging setup using structlog.
Call configure_logging() once at startup; then use get_logger() everywhere.
"""

from __future__ import annotations

import logging
import sys

import structlog

from sync.config import settings


def configure_logging() -> None:
    """Configure structlog for the process. Call once at process start."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    def _add_logger_name(logger: object, method: str, event_dict: dict) -> dict:
        name = getattr(logger, "name", None)
        if name:
            event_dict["logger"] = name
        return event_dict

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        _add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    for noisy in ("httpx", "httpcore", "boto3", "botocore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a bound structlog logger with the given name."""
    return structlog.get_logger(name)
