"""Async SQLAlchemy engine/session management shared by any module that
persists to a relational database (security's audit log, memory's episodic
store, ...).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for ORM models across modules."""


class Database:
    """Wraps an async engine + session factory for a single DSN.

    Modules are handed a `Database` built from the process Postgres DSN in
    production; tests build one from an in-memory SQLite DSN instead. ORM
    models are kept portable between the two — Postgres-only column types
    (JSONB, pgvector, ...) are deferred until a module actually needs them,
    noted in that module's README.
    """

    def __init__(self, dsn: str, *, echo: bool = False) -> None:
        self.engine: AsyncEngine = create_async_engine(dsn, echo=echo)
        self._sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_all(self) -> None:
        """Create all tables known to `Base.metadata`.

        Dev/test convenience only — production schema changes go through
        Alembic migrations (added alongside the first real deployment).
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            yield session

    async def dispose(self) -> None:
        await self.engine.dispose()
