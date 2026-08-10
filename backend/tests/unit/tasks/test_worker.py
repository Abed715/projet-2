import asyncio

import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.core.db import Database
from jarvis.tasks.engine import TaskEngine
from jarvis.tasks.models import TaskStatus
from jarvis.tasks.queue import TaskQueue
from jarvis.tasks.store import TaskStore
from jarvis.tasks.worker import TaskWorker


@pytest.fixture
async def store() -> TaskStore:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    return TaskStore(database)


@pytest.fixture
def engine(store: TaskStore) -> TaskEngine:
    queue = TaskQueue(FakeRedis(), stream_name="test:tasks", group_name="test:workers")
    return TaskEngine(store=store, queue=queue)


@pytest.mark.asyncio
async def test_worker_processes_a_submitted_task_then_stops(
    engine: TaskEngine, store: TaskStore
) -> None:
    processed: list[dict[str, object]] = []

    async def handler(payload: dict[str, object]) -> dict[str, object]:
        processed.append(payload)
        return {"done": True}

    engine.register_handler("job", handler)
    task = await engine.submit("job", {"n": 1})

    worker = TaskWorker(engine, consumer_name="worker-1", poll_interval_seconds=0.01)
    stop_event = asyncio.Event()

    async def stop_once_processed() -> None:
        while not processed:
            await asyncio.sleep(0.01)
        stop_event.set()

    await asyncio.wait_for(
        asyncio.gather(worker.run(stop_event), stop_once_processed()), timeout=5
    )

    assert processed == [{"n": 1}]
    stored = await store.get(task.id)
    assert stored.status is TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_worker_stops_promptly_when_queue_is_empty(engine: TaskEngine) -> None:
    worker = TaskWorker(engine, consumer_name="worker-1", poll_interval_seconds=0.01)
    stop_event = asyncio.Event()
    stop_event.set()  # already stopped: run() must return without polling forever

    await asyncio.wait_for(worker.run(stop_event), timeout=5)
