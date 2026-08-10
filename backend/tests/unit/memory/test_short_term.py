import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.memory.short_term import ShortTermMemory, Turn


@pytest.fixture
async def redis() -> FakeRedis:
    client = FakeRedis()
    yield client
    await client.aclose()


@pytest.mark.asyncio
async def test_append_and_get_turns_roundtrip(redis: FakeRedis) -> None:
    memory = ShortTermMemory(redis)

    await memory.append("session-1", Turn(role="user", content="hello"))
    await memory.append("session-1", Turn(role="assistant", content="hi there"))

    turns = await memory.get_turns("session-1")

    assert [(t.role, t.content) for t in turns] == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]


@pytest.mark.asyncio
async def test_sessions_are_isolated(redis: FakeRedis) -> None:
    memory = ShortTermMemory(redis)

    await memory.append("session-a", Turn(role="user", content="a"))
    await memory.append("session-b", Turn(role="user", content="b"))

    assert [t.content for t in await memory.get_turns("session-a")] == ["a"]
    assert [t.content for t in await memory.get_turns("session-b")] == ["b"]


@pytest.mark.asyncio
async def test_buffer_is_trimmed_to_max_turns(redis: FakeRedis) -> None:
    memory = ShortTermMemory(redis, max_turns=3)

    for i in range(5):
        await memory.append("session-1", Turn(role="user", content=str(i)))

    turns = await memory.get_turns("session-1")

    assert [t.content for t in turns] == ["2", "3", "4"]


@pytest.mark.asyncio
async def test_empty_session_returns_no_turns(redis: FakeRedis) -> None:
    memory = ShortTermMemory(redis)

    assert await memory.get_turns("never-seen") == []


@pytest.mark.asyncio
async def test_clear_empties_the_buffer(redis: FakeRedis) -> None:
    memory = ShortTermMemory(redis)
    await memory.append("session-1", Turn(role="user", content="hello"))

    await memory.clear("session-1")

    assert await memory.get_turns("session-1") == []


@pytest.mark.asyncio
async def test_ttl_is_set_on_append(redis: FakeRedis) -> None:
    memory = ShortTermMemory(redis, ttl_seconds=120)

    await memory.append("session-1", Turn(role="user", content="hello"))

    ttl = await redis.ttl("jarvis:short_term:session-1")
    assert 0 < ttl <= 120
