"""
Redis-based prediction cache.

Caches prediction results keyed by SHA-256 hash of the image bytes.
Avoids redundant inference when the same image is uploaded multiple times.

Requires: redis[hiredis] package and a running Redis instance.
Configure via REDIS_URL environment variable.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from typing import Any

_redis_client = None


def _get_redis():
    """Lazy-initialize async Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis

            url = os.getenv("REDIS_URL", "redis://localhost:6379/2")
            _redis_client = redis.from_url(url, decode_responses=True)
            _redis_client.ping()  # verify connection
        except Exception:
            _redis_client = None
    return _redis_client


def image_hash(image_bytes: bytes) -> str:
    """Compute SHA-256 hash of image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


def get_cached_prediction(hash_key: str) -> dict[str, Any] | None:
    """
    Retrieve cached prediction result.

    Returns None if not found or Redis is unavailable.
    """
    client = _get_redis()
    if client is None:
        return None
    try:
        data = client.get(f"pred:{hash_key}")
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_prediction(hash_key: str, result: dict[str, Any], ttl: int = 3600) -> None:
    """
    Cache a prediction result with TTL (default 1 hour).

    Silently fails if Redis is unavailable.
    """
    client = _get_redis()
    if client is None:
        return
    try:
        # Exclude large fields from cache
        cacheable = {k: v for k, v in result.items() if k != "gradcam_image"}
        client.setex(f"pred:{hash_key}", ttl, json.dumps(cacheable))
    except Exception:
        pass  # cache miss is not critical


def invalidate_cache(hash_key: str) -> None:
    """Remove a specific prediction from cache."""
    client = _get_redis()
    if client is None:
        return
    with contextlib.suppress(Exception):
        client.delete(f"pred:{hash_key}")
