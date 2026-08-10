"""Append-only audit log: who/what agent, which tool, what parameters
(redacted), decision, and when. See ARCHITECTURE.md §8.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.core.db import Base, Database

_SENSITIVE_KEY_MARKERS = ("password", "token", "secret", "api_key", "apikey", "authorization")


def redact(params: dict[str, object]) -> dict[str, object]:
    """Mask values whose key looks like a credential before they're logged.

    A best-effort convenience, not a security boundary: callers that know a
    parameter is sensitive should still avoid passing it through in the
    first place.
    """
    def _mask(key: str, value: object) -> object:
        if any(marker in key.lower() for marker in _SENSITIVE_KEY_MARKERS):
            return "***REDACTED***"
        return value

    return {key: _mask(key, value) for key, value in params.items()}


@dataclass(frozen=True, slots=True)
class AuditEntry:
    correlation_id: str
    actor: str
    tool_name: str
    decision: str
    params: dict[str, object] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class AuditLog(Protocol):
    """Interface every audit log implementation satisfies."""

    async def record(self, entry: AuditEntry) -> None: ...

    async def list_for_correlation(self, correlation_id: str) -> list[AuditEntry]: ...


class InMemoryAuditLog:
    """Append-only in-memory audit log. Dev/test use only."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    async def record(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    async def list_for_correlation(self, correlation_id: str) -> list[AuditEntry]:
        return [entry for entry in self._entries if entry.correlation_id == correlation_id]


class _AuditLogRecord(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    tool_name: Mapped[str] = mapped_column(String(255))
    decision: Mapped[str] = mapped_column(String(32))
    params: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAuditLog:
    """Postgres-backed (SQLite in tests) append-only audit log."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def record(self, entry: AuditEntry) -> None:
        async with self._database.session() as session:
            session.add(
                _AuditLogRecord(
                    id=entry.id,
                    correlation_id=entry.correlation_id,
                    actor=entry.actor,
                    tool_name=entry.tool_name,
                    decision=entry.decision,
                    params=entry.params,
                    occurred_at=entry.occurred_at,
                )
            )
            await session.commit()

    async def list_for_correlation(self, correlation_id: str) -> list[AuditEntry]:
        async with self._database.session() as session:
            result = await session.execute(
                select(_AuditLogRecord)
                .where(_AuditLogRecord.correlation_id == correlation_id)
                .order_by(_AuditLogRecord.occurred_at)
            )
            rows = result.scalars().all()

        return [
            AuditEntry(
                id=row.id,
                correlation_id=row.correlation_id,
                actor=row.actor,
                tool_name=row.tool_name,
                decision=row.decision,
                params=row.params,
                occurred_at=row.occurred_at,
            )
            for row in rows
        ]
