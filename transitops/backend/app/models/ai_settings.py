"""AISettings ORM model — docs/02-DATABASE.md §3 table: ai_settings.

Singleton row: id=1 enforced by CHECK(id=1) and DEFAULT 1.
role_tool_permissions is a JSONB column storing the per-role tool allowlist
from docs/06-AI-FEATURES.md §4, managed via the admin AI Settings page.
"""
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.db.base_class import Base


class AISettings(Base):
    """Singleton AI configuration row — id is always 1, enforced by CHECK."""
    __tablename__ = "ai_settings"

    id = Column(
        SmallInteger,
        primary_key=True,
        server_default=text("1"),
    )
    chatbot_enabled = Column(
        Boolean, nullable=False, server_default=text("TRUE")
    )
    model = Column(
        String(80),
        nullable=False,
        server_default=text("'anthropic/claude-3.5-haiku'"),
    )
    temperature = Column(
        Numeric(3, 2), nullable=False, server_default=text("0.30")
    )
    max_tokens = Column(
        Integer, nullable=False, server_default=text("1024")
    )
    system_prompt = Column(Text, nullable=False)
    role_tool_permissions = Column(JSONB, nullable=False)                  # {"driver": ["get_vehicles", ...], ...}
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_ai_settings_singleton"),
        CheckConstraint("temperature BETWEEN 0 AND 2", name="ck_ai_settings_temperature"),
        CheckConstraint(
            "max_tokens BETWEEN 128 AND 8192", name="ck_ai_settings_max_tokens"
        ),
    )

    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<AISettings model={self.model} enabled={self.chatbot_enabled}>"
