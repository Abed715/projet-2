import pytest
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.core.db import Base, Database


class _Widget(Base):
    __tablename__ = "widgets_test_db"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


@pytest.fixture
async def database() -> Database:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.create_all()
    return db


@pytest.mark.asyncio
async def test_session_can_insert_and_query(database: Database) -> None:
    async with database.session() as session:
        session.add(_Widget(id=1, name="gizmo"))
        await session.commit()

    async with database.session() as session:
        result = await session.execute(select(_Widget).where(_Widget.id == 1))
        widget = result.scalar_one()

    assert widget.name == "gizmo"


@pytest.mark.asyncio
async def test_sessions_are_isolated_contexts(database: Database) -> None:
    async with database.session() as session_a, database.session() as session_b:
        assert session_a is not session_b


@pytest.mark.asyncio
async def test_dispose_closes_the_engine(database: Database) -> None:
    await database.dispose()  # should not raise
