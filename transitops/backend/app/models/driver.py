"""Driver model — compliance profile + status state machine (docs/02 §3 `drivers`)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import DriverStatus, pg_enum


class Driver(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint(
            "contact_number ~ '^[0-9+][0-9 -]{7,14}$'", name="ck_drivers_contact"
        ),
        CheckConstraint(
            "safety_score BETWEEN 0 AND 100", name="ck_drivers_safety_score"
        ),
        Index("ix_drivers_status", "status"),
        Index("ix_drivers_license_expiry", "license_expiry"),
    )

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    license_number: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True
    )  # BR-1
    license_category: Mapped[str] = mapped_column(String(10), nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    contact_number: Mapped[str] = mapped_column(String(15), nullable=False)
    safety_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("100")
    )
    status: Mapped[DriverStatus] = mapped_column(
        pg_enum(DriverStatus, "driver_status"),
        nullable=False,
        server_default=text("'available'"),
    )
