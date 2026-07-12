"""AI settings — singleton config row (id=1) with per-role tool permissions (docs/02 §3)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AISettings(Base):
    __tablename__ = "ai_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_ai_settings_singleton"),
        CheckConstraint("temperature BETWEEN 0 AND 2", name="ck_ai_settings_temperature"),
        CheckConstraint(
            "max_tokens BETWEEN 128 AND 8192", name="ck_ai_settings_max_tokens"
        ),
    )

    id: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, server_default=text("1"), autoincrement=False
    )
    chatbot_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    model: Mapped[str] = mapped_column(
        String(80), nullable=False, server_default=text("'anthropic/claude-3.5-haiku'")
    )
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, server_default=text("0.30")
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1024")
    )
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    role_tool_permissions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
