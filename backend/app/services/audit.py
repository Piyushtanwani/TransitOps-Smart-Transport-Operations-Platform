"""Audit trail helper — one row per privileged/state-changing action."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def audit(
    db: Session,
    actor: Any | None,
    action: str,
    entity: Any | None = None,
    *,
    payload: dict | None = None,
) -> None:
    """Stage an `audit_logs` row (committed by the caller's transaction).

    `entity` may be an ORM instance (name + id derived) or omitted.
    """
    entity_name = ""
    entity_id = None
    if entity is not None:
        entity_name = getattr(entity, "__tablename__", str(entity))
        entity_id = getattr(entity, "id", None)
    db.add(
        AuditLog(
            user_id=getattr(actor, "id", None),
            action=action,
            entity=entity_name[:30],
            entity_id=entity_id,
            payload=payload,
        )
    )
