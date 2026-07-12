"""Vehicle registry logic (docs/03 §4, docs/04 BR-1/BR-2, §4.8 retire guard)."""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError, NotFoundError
from app.core.pagination import Pagination, paginate
from app.models.enums import MaintenanceStatus, TripStatus, VehicleStatus, VehicleType
from app.models.maintenance import MaintenanceLog
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.audit import audit

_SORTABLE = {
    "registration_number": Vehicle.registration_number,
    "name": Vehicle.name,
    "odometer_km": Vehicle.odometer_km,
    "acquisition_cost": Vehicle.acquisition_cost,
    "status": Vehicle.status,
    "created_at": Vehicle.created_at,
}


def list_vehicles(
    db: Session,
    pg: Pagination,
    *,
    status: VehicleStatus | None = None,
    type_: VehicleType | None = None,
    region: str | None = None,
    q: str | None = None,
    dispatchable: bool = False,
) -> tuple[list[Vehicle], int]:
    stmt = select(Vehicle)
    if dispatchable:  # BR-2: only available vehicles reach the dispatch pool
        stmt = stmt.where(Vehicle.status == VehicleStatus.available)
    elif status is not None:
        stmt = stmt.where(Vehicle.status == status)
    if type_ is not None:
        stmt = stmt.where(Vehicle.type == type_)
    if region:
        stmt = stmt.where(Vehicle.region == region)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Vehicle.registration_number.ilike(like), Vehicle.name.ilike(like))
        )
    return paginate(db, stmt, pg, _SORTABLE, Vehicle.registration_number)


def get_vehicle(db: Session, vehicle_id: uuid.UUID) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")
    return vehicle


def vehicle_rollups(db: Session, vehicle_id: uuid.UUID) -> dict:
    """Two cheap subqueries for the detail view (docs/03 §4)."""
    open_maint = db.execute(
        select(MaintenanceLog.id)
        .where(
            MaintenanceLog.vehicle_id == vehicle_id,
            MaintenanceLog.status == MaintenanceStatus.open,
        )
        .limit(1)
    ).first()
    active_code = db.execute(
        select(Trip.trip_code)
        .where(Trip.vehicle_id == vehicle_id, Trip.status == TripStatus.dispatched)
        .limit(1)
    ).scalar_one_or_none()
    return {"open_maintenance": open_maint is not None, "active_trip_code": active_code}


def create_vehicle(db: Session, data: VehicleCreate, actor: User) -> Vehicle:
    vehicle = Vehicle(
        registration_number=data.registration_number,
        name=data.name,
        type=data.type,
        max_load_capacity_kg=data.max_load_capacity_kg,
        odometer_km=data.odometer_km,
        acquisition_cost=data.acquisition_cost,
        region=data.region,
    )
    db.add(vehicle)
    try:
        db.flush()
    except IntegrityError as exc:  # BR-1
        db.rollback()
        raise DomainError(
            "DUPLICATE_REGISTRATION",
            f"A vehicle with registration {data.registration_number} already exists.",
            field="registration_number",
        ) from exc
    audit(db, actor, "vehicle.create", vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def update_vehicle(
    db: Session, vehicle_id: uuid.UUID, data: VehicleUpdate, actor: User
) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    audit(db, actor, "vehicle.update", vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def retire_vehicle(db: Session, vehicle_id: uuid.UUID, actor: User) -> Vehicle:
    """Retire from available/in_shop; blocked while a maintenance job is open (§4.8)."""
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id).with_for_update()
    ).scalar_one_or_none()
    if vehicle is None:
        raise NotFoundError("vehicle")
    if vehicle.status not in (VehicleStatus.available, VehicleStatus.in_shop):
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"{vehicle.registration_number} is {vehicle.status.value} and cannot be retired.",
        )
    open_job = db.execute(
        select(MaintenanceLog)
        .where(
            MaintenanceLog.vehicle_id == vehicle_id,
            MaintenanceLog.status == MaintenanceStatus.open,
        )
        .limit(1)
    ).scalar_one_or_none()
    if open_job is not None:
        raise DomainError(
            "VEHICLE_HAS_OPEN_MAINTENANCE",
            f"Close the open maintenance job '{open_job.title}' before retiring "
            f"{vehicle.registration_number}.",
        )
    vehicle.status = VehicleStatus.retired
    audit(db, actor, "vehicle.retire", vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def unretire_vehicle(db: Session, vehicle_id: uuid.UUID, actor: User) -> Vehicle:
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id).with_for_update()
    ).scalar_one_or_none()
    if vehicle is None:
        raise NotFoundError("vehicle")
    if vehicle.status != VehicleStatus.retired:
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"{vehicle.registration_number} is {vehicle.status.value}, not retired.",
        )
    vehicle.status = VehicleStatus.available
    audit(db, actor, "vehicle.unretire", vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, vehicle_id: uuid.UUID, actor: User) -> None:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")
    db.delete(vehicle)
    try:
        db.flush()
    except IntegrityError as exc:  # FK RESTRICT — trips/logs reference it
        db.rollback()
        raise DomainError(
            "VEHICLE_HAS_HISTORY",
            f"{vehicle.registration_number} has trips or logs and cannot be deleted. "
            "Retire it instead.",
        ) from exc
    audit(db, actor, "vehicle.delete", None, payload={"vehicle_id": str(vehicle_id)})
    db.commit()
