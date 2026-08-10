"""Redis Streams-backed job queue: `TaskEngine.submit` enqueues a task id,
`TaskWorker` dequeues via a consumer group and acks on completion — the
at-least-once delivery Redis Streams consumer groups provide.
"""

from __future__ import annotations

from typing import Any, Protocol

import redis.exceptions

_FIELD_TASK_ID = "task_id"
_DEFAULT_STREAM_NAME = "jarvis:tasks"
_DEFAULT_GROUP_NAME = "jarvis:workers"


class StreamLike(Protocol):
    """The subset of `redis.asyncio.Redis`'s Streams API this module needs.

    Declared as a `Protocol` (same pattern as `memory.short_term.RedisLike`)
    so tests substitute `fakeredis.aioredis.FakeRedis` instead of a real
    Redis server.
    """

    async def xadd(self, name: str, fields: dict[str, str]) -> object: ...

    async def xgroup_create(
        self, name: str, groupname: str, id: str = "0", mkstream: bool = False
    ) -> object: ...

    async def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: dict[str, str],
        count: int | None = None,
    ) -> Any: ...

    async def xack(self, name: str, groupname: str, *ids: str) -> object: ...


def _decode(value: bytes | str) -> str:
    return value.decode() if isinstance(value, bytes) else value


class TaskQueue:
    def __init__(
        self,
        redis: StreamLike,
        *,
        stream_name: str = _DEFAULT_STREAM_NAME,
        group_name: str = _DEFAULT_GROUP_NAME,
    ) -> None:
        self._redis = redis
        self._stream_name = stream_name
        self._group_name = group_name
        self._group_ready = False

    async def _ensure_group(self) -> None:
        if self._group_ready:
            return
        try:
            await self._redis.xgroup_create(
                self._stream_name, self._group_name, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        self._group_ready = True

    async def enqueue(self, task_id: str) -> None:
        await self._ensure_group()
        await self._redis.xadd(self._stream_name, {_FIELD_TASK_ID: task_id})

    async def dequeue(self, consumer_name: str, *, count: int = 1) -> list[tuple[str, str]]:
        """Read up to `count` new messages for `consumer_name`, returning
        `(message_id, task_id)` pairs. Each message must be acked via
        `ack()` once its task has been processed (or requeued) — that's
        what makes redelivery-on-crash possible.
        """
        await self._ensure_group()
        response = await self._redis.xreadgroup(
            self._group_name, consumer_name, {self._stream_name: ">"}, count=count
        )
        if not response:
            return []

        _stream_name, messages = response[0]
        results: list[tuple[str, str]] = []
        for message_id, fields in messages:
            decoded_fields = {_decode(k): _decode(v) for k, v in fields.items()}
            results.append((_decode(message_id), decoded_fields[_FIELD_TASK_ID]))
        return results

    async def ack(self, message_id: str) -> None:
        await self._redis.xack(self._stream_name, self._group_name, message_id)
