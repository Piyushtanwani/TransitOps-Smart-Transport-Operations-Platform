"""Vehicle model — fleet asset with status state machine (docs/02 §3 `vehicles`)."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import VehicleStatus, VehicleType, pg_enum


class Vehicle(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("max_load_capacity_kg > 0", name="ck_vehicles_capacity_pos"),
        CheckConstraint("odometer_km >= 0", name="ck_vehicles_odometer_nonneg"),
        CheckConstraint("acquisition_cost > 0", name="ck_vehicles_acqcost_pos"),
        Index("ix_vehicles_status", "status"),
        Index("ix_vehicles_type_region", "type", "region"),
    )

    registration_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )  # BR-1
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[VehicleType] = mapped_column(
        pg_enum(VehicleType, "vehicle_type"), nullable=False
    )
    max_load_capacity_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    odometer_km: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0")
    )
    acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    region: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(
        pg_enum(VehicleStatus, "vehicle_status"),
        nullable=False,
        server_default=text("'available'"),
    )
