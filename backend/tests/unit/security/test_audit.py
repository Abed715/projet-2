import pytest

from jarvis.core.db import Database
from jarvis.security.audit import AuditEntry, InMemoryAuditLog, SqlAuditLog, redact


def test_redact_masks_credential_looking_keys() -> None:
    params = {"username": "alice", "password": "hunter2", "api_key": "sk-abc", "count": 3}

    redacted = redact(params)

    assert redacted["username"] == "alice"
    assert redacted["count"] == 3
    assert redacted["password"] == "***REDACTED***"
    assert redacted["api_key"] == "***REDACTED***"


def test_redact_is_case_insensitive() -> None:
    redacted = redact({"AUTH_TOKEN": "abc"})

    assert redacted["AUTH_TOKEN"] == "***REDACTED***"


@pytest.mark.asyncio
async def test_in_memory_audit_log_records_and_filters_by_correlation() -> None:
    log = InMemoryAuditLog()
    entry_a = AuditEntry(
        correlation_id="corr-1", actor="coordinator", tool_name="read_file", decision="allow"
    )
    entry_b = AuditEntry(
        correlation_id="corr-2", actor="coordinator", tool_name="read_file", decision="allow"
    )

    await log.record(entry_a)
    await log.record(entry_b)

    results = await log.list_for_correlation("corr-1")

    assert [e.id for e in results] == [entry_a.id]


@pytest.mark.asyncio
async def test_sql_audit_log_persists_and_orders_by_time() -> None:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    log = SqlAuditLog(database)

    first = AuditEntry(
        correlation_id="corr-1", actor="planner", tool_name="search_web", decision="allow",
        params={"query": "weather"},
    )
    second = AuditEntry(
        correlation_id="corr-1",
        actor="planner",
        tool_name="delete_file",
        decision="requires_confirmation",
    )

    await log.record(first)
    await log.record(second)

    results = await log.list_for_correlation("corr-1")

    assert [e.tool_name for e in results] == ["search_web", "delete_file"]
    assert results[0].params == {"query": "weather"}


@pytest.mark.asyncio
async def test_sql_audit_log_filters_by_correlation() -> None:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    log = SqlAuditLog(database)

    await log.record(
        AuditEntry(correlation_id="corr-a", actor="x", tool_name="t", decision="allow")
    )
    await log.record(
        AuditEntry(correlation_id="corr-b", actor="x", tool_name="t", decision="allow")
    )

    results = await log.list_for_correlation("corr-a")

    assert len(results) == 1
    assert results[0].correlation_id == "corr-a"
