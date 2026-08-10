"""Shell service: executes a fixed-argv command through the Sandbox
Executor. Never invoked via a shell string — arguments are always argv, so
there is no shell-injection surface. See `security.sandbox`.
"""

from __future__ import annotations

from jarvis.security import SandboxExecutor, SandboxResult


class ShellService:
    def __init__(self, executor: SandboxExecutor) -> None:
        self._executor = executor

    async def run(self, command: list[str]) -> SandboxResult:
        return await self._executor.run(command)
