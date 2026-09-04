"""Shared API dependencies (authentication / authorization)."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise _credentials_exc
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _credentials_exc from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise _credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_user_by_identifier(db: AsyncSession, identifier: str) -> User | None:
    """Look up a user by username or email (used at login)."""
    stmt = select(User).where((User.username == identifier) | (User.email == identifier.lower()))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
