import os
import sys

import psutil
import pytest

from jarvis.automation.process import ProcessInfo, ProcessService
from jarvis.core.exceptions import ConfigurationError, NotFoundError


@pytest.fixture
def service() -> ProcessService:
    return ProcessService()


@pytest.mark.asyncio
async def test_open_application_rejects_empty_command(service: ProcessService) -> None:
    with pytest.raises(ConfigurationError):
        await service.open_application([])


@pytest.mark.asyncio
async def test_open_application_rejects_missing_executable(service: ProcessService) -> None:
    with pytest.raises(ConfigurationError):
        await service.open_application(["definitely-not-a-real-executable-xyz"])


@pytest.mark.asyncio
async def test_open_and_close_real_process(service: ProcessService) -> None:
    pid = await service.open_application([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        assert psutil.pid_exists(pid)
    finally:
        await service.close_application(pid, force=True)


@pytest.mark.asyncio
async def test_close_application_raises_not_found_for_unknown_pid(
    service: ProcessService,
) -> None:
    unused_pid = 999_999_999
    with pytest.raises(NotFoundError):
        await service.close_application(unused_pid)


@pytest.mark.asyncio
async def test_list_processes_includes_current_process(service: ProcessService) -> None:
    processes = await service.list_processes()

    assert any(isinstance(p, ProcessInfo) for p in processes)
    assert any(p.pid == os.getpid() for p in processes)
