"""Expense schemas (docs/03 §4 Fuel & Expenses)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExpenseType


class ExpenseCreate(BaseModel):
    vehicle_id: uuid.UUID
    type: ExpenseType
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)
    incurred_at: date | None = None
    trip_id: uuid.UUID | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    trip_id: uuid.UUID | None
    type: ExpenseType
    amount: Decimal
    description: str | None
    incurred_at: date
    created_by: uuid.UUID
    created_at: datetime
