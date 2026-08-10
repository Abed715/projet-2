"""Interval-based recurring task submission — the "cron-like" scheduler
from ARCHITECTURE.md's Task Engine, simplified to fixed intervals rather
than full cron expression parsing (no new dependency, and every current
use case — "run X every N minutes" — needs nothing richer; see
`tasks/README.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jarvis.tasks.engine import TaskEngine
from jarvis.tasks.models import Task


@dataclass
class _ScheduledTask:
    name: str
    payload: dict[str, object]
    interval_seconds: float
    next_run_at: datetime


class Scheduler:
    """Holds a set of (task name, payload, interval) entries and submits
    each to a `TaskEngine` once its interval elapses. There is no internal
    timer — call `tick()` periodically (e.g. alongside a `TaskWorker.run`
    loop) to advance it.
    """

    def __init__(self, engine: TaskEngine) -> None:
        self._engine = engine
        self._scheduled: list[_ScheduledTask] = []

    def register(
        self,
        name: str,
        payload: dict[str, object],
        *,
        interval_seconds: float,
        start_immediately: bool = True,
    ) -> None:
        now = datetime.now(UTC)
        next_run_at = (
            now if start_immediately else now + timedelta(seconds=interval_seconds)
        )
        self._scheduled.append(
            _ScheduledTask(
                name=name,
                payload=payload,
                interval_seconds=interval_seconds,
                next_run_at=next_run_at,
            )
        )

    async def tick(self, *, now: datetime | None = None) -> list[Task]:
        moment = now if now is not None else datetime.now(UTC)
        submitted: list[Task] = []
        for scheduled in self._scheduled:
            if scheduled.next_run_at <= moment:
                task = await self._engine.submit(scheduled.name, scheduled.payload)
                submitted.append(task)
                scheduled.next_run_at = moment + timedelta(seconds=scheduled.interval_seconds)
        return submitted
