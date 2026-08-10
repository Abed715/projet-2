"""LLM provider router: a named registry so callers select a provider by
name (`"anthropic"`, later `"openai"`/`"ollama"`) without depending on a
concrete adapter class.
"""

from __future__ import annotations

from jarvis.brain.providers.base import LLMProvider
from jarvis.core.exceptions import ConfigurationError


class LLMRouter:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> LLMProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ConfigurationError(f"no LLM provider registered as {name!r}") from exc

    def has(self, name: str) -> bool:
        return name in self._providers
