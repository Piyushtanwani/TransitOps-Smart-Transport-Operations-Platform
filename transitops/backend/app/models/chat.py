"""Chat ORM models — docs/02-DATABASE.md §3 tables: chat_sessions, chat_messages.

All chat history is persisted in PostgreSQL (never localStorage) — see CLAUDE.md §1.
tool_calls JSONB column stores the tool invocations for transparency (judges can inspect
what the AI called).
"""
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum

from app.db.base_class import Base
from app.models.enums import ChatRole


class ChatSession(Base):
    """One conversation thread per user — multiple sessions allowed."""
    __tablename__ = "chat_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(120), nullable=False, server_default=text("'New chat'"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.id} user={self.user_id}>"


class ChatMessage(Base):
    """Individual message in a chat session — role ∈ {user, assistant, tool}."""
    __tablename__ = "chat_messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(
        SAEnum(
            ChatRole,
            name="chat_role",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    tool_calls = Column(JSONB, nullable=True)                              # persisted for transparency
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_chat_messages_session", "session_id", "created_at"),
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage role={self.role} session={self.session_id}>"
