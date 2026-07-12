"""Fuel log — liters/cost per vehicle, optionally linked to a trip (docs/02 §3)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin


class FuelLog(UUIDPKMixin, Base):
    __tablename__ = "fuel_logs"
    __table_args__ = (
        CheckConstraint("liters > 0", name="ck_fuel_liters_pos"),
        CheckConstraint("cost >= 0", name="ck_fuel_cost_nonneg"),
        CheckConstraint(
            "odometer_at_fill IS NULL OR odometer_at_fill >= 0",
            name="ck_fuel_odometer_nonneg",
        ),
        Index("ix_fuel_vehicle_date", "vehicle_id", "filled_at"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True
    )
    liters: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    odometer_at_fill: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    filled_at: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle")  # noqa: F821
    trip: Mapped["Trip | None"] = relationship("Trip")  # noqa: F821
