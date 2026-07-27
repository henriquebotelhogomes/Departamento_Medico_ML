"""Structured logging configuration (structlog) + request-id context."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

# Correlation id available to every log line within a request.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def _add_request_id(_logger: object, _name: str, event_dict: dict) -> dict:
    rid = request_id_var.get()
    if rid is not None:
        event_dict["request_id"] = rid
    return event_dict


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """Configure structlog + stdlib logging once at startup."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_request_id,
        structlog.processors.StackInfoRenderer(),
    ]

    renderer = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy...) through a plain handler.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
