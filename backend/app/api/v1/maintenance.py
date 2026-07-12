"""Maintenance endpoints (docs/03 §4). Read: all roles. Create/close/edit: FM."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.enums import MaintenanceStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.maintenance import (
    MaintenanceClose,
    MaintenanceCreate,
    MaintenanceOut,
    MaintenanceUpdate,
)
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])
_fm = require_roles("fleet_manager")


@router.get("", response_model=Page[MaintenanceOut], summary="List maintenance jobs")
def list_maintenance(
    pg: Pagination = Depends(pagination),
    status: MaintenanceStatus | None = Query(None),
    vehicle_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[MaintenanceOut]:
    items, total = maintenance_service.list_maintenance(
        db, pg, status=status, vehicle_id=vehicle_id
    )
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.post("", response_model=MaintenanceOut, status_code=201, summary="Open maintenance (FM)")
def create_maintenance(
    body: MaintenanceCreate, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> MaintenanceOut:
    return maintenance_service.create_maintenance(db, body, actor)


@router.get("/{maint_id}", response_model=MaintenanceOut, summary="Maintenance detail")
def get_maintenance(
    maint_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> MaintenanceOut:
    return maintenance_service.get_maintenance(db, maint_id)


@router.patch("/{maint_id}", response_model=MaintenanceOut, summary="Edit open job (FM)")
def update_maintenance(
    maint_id: uuid.UUID,
    body: MaintenanceUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(_fm),
) -> MaintenanceOut:
    return maintenance_service.update_maintenance(db, maint_id, body, actor)


@router.post("/{maint_id}/close", response_model=MaintenanceOut, summary="Close maintenance (FM)")
def close_maintenance(
    maint_id: uuid.UUID,
    body: MaintenanceClose = Body(default=MaintenanceClose()),
    db: Session = Depends(get_db),
    actor: User = Depends(_fm),
) -> MaintenanceOut:
    return maintenance_service.close_maintenance(db, maint_id, body, actor)
