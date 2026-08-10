"""Ties `TaskStore` + `TaskQueue` + a per-task-name handler registry
together: `submit` persists a task and enqueues it, `run_once` (driven by
`TaskWorker`'s poll loop, or called directly in tests) dequeues one
message, runs the matching handler, and updates status — retrying up to
`max_attempts` before marking the task `FAILED`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from jarvis.core.exceptions import ConfigurationError, NotFoundError
from jarvis.tasks.models import Task, TaskStatus
from jarvis.tasks.queue import TaskQueue
from jarvis.tasks.store import TaskStore

TaskHandler = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


class TaskEngine:
    def __init__(self, *, store: TaskStore, queue: TaskQueue) -> None:
        self._store = store
        self._queue = queue
        self._handlers: dict[str, TaskHandler] = {}

    def register_handler(self, name: str, handler: TaskHandler) -> None:
        self._handlers[name] = handler

    async def submit(
        self, name: str, payload: dict[str, object], *, max_attempts: int = 3
    ) -> Task:
        if name not in self._handlers:
            raise ConfigurationError(f"no handler registered for task {name!r}")
        task = Task(name=name, payload=payload, max_attempts=max_attempts)
        await self._store.create(task)
        await self._queue.enqueue(task.id)
        return task

    async def run_once(self, consumer_name: str) -> Task | None:
        """Dequeue and process a single task.

        Returns `None` if the queue had nothing to do. This is the unit
        `TaskWorker`'s poll loop calls repeatedly in production, and what
        tests call directly to drive the engine deterministically without
        a background loop.
        """
        messages = await self._queue.dequeue(consumer_name, count=1)
        if not messages:
            return None
        message_id, task_id = messages[0]

        try:
            task = await self._store.get(task_id)
        except NotFoundError:
            await self._queue.ack(message_id)
            return None

        if task.status in (TaskStatus.CANCELLED, TaskStatus.PAUSED):
            await self._queue.ack(message_id)
            return task

        handler = self._handlers.get(task.name)
        if handler is None:
            task = await self._store.update(
                task_id, status=TaskStatus.FAILED, error=f"no handler registered for {task.name!r}"
            )
            await self._queue.ack(message_id)
            return task

        task = await self._store.update(task_id, status=TaskStatus.RUNNING)
        try:
            result = await handler(task.payload)
        except Exception as exc:
            attempt = task.attempt + 1
            if attempt >= task.max_attempts:
                task = await self._store.update(
                    task_id, status=TaskStatus.FAILED, attempt=attempt, error=str(exc)
                )
            else:
                task = await self._store.update(
                    task_id, status=TaskStatus.PENDING, attempt=attempt, error=str(exc)
                )
                await self._queue.enqueue(task_id)
        else:
            task = await self._store.update(task_id, status=TaskStatus.COMPLETED, result=result)
        finally:
            await self._queue.ack(message_id)

        return task

    async def pause(self, task_id: str) -> Task:
        task = await self._store.get(task_id)
        if task.status is not TaskStatus.PENDING:
            raise ConfigurationError(
                f"can only pause a pending task (task {task_id!r} is {task.status})"
            )
        return await self._store.update(task_id, status=TaskStatus.PAUSED)

    async def resume(self, task_id: str) -> Task:
        task = await self._store.get(task_id)
        if task.status is not TaskStatus.PAUSED:
            raise ConfigurationError(
                f"can only resume a paused task (task {task_id!r} is {task.status})"
            )
        task = await self._store.update(task_id, status=TaskStatus.PENDING)
        await self._queue.enqueue(task_id)
        return task

    async def cancel(self, task_id: str) -> Task:
        """Cancel a task that hasn't started running yet.

        Only `PENDING`/`PAUSED` tasks can be cancelled — a `RUNNING` task's
        handler is already executing with no cooperative cancellation
        hook, so flipping its status here wouldn't stop it and would just
        race with `run_once`'s own final status update. See
        `tasks/README.md`.
        """
        task = await self._store.get(task_id)
        if task.status not in (TaskStatus.PENDING, TaskStatus.PAUSED):
            raise ConfigurationError(
                f"cannot cancel a {task.status} task (task {task_id!r}) — "
                "only pending or paused tasks can be cancelled"
            )
        return await self._store.update(task_id, status=TaskStatus.CANCELLED)
