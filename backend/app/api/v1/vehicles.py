"""Vehicle endpoints (docs/03 §4 Vehicles). Read: all roles. Write/retire: FM."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.enums import VehicleStatus, VehicleType
from app.models.user import User
from app.schemas.common import Page
from app.schemas.vehicle import VehicleCreate, VehicleDetail, VehicleOut, VehicleUpdate
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])
_fm = require_roles("fleet_manager")


@router.get("", response_model=Page[VehicleOut], summary="List vehicles")
def list_vehicles(
    pg: Pagination = Depends(pagination),
    status: VehicleStatus | None = Query(None),
    type: VehicleType | None = Query(None),
    region: str | None = Query(None),
    q: str | None = Query(None, description="registration or name substring"),
    dispatchable: bool = Query(False, description="only status=available (BR-2)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[VehicleOut]:
    items, total = vehicle_service.list_vehicles(
        db, pg, status=status, type_=type, region=region, q=q, dispatchable=dispatchable
    )
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.post("", response_model=VehicleOut, status_code=201, summary="Create vehicle (FM)")
def create_vehicle(
    body: VehicleCreate, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> VehicleOut:
    return vehicle_service.create_vehicle(db, body, actor)


@router.get("/{vehicle_id}", response_model=VehicleDetail, summary="Vehicle detail")
def get_vehicle(
    vehicle_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> VehicleDetail:
    vehicle = vehicle_service.get_vehicle(db, vehicle_id)
    detail = VehicleDetail.model_validate(vehicle)
    rollups = vehicle_service.vehicle_rollups(db, vehicle_id)
    detail.open_maintenance = rollups["open_maintenance"]
    detail.active_trip_code = rollups["active_trip_code"]
    return detail


@router.patch("/{vehicle_id}", response_model=VehicleOut, summary="Update vehicle (FM)")
def update_vehicle(
    vehicle_id: uuid.UUID,
    body: VehicleUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(_fm),
) -> VehicleOut:
    return vehicle_service.update_vehicle(db, vehicle_id, body, actor)


@router.post("/{vehicle_id}/retire", response_model=VehicleOut, summary="Retire vehicle (FM)")
def retire_vehicle(
    vehicle_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> VehicleOut:
    return vehicle_service.retire_vehicle(db, vehicle_id, actor)


@router.post("/{vehicle_id}/unretire", response_model=VehicleOut, summary="Unretire vehicle (FM)")
def unretire_vehicle(
    vehicle_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> VehicleOut:
    return vehicle_service.unretire_vehicle(db, vehicle_id, actor)


@router.delete("/{vehicle_id}", status_code=204, summary="Delete vehicle (FM)")
def delete_vehicle(
    vehicle_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(_fm)
) -> Response:
    vehicle_service.delete_vehicle(db, vehicle_id, actor)
    return Response(status_code=204)
