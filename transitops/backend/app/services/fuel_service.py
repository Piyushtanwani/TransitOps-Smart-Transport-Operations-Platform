"""Fuel log logic (docs/03 §4 Fuel & Expenses)."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.pagination import Pagination, paginate
from app.models.fuel_log import FuelLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.fuel import FuelLogCreate
from app.services.audit import audit

_SORTABLE = {
    "filled_at": FuelLog.filled_at,
    "cost": FuelLog.cost,
    "liters": FuelLog.liters,
    "created_at": FuelLog.created_at,
}


def list_fuel_logs(
    db: Session,
    pg: Pagination,
    *,
    vehicle_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[FuelLog], int]:
    stmt = select(FuelLog)
    if vehicle_id is not None:
        stmt = stmt.where(FuelLog.vehicle_id == vehicle_id)
    if date_from is not None:
        stmt = stmt.where(FuelLog.filled_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(FuelLog.filled_at <= date_to)
    return paginate(db, stmt, pg, _SORTABLE, FuelLog.filled_at)


def create_fuel_log(db: Session, data: FuelLogCreate, actor: User) -> FuelLog:
    vehicle = db.get(Vehicle, data.vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")

    fuel_log = FuelLog(
        vehicle_id=data.vehicle_id,
        trip_id=data.trip_id,
        liters=data.liters,
        cost=data.cost,
        odometer_at_fill=data.odometer_at_fill,
        created_by=actor.id,
    )
    if data.filled_at is not None:
        fuel_log.filled_at = data.filled_at
    db.add(fuel_log)
    db.flush()
    audit(db, actor, "fuel.create", fuel_log)
    db.commit()
    db.refresh(fuel_log)
    return fuel_log
