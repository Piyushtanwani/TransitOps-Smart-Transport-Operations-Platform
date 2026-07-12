"""User management schemas (docs/03 §4 Users). FM-only surface."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.enums import UserRole

_PW_MSG = "Password must be at least 8 characters and include at least one digit."


def _check_password(v: str) -> str:
    if len(v) < 8 or not any(c.isdigit() for c in v):
        raise ValueError(_PW_MSG)
    return v


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    password: str

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str) -> str:
        return _check_password(v)


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str | None) -> str | None:
        return _check_password(v) if v is not None else v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
