"""Maintenance schemas (docs/03 §4 Maintenance)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MaintenanceStatus


class MaintenanceCreate(BaseModel):
    vehicle_id: uuid.UUID
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    cost: Decimal = Field(default=Decimal("0"), ge=0)


class MaintenanceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    cost: Decimal | None = Field(default=None, ge=0)


class MaintenanceClose(BaseModel):
    cost: Decimal | None = Field(default=None, ge=0)


class MaintenanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    title: str
    description: str | None
    cost: Decimal
    status: MaintenanceStatus
    opened_at: datetime
    closed_at: datetime | None
    created_by: uuid.UUID
