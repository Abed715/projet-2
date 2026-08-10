import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.brain.conversation import ConversationEngine
from jarvis.brain.providers.base import CompletionResult, Message
from jarvis.brain.router import LLMRouter
from jarvis.memory.short_term import ShortTermMemory


class _RecordingProvider:
    def __init__(self, reply: str = "assistant reply") -> None:
        self.reply = reply
        self.received_messages: list[Message] | None = None
        self.received_system: str | None = None

    async def complete(
        self, messages: list[Message], *, system: str | None = None
    ) -> CompletionResult:
        self.received_messages = messages
        self.received_system = system
        return CompletionResult(content=self.reply, model="fake-model", stop_reason="end_turn")


@pytest.fixture
async def redis() -> FakeRedis:
    client = FakeRedis()
    yield client
    await client.aclose()


@pytest.fixture
def engine(redis: FakeRedis) -> tuple[ConversationEngine, LLMRouter, _RecordingProvider]:
    memory = ShortTermMemory(redis)
    router = LLMRouter()
    provider = _RecordingProvider()
    router.register("anthropic", provider)
    return ConversationEngine(memory=memory, router=router), router, provider


@pytest.mark.asyncio
async def test_respond_returns_provider_reply(
    engine: tuple[ConversationEngine, LLMRouter, _RecordingProvider],
) -> None:
    conversation_engine, _, provider = engine

    reply = await conversation_engine.respond(
        "session-1", "hello", system_prompt="be helpful", provider_name="anthropic"
    )

    assert reply == provider.reply


@pytest.mark.asyncio
async def test_respond_passes_system_prompt(
    engine: tuple[ConversationEngine, LLMRouter, _RecordingProvider],
) -> None:
    conversation_engine, _, provider = engine

    await conversation_engine.respond(
        "session-1", "hello", system_prompt="be terse", provider_name="anthropic"
    )

    assert provider.received_system == "be terse"


@pytest.mark.asyncio
async def test_respond_persists_both_turns_to_short_term_memory(
    engine: tuple[ConversationEngine, LLMRouter, _RecordingProvider], redis: FakeRedis
) -> None:
    conversation_engine, _, _ = engine
    memory = ShortTermMemory(redis)

    await conversation_engine.respond(
        "session-1", "hello", system_prompt="", provider_name="anthropic"
    )

    turns = await memory.get_turns("session-1")
    assert [(t.role, t.content) for t in turns] == [
        ("user", "hello"),
        ("assistant", "assistant reply"),
    ]


@pytest.mark.asyncio
async def test_respond_includes_prior_history_in_next_call(
    engine: tuple[ConversationEngine, LLMRouter, _RecordingProvider],
) -> None:
    conversation_engine, _, provider = engine

    await conversation_engine.respond(
        "session-1", "first", system_prompt="", provider_name="anthropic"
    )
    await conversation_engine.respond(
        "session-1", "second", system_prompt="", provider_name="anthropic"
    )

    assert provider.received_messages is not None
    contents = [m.content for m in provider.received_messages]
    assert contents == ["first", "assistant reply", "second"]


@pytest.mark.asyncio
async def test_respond_isolates_sessions(
    engine: tuple[ConversationEngine, LLMRouter, _RecordingProvider], redis: FakeRedis
) -> None:
    conversation_engine, _, _ = engine
    memory = ShortTermMemory(redis)

    await conversation_engine.respond(
        "session-a", "hi from a", system_prompt="", provider_name="anthropic"
    )
    await conversation_engine.respond(
        "session-b", "hi from b", system_prompt="", provider_name="anthropic"
    )

    turns_a = await memory.get_turns("session-a")
    assert [t.content for t in turns_a] == ["hi from a", "assistant reply"]
