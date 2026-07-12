"""Expense ORM model — docs/02-DATABASE.md §3 table: expenses.

trip_id is optional (SET NULL): expenses can be unlinked from a trip (e.g.
depot charges, tolls on multi-trip days). Type is a DB ENUM so illegal
categories cannot be stored.
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
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
from app.models.enums import ExpenseType


class Expense(Base):
    """Other operational expense (toll, parking, fine, loading, other)."""
    __tablename__ = "expenses"

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
    type = Column(
        SAEnum(
            ExpenseType,
            name="expense_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=True)
    incurred_at = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount"),
        Index("ix_expenses_vehicle_date", "vehicle_id", "incurred_at"),
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="expenses")
    trip = relationship("Trip", back_populates="expenses")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Expense {self.type} ₹{self.amount}>"
