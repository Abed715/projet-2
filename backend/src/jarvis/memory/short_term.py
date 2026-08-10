"""Short-term (working) memory: the active conversation buffer, capped and
TTL'd per session. Backed by Redis in production; any client exposing the
`RedisLike` subset of the `redis.asyncio.Redis` interface works in tests
(including `fakeredis`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Turn:
    role: str
    content: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class RedisLike(Protocol):
    """The subset of `redis.asyncio.Redis` this module needs.

    Declared as a `Protocol` (rather than importing the concrete client type)
    so tests can substitute `fakeredis.aioredis.FakeRedis` — or any other
    compatible client — without a real Redis server.
    """

    async def rpush(self, name: str, *values: str) -> int: ...

    async def lrange(self, name: str, start: int, end: int) -> list[str]: ...

    async def ltrim(self, name: str, start: int, end: int) -> bool: ...

    async def expire(self, name: str, seconds: int) -> bool: ...

    async def delete(self, *names: str) -> int: ...


class ShortTermMemory:
    """Active conversation buffer.

    Turns pushed past `max_turns` are trimmed from the live buffer — not
    deleted from history. Compressing them into durable episodic memory
    before they age out is the Memory Agent's job (ARCHITECTURE.md §6),
    landing with `jarvis.agents` in Phase 2.
    """

    def __init__(self, redis: RedisLike, *, max_turns: int = 50, ttl_seconds: int = 3600) -> None:
        self._redis = redis
        self._max_turns = max_turns
        self._ttl_seconds = ttl_seconds

    def _key(self, session_id: str) -> str:
        return f"jarvis:short_term:{session_id}"

    async def append(self, session_id: str, turn: Turn) -> None:
        key = self._key(session_id)
        payload = json.dumps(
            {
                "role": turn.role,
                "content": turn.content,
                "occurred_at": turn.occurred_at.isoformat(),
            }
        )
        await self._redis.rpush(key, payload)
        await self._redis.ltrim(key, -self._max_turns, -1)
        await self._redis.expire(key, self._ttl_seconds)

    async def get_turns(self, session_id: str) -> list[Turn]:
        raw_turns = await self._redis.lrange(self._key(session_id), 0, -1)
        return [
            Turn(
                role=data["role"],
                content=data["content"],
                occurred_at=datetime.fromisoformat(data["occurred_at"]),
            )
            for data in (json.loads(item) for item in raw_turns)
        ]

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
