"""Episodic (long-term, structured) memory: conversation history, task
history, project history, and user preferences. Postgres-backed in
production, SQLite in tests, via `jarvis.core.db`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.core.db import Base, Database


class EpisodeKind(StrEnum):
    """What kind of durable fact an episode records."""

    CONVERSATION_TURN = "conversation_turn"
    TASK = "task"
    PROJECT = "project"
    PREFERENCE = "preference"
    SUMMARY = "summary"


@dataclass(frozen=True, slots=True)
class Episode:
    session_id: str
    kind: EpisodeKind
    content: dict[str, object]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class _EpisodeRecord(Base):
    __tablename__ = "episodic_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EpisodicStore:
    """Durable, queryable memory: everything worth remembering past a
    single session's short-term buffer.
    """

    def __init__(self, database: Database) -> None:
        self._database = database

    async def record(self, episode: Episode) -> None:
        async with self._database.session() as session:
            session.add(
                _EpisodeRecord(
                    id=episode.id,
                    session_id=episode.session_id,
                    kind=episode.kind.value,
                    content=episode.content,
                    created_at=episode.created_at,
                )
            )
            await session.commit()

    async def list_for_session(
        self, session_id: str, *, kind: EpisodeKind | None = None
    ) -> list[Episode]:
        async with self._database.session() as session:
            stmt = select(_EpisodeRecord).where(_EpisodeRecord.session_id == session_id)
            if kind is not None:
                stmt = stmt.where(_EpisodeRecord.kind == kind.value)
            stmt = stmt.order_by(_EpisodeRecord.created_at)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        return [
            Episode(
                id=row.id,
                session_id=row.session_id,
                kind=EpisodeKind(row.kind),
                content=row.content,
                created_at=row.created_at,
            )
            for row in rows
        ]
