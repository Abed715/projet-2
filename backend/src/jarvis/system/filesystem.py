"""Filesystem service: read/write/list/move/delete confined to a
configured workspace directory. See ARCHITECTURE.md — "computer control:
move files, rename files."
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from jarvis.core.exceptions import NotFoundError, PermissionDeniedError


class FilesystemService:
    """All paths are relative to `workspace_dir` and cannot escape it.

    Every entry point resolves the candidate path and verifies it remains
    within the workspace root before touching the filesystem — this also
    catches an absolute-path input (e.g. `/etc/passwd`), since joining an
    absolute path onto a base with `Path.__truediv__` discards the base,
    and the resolved result then fails the containment check.
    """

    def __init__(self, workspace_dir: Path) -> None:
        self._workspace_dir = workspace_dir.resolve()
        self._workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self._workspace_dir / relative_path).resolve()
        try:
            candidate.relative_to(self._workspace_dir)
        except ValueError as exc:
            raise PermissionDeniedError(
                f"path {relative_path!r} escapes the workspace directory"
            ) from exc
        return candidate

    async def read_file(self, relative_path: str) -> str:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise NotFoundError(f"file not found: {relative_path!r}")
        return await asyncio.to_thread(path.read_text)

    async def write_file(self, relative_path: str, content: str) -> None:
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, content)

    async def list_dir(self, relative_path: str = ".") -> list[str]:
        path = self._resolve(relative_path)
        if not path.is_dir():
            raise NotFoundError(f"directory not found: {relative_path!r}")
        return sorted(entry.name for entry in path.iterdir())

    async def move(self, source: str, destination: str) -> None:
        source_path = self._resolve(source)
        destination_path = self._resolve(destination)
        if not source_path.exists():
            raise NotFoundError(f"source not found: {source!r}")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.move, str(source_path), str(destination_path))

    async def delete(self, relative_path: str) -> None:
        path = self._resolve(relative_path)
        if not path.exists():
            raise NotFoundError(f"path not found: {relative_path!r}")
        if path.is_dir():
            await asyncio.to_thread(shutil.rmtree, path)
        else:
            await asyncio.to_thread(path.unlink)
