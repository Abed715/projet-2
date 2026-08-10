import sys
from pathlib import Path

import pytest

from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry
from jarvis.core.exceptions import ValidationError
from jarvis.security import InMemoryAuditLog, PermissionEngine, Role
from jarvis.security.sandbox import SandboxExecutor
from jarvis.system.filesystem import FilesystemService
from jarvis.system.shell import ShellService
from jarvis.system.tools import register_system_tools


@pytest.fixture
def permission_engine() -> PermissionEngine:
    return PermissionEngine()


@pytest.fixture
def registry(tmp_path: Path, permission_engine: PermissionEngine) -> ToolRegistry:
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(permission_engine, audit_log)
    filesystem = FilesystemService(tmp_path)
    shell = ShellService(SandboxExecutor(workspace_dir=tmp_path))
    register_system_tools(registry, filesystem=filesystem, shell=shell)
    return registry


def test_all_tools_registered(registry: ToolRegistry) -> None:
    names = {tool.name for tool in registry.list_tools()}
    assert names == {
        "read_file",
        "list_dir",
        "write_file",
        "move_file",
        "delete_file",
        "run_shell_command",
    }


@pytest.mark.asyncio
async def test_guest_can_read_and_list(registry: ToolRegistry) -> None:
    write_result = await registry.invoke(
        name="write_file",
        arguments={"path": "a.txt", "content": "hi"},
        role=Role.OPERATOR,
        session_id="s1",
        actor="coding",
        correlation_id="c1",
    )
    assert write_result.status is ToolInvocationStatus.OK

    read_result = await registry.invoke(
        name="read_file",
        arguments={"path": "a.txt"},
        role=Role.GUEST,
        session_id="s1",
        actor="coding",
        correlation_id="c2",
    )

    assert read_result.status is ToolInvocationStatus.OK
    assert read_result.result == {"content": "hi"}


@pytest.mark.asyncio
async def test_write_file_requires_operator_or_above(registry: ToolRegistry) -> None:
    from jarvis.core.exceptions import PermissionDeniedError

    with pytest.raises(PermissionDeniedError):
        await registry.invoke(
            name="write_file",
            arguments={"path": "a.txt", "content": "hi"},
            role=Role.GUEST,
            session_id="s1",
            actor="coding",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_delete_file_requires_confirmation(registry: ToolRegistry) -> None:
    await registry.invoke(
        name="write_file",
        arguments={"path": "a.txt", "content": "hi"},
        role=Role.OWNER,
        session_id="s1",
        actor="coding",
        correlation_id="c1",
    )

    result = await registry.invoke(
        name="delete_file",
        arguments={"path": "a.txt"},
        role=Role.OWNER,
        session_id="s1",
        actor="coding",
        correlation_id="c2",
    )

    assert result.status is ToolInvocationStatus.REQUIRES_CONFIRMATION


@pytest.mark.asyncio
async def test_run_shell_command_executes(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="run_shell_command",
        arguments={"command": [sys.executable, "-c", "print('ran')"]},
        role=Role.OWNER,
        session_id="s1",
        actor="coding",
        correlation_id="c1",
    )

    # DANGEROUS: first call from a fresh session requires confirmation.
    assert result.status is ToolInvocationStatus.REQUIRES_CONFIRMATION


@pytest.mark.asyncio
async def test_run_shell_command_after_grant(
    registry: ToolRegistry, permission_engine: PermissionEngine
) -> None:
    permission_engine.grant_for_session("s1", "run_shell_command")

    result = await registry.invoke(
        name="run_shell_command",
        arguments={"command": [sys.executable, "-c", "print('ran')"]},
        role=Role.OWNER,
        session_id="s1",
        actor="coding",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert isinstance(result.result, dict)
    assert result.result["stdout"].strip() == "ran"


@pytest.mark.asyncio
async def test_run_shell_command_rejects_non_list_command(
    registry: ToolRegistry, permission_engine: PermissionEngine
) -> None:
    permission_engine.grant_for_session("s1", "run_shell_command")

    with pytest.raises(ValidationError):
        await registry.invoke(
            name="run_shell_command",
            arguments={"command": "not a list"},
            role=Role.OWNER,
            session_id="s1",
            actor="coding",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_read_file_rejects_non_string_path(registry: ToolRegistry) -> None:
    with pytest.raises(ValidationError):
        await registry.invoke(
            name="read_file",
            arguments={"path": 123},
            role=Role.GUEST,
            session_id="s1",
            actor="coding",
            correlation_id="c1",
        )
