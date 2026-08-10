"""Claude (Anthropic) adapter for the `LLMProvider` protocol.

Uses `anthropic.AsyncAnthropic`'s non-streaming `messages.create` — enough
for the short conversational replies this phase needs. Streaming and tool
use land when they're actually needed (long outputs, the tool registry
invoking domain tools).
"""

from __future__ import annotations

from typing import Any

from jarvis.brain.providers.base import CompletionResult, LLMProvider, Message

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_MAX_TOKENS = 4096


class ClaudeProvider:
    """Adapter over `anthropic.AsyncAnthropic` satisfying `LLMProvider`.

    `client` is typed as `Any` rather than the real SDK class so tests can
    substitute a lightweight double exposing only `messages.create(...)` —
    the real `AsyncAnthropic` client satisfies that shape at runtime.
    """

    def __init__(
        self,
        client: Any,
        *,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def complete(
        self, messages: list[Message], *, system: str | None = None
    ) -> CompletionResult:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system is not None:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)

        text = "".join(block.text for block in response.content if block.type == "text")
        return CompletionResult(
            content=text, model=response.model, stop_reason=response.stop_reason
        )


_claude_provider_satisfies_protocol: type[LLMProvider] = ClaudeProvider
