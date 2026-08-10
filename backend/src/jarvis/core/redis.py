"""Thin factory around `redis.asyncio` so callers depend on a single import
site (and tests can substitute `fakeredis.aioredis` behind the same type).
"""

from __future__ import annotations

from redis.asyncio import Redis


def create_redis_client(url: str) -> Redis:
    """Build an async Redis client from a `redis://` URL.

    Kept separate from `jarvis.core.settings` so callers can pass a test
    double's URL, or substitute a `fakeredis` client directly, without
    touching process-wide settings.
    """
    return Redis.from_url(url, decode_responses=True)
