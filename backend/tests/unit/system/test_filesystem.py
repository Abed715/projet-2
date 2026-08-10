from pathlib import Path

import pytest

from jarvis.core.exceptions import NotFoundError, PermissionDeniedError
from jarvis.system.filesystem import FilesystemService


@pytest.fixture
def fs(tmp_path: Path) -> FilesystemService:
    return FilesystemService(tmp_path)


@pytest.mark.asyncio
async def test_write_then_read_roundtrips(fs: FilesystemService) -> None:
    await fs.write_file("notes.txt", "hello world")

    content = await fs.read_file("notes.txt")

    assert content == "hello world"


@pytest.mark.asyncio
async def test_write_creates_parent_directories(fs: FilesystemService) -> None:
    await fs.write_file("a/b/c.txt", "nested")

    assert await fs.read_file("a/b/c.txt") == "nested"


@pytest.mark.asyncio
async def test_read_missing_file_raises(fs: FilesystemService) -> None:
    with pytest.raises(NotFoundError):
        await fs.read_file("missing.txt")


@pytest.mark.asyncio
async def test_list_dir_returns_sorted_entries(fs: FilesystemService) -> None:
    await fs.write_file("b.txt", "")
    await fs.write_file("a.txt", "")

    entries = await fs.list_dir(".")

    assert entries == ["a.txt", "b.txt"]


@pytest.mark.asyncio
async def test_list_missing_dir_raises(fs: FilesystemService) -> None:
    with pytest.raises(NotFoundError):
        await fs.list_dir("nope")


@pytest.mark.asyncio
async def test_move_relocates_file(fs: FilesystemService) -> None:
    await fs.write_file("src.txt", "payload")

    await fs.move("src.txt", "dst.txt")

    assert await fs.read_file("dst.txt") == "payload"
    with pytest.raises(NotFoundError):
        await fs.read_file("src.txt")


@pytest.mark.asyncio
async def test_move_missing_source_raises(fs: FilesystemService) -> None:
    with pytest.raises(NotFoundError):
        await fs.move("nope.txt", "dst.txt")


@pytest.mark.asyncio
async def test_delete_removes_file(fs: FilesystemService) -> None:
    await fs.write_file("gone.txt", "x")

    await fs.delete("gone.txt")

    with pytest.raises(NotFoundError):
        await fs.read_file("gone.txt")


@pytest.mark.asyncio
async def test_delete_removes_directory_recursively(fs: FilesystemService) -> None:
    await fs.write_file("dir/file.txt", "x")

    await fs.delete("dir")

    with pytest.raises(NotFoundError):
        await fs.list_dir("dir")


@pytest.mark.asyncio
async def test_delete_missing_path_raises(fs: FilesystemService) -> None:
    with pytest.raises(NotFoundError):
        await fs.delete("nope.txt")


@pytest.mark.asyncio
async def test_read_rejects_relative_traversal(fs: FilesystemService) -> None:
    with pytest.raises(PermissionDeniedError):
        await fs.read_file("../outside.txt")


@pytest.mark.asyncio
async def test_read_rejects_absolute_path_escape(fs: FilesystemService) -> None:
    with pytest.raises(PermissionDeniedError):
        await fs.read_file("/etc/passwd")


@pytest.mark.asyncio
async def test_write_rejects_traversal(fs: FilesystemService) -> None:
    with pytest.raises(PermissionDeniedError):
        await fs.write_file("../escape.txt", "x")
