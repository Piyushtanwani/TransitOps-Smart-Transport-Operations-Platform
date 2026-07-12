"""User management endpoints — Fleet Manager only (docs/03 §4 Users)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])
_fm = require_roles("fleet_manager")


@router.get("", response_model=Page[UserOut], summary="List users (FM)")
def list_users(
    pg: Pagination = Depends(pagination),
    role: UserRole | None = Query(None),
    q: str | None = Query(None, description="name or email substring"),
    db: Session = Depends(get_db),
    _: User = Depends(_fm),
) -> Page[UserOut]:
    items, total = user_service.list_users(db, pg, role, q)
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.post("", response_model=UserOut, status_code=201, summary="Create user (FM)")
def create_user(
    body: UserCreate, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> User:
    return user_service.create_user(db, body, actor)


@router.patch("/{user_id}", response_model=UserOut, summary="Update user (FM)")
def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(_fm),
) -> User:
    return user_service.update_user(db, user_id, body, actor)


@router.delete("/{user_id}", status_code=204, summary="Deactivate user (FM)")
def delete_user(
    user_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> Response:
    user_service.deactivate_user(db, user_id, actor)
    return Response(status_code=204)
