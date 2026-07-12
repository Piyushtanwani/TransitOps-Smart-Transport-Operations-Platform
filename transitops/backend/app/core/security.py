"""Password hashing (bcrypt) + JWT access/refresh token issue/decode."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# passlib 1.7.4 logs a benign "error reading bcrypt version" against bcrypt>=4.1; mute it.
logging.getLogger("passlib").setLevel(logging.ERROR)

ALGORITHM = "HS256"
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (cost 12)."""
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time verify of a plaintext password against a bcrypt hash."""
    try:
        return _pwd.verify(plain, hashed)
    except ValueError:
        return False


def _role_value(user: Any) -> str:
    role = getattr(user, "role", None)
    return role.value if hasattr(role, "value") else str(role)


def create_access_token(user: Any) -> str:
    """Access JWT: claims sub (user id), role, type='access', exp = now + TTL minutes."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user.id),
        "role": _role_value(user),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TTL_MIN),
    }
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user: Any) -> str:
    """Refresh JWT: unique jti, type='refresh', exp = now + TTL days."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user.id),
        "role": _role_value(user),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TTL_DAYS),
    }
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode + verify a JWT. Raises `TokenError` on invalid/expired tokens."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("TOKEN_EXPIRED", "Your session has expired. Please log in again.") from exc
    except JWTError as exc:
        raise TokenError("INVALID_TOKEN", "Invalid authentication token.") from exc


class TokenError(Exception):
    """Raised by `decode_token` — mapped to 401 by the deps layer."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
