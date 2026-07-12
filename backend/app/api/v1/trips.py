"""Trip endpoints (docs/03 §4 Trips). Read: all roles. Create/lifecycle: FM + D."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.core.pagination import Pagination, pagination
from app.models.enums import TripStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.trip import TripCancel, TripComplete, TripCreate, TripOut
from app.services import trip_service

router = APIRouter(prefix="/trips", tags=["Trips"])
_dispatch = require_roles("fleet_manager", "driver")


@router.get("", response_model=Page[TripOut], summary="List trips")
def list_trips(
    pg: Pagination = Depends(pagination),
    status: TripStatus | None = Query(None),
    vehicle_id: uuid.UUID | None = Query(None),
    driver_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    q: str | None = Query(None, description="code / source / destination substring"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[TripOut]:
    items, total = trip_service.list_trips(
        db, pg, status=status, vehicle_id=vehicle_id, driver_id=driver_id,
        date_from=date_from, date_to=date_to, q=q,
    )
    return Page(items=items, total=total, page=pg.page, page_size=pg.page_size)


@router.post("", response_model=TripOut, status_code=201, summary="Create draft trip (FM/D)")
def create_trip(
    body: TripCreate, db: Session = Depends(get_db), actor: User = Depends(_dispatch)
) -> TripOut:
    return trip_service.create(db, body, actor)


@router.get("/{trip_id}", response_model=TripOut, summary="Trip detail")
def get_trip(
    trip_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> TripOut:
    return trip_service.get_trip(db, trip_id)


@router.post("/{trip_id}/dispatch", response_model=TripOut, summary="Dispatch trip (FM/D)")
def dispatch_trip(
    trip_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(_dispatch)
) -> TripOut:
    return trip_service.dispatch(db, trip_id, actor)


@router.post("/{trip_id}/complete", response_model=TripOut, summary="Complete trip (FM/D)")
def complete_trip(
    trip_id: uuid.UUID,
    body: TripComplete,
    db: Session = Depends(get_db),
    actor: User = Depends(_dispatch),
) -> TripOut:
    return trip_service.complete(db, trip_id, body, actor)


@router.post("/{trip_id}/cancel", response_model=TripOut, summary="Cancel trip (FM/D)")
def cancel_trip(
    trip_id: uuid.UUID,
    body: TripCancel = Body(default=TripCancel()),
    db: Session = Depends(get_db),
    actor: User = Depends(_dispatch),
) -> TripOut:
    return trip_service.cancel(db, trip_id, actor, reason=body.reason)
