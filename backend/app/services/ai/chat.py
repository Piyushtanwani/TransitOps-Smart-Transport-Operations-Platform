"""RBAC-aware tool-calling chat loop with persistence (docs/06 §3)."""
from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import ChatRole
from app.models.user import User
from app.services.ai.client import OpenRouterError, call_openrouter
from app.services.ai.context import build_system_prompt
from app.services.ai.settings import ensure_ai_enabled, get_settings_row, resolve_api_key
from app.services.ai.tools import TOOLS
from app.services.audit import audit

_MAX_ITERATIONS = 4
_HISTORY = 20


def _get_or_create_session(db, user, session_id, first_message) -> ChatSession:
    if session_id is not None:
        session = db.get(ChatSession, session_id)
        if session is None or session.user_id != user.id:
            raise NotFoundError("session")
        return session
    session = ChatSession(user_id=user.id, title=first_message[:40] or "New chat")
    db.add(session)
    db.flush()
    return session


def _persist(db, session, role: ChatRole, content: str, tool_calls=None) -> None:
    db.add(
        ChatMessage(session_id=session.id, role=role, content=content, tool_calls=tool_calls)
    )


def _history(db, session) -> list[dict]:
    rows = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(_HISTORY)
    ).scalars().all()
    rows.reverse()
    out = []
    for m in rows:
        if m.role in (ChatRole.user, ChatRole.assistant):
            out.append({"role": m.role.value, "content": m.content})
    return out


def chat(db: Session, user: User, message: str, session_id: uuid.UUID | None = None) -> dict:
    row = ensure_ai_enabled(db)  # raises 503 AI_DISABLED when unconfigured/off
    session = _get_or_create_session(db, user, session_id, message)
    _persist(db, session, ChatRole.user, message)
    db.flush()

    system = build_system_prompt(db, user)
    messages = [{"role": "system", "content": system}, *_history(db, session)]

    allowed = set(get_settings_row(db).role_tool_permissions.get(user.role.value, []))
    tool_schemas = [t.openai_schema() for name, t in TOOLS.items() if name in allowed]

    collected: list[dict] = []
    reply = ""
    choice: dict = {}

    for _ in range(_MAX_ITERATIONS):
        try:
            resp = call_openrouter(
                messages,
                model=row.model,
                temperature=float(row.temperature),
                max_tokens=row.max_tokens,
                tools=tool_schemas or None,
                api_key=resolve_api_key(row),
            )
        except OpenRouterError:
            reply = "The AI assistant is temporarily unavailable. Please try again shortly."
            return _finish(db, user, session, reply, collected, row.model)

        choice = resp["choices"][0]["message"]
        tool_calls = choice.get("tool_calls")
        if not tool_calls:
            reply = choice.get("content") or ""
            return _finish(db, user, session, reply, collected, row.model)

        messages.append(
            {"role": "assistant", "content": choice.get("content") or "", "tool_calls": tool_calls}
        )
        for tc in tool_calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            collected.append({"tool": fn, "args": args})
            if fn not in allowed or fn not in TOOLS:  # re-check allowlist in code
                result: object = {
                    "error": "AI_TOOL_FORBIDDEN",
                    "message": f"Your role is not permitted to use {fn}.",
                }
            else:
                try:
                    result = TOOLS[fn].executor(db, user, **args)
                except Exception as exc:  # noqa: BLE001 — surface as tool error, never 500
                    result = {"error": "TOOL_ERROR", "message": str(exc)}
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", fn),
                "content": json.dumps(result, default=str),
            })

    reply = choice.get("content") or "I could not complete that request within the tool limit."
    return _finish(db, user, session, reply, collected, row.model)


def _finish(db, user, session, reply, collected, model) -> dict:
    _persist(db, session, ChatRole.assistant, reply, tool_calls=collected or None)
    audit(db, user, "ai.chat", None, payload={"model": model, "tool_calls": len(collected)})
    db.commit()
    return {"session_id": session.id, "reply": reply, "tool_calls": collected}


# --- session helpers ---

def create_session(db: Session, user: User) -> ChatSession:
    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions(db: Session, user: User) -> list[ChatSession]:
    return list(
        db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(ChatSession.created_at.desc())
        ).scalars()
    )


def get_session_messages(db: Session, user: User, session_id: uuid.UUID) -> list[ChatMessage]:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise NotFoundError("session")
    return list(
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        ).scalars()
    )
