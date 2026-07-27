"""Supabase Storage backend (production).

Uploads objects to a Supabase Storage bucket and returns signed URLs. The
supabase client is synchronous, so calls run in a worker thread to avoid
blocking the event loop.
"""

from __future__ import annotations

import anyio

from app.storage.base import StorageBackend

SIGNED_URL_TTL_SECONDS = 3600  # 1 hour


class SupabaseStorage(StorageBackend):
    def __init__(self, url: str, service_key: str, bucket: str) -> None:
        if not (url and service_key and bucket):
            raise ValueError(
                "SupabaseStorage requires SUPABASE_URL, SUPABASE_SERVICE_KEY and SUPABASE_BUCKET"
            )
        from supabase import create_client

        self._client = create_client(url, service_key)
        self._bucket = bucket

    def _bucket_api(self):
        return self._client.storage.from_(self._bucket)

    async def save(self, data: bytes, *, filename: str, content_type: str) -> str:
        key = self.build_key(filename)

        def _upload() -> None:
            self._bucket_api().upload(
                path=key,
                file=data,
                file_options={"content-type": content_type, "upsert": "false"},
            )

        await anyio.to_thread.run_sync(_upload)
        return key

    async def url(self, key: str) -> str | None:
        def _sign() -> str | None:
            res = self._bucket_api().create_signed_url(key, SIGNED_URL_TTL_SECONDS)
            if isinstance(res, dict):
                return res.get("signedURL") or res.get("signed_url")
            return None

        return await anyio.to_thread.run_sync(_sign)

    async def delete(self, key: str) -> None:
        def _remove() -> None:
            self._bucket_api().remove([key])

        await anyio.to_thread.run_sync(_remove)
