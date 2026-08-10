import pytest
from fakeredis.aioredis import FakeRedis

from jarvis.tasks.queue import TaskQueue


@pytest.fixture
async def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def queue(redis: FakeRedis) -> TaskQueue:
    return TaskQueue(redis, stream_name="test:tasks", group_name="test:workers")


@pytest.mark.asyncio
async def test_enqueue_then_dequeue_roundtrips_task_id(queue: TaskQueue) -> None:
    await queue.enqueue("task-1")

    messages = await queue.dequeue("consumer-1")

    assert len(messages) == 1
    _message_id, task_id = messages[0]
    assert task_id == "task-1"


@pytest.mark.asyncio
async def test_dequeue_on_empty_queue_returns_no_messages(queue: TaskQueue) -> None:
    assert await queue.dequeue("consumer-1") == []


@pytest.mark.asyncio
async def test_unacked_message_is_not_redelivered_to_a_new_read(queue: TaskQueue) -> None:
    await queue.enqueue("task-1")
    await queue.dequeue("consumer-1")

    # A second `dequeue` for *new* messages (">") shouldn't see task-1 again
    # while it's still pending ack — that's the whole point of consumer
    # groups. Enqueue a second task to prove the queue still moves forward.
    await queue.enqueue("task-2")
    messages = await queue.dequeue("consumer-1")

    assert [task_id for _message_id, task_id in messages] == ["task-2"]


@pytest.mark.asyncio
async def test_ack_completes_the_message(queue: TaskQueue) -> None:
    await queue.enqueue("task-1")
    message_id, _task_id = (await queue.dequeue("consumer-1"))[0]

    # Acking twice must not raise — xack is idempotent.
    await queue.ack(message_id)
    await queue.ack(message_id)


@pytest.mark.asyncio
async def test_multiple_consumers_split_the_stream(queue: TaskQueue) -> None:
    await queue.enqueue("task-1")
    await queue.enqueue("task-2")

    first = await queue.dequeue("consumer-1", count=1)
    second = await queue.dequeue("consumer-2", count=1)

    assert [task_id for _mid, task_id in first] == ["task-1"]
    assert [task_id for _mid, task_id in second] == ["task-2"]
