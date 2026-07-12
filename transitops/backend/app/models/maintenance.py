"""MaintenanceLog ORM model — docs/02-DATABASE.md §3 table: maintenance_logs.

Partial unique index:
  uq_maint_open_per_vehicle  — one open job per vehicle at a time (BR-9)

CHECK:
  ck_maint_closed  — closed records must have a closed_at timestamp
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum

from app.db.base_class import Base
from app.models.enums import MaintenanceStatus


class MaintenanceLog(Base):
    """Maintenance record — opening sets vehicle in_shop (BR-9); closing restores available (BR-10)."""
    __tablename__ = "maintenance_logs"

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
    title = Column(String(120), nullable=False)                            # e.g. "Oil Change"
    description = Column(Text, nullable=True)
    cost = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    status = Column(
        SAEnum(
            MaintenanceStatus,
            name="maintenance_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        server_default=text("'open'"),
    )
    opened_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("cost >= 0", name="ck_maintenance_cost"),
        CheckConstraint(
            "status <> 'closed' OR closed_at IS NOT NULL",
            name="ck_maint_closed",
        ),
        # Partial unique: only one open maintenance job per vehicle at a time
        Index(
            "uq_maint_open_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        Index("ix_maint_vehicle", "vehicle_id"),
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_logs")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<MaintenanceLog {self.title} ({self.status})>"
