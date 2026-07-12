"""Fuel log endpoints (docs/03 §4 Fuel & Expenses). Write: FM/driver/FA. Read: FM/FA."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.user import User
from app.schemas.common import Page
from app.schemas.fuel import FuelLogCreate, FuelLogOut
from app.services import fuel_service

router = APIRouter(prefix="/fuel-logs", tags=["Fuel"])
_write = require_roles("fleet_manager", "driver", "financial_analyst")
_read = require_roles("fleet_manager", "financial_analyst")


@router.get("", response_model=Page[FuelLogOut], summary="List fuel logs (FM, FA)")
def list_fuel_logs(
    pg: Pagination = Depends(pagination),
    vehicle_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(_read),
) -> Page[FuelLogOut]:
    items, total = fuel_service.list_fuel_logs(
        db, pg, vehicle_id=vehicle_id, date_from=date_from, date_to=date_to
    )
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.post(
    "",
    response_model=FuelLogOut,
    status_code=201,
    summary="Create fuel log (FM, driver, FA)",
)
def create_fuel_log(
    body: FuelLogCreate, db: Session = Depends(get_db), actor: User = Depends(_write)
) -> FuelLogOut:
    return fuel_service.create_fuel_log(db, body, actor)
