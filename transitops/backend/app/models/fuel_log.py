"""FuelLog ORM model — docs/02-DATABASE.md §3 table: fuel_logs.

trip_id is optional (SET NULL on trip delete): fuel can be logged outside
a trip context, or linked to a completed trip for the completion fuel flow.
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.db.base_class import Base


class FuelLog(Base):
    """Fuel fill record — contributes to operational cost and fuel-efficiency KPI."""
    __tablename__ = "fuel_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
    )
    liters = Column(Numeric(8, 2), nullable=False)
    cost = Column(Numeric(12, 2), nullable=False)
    odometer_at_fill = Column(Numeric(12, 2), nullable=True)
    filled_at = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("liters > 0", name="ck_fuel_logs_liters"),
        CheckConstraint("cost >= 0", name="ck_fuel_logs_cost"),
        CheckConstraint(
            "odometer_at_fill IS NULL OR odometer_at_fill >= 0",
            name="ck_fuel_logs_odometer_at_fill",
        ),
        Index("ix_fuel_vehicle_date", "vehicle_id", "filled_at"),
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="fuel_logs")
    trip = relationship("Trip", back_populates="fuel_logs")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<FuelLog {self.liters}L @ {self.filled_at}>"
