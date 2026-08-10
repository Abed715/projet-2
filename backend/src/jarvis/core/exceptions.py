"""Base exception hierarchy. Module-specific errors should subclass these so
the API layer can map them to HTTP responses in one place.
"""

from __future__ import annotations


class JarvisError(Exception):
    """Base class for all errors raised intentionally by JARVIS code."""

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(JarvisError):
    """Raised when configuration is missing or invalid at boot/use time."""


class NotFoundError(JarvisError):
    """Raised when a requested resource does not exist."""


class ValidationError(JarvisError):
    """Raised when input fails domain validation (distinct from Pydantic's)."""


class PermissionDeniedError(JarvisError):
    """Raised by the security layer when an action is not permitted."""
