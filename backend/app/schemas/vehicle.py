"""Vehicle schemas (docs/03 §4 Vehicles). Status is never set via create/patch."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VehicleStatus, VehicleType


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=80)
    type: VehicleType
    max_load_capacity_kg: Decimal = Field(gt=0)
    odometer_km: Decimal = Field(default=Decimal("0"), ge=0)
    acquisition_cost: Decimal = Field(gt=0)
    region: str = Field(min_length=1, max_length=40)


class VehicleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: VehicleType | None = None
    max_load_capacity_kg: Decimal | None = Field(default=None, gt=0)
    acquisition_cost: Decimal | None = Field(default=None, gt=0)
    region: str | None = Field(default=None, min_length=1, max_length=40)
    odometer_km: Decimal | None = Field(default=None, ge=0)


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    registration_number: str
    name: str
    type: VehicleType
    max_load_capacity_kg: Decimal
    odometer_km: Decimal
    acquisition_cost: Decimal
    region: str
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime


class VehicleDetail(VehicleOut):
    """Detail view adds cheap rollups (docs/03 §4)."""

    open_maintenance: bool = False
    active_trip_code: str | None = None
