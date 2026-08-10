from datetime import UTC, datetime, timedelta

import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.core.db import Database
from jarvis.tasks.engine import TaskEngine
from jarvis.tasks.queue import TaskQueue
from jarvis.tasks.scheduler import Scheduler
from jarvis.tasks.store import TaskStore


@pytest.fixture
async def engine() -> TaskEngine:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    store = TaskStore(database)
    queue = TaskQueue(FakeRedis(), stream_name="test:tasks", group_name="test:workers")
    engine = TaskEngine(store=store, queue=queue)
    engine.register_handler("heartbeat", lambda payload: _noop())
    return engine


async def _noop() -> dict[str, object]:
    return {}


@pytest.mark.asyncio
async def test_tick_submits_task_that_starts_immediately(engine: TaskEngine) -> None:
    scheduler = Scheduler(engine)
    scheduler.register("heartbeat", {}, interval_seconds=60)

    submitted = await scheduler.tick()

    assert len(submitted) == 1
    assert submitted[0].name == "heartbeat"


@pytest.mark.asyncio
async def test_tick_does_not_resubmit_before_interval_elapses(engine: TaskEngine) -> None:
    scheduler = Scheduler(engine)
    scheduler.register("heartbeat", {}, interval_seconds=60)
    now = datetime.now(UTC)

    first = await scheduler.tick(now=now)
    second = await scheduler.tick(now=now + timedelta(seconds=1))

    assert len(first) == 1
    assert len(second) == 0


@pytest.mark.asyncio
async def test_tick_resubmits_after_interval_elapses(engine: TaskEngine) -> None:
    scheduler = Scheduler(engine)
    scheduler.register("heartbeat", {}, interval_seconds=60)
    now = datetime.now(UTC)

    await scheduler.tick(now=now)
    second = await scheduler.tick(now=now + timedelta(seconds=61))

    assert len(second) == 1


@pytest.mark.asyncio
async def test_start_immediately_false_delays_first_run(engine: TaskEngine) -> None:
    scheduler = Scheduler(engine)
    scheduler.register("heartbeat", {}, interval_seconds=60, start_immediately=False)

    immediate = await scheduler.tick()

    assert immediate == []
