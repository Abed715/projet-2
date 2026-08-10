"""Durable task metadata: status, attempts, result/error. Postgres-backed in
production, SQLite in tests, via `jarvis.core.db` — mirrors
`memory.episodic.EpisodicStore`'s ORM-model pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.core.db import Base, Database
from jarvis.core.exceptions import NotFoundError
from jarvis.tasks.models import Task, TaskStatus


class _TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    result: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _to_task(row: _TaskRecord) -> Task:
    return Task(
        id=row.id,
        name=row.name,
        payload=row.payload,
        status=TaskStatus(row.status),
        attempt=row.attempt,
        max_attempts=row.max_attempts,
        result=row.result,
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class TaskStore:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def create(self, task: Task) -> None:
        async with self._database.session() as session:
            session.add(
                _TaskRecord(
                    id=task.id,
                    name=task.name,
                    payload=task.payload,
                    status=task.status.value,
                    attempt=task.attempt,
                    max_attempts=task.max_attempts,
                    result=task.result,
                    error=task.error,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                )
            )
            await session.commit()

    async def get(self, task_id: str) -> Task:
        async with self._database.session() as session:
            row = await session.get(_TaskRecord, task_id)
        if row is None:
            raise NotFoundError(f"no task with id {task_id!r}")
        return _to_task(row)

    async def list_by_status(self, status: TaskStatus) -> list[Task]:
        async with self._database.session() as session:
            stmt = (
                select(_TaskRecord)
                .where(_TaskRecord.status == status.value)
                .order_by(_TaskRecord.created_at)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [_to_task(row) for row in rows]

    async def update(
        self,
        task_id: str,
        *,
        status: TaskStatus | None = None,
        attempt: int | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> Task:
        async with self._database.session() as session:
            row = await session.get(_TaskRecord, task_id)
            if row is None:
                raise NotFoundError(f"no task with id {task_id!r}")
            if status is not None:
                row.status = status.value
            if attempt is not None:
                row.attempt = attempt
            if result is not None:
                row.result = result
            if error is not None:
                row.error = error
            row.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(row)
            return _to_task(row)
