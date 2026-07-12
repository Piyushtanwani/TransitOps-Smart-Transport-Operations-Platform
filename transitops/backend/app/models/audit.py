"""AuditLog ORM model — docs/02-DATABASE.md §3 table: audit_logs.

BIGSERIAL PK (auto-incrementing integer) — not UUID — so audit entries are
naturally ordered by insertion and the serial itself is a monotonic audit trail.
JSONB payload stores the before/after state snapshot.
"""
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.db.base_class import Base


class AuditLog(Base):
    """Immutable audit entry — written inside every lifecycle-changing service call."""
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)          # BIGSERIAL
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,                                                      # nullable: system events
    )
    action = Column(String(60), nullable=False)                            # 'trip.dispatch', 'vehicle.create' …
    entity = Column(String(30), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user={self.user_id}>"
