"""Prediction endpoint tests (inference is mocked via FakePredictor)."""

from __future__ import annotations

import io

import httpx
from PIL import Image

from tests.conftest import auth_headers


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (256, 256), color=(120, 120, 120)).save(buf, format="PNG")
    return buf.getvalue()


async def _predict(client: httpx.AsyncClient, headers: dict) -> httpx.Response:
    files = {"file": ("xray.png", _png_bytes(), "image/png")}
    return await client.post("/api/predictions", files=files, headers=headers)


async def test_predict_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await _predict(client, headers={})
    assert resp.status_code == 401


async def test_predict_success(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    resp = await _predict(client, headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["label"] == "Normal"
    assert body["predicted_class"] == 1
    assert 0.0 <= body["confidence"] <= 1.0
    assert len(body["probs"]) == 4
    assert body["image_url"]


async def test_predict_rejects_non_image(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    files = {"file": ("note.txt", b"hello", "text/plain")}
    resp = await client.post("/api/predictions", files=files, headers=headers)
    assert resp.status_code == 415


async def test_history_and_detail(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    await _predict(client, headers)
    await _predict(client, headers)

    listing = await client.get("/api/predictions", headers=headers)
    assert listing.status_code == 200
    data = listing.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    pid = data["items"][0]["id"]
    detail = await client.get(f"/api/predictions/{pid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == pid


async def test_delete_prediction(client: httpx.AsyncClient) -> None:
    headers = await auth_headers(client)
    created = await _predict(client, headers)
    pid = created.json()["id"]

    deleted = await client.delete(f"/api/predictions/{pid}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/predictions/{pid}", headers=headers)
    assert missing.status_code == 404


async def test_history_isolated_between_users(client: httpx.AsyncClient) -> None:
    demo = await auth_headers(client)
    await _predict(client, demo)

    await client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "secret1"},
    )
    carol = await auth_headers(client, "carol", "secret1")
    listing = await client.get("/api/predictions", headers=carol)
    assert listing.json()["total"] == 0
