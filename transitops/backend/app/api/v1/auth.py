"""Auth endpoints: login, refresh (rotation), me (docs/03 §4)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.errors import AuthError
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserPublic

router = APIRouter(prefix="/auth", tags=["Auth"])

# Same message for unknown-email and wrong-password — no user enumeration (docs/03 §4).
_INVALID = ("INVALID_CREDENTIALS", "Invalid email or password.")


def _issue(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenPair, summary="Email + password login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.execute(
        select(User).where(User.email == str(body.email))
    ).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise AuthError(*_INVALID)
    if not user.is_active:
        raise AuthError(*_INVALID)
    return _issue(user)


@router.post("/refresh", response_model=TokenPair, summary="Rotate access + refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token)
    except TokenError as exc:
        raise AuthError(exc.code, exc.message) from exc
    if payload.get("type") != "refresh":
        raise AuthError("INVALID_TOKEN", "A refresh token is required.")
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except (ValueError, TypeError) as exc:
        raise AuthError("INVALID_TOKEN", "Invalid authentication token.") from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthError(*_INVALID)
    # Rotation returns a fresh pair; server-side jti allowlist is the noted prod upgrade.
    return _issue(user)


@router.get("/me", response_model=UserPublic, summary="Current authenticated user")
def me(user: User = Depends(get_current_user)) -> User:
    return user
