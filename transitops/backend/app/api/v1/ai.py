"""AI settings endpoints (docs/03 §4 AI, docs/06 §5). Chat endpoints add in BE-14."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ai import AISettingsFull, AISettingsPublic, AISettingsUpdate
from app.services.ai.settings import get_settings_row, update_settings

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/settings", summary="AI settings (redacted for non-FM)")
def get_ai_settings(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> AISettingsPublic | AISettingsFull:
    row = get_settings_row(db)
    if user.role == UserRole.fleet_manager:
        return AISettingsFull.model_validate(row)
    return AISettingsPublic(chatbot_enabled=row.chatbot_enabled, model=row.model)


@router.put("/settings", response_model=AISettingsFull, summary="Update AI settings (FM)")
def put_ai_settings(
    body: AISettingsUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("fleet_manager")),
) -> AISettingsFull:
    data = body.model_dump(exclude_unset=True)
    row = update_settings(db, data, actor)
    return AISettingsFull.model_validate(row)
