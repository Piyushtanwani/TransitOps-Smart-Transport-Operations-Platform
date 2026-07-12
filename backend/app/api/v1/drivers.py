"""Driver endpoints (docs/03 §4 Drivers). Read: all roles. Write/status: FM + SO."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.enums import DriverStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.driver import DriverCreate, DriverOut, DriverStatusUpdate, DriverUpdate
from app.services import driver_service

router = APIRouter(prefix="/drivers", tags=["Drivers"])
_write = require_roles("fleet_manager", "safety_officer")


@router.get("", response_model=Page[DriverOut], summary="List drivers")
def list_drivers(
    pg: Pagination = Depends(pagination),
    status: DriverStatus | None = Query(None),
    license_valid: bool | None = Query(None),
    q: str | None = Query(None, description="name or license substring"),
    assignable: bool = Query(False, description="available AND licence valid (BR-3)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[DriverOut]:
    items, total = driver_service.list_drivers(
        db, pg, status=status, license_valid=license_valid, q=q, assignable=assignable
    )
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.get("/expiring", response_model=list[DriverOut], summary="Licences expiring within N days")
def expiring(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DriverOut]:
    return driver_service.expiring_drivers(db, days)


@router.post("", response_model=DriverOut, status_code=201, summary="Create driver (FM/SO)")
def create_driver(
    body: DriverCreate, db: Session = Depends(get_db), actor: User = Depends(_write)
) -> DriverOut:
    return driver_service.create_driver(db, body, actor)


@router.get("/{driver_id}", response_model=DriverOut, summary="Driver detail")
def get_driver(
    driver_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DriverOut:
    return driver_service.get_driver(db, driver_id)


@router.patch("/{driver_id}", response_model=DriverOut, summary="Update driver (FM/SO)")
def update_driver(
    driver_id: uuid.UUID,
    body: DriverUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(_write),
) -> DriverOut:
    return driver_service.update_driver(db, driver_id, body, actor)


@router.post(
    "/{driver_id}/status", response_model=DriverOut, summary="Change driver status (FM/SO)"
)
def set_status(
    driver_id: uuid.UUID,
    body: DriverStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(_write),
) -> DriverOut:
    return driver_service.set_driver_status(db, driver_id, DriverStatus(body.status), actor)
