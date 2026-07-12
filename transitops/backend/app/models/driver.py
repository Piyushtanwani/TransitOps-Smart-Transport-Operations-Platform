"""Driver ORM model — docs/02-DATABASE.md §3 table: drivers.

Indexes:
  ix_drivers_status          — dispatch/assignable filter
  ix_drivers_license_expiry  — expiry alert banner (BR-3)
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum

from app.db.base_class import Base
from app.models.enums import DriverStatus


class Driver(Base):
    """Driver profile — license expiry + safety score tracked."""
    __tablename__ = "drivers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    full_name = Column(String(120), nullable=False)
    license_number = Column(String(30), nullable=False, unique=True)       # BR-1
    license_category = Column(String(10), nullable=False)                  # LMV / HMV / MCWG …
    license_expiry = Column(Date, nullable=False)
    contact_number = Column(String(15), nullable=False)
    safety_score = Column(
        Numeric(5, 2), nullable=False, server_default=text("100")
    )
    status = Column(
        SAEnum(
            DriverStatus,
            name="driver_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        server_default=text("'available'"),
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            r"contact_number ~ '^[0-9+][0-9 -]{7,14}$'",
            name="ck_drivers_contact_number",
        ),
        CheckConstraint(
            "safety_score BETWEEN 0 AND 100",
            name="ck_drivers_safety_score",
        ),
        Index("ix_drivers_status", "status"),
        Index("ix_drivers_license_expiry", "license_expiry"),
    )

    # Relationships
    trips = relationship("Trip", back_populates="driver")

    def __repr__(self) -> str:
        return f"<Driver {self.full_name} ({self.status})>"
