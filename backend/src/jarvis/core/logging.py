"""Structured logging with a correlation ID threaded through `contextvars`
so a single request/task can be traced across module boundaries.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar, Token
from typing import Any

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

_CONFIGURED = False


def set_correlation_id(correlation_id: str | None) -> Token[str | None]:
    """Set the correlation ID for the current async context; returns a token
    that can be passed to `reset_correlation_id` to restore the prior value.
    """
    return _correlation_id.set(correlation_id)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


class _CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(*, level: str = "INFO", json_format: bool = False) -> None:
    """Configure the root logger. Idempotent — safe to call multiple times
    (e.g. once at app startup, once at the top of a script/test fixture).
    """
    global _CONFIGURED

    root = logging.getLogger()
    root.setLevel(level.upper())

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(stream=sys.stdout)
    if json_format:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s [%(correlation_id)s] %(message)s"
            )
        )
    handler.addFilter(_CorrelationIdFilter())
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, configuring root logging with defaults on
    first use if `configure_logging` was never called explicitly.
    """
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
