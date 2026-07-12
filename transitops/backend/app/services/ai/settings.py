"""AI settings singleton access + graceful-degradation guard (docs/06)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.ai_settings import AISettings
from app.models.user import User
from app.services.ai.defaults import DEFAULT_ROLE_TOOL_PERMISSIONS, DEFAULT_SYSTEM_PROMPT
from app.services.audit import audit


def get_settings_row(db: Session) -> AISettings:
    """Return the singleton ai_settings row, creating defaults if absent."""
    row = db.get(AISettings, 1)
    if row is None:
        row = AISettings(
            id=1,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            role_tool_permissions=DEFAULT_ROLE_TOOL_PERMISSIONS,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def resolve_api_key(row: AISettings) -> str:
    """DB-stored key (set from the admin UI) wins; env var is the fallback."""
    return (row.openrouter_api_key or "").strip() or get_settings().OPENROUTER_API_KEY.strip()


def ensure_ai_enabled(db: Session) -> AISettings:
    """Raise 503 AI_DISABLED when no key is available or the chatbot is switched off."""
    row = get_settings_row(db)
    if not resolve_api_key(row):
        raise DomainError(
            "AI_DISABLED",
            "OpenRouter is not configured. A Fleet Manager can add an API key in AI Settings.",
            status_code=503,
        )
    if not row.chatbot_enabled:
        raise DomainError(
            "AI_DISABLED",
            "The AI assistant is turned off. A Fleet Manager can enable it in AI Settings.",
            status_code=503,
        )
    return row


def update_settings(db: Session, data: dict, actor: User) -> AISettings:
    row = get_settings_row(db)
    for field, value in data.items():
        setattr(row, field, value)
    row.updated_by = actor.id
    audit(db, actor, "ai.settings.update", None, payload={"fields": list(data.keys())})
    db.commit()
    db.refresh(row)
    return row
