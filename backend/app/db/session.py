"""Async engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _prepare_sqlite_dir(database_url: str) -> None:
    """Ensure the parent directory of a SQLite file exists."""
    marker = "sqlite+aiosqlite:///"
    if database_url.startswith(marker):
        raw = database_url[len(marker):]
        if raw and raw != ":memory:":
            db_path = (
                Path(raw)
                if raw.startswith("/")
                else settings.resolve_path(raw.lstrip("/"))
            )
            db_path.parent.mkdir(parents=True, exist_ok=True)


_prepare_sqlite_dir(settings.database_url)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        yield session
