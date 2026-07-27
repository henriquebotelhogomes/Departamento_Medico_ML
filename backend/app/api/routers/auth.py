"""Authentication endpoints: register, login, refresh, me."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_user_by_identifier
from app.core.logging import get_logger
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DbSession) -> User:
    email = payload.email.lower()
    exists = await db.execute(
        select(User).where((User.username == payload.username) | (User.email == email))
    )
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )
    user = User(
        username=payload.username,
        email=email,
        hashed_password=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("user_registered", user_id=user.id, username=user.username)
    return user


@router.post("/login", response_model=TokenPair)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenPair:
    """Login with username OR email in the ``username`` field."""
    user = await get_user_by_identifier(db, form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    logger.info("user_login", user_id=user.id, username=user.username)
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != REFRESH_TOKEN_TYPE:
            raise ValueError("wrong token type")
        user_id = int(data["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser) -> User:
    return current_user
