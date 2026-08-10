"""Integration tests against a real Redis instance.

`tests/unit/memory/test_short_term.py` exercises `ShortTermMemory` against
`fakeredis`; this confirms the same `redis.asyncio` client construction
(`jarvis.core.redis.create_redis_client`) also works against the real
server. Skipped automatically when no Redis is reachable; CI provides a
real service container.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from jarvis.core.redis import create_redis_client
from jarvis.core.settings import get_settings
from jarvis.memory.short_term import ShortTermMemory, Turn


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    client = create_redis_client(get_settings().redis_url)
    try:
        await client.ping()
    except (RedisConnectionError, OSError, TimeoutError) as exc:
        await client.aclose()
        pytest.skip(f"Redis not reachable: {exc}")
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.mark.asyncio
async def test_short_term_memory_against_real_redis(redis_client: Redis) -> None:
    memory = ShortTermMemory(redis_client)

    await memory.append("integration-session", Turn(role="user", content="hello"))
    turns = await memory.get_turns("integration-session")

    assert [t.content for t in turns] == ["hello"]
