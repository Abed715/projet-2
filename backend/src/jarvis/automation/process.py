"""Process management: launch, terminate, and list OS processes via
`psutil`/`subprocess`. Unlike the rest of `automation`, this is headless-safe
— no display or clipboard mechanism is required — so it talks to `psutil`
directly rather than going through a swappable backend Protocol.
"""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass

import psutil

from jarvis.core.exceptions import ConfigurationError, NotFoundError


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    pid: int
    name: str
    status: str


class ProcessService:
    """Opens, closes, and lists OS processes.

    Processes launched via `open_application` are not awaited or reaped —
    they are handed off to the OS. This is a known limitation: long-running
    JARVIS instances that open many short-lived applications may accumulate
    zombie entries until this process exits. Acceptable for this phase; a
    future task-engine integration (Phase 6) can track and reap children.
    """

    async def open_application(self, command: list[str]) -> int:
        if not command:
            raise ConfigurationError("command must not be empty")

        def _spawn() -> int:
            try:
                process = subprocess.Popen(command)  # noqa: S603
            except FileNotFoundError as exc:
                raise ConfigurationError(f"executable not found: {command[0]!r}") from exc
            return process.pid

        return await asyncio.to_thread(_spawn)

    async def close_application(self, pid: int, *, force: bool = False) -> None:
        def _close() -> None:
            try:
                process = psutil.Process(pid)
                process.kill() if force else process.terminate()
            except psutil.NoSuchProcess as exc:
                raise NotFoundError(f"no process with pid {pid}") from exc

        await asyncio.to_thread(_close)

    async def list_processes(self) -> list[ProcessInfo]:
        def _list() -> list[ProcessInfo]:
            return [
                ProcessInfo(
                    pid=proc.info["pid"], name=proc.info["name"], status=proc.info["status"]
                )
                for proc in psutil.process_iter(["pid", "name", "status"])
            ]

        return await asyncio.to_thread(_list)
