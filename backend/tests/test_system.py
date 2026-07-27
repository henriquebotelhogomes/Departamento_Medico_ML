"""System and statistics endpoint tests."""

from __future__ import annotations

import io

import httpx
from PIL import Image

from tests.conftest import auth_headers


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (256, 256), color=(90, 90, 90)).save(buf, format="PNG")
    return buf.getvalue()


async def test_health(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_version(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app"]
    assert len(body["classes"]) == 4


async def test_stats_empty(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    resp = await client.get("/api/stats", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_predictions"] == 0
    assert len(body["by_class"]) == 4


async def test_stats_after_predictions(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    files = {"file": ("x.png", _png_bytes(), "image/png")}
    await client.post("/api/predictions", files=files, headers=headers)

    resp = await client.get("/api/stats", headers=headers)
    body = resp.json()
    assert body["total_predictions"] == 1
    assert body["average_confidence"] > 0
    normal = next(c for c in body["by_class"] if c["class_id"] == 1)
    assert normal["count"] == 1
    assert len(body["over_time"]) >= 1
