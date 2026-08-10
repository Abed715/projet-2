import pytest

from jarvis.core.db import Database
from jarvis.core.exceptions import NotFoundError
from jarvis.tasks.models import Task, TaskStatus
from jarvis.tasks.store import TaskStore


@pytest.fixture
async def store() -> TaskStore:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    return TaskStore(database)


@pytest.mark.asyncio
async def test_create_and_get_roundtrip(store: TaskStore) -> None:
    task = Task(name="send_email", payload={"to": "a@example.com"})
    await store.create(task)

    fetched = await store.get(task.id)

    assert fetched.id == task.id
    assert fetched.name == "send_email"
    assert fetched.payload == {"to": "a@example.com"}
    assert fetched.status is TaskStatus.PENDING


@pytest.mark.asyncio
async def test_get_missing_task_raises_not_found(store: TaskStore) -> None:
    with pytest.raises(NotFoundError):
        await store.get("does-not-exist")


@pytest.mark.asyncio
async def test_update_changes_status_attempt_result_error(store: TaskStore) -> None:
    task = Task(name="job", payload={})
    await store.create(task)

    updated = await store.update(
        task.id, status=TaskStatus.COMPLETED, attempt=1, result={"ok": True}
    )

    assert updated.status is TaskStatus.COMPLETED
    assert updated.attempt == 1
    assert updated.result == {"ok": True}


@pytest.mark.asyncio
async def test_update_missing_task_raises_not_found(store: TaskStore) -> None:
    with pytest.raises(NotFoundError):
        await store.update("does-not-exist", status=TaskStatus.CANCELLED)


@pytest.mark.asyncio
async def test_list_by_status_filters_and_orders(store: TaskStore) -> None:
    a = Task(name="a", payload={})
    b = Task(name="b", payload={})
    c = Task(name="c", payload={})
    await store.create(a)
    await store.create(b)
    await store.create(c)
    await store.update(b.id, status=TaskStatus.COMPLETED)

    pending = await store.list_by_status(TaskStatus.PENDING)

    assert [t.id for t in pending] == [a.id, c.id]
