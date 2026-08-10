import pytest

from jarvis.brain.providers.base import Message
from jarvis.brain.providers.claude import ClaudeProvider


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeThinkingBlock:
    def __init__(self) -> None:
        self.type = "thinking"
        self.thinking = "reasoning..."


class _FakeResponse:
    def __init__(self, content: list[object], model: str, stop_reason: str | None) -> None:
        self.content = content
        self.model = model
        self.stop_reason = stop_reason


class _FakeMessagesEndpoint:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.last_kwargs: dict[str, object] | None = None

    async def create(self, **kwargs: object) -> _FakeResponse:
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.messages = _FakeMessagesEndpoint(response)


@pytest.mark.asyncio
async def test_complete_returns_text_from_response() -> None:
    response = _FakeResponse(
        content=[_FakeTextBlock("Hello there")], model="claude-opus-5", stop_reason="end_turn"
    )
    client = _FakeAnthropicClient(response)
    provider = ClaudeProvider(client)

    result = await provider.complete([Message(role="user", content="hi")])

    assert result.content == "Hello there"
    assert result.model == "claude-opus-5"
    assert result.stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_complete_ignores_non_text_blocks() -> None:
    response = _FakeResponse(
        content=[_FakeThinkingBlock(), _FakeTextBlock("answer")],
        model="claude-opus-5",
        stop_reason="end_turn",
    )
    client = _FakeAnthropicClient(response)
    provider = ClaudeProvider(client)

    result = await provider.complete([Message(role="user", content="hi")])

    assert result.content == "answer"


@pytest.mark.asyncio
async def test_complete_sends_correct_request_shape() -> None:
    response = _FakeResponse(content=[_FakeTextBlock("ok")], model="m", stop_reason="end_turn")
    client = _FakeAnthropicClient(response)
    provider = ClaudeProvider(client, model="claude-sonnet-5", max_tokens=1234)

    await provider.complete(
        [Message(role="user", content="hi"), Message(role="assistant", content="hello")],
        system="be terse",
    )

    kwargs = client.messages.last_kwargs
    assert kwargs is not None
    assert kwargs["model"] == "claude-sonnet-5"
    assert kwargs["max_tokens"] == 1234
    assert kwargs["system"] == "be terse"
    assert kwargs["messages"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


@pytest.mark.asyncio
async def test_complete_omits_system_when_not_given() -> None:
    response = _FakeResponse(content=[_FakeTextBlock("ok")], model="m", stop_reason="end_turn")
    client = _FakeAnthropicClient(response)
    provider = ClaudeProvider(client)

    await provider.complete([Message(role="user", content="hi")])

    assert "system" not in (client.messages.last_kwargs or {})


@pytest.mark.asyncio
async def test_default_model_and_max_tokens() -> None:
    response = _FakeResponse(content=[_FakeTextBlock("ok")], model="m", stop_reason="end_turn")
    client = _FakeAnthropicClient(response)
    provider = ClaudeProvider(client)

    await provider.complete([Message(role="user", content="hi")])

    kwargs = client.messages.last_kwargs
    assert kwargs is not None
    assert kwargs["model"] == "claude-opus-5"
    assert kwargs["max_tokens"] == 4096
