"""User ORM model — docs/02-DATABASE.md §3 table: users."""
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum

from app.db.base_class import Base
from app.models.enums import UserRole


class User(Base):
    """Stores all authenticated principals (4 roles: fleet_manager, driver,
    safety_officer, financial_analyst).
    """
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(
        SAEnum(
            UserRole,
            name="user_role",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, server_default=text("TRUE"))
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
            r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'",
            name="ck_users_email",
        ),
    )

    # Relationships (back-populated by child models)
    trips_created = relationship("Trip", foreign_keys="Trip.created_by", back_populates="creator")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
