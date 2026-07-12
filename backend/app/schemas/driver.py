"""Driver schemas (docs/03 §4 Drivers). Status changes go through /status only."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DriverStatus

_CONTACT = r"^[0-9+][0-9 -]{7,14}$"


class DriverCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    license_number: str = Field(min_length=1, max_length=30)
    license_category: str = Field(min_length=1, max_length=10)
    license_expiry: date
    contact_number: str = Field(pattern=_CONTACT)
    safety_score: Decimal = Field(default=Decimal("100"), ge=0, le=100)


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    license_number: str | None = Field(default=None, min_length=1, max_length=30)
    license_category: str | None = Field(default=None, min_length=1, max_length=10)
    license_expiry: date | None = None
    contact_number: str | None = Field(default=None, pattern=_CONTACT)
    safety_score: Decimal | None = Field(default=None, ge=0, le=100)


class DriverStatusUpdate(BaseModel):
    # on_trip is never set manually (docs/04 §2).
    status: Literal["off_duty", "available", "suspended"]


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    license_number: str
    license_category: str
    license_expiry: date
    contact_number: str
    safety_score: Decimal
    status: DriverStatus
    created_at: datetime
    updated_at: datetime
