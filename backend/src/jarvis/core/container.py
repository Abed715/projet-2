"""Minimal, explicit dependency-injection container.

No autowiring/magic: modules register factories under a key (usually a type),
callers resolve by the same key. `api` is the composition root that wires
concrete implementations in; everything else depends on interfaces.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from jarvis.core.exceptions import ConfigurationError

T = TypeVar("T")


class Container:
    """A registry of singleton and factory providers, keyed by type."""

    def __init__(self) -> None:
        self._factories: dict[type, Callable[[], object]] = {}
        self._singletons: dict[type, object] = {}

    def register_factory(self, key: type[T], factory: Callable[[], T]) -> None:
        """Register a provider that is called fresh on every `resolve`."""
        self._factories[key] = factory

    def register_instance(self, key: type[T], instance: T) -> None:
        """Register a pre-built singleton instance."""
        self._singletons[key] = instance

    def resolve(self, key: type[T]) -> T:
        if key in self._singletons:
            return cast(T, self._singletons[key])
        if key in self._factories:
            return cast(T, self._factories[key]())
        raise ConfigurationError(f"No provider registered for {key!r}")

    def has(self, key: type) -> bool:
        return key in self._singletons or key in self._factories
