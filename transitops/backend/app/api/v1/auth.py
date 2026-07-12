"""Auth endpoints: login, refresh (rotation), me (docs/03 §4)."""
from __future__ import annotations

import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.errors import APIError, AuthError
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

_INVALID = ("INVALID_CREDENTIALS", "Invalid email or password.")

# Product choice (overrides the earlier no-enumeration stance, see Change Log):
# specific, human-friendly login errors — balanced by per-identity rate limiting below.
_MAX_FAILURES = 8
_WINDOW = timedelta(minutes=5)
_failed_logins: dict[str, deque] = defaultdict(deque)


def _throttle(key: str) -> None:
    now = datetime.now(UTC)
    attempts = _failed_logins[key]
    while attempts and now - attempts[0] > _WINDOW:
        attempts.popleft()
    if len(attempts) >= _MAX_FAILURES:
        raise APIError(
            "TOO_MANY_ATTEMPTS",
            "Too many failed sign-in attempts. Please wait a few minutes and try again.",
            status_code=429,
        )


def _record_failure(key: str) -> None:
    _failed_logins[key].append(datetime.now(UTC))


def _issue(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenPair, summary="Email + password login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    email = str(body.email).strip().lower()
    key = f"{request.client.host if request.client else 'unknown'}:{email}"
    _throttle(key)

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        _record_failure(key)
        raise AuthError(
            "EMAIL_NOT_FOUND",
            "No account found with this email address.",
            field="email",
        )
    if not verify_password(body.password, user.hashed_password):
        _record_failure(key)
        raise AuthError(
            "INCORRECT_PASSWORD",
            "Incorrect password. Please try again.",
            field="password",
        )
    if not user.is_active:
        raise AuthError(
            "ACCOUNT_DISABLED",
            "This account has been deactivated. Please contact your Fleet Manager.",
            field="email",
        )
    _failed_logins.pop(key, None)  # success clears the counter
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
