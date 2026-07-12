"""Expense logic (docs/03 §4 Fuel & Expenses)."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.pagination import Pagination, paginate
from app.models.expense import Expense
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.expense import ExpenseCreate
from app.services.audit import audit

_SORTABLE = {
    "incurred_at": Expense.incurred_at,
    "amount": Expense.amount,
    "type": Expense.type,
    "created_at": Expense.created_at,
}


def list_expenses(
    db: Session,
    pg: Pagination,
    *,
    vehicle_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Expense], int]:
    stmt = select(Expense)
    if vehicle_id is not None:
        stmt = stmt.where(Expense.vehicle_id == vehicle_id)
    if date_from is not None:
        stmt = stmt.where(Expense.incurred_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Expense.incurred_at <= date_to)
    return paginate(db, stmt, pg, _SORTABLE, Expense.incurred_at)


def create_expense(db: Session, data: ExpenseCreate, actor: User) -> Expense:
    vehicle = db.get(Vehicle, data.vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")

    expense = Expense(
        vehicle_id=data.vehicle_id,
        trip_id=data.trip_id,
        type=data.type,
        amount=data.amount,
        description=data.description,
        created_by=actor.id,
    )
    if data.incurred_at is not None:
        expense.incurred_at = data.incurred_at
    db.add(expense)
    db.flush()
    audit(db, actor, "expense.create", expense)
    db.commit()
    db.refresh(expense)
    return expense
