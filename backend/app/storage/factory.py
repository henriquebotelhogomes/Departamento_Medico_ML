"""Storage backend factory (chooses the implementation from settings)."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.storage.base import StorageBackend


@lru_cache
def get_storage() -> StorageBackend:
    """Return the configured storage backend (cached singleton)."""
    backend = settings.storage_backend.lower()
    if backend == "supabase":
        from app.storage.supabase_storage import SupabaseStorage

        return SupabaseStorage(
            url=settings.supabase_url,
            service_key=settings.supabase_service_key,
            bucket=settings.supabase_bucket,
        )

    from app.storage.local import LocalStorage

    return LocalStorage(base_dir=settings.resolve_path(settings.local_storage_dir))
