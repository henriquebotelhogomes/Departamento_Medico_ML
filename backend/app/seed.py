"""Idempotent seeding of the demo account (portfolio showcase)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.user import User

logger = get_logger(__name__)


async def seed_demo_user(db: AsyncSession) -> None:
    """Create the demo user if it does not exist yet. Safe to call repeatedly."""
    username = settings.demo_username
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none() is not None:
        logger.info("demo_user_exists", username=username)
        return

    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password(settings.demo_password),
        role="user",
    )
    db.add(user)
    await db.commit()
    logger.info("demo_user_created", username=username)
