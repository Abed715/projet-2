from datetime import UTC, datetime, timedelta

import pytest

from jarvis.core.db import Database
from jarvis.memory.episodic import Episode, EpisodeKind, EpisodicStore


@pytest.fixture
async def store() -> EpisodicStore:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    return EpisodicStore(database)


@pytest.mark.asyncio
async def test_record_and_list_for_session(store: EpisodicStore) -> None:
    await store.record(
        Episode(session_id="s1", kind=EpisodeKind.PREFERENCE, content={"likes": "tea"})
    )

    episodes = await store.list_for_session("s1")

    assert len(episodes) == 1
    assert episodes[0].content == {"likes": "tea"}
    assert episodes[0].kind is EpisodeKind.PREFERENCE


@pytest.mark.asyncio
async def test_list_filters_by_kind(store: EpisodicStore) -> None:
    await store.record(Episode(session_id="s1", kind=EpisodeKind.TASK, content={"title": "t1"}))
    await store.record(
        Episode(session_id="s1", kind=EpisodeKind.PREFERENCE, content={"likes": "tea"})
    )

    tasks = await store.list_for_session("s1", kind=EpisodeKind.TASK)

    assert len(tasks) == 1
    assert tasks[0].kind is EpisodeKind.TASK


@pytest.mark.asyncio
async def test_sessions_are_isolated(store: EpisodicStore) -> None:
    await store.record(Episode(session_id="s1", kind=EpisodeKind.TASK, content={}))
    await store.record(Episode(session_id="s2", kind=EpisodeKind.TASK, content={}))

    assert len(await store.list_for_session("s1")) == 1
    assert len(await store.list_for_session("s2")) == 1


@pytest.mark.asyncio
async def test_results_are_ordered_by_created_at(store: EpisodicStore) -> None:
    now = datetime.now(UTC)
    first = Episode(
        session_id="s1", kind=EpisodeKind.SUMMARY, content={"n": 1}, created_at=now
    )
    second = Episode(
        session_id="s1",
        kind=EpisodeKind.SUMMARY,
        content={"n": 2},
        created_at=now + timedelta(seconds=1),
    )

    # record out of order to prove the store sorts, not just preserves insert order
    await store.record(second)
    await store.record(first)

    episodes = await store.list_for_session("s1")

    assert [e.content["n"] for e in episodes] == [1, 2]


@pytest.mark.asyncio
async def test_empty_session_returns_no_episodes(store: EpisodicStore) -> None:
    assert await store.list_for_session("never-seen") == []
