"""Internal event bus interface.

Domain modules publish events (e.g. `MemoryCandidate`) instead of calling
each other directly. Phase 0 ships an in-memory implementation sufficient for
a single-process deployment; a Redis-backed implementation lands in Phase 1
behind the same `EventBus` protocol.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

Handler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Event:
    """A single event on the bus."""

    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus(Protocol):
    """Publish/subscribe interface every event bus implementation satisfies."""

    async def publish(self, event: Event) -> None: ...

    def subscribe(self, topic: str, handler: Handler) -> None: ...


class InMemoryEventBus:
    """Simple asyncio-based pub/sub bus for single-process deployments.

    Handler exceptions are logged and do not interrupt other subscribers or
    the publisher — a misbehaving consumer must not take down the producer.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = {}

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    async def publish(self, event: Event) -> None:
        handlers = self._subscribers.get(event.topic, [])
        if not handlers:
            return
        results = await asyncio.gather(
            *(handler(event) for handler in handlers), return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                from jarvis.core.logging import get_logger

                get_logger(__name__).exception(
                    "event handler failed for topic=%s", event.topic, exc_info=result
                )
