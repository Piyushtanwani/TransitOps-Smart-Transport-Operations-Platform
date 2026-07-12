"""Vehicle ORM model — docs/02-DATABASE.md §3 table: vehicles.

Indexes:
  ix_vehicles_status        — on status (dashboard filter, dispatch pool)
  ix_vehicles_type_region   — on (type, region) (dashboard filter)
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
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
from app.models.enums import VehicleStatus, VehicleType


class Vehicle(Base):
    """Fleet asset — unique registration, typed, capacity-checked."""
    __tablename__ = "vehicles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    registration_number = Column(String(20), nullable=False, unique=True)  # BR-1
    name = Column(String(80), nullable=False)                              # e.g. "Tata Ace Van-05"
    type = Column(
        SAEnum(
            VehicleType,
            name="vehicle_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    max_load_capacity_kg = Column(
        Numeric(10, 2), nullable=False
    )
    odometer_km = Column(
        Numeric(12, 2), nullable=False, server_default=text("0")
    )
    acquisition_cost = Column(
        Numeric(14, 2), nullable=False
    )                                                                       # ROI divisor
    region = Column(String(40), nullable=False)                            # North/South/East/West
    status = Column(
        SAEnum(
            VehicleStatus,
            name="vehicle_status",
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
        CheckConstraint("max_load_capacity_kg > 0", name="ck_vehicles_max_load_capacity_kg"),
        CheckConstraint("odometer_km >= 0", name="ck_vehicles_odometer_km"),
        CheckConstraint("acquisition_cost > 0", name="ck_vehicles_acquisition_cost"),
        Index("ix_vehicles_status", "status"),
        Index("ix_vehicles_type_region", "type", "region"),
    )

    # Relationships
    trips = relationship("Trip", back_populates="vehicle")
    maintenance_logs = relationship("MaintenanceLog", back_populates="vehicle")
    fuel_logs = relationship("FuelLog", back_populates="vehicle")
    expenses = relationship("Expense", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle {self.registration_number} ({self.status})>"
