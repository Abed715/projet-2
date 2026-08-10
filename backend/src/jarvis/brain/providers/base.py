"""LLM provider abstraction: one interface, swappable backends.

Concrete adapters (Claude first — see README.md; OpenAI/Ollama follow the
same interface in a later phase) live alongside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Message:
    """A single turn in a conversation passed to a provider.

    `role` is `"user"` or `"assistant"` — never `"system"`; the system
    prompt is a separate argument to `LLMProvider.complete`, matching how
    every current provider's API separates the two.
    """

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class CompletionResult:
    content: str
    model: str
    stop_reason: str | None


class LLMProvider(Protocol):
    """One conversational-completion interface every provider adapter satisfies."""

    async def complete(
        self, messages: list[Message], *, system: str | None = None
    ) -> CompletionResult: ...
