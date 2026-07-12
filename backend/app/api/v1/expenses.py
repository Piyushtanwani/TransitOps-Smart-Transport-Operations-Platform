"""Expense endpoints (docs/03 §4 Fuel & Expenses). Write: FM/FA. Read: FM/FA."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.user import User
from app.schemas.common import Page
from app.schemas.expense import ExpenseCreate, ExpenseOut
from app.services import expense_service

router = APIRouter(prefix="/expenses", tags=["Expenses"])
_write = require_roles("fleet_manager", "financial_analyst")
_read = require_roles("fleet_manager", "financial_analyst")


@router.get("", response_model=Page[ExpenseOut], summary="List expenses (FM, FA)")
def list_expenses(
    pg: Pagination = Depends(pagination),
    vehicle_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(_read),
) -> Page[ExpenseOut]:
    items, total = expense_service.list_expenses(
        db, pg, vehicle_id=vehicle_id, date_from=date_from, date_to=date_to
    )
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.post(
    "", response_model=ExpenseOut, status_code=201, summary="Create expense (FM, FA)"
)
def create_expense(
    body: ExpenseCreate, db: Session = Depends(get_db), actor: User = Depends(_write)
) -> ExpenseOut:
    return expense_service.create_expense(db, body, actor)
