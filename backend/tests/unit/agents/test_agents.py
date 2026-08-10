import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.agents import create_coordinator, create_planner, create_reasoning_agent
from jarvis.agents.base import Agent
from jarvis.brain.conversation import ConversationEngine
from jarvis.brain.providers.base import CompletionResult, Message
from jarvis.brain.router import LLMRouter
from jarvis.memory.short_term import ShortTermMemory


class _RecordingProvider:
    def __init__(self) -> None:
        self.received_system: str | None = None

    async def complete(
        self, messages: list[Message], *, system: str | None = None
    ) -> CompletionResult:
        self.received_system = system
        return CompletionResult(content="reply", model="fake", stop_reason="end_turn")


@pytest.fixture
async def redis() -> FakeRedis:
    client = FakeRedis()
    yield client
    await client.aclose()


@pytest.fixture
def wired(redis: FakeRedis) -> tuple[ConversationEngine, _RecordingProvider]:
    memory = ShortTermMemory(redis)
    router = LLMRouter()
    provider = _RecordingProvider()
    router.register("anthropic", provider)
    return ConversationEngine(memory=memory, router=router), provider


@pytest.mark.asyncio
async def test_coordinator_responds(wired: tuple[ConversationEngine, _RecordingProvider]) -> None:
    engine, _ = wired
    coordinator = create_coordinator(engine)

    reply = await coordinator.respond("s1", "hello")

    assert reply.content == "reply"
    assert coordinator.name == "coordinator"


@pytest.mark.asyncio
async def test_coordinator_uses_its_own_system_prompt(
    wired: tuple[ConversationEngine, _RecordingProvider],
) -> None:
    engine, provider = wired
    coordinator = create_coordinator(engine)

    await coordinator.respond("s1", "hello")

    assert provider.received_system is not None
    assert "JARVIS" in provider.received_system


@pytest.mark.asyncio
async def test_planner_and_reasoning_have_distinct_prompts(
    wired: tuple[ConversationEngine, _RecordingProvider],
) -> None:
    engine, provider = wired
    planner = create_planner(engine)
    await planner.respond("s1", "goal")
    planner_prompt = provider.received_system

    reasoning = create_reasoning_agent(engine)
    await reasoning.respond("s2", "question")
    reasoning_prompt = provider.received_system

    assert planner.name == "planner"
    assert reasoning.name == "reasoning"
    assert planner_prompt != reasoning_prompt


@pytest.mark.asyncio
async def test_agent_respond_returns_agent_reply_type(
    wired: tuple[ConversationEngine, _RecordingProvider],
) -> None:
    engine, _ = wired
    agent = Agent(
        name="custom", system_prompt="be custom", engine=engine, provider_name="anthropic"
    )

    reply = await agent.respond("s1", "hi")

    assert reply.content == "reply"
