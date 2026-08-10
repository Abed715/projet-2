import sys
from pathlib import Path

import pytest

from jarvis.security.sandbox import SandboxExecutor
from jarvis.system.shell import ShellService


@pytest.fixture
def shell(tmp_path: Path) -> ShellService:
    return ShellService(SandboxExecutor(workspace_dir=tmp_path))


@pytest.mark.asyncio
async def test_run_delegates_to_executor(shell: ShellService) -> None:
    result = await shell.run([sys.executable, "-c", "print('via shell service')"])

    assert result.stdout.strip() == "via shell service"
    assert result.return_code == 0
