"""jarvis.core — foundation primitives every other module depends on.

See README.md for the full public interface and design notes.
"""

from jarvis.core.container import Container
from jarvis.core.events import Event, EventBus, InMemoryEventBus
from jarvis.core.exceptions import (
    ConfigurationError,
    JarvisError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from jarvis.core.logging import configure_logging, get_correlation_id, get_logger
from jarvis.core.settings import Settings, get_settings

__all__ = [
    "Container",
    "Event",
    "EventBus",
    "InMemoryEventBus",
    "ConfigurationError",
    "JarvisError",
    "NotFoundError",
    "PermissionDeniedError",
    "ValidationError",
    "configure_logging",
    "get_correlation_id",
    "get_logger",
    "Settings",
    "get_settings",
]
