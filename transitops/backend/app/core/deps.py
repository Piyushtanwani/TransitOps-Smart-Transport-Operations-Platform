"""Request dependencies: DB session, current user (JWT→DB), role gate."""
from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AuthError, ForbiddenError
from app.core.security import TokenError, decode_token
from app.db.session import SessionLocal
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("INVALID_CREDENTIALS", "Not authenticated.")
    return token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Decode the access token, load the user, enforce active + access-type."""
    token = _bearer_token(request)
    try:
        payload = decode_token(token)
    except TokenError as exc:
        raise AuthError(exc.code, exc.message) from exc

    if payload.get("type") != "access":
        raise AuthError("INVALID_TOKEN", "Invalid authentication token.")

    sub = payload.get("sub")
    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, TypeError) as exc:
        raise AuthError("INVALID_TOKEN", "Invalid authentication token.") from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        # Revocation without a token blacklist: a deactivated user cannot authenticate.
        raise AuthError("INVALID_CREDENTIALS", "Not authenticated.")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    """Dependency factory → 403 `FORBIDDEN_ROLE` unless the user holds one of `roles`."""
    allowed = set(roles)

    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed:
            raise ForbiddenError()
        return user

    return _guard
