"""Authentication flow tests, including the seeded demo account."""

from __future__ import annotations

import httpx

from tests.conftest import _register, auth_headers


async def test_demo_login(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/auth/login", data={"username": "demo123", "password": "demo123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]


async def test_demo_login_with_email(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login", data={"username": "demo123@example.com", "password": "demo123"}
    )
    assert resp.status_code == 200


async def test_login_wrong_password(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/auth/login", data={"username": "demo123", "password": "nope"})
    assert resp.status_code == 401


async def test_register_and_me(client: httpx.AsyncClient) -> None:
    resp = await _register(client, "alice", "alice@example.com", "secret1")
    assert resp.status_code == 201, resp.text
    headers = await auth_headers(client, "alice", "secret1")
    me = await client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


async def test_register_duplicate(client: httpx.AsyncClient) -> None:
    await _register(client, "bob", "bob@example.com", "secret1")
    dup = await _register(client, "bob", "other@example.com", "secret1")
    assert dup.status_code == 409


async def test_me_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_refresh_token(client: httpx.AsyncClient) -> None:
    login = await client.post(
        "/api/auth/login", data={"username": "demo123", "password": "demo123"}
    )
    refresh = login.json()["refresh_token"]
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]
