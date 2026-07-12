"""AI settings endpoints (docs/03 §4 AI, docs/06 §5). Chat endpoints add in BE-14."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ai import (
    AISettingsFull,
    AISettingsPublic,
    AISettingsUpdate,
    ChatRequest,
    ChatResponse,
    MessageOut,
    SessionOut,
)
from app.services.ai import chat as chat_service
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


@router.get("/sessions", response_model=list[SessionOut], summary="List my chat sessions")
def list_sessions(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[SessionOut]:
    return chat_service.list_sessions(db, user)


@router.post("/sessions", response_model=SessionOut, status_code=201, summary="New chat session")
def create_session(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> SessionOut:
    return chat_service.create_session(db, user)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[MessageOut],
    summary="Messages in a session (owner only)",
)
def session_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MessageOut]:
    return chat_service.get_session_messages(db, user, session_id)


@router.post("/chat", response_model=ChatResponse, summary="Chat with the fleet assistant")
def chat(
    body: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> ChatResponse:
    result = chat_service.chat(db, user, body.message, session_id=body.session_id)
    return ChatResponse(**result)
