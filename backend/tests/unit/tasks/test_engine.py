import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.core.db import Database
from jarvis.core.exceptions import ConfigurationError
from jarvis.tasks.engine import TaskEngine
from jarvis.tasks.models import TaskStatus
from jarvis.tasks.queue import TaskQueue
from jarvis.tasks.store import TaskStore


@pytest.fixture
async def engine() -> TaskEngine:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    store = TaskStore(database)
    queue = TaskQueue(FakeRedis(), stream_name="test:tasks", group_name="test:workers")
    return TaskEngine(store=store, queue=queue)


@pytest.mark.asyncio
async def test_submit_without_handler_raises_configuration_error(engine: TaskEngine) -> None:
    with pytest.raises(ConfigurationError):
        await engine.submit("unregistered", {})


@pytest.mark.asyncio
async def test_run_once_on_empty_queue_returns_none(engine: TaskEngine) -> None:
    engine.register_handler("noop", lambda payload: _ok())

    assert await engine.run_once("worker-1") is None


async def _ok(result: dict[str, object] | None = None) -> dict[str, object]:
    return result or {}


@pytest.mark.asyncio
async def test_successful_task_runs_to_completion(engine: TaskEngine) -> None:
    async def handler(payload: dict[str, object]) -> dict[str, object]:
        return {"greeting": f"hello {payload['name']}"}

    engine.register_handler("greet", handler)
    submitted = await engine.submit("greet", {"name": "jarvis"})

    completed = await engine.run_once("worker-1")

    assert completed is not None
    assert completed.id == submitted.id
    assert completed.status is TaskStatus.COMPLETED
    assert completed.result == {"greeting": "hello jarvis"}


@pytest.mark.asyncio
async def test_failing_task_retries_then_fails_after_max_attempts(engine: TaskEngine) -> None:
    async def always_fails(payload: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("boom")

    engine.register_handler("doomed", always_fails)
    submitted = await engine.submit("doomed", {}, max_attempts=2)

    first = await engine.run_once("worker-1")
    assert first is not None
    assert first.status is TaskStatus.PENDING
    assert first.attempt == 1

    second = await engine.run_once("worker-1")
    assert second is not None
    assert second.id == submitted.id
    assert second.status is TaskStatus.FAILED
    assert second.attempt == 2
    assert second.error == "boom"


@pytest.mark.asyncio
async def test_pause_then_resume_round_trip(engine: TaskEngine) -> None:
    engine.register_handler("job", lambda payload: _ok())
    task = await engine.submit("job", {})

    paused = await engine.pause(task.id)
    assert paused.status is TaskStatus.PAUSED

    # A paused task sitting in the queue is acked and skipped, not run.
    skipped = await engine.run_once("worker-1")
    assert skipped is not None
    assert skipped.status is TaskStatus.PAUSED

    resumed = await engine.resume(task.id)
    assert resumed.status is TaskStatus.PENDING

    completed = await engine.run_once("worker-1")
    assert completed is not None
    assert completed.status is TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_pause_non_pending_task_raises(engine: TaskEngine) -> None:
    engine.register_handler("job", lambda payload: _ok())
    task = await engine.submit("job", {})
    await engine.run_once("worker-1")  # now COMPLETED

    with pytest.raises(ConfigurationError):
        await engine.pause(task.id)


@pytest.mark.asyncio
async def test_cancel_pending_task(engine: TaskEngine) -> None:
    engine.register_handler("job", lambda payload: _ok())
    task = await engine.submit("job", {})

    cancelled = await engine.cancel(task.id)

    assert cancelled.status is TaskStatus.CANCELLED

    skipped = await engine.run_once("worker-1")
    assert skipped is not None
    assert skipped.status is TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_completed_task_raises(engine: TaskEngine) -> None:
    engine.register_handler("job", lambda payload: _ok())
    task = await engine.submit("job", {})
    await engine.run_once("worker-1")  # now COMPLETED

    with pytest.raises(ConfigurationError):
        await engine.cancel(task.id)
