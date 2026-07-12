"""Trip model — dispatch lifecycle + BR-4 partial unique indexes (docs/02 §3 `trips`)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import TripStatus, pg_enum

# App-generated trip codes (TRP-0001) draw from this sequence — see BE-07.
trip_code_seq = Sequence("trip_code_seq", start=1, metadata=Base.metadata)


class Trip(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint(
            "end_odometer IS NULL OR start_odometer IS NULL OR end_odometer >= start_odometer",
            name="ck_trips_odometer",
        ),
        CheckConstraint(
            "status <> 'completed' OR (start_odometer IS NOT NULL AND end_odometer IS NOT NULL)",
            name="ck_trips_completed_fields",
        ),
        Index("ix_trips_status", "status"),
        Index("ix_trips_vehicle", "vehicle_id"),
        Index("ix_trips_driver", "driver_id"),
        # ★ BR-4: the DB itself forbids a second dispatched trip per vehicle/driver.
        Index(
            "uq_trips_active_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("status = 'dispatched'"),
        ),
        Index(
            "uq_trips_active_driver",
            "driver_id",
            unique=True,
            postgresql_where=text("status = 'dispatched'"),
        ),
    )

    trip_code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False
    )
    cargo_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    planned_distance_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    status: Mapped[TripStatus] = mapped_column(
        pg_enum(TripStatus, "trip_status"),
        nullable=False,
        server_default=text("'draft'"),
    )
    start_odometer: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    end_odometer: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle")  # noqa: F821
    driver: Mapped["Driver"] = relationship("Driver")  # noqa: F821
    creator: Mapped["User"] = relationship("User")  # noqa: F821
