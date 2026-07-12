"""Maintenance log — one open job per vehicle (docs/02 §3 `maintenance_logs`)."""
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
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin
from app.models.enums import MaintenanceStatus, pg_enum


class MaintenanceLog(UUIDPKMixin, Base):
    __tablename__ = "maintenance_logs"
    __table_args__ = (
        CheckConstraint(
            "status <> 'closed' OR closed_at IS NOT NULL", name="ck_maint_closed"
        ),
        # one open maintenance job per vehicle
        Index(
            "uq_maint_open_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        Index("ix_maint_vehicle", "vehicle_id"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0")
    )
    status: Mapped[MaintenanceStatus] = mapped_column(
        pg_enum(MaintenanceStatus, "maintenance_status"),
        nullable=False,
        server_default=text("'open'"),
    )
    opened_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle")  # noqa: F821
