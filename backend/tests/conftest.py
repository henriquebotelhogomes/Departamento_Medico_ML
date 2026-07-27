"""Pytest fixtures: isolated SQLite DB, temp storage and a fake predictor."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

# Configure the environment BEFORE importing the app so settings pick it up.
_TMP = Path(tempfile.mkdtemp(prefix="radioai_test_"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_DIR"] = str(_TMP / "uploads")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "development"

import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402

from app.api.routers import predictions as predictions_router  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_demo_user  # noqa: E402


class FakePredictor:
    is_ready = True

    def predict(self, image_bytes: bytes) -> dict:
        return {
            "predicted_class": 1,
            "label": "Normal",
            "confidence": 0.97,
            "probs": {0: 0.01, 1: 0.97, 2: 0.01, 3: 0.01},
            "inference_ms": 12.3,
        }


@pytest.fixture(autouse=True)
def _fake_predictor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(predictions_router, "get_predictor", lambda: FakePredictor())


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_demo_user(session)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _register(client: httpx.AsyncClient, username: str, email: str, password: str):
    return await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


async def auth_headers(
    client: httpx.AsyncClient, username: str = "demo123", password: str = "demo123"
) -> dict[str, str]:
    resp = await client.post(
        "/api/auth/login", data={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
