"""Sandbox Executor: runs shell commands as isolated subprocesses rather
than directly on the host. See ARCHITECTURE.md §8.

This is process-level isolation, not OS-level sandboxing: commands run as
argv (never through a shell, so there is no shell-injection surface), are
confined to a configured workspace directory, run with a minimal explicit
environment (no inherited host secrets), and are killed on timeout. It does
not provide namespace/seccomp/container isolation — that's a deliberate
scope boundary, not an oversight; see README.md.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from jarvis.core.exceptions import ConfigurationError, PermissionDeniedError

DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class SandboxResult:
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool


class SandboxExecutor:
    """Runs argv commands confined to `workspace_dir`."""

    def __init__(
        self,
        *,
        workspace_dir: Path,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        env: dict[str, str] | None = None,
    ) -> None:
        self._workspace_dir = workspace_dir.resolve()
        self._timeout_seconds = timeout_seconds
        self._env = dict(env or {})

    def _resolve_cwd(self, cwd: Path | None) -> Path:
        if cwd is not None:
            candidate = (self._workspace_dir / cwd).resolve()
        else:
            candidate = self._workspace_dir
        try:
            candidate.relative_to(self._workspace_dir)
        except ValueError as exc:
            raise PermissionDeniedError(
                f"working directory {cwd} escapes the sandbox workspace"
            ) from exc
        return candidate

    async def run(self, command: list[str], *, cwd: Path | None = None) -> SandboxResult:
        if not command:
            raise ConfigurationError("command must be a non-empty argv list")

        working_dir = self._resolve_cwd(cwd)
        working_dir.mkdir(parents=True, exist_ok=True)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(working_dir),
                env=self._env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise ConfigurationError(f"command not found: {command[0]!r}") from exc

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=self._timeout_seconds
            )
            timed_out = False
        except TimeoutError:
            process.kill()
            await process.wait()
            stdout_bytes, stderr_bytes = b"", b""
            timed_out = True

        return SandboxResult(
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
            return_code=process.returncode if process.returncode is not None else -1,
            timed_out=timed_out,
        )
