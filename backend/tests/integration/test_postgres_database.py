"""Integration tests against a real Postgres instance.

Unit tests exercise the ORM layer against SQLite (see tests/unit/core,
tests/unit/security, tests/unit/memory) — these confirm the same code also
works against the real `asyncpg` driver and Postgres-specific behavior.
Skipped automatically when no Postgres is reachable (e.g. running locally
without `docker compose up`); CI provides a real service container.
"""

from __future__ import annotations

import random
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import String, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.core.db import Base, Database
from jarvis.core.settings import get_settings


class _IntegrationWidget(Base):
    __tablename__ = "widgets_integration_test"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    db = Database(get_settings().postgres_dsn)
    try:
        await db.create_all()
    except (OperationalError, OSError, TimeoutError) as exc:
        await db.dispose()
        pytest.skip(f"Postgres not reachable: {exc}")
    yield db
    await db.dispose()


@pytest.mark.asyncio
async def test_insert_and_query_against_real_postgres(database: Database) -> None:
    widget_id = random.randint(1, 2_000_000_000)  # avoid collisions on repeat local runs

    async with database.session() as session:
        session.add(_IntegrationWidget(id=widget_id, name="gizmo"))
        await session.commit()

    async with database.session() as session:
        result = await session.execute(
            select(_IntegrationWidget).where(_IntegrationWidget.id == widget_id)
        )
        widget = result.scalar_one()

    assert widget.name == "gizmo"
