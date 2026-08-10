"""Registers `system`'s filesystem and shell capabilities as tools in
`brain`'s `ToolRegistry`, each tagged with the risk level `security.rbac`
enforces before it runs.
"""

from __future__ import annotations

from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ValidationError
from jarvis.security import RiskLevel
from jarvis.system.filesystem import FilesystemService
from jarvis.system.shell import ShellService


def _require_str(arguments: dict[str, object], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str):
        raise ValidationError(f"{key!r} must be a string")
    return value


def register_system_tools(
    registry: ToolRegistry, *, filesystem: FilesystemService, shell: ShellService
) -> None:
    async def read_file(arguments: dict[str, object]) -> object:
        path = _require_str(arguments, "path")
        return {"content": await filesystem.read_file(path)}

    async def write_file(arguments: dict[str, object]) -> object:
        path = _require_str(arguments, "path")
        content = _require_str(arguments, "content")
        await filesystem.write_file(path, content)
        return {"status": "written", "path": path}

    async def list_dir(arguments: dict[str, object]) -> object:
        path = arguments.get("path", ".")
        if not isinstance(path, str):
            raise ValidationError("'path' must be a string")
        return {"entries": await filesystem.list_dir(path)}

    async def move_file(arguments: dict[str, object]) -> object:
        source = _require_str(arguments, "source")
        destination = _require_str(arguments, "destination")
        await filesystem.move(source, destination)
        return {"status": "moved", "source": source, "destination": destination}

    async def delete_file(arguments: dict[str, object]) -> object:
        path = _require_str(arguments, "path")
        await filesystem.delete(path)
        return {"status": "deleted", "path": path}

    async def run_shell_command(arguments: dict[str, object]) -> object:
        command = arguments.get("command")
        if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
            raise ValidationError("'command' must be a list of strings")
        result = await shell.run(command)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.return_code,
            "timed_out": result.timed_out,
        }

    registry.register(
        ToolSpec(
            name="read_file",
            description="Read a text file from the workspace.",
            risk_level=RiskLevel.SAFE,
            handler=read_file,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to the workspace root"}
                },
                "required": ["path"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="list_dir",
            description="List entries in a workspace directory.",
            risk_level=RiskLevel.SAFE,
            handler=list_dir,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the workspace root, default '.'",
                    }
                },
            },
        )
    )
    registry.register(
        ToolSpec(
            name="write_file",
            description="Create or overwrite a text file in the workspace.",
            risk_level=RiskLevel.SENSITIVE,
            handler=write_file,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the workspace root",
                    },
                    "content": {"type": "string", "description": "Full file contents to write"},
                },
                "required": ["path", "content"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="move_file",
            description="Move or rename a file within the workspace.",
            risk_level=RiskLevel.SENSITIVE,
            handler=move_file,
            input_schema={
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source", "destination"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="delete_file",
            description="Permanently delete a file or directory in the workspace.",
            risk_level=RiskLevel.DANGEROUS,
            handler=delete_file,
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="run_shell_command",
            description="Run a shell command (argv list, no shell interpolation) in the workspace.",
            risk_level=RiskLevel.DANGEROUS,
            handler=run_shell_command,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": 'Argv, e.g. ["ls", "-la"]',
                    }
                },
                "required": ["command"],
            },
        )
    )
