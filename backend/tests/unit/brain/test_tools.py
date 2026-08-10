import pytest

from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry, ToolSpec
from jarvis.core.exceptions import ConfigurationError, PermissionDeniedError
from jarvis.security import InMemoryAuditLog, PermissionEngine, RiskLevel, Role


async def _echo_handler(arguments: dict[str, object]) -> object:
    return {"echoed": arguments}


@pytest.fixture
def audit_log() -> InMemoryAuditLog:
    return InMemoryAuditLog()


@pytest.fixture
def registry(audit_log: InMemoryAuditLog) -> ToolRegistry:
    engine = PermissionEngine()
    registry = ToolRegistry(engine, audit_log)
    registry.register(
        ToolSpec(
            name="read_file", description="reads a file", risk_level=RiskLevel.SAFE,
            handler=_echo_handler,
        )
    )
    registry.register(
        ToolSpec(
            name="delete_file", description="deletes a file", risk_level=RiskLevel.DANGEROUS,
            handler=_echo_handler,
        )
    )
    return registry


def test_get_unregistered_tool_raises(registry: ToolRegistry) -> None:
    with pytest.raises(ConfigurationError):
        registry.get("unknown")


def test_list_tools(registry: ToolRegistry) -> None:
    names = {tool.name for tool in registry.list_tools()}
    assert names == {"read_file", "delete_file"}


@pytest.mark.asyncio
async def test_invoke_safe_tool_runs_handler(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="read_file",
        arguments={"path": "a.txt"},
        role=Role.GUEST,
        session_id="s1",
        actor="coordinator",
        correlation_id="corr-1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert result.result == {"echoed": {"path": "a.txt"}}


@pytest.mark.asyncio
async def test_invoke_denied_tool_raises(registry: ToolRegistry) -> None:
    with pytest.raises(PermissionDeniedError):
        await registry.invoke(
            name="delete_file",
            arguments={},
            role=Role.GUEST,
            session_id="s1",
            actor="coordinator",
            correlation_id="corr-1",
        )


@pytest.mark.asyncio
async def test_invoke_dangerous_tool_requires_confirmation(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="delete_file",
        arguments={},
        role=Role.OWNER,
        session_id="s1",
        actor="coordinator",
        correlation_id="corr-1",
    )

    assert result.status is ToolInvocationStatus.REQUIRES_CONFIRMATION
    assert result.result is None


@pytest.mark.asyncio
async def test_every_invocation_is_audited(
    registry: ToolRegistry, audit_log: InMemoryAuditLog
) -> None:
    await registry.invoke(
        name="read_file", arguments={"secret_key": "shh"}, role=Role.GUEST,
        session_id="s1", actor="coordinator", correlation_id="corr-42",
    )

    entries = await audit_log.list_for_correlation("corr-42")
    assert len(entries) == 1
    assert entries[0].tool_name == "read_file"
    assert entries[0].decision == "allow"
    assert entries[0].params["secret_key"] == "***REDACTED***"
