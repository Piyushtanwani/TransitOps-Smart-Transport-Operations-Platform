"""User management logic (docs/03 §4 Users). FM-only; deactivate never hard-deletes."""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError, NotFoundError
from app.core.pagination import Pagination, paginate
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit import audit

_SORTABLE = {
    "email": User.email,
    "full_name": User.full_name,
    "role": User.role,
    "created_at": User.created_at,
}


def list_users(
    db: Session, pg: Pagination, role: UserRole | None = None, q: str | None = None
) -> tuple[list[User], int]:
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.full_name.ilike(like), User.email.ilike(like)))
    return paginate(db, stmt, pg, _SORTABLE, User.created_at)


def create_user(db: Session, data: UserCreate, actor: User) -> User:
    user = User(
        email=str(data.email),
        full_name=data.full_name,
        role=data.role,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(
            "DUPLICATE_EMAIL",
            f"A user with email {data.email} already exists.",
            field="email",
        ) from exc
    audit(db, actor, "user.create", user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: uuid.UUID, data: UserUpdate, actor: User) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("user")
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    audit(db, actor, "user.update", user)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: uuid.UUID, actor: User) -> None:
    """Soft-delete: is_active=False preserves audit integrity (docs/03 §4)."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("user")
    user.is_active = False
    audit(db, actor, "user.deactivate", user)
    db.commit()
