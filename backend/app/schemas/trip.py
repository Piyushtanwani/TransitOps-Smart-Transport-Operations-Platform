"""Trip schemas (docs/03 §4 Trips). trip_code is server-generated, never client-set."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TripStatus


class TripCreate(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    cargo_weight_kg: Decimal = Field(gt=0)
    planned_distance_km: Decimal = Field(gt=0)
    revenue: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = None


class TripComplete(BaseModel):
    end_odometer: Decimal = Field(ge=0)
    revenue: Decimal | None = Field(default=None, ge=0)
    fuel_liters: Decimal | None = Field(default=None, gt=0)
    fuel_cost: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _fuel_both_or_neither(self) -> "TripComplete":
        if (self.fuel_liters is None) != (self.fuel_cost is None):
            raise ValueError("Provide both fuel_liters and fuel_cost, or neither.")
        return self


class TripCancel(BaseModel):
    reason: str | None = None


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_code: str
    source: str
    destination: str
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    cargo_weight_kg: Decimal
    planned_distance_km: Decimal
    revenue: Decimal
    status: TripStatus
    start_odometer: Decimal | None
    end_odometer: Decimal | None
    notes: str | None
    created_by: uuid.UUID
    dispatched_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
