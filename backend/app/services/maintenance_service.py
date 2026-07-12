"""Maintenance workflow (docs/04 BR-9/BR-10). Opening/closing drives vehicle status."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError, NotFoundError
from app.core.pagination import Pagination, paginate
from app.models.enums import MaintenanceStatus, TripStatus, VehicleStatus
from app.models.maintenance import MaintenanceLog
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.maintenance import MaintenanceClose, MaintenanceCreate, MaintenanceUpdate
from app.services.audit import audit

_SORTABLE = {
    "opened_at": MaintenanceLog.opened_at,
    "status": MaintenanceLog.status,
    "cost": MaintenanceLog.cost,
}


def list_maintenance(
    db: Session,
    pg: Pagination,
    *,
    status: MaintenanceStatus | None = None,
    vehicle_id: uuid.UUID | None = None,
) -> tuple[list[MaintenanceLog], int]:
    stmt = select(MaintenanceLog)
    if status is not None:
        stmt = stmt.where(MaintenanceLog.status == status)
    if vehicle_id is not None:
        stmt = stmt.where(MaintenanceLog.vehicle_id == vehicle_id)
    return paginate(db, stmt, pg, _SORTABLE, MaintenanceLog.opened_at)


def get_maintenance(db: Session, maint_id: uuid.UUID) -> MaintenanceLog:
    m = db.get(MaintenanceLog, maint_id)
    if m is None:
        raise NotFoundError("maintenance")
    return m


def create_maintenance(db: Session, data: MaintenanceCreate, actor: User) -> MaintenanceLog:
    """BR-9: vehicle must be available; opening sets it to in_shop (one txn, row lock)."""
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.id == data.vehicle_id).with_for_update()
    ).scalar_one_or_none()
    if vehicle is None:
        raise NotFoundError("vehicle")

    if vehicle.status == VehicleStatus.on_trip:
        code = db.execute(
            select(Trip.trip_code)
            .where(Trip.vehicle_id == vehicle.id, Trip.status == TripStatus.dispatched)
            .limit(1)
        ).scalar_one_or_none()
        raise DomainError(
            "VEHICLE_NOT_AVAILABLE",
            f"{vehicle.registration_number} is on trip {code}; complete or cancel it first.",
        )
    if vehicle.status == VehicleStatus.retired:
        raise DomainError(
            "VEHICLE_NOT_AVAILABLE", f"{vehicle.registration_number} is retired."
        )
    if vehicle.status == VehicleStatus.in_shop:
        raise DomainError(
            "VEHICLE_HAS_OPEN_MAINTENANCE",
            f"{vehicle.registration_number} already has an open maintenance job.",
        )

    m = MaintenanceLog(
        vehicle_id=vehicle.id,
        title=data.title,
        description=data.description,
        cost=data.cost,
        status=MaintenanceStatus.open,
        created_by=actor.id,
    )
    db.add(m)
    vehicle.status = VehicleStatus.in_shop  # BR-9
    try:
        db.flush()
    except IntegrityError as exc:  # uq_maint_open_per_vehicle race
        db.rollback()
        raise DomainError(
            "VEHICLE_HAS_OPEN_MAINTENANCE",
            f"{vehicle.registration_number} already has an open maintenance job.",
        ) from exc
    audit(db, actor, "maintenance.create", m)
    db.commit()
    db.refresh(m)
    return m


def update_maintenance(
    db: Session, maint_id: uuid.UUID, data: MaintenanceUpdate, actor: User
) -> MaintenanceLog:
    m = db.get(MaintenanceLog, maint_id)
    if m is None:
        raise NotFoundError("maintenance")
    if m.status != MaintenanceStatus.open:
        raise DomainError(
            "INVALID_STATUS_TRANSITION", "Closed maintenance jobs cannot be edited."
        )
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    audit(db, actor, "maintenance.update", m)
    db.commit()
    db.refresh(m)
    return m


def close_maintenance(
    db: Session, maint_id: uuid.UUID, data: MaintenanceClose, actor: User
) -> MaintenanceLog:
    """BR-10: closing restores the vehicle to available unless it is retired."""
    m = db.get(MaintenanceLog, maint_id)
    if m is None:
        raise NotFoundError("maintenance")
    if m.status == MaintenanceStatus.closed:
        raise DomainError(
            "INVALID_STATUS_TRANSITION", "This maintenance job is already closed."
        )
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.id == m.vehicle_id).with_for_update()
    ).scalar_one()

    if data.cost is not None:
        m.cost = data.cost
    m.status = MaintenanceStatus.closed
    m.closed_at = datetime.now(UTC)
    if vehicle.status != VehicleStatus.retired:  # BR-10 exception
        vehicle.status = VehicleStatus.available
    audit(db, actor, "maintenance.close", m)
    db.commit()
    db.refresh(m)
    return m
