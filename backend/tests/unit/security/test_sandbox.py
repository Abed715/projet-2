import sys
from pathlib import Path

import pytest

from jarvis.core.exceptions import ConfigurationError, PermissionDeniedError
from jarvis.security.sandbox import SandboxExecutor


@pytest.fixture
def executor(tmp_path: Path) -> SandboxExecutor:
    return SandboxExecutor(workspace_dir=tmp_path, timeout_seconds=5.0)


@pytest.mark.asyncio
async def test_run_captures_stdout_and_return_code(executor: SandboxExecutor) -> None:
    result = await executor.run([sys.executable, "-c", "print('hello')"])

    assert result.stdout.strip() == "hello"
    assert result.return_code == 0
    assert result.timed_out is False


@pytest.mark.asyncio
async def test_run_captures_stderr_and_nonzero_exit(executor: SandboxExecutor) -> None:
    result = await executor.run(
        [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"]
    )

    assert "boom" in result.stderr
    assert result.return_code == 3


@pytest.mark.asyncio
async def test_run_kills_process_on_timeout() -> None:
    executor = SandboxExecutor(workspace_dir=Path.cwd(), timeout_seconds=0.2)

    result = await executor.run([sys.executable, "-c", "import time; time.sleep(5)"])

    assert result.timed_out is True
    assert result.return_code != 0


@pytest.mark.asyncio
async def test_run_rejects_empty_command(executor: SandboxExecutor) -> None:
    with pytest.raises(ConfigurationError):
        await executor.run([])


@pytest.mark.asyncio
async def test_run_rejects_unknown_executable(executor: SandboxExecutor) -> None:
    with pytest.raises(ConfigurationError):
        await executor.run(["definitely-not-a-real-command-xyz"])


@pytest.mark.asyncio
async def test_run_rejects_cwd_escaping_workspace(
    executor: SandboxExecutor, tmp_path: Path
) -> None:
    outside = tmp_path.parent

    with pytest.raises(PermissionDeniedError):
        await executor.run([sys.executable, "-c", "pass"], cwd=outside)


@pytest.mark.asyncio
async def test_run_uses_workspace_as_default_cwd(executor: SandboxExecutor, tmp_path: Path) -> None:
    result = await executor.run([sys.executable, "-c", "import os; print(os.getcwd())"])

    assert result.stdout.strip() == str(tmp_path.resolve())


@pytest.mark.asyncio
async def test_run_does_not_inherit_host_environment(
    executor: SandboxExecutor, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JARVIS_TEST_SECRET", "leaked-if-inherited")

    result = await executor.run(
        [sys.executable, "-c", "import os; print(repr(os.environ.get('JARVIS_TEST_SECRET')))"]
    )

    assert result.stdout.strip() == "None"


@pytest.mark.asyncio
async def test_run_passes_explicit_env(tmp_path: Path) -> None:
    executor = SandboxExecutor(workspace_dir=tmp_path, env={"MY_VAR": "hello"})

    result = await executor.run(
        [sys.executable, "-c", "import os; print(os.environ.get('MY_VAR'))"]
    )

    assert result.stdout.strip() == "hello"
