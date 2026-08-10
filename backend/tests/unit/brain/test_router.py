import pytest

from jarvis.brain.providers.base import CompletionResult, Message
from jarvis.brain.router import LLMRouter
from jarvis.core.exceptions import ConfigurationError


class _EchoProvider:
    async def complete(
        self, messages: list[Message], *, system: str | None = None
    ) -> CompletionResult:
        return CompletionResult(content="echo", model="echo-model", stop_reason="end_turn")


def test_register_and_get() -> None:
    router = LLMRouter()
    provider = _EchoProvider()

    router.register("anthropic", provider)

    assert router.get("anthropic") is provider


def test_get_unregistered_raises() -> None:
    router = LLMRouter()

    with pytest.raises(ConfigurationError):
        router.get("openai")


def test_has() -> None:
    router = LLMRouter()
    assert router.has("anthropic") is False

    router.register("anthropic", _EchoProvider())
    assert router.has("anthropic") is True
