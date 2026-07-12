"""Fuel log schemas (docs/03 §4 Fuel & Expenses)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FuelLogCreate(BaseModel):
    vehicle_id: uuid.UUID
    liters: Decimal = Field(gt=0)
    cost: Decimal = Field(ge=0)
    filled_at: date | None = None
    odometer_at_fill: Decimal | None = Field(default=None, ge=0)
    trip_id: uuid.UUID | None = None


class FuelLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    trip_id: uuid.UUID | None
    liters: Decimal
    cost: Decimal
    odometer_at_fill: Decimal | None
    filled_at: date
    created_by: uuid.UUID
    created_at: datetime
