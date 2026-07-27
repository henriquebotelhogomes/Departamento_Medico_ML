"""Storage backend interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime


class StorageBackend(ABC):
    """Abstract file storage. Implementations persist raw bytes and return a key."""

    @abstractmethod
    async def save(self, data: bytes, *, filename: str, content_type: str) -> str:
        """Persist ``data`` and return an opaque storage key."""

    @abstractmethod
    async def url(self, key: str) -> str | None:
        """Return a (possibly signed / temporary) URL to fetch the object."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the object. Missing objects are ignored."""

    @staticmethod
    def build_key(filename: str) -> str:
        """Generate a collision-free, date-partitioned storage key."""
        ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
        day = datetime.now(UTC).strftime("%Y/%m/%d")
        return f"{day}/{uuid.uuid4().hex}{ext}"
