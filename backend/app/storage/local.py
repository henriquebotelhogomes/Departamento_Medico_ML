"""Local filesystem storage backend (development default)."""

from __future__ import annotations

from pathlib import Path

import anyio

from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """Stores files on disk and serves them through the /media static mount."""

    def __init__(self, base_dir: Path, url_prefix: str = "/media") -> None:
        self.base_dir = base_dir
        self.url_prefix = url_prefix.rstrip("/")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, *, filename: str, content_type: str) -> str:
        key = self.build_key(filename)
        dest = self.base_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        await anyio.to_thread.run_sync(dest.write_bytes, data)
        return key

    async def url(self, key: str) -> str | None:
        return f"{self.url_prefix}/{key}"

    async def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            await anyio.to_thread.run_sync(path.unlink)
