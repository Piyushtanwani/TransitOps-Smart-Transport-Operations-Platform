"""Trip lifecycle service — locked transactional transitions (docs/04 §3, BR-2..BR-8).

Lock order is always trip → vehicle → driver to avoid deadlocks. Every business
rule is re-checked against locked rows before any status mutation.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError, NotFoundError
from app.core.pagination import Pagination, paginate
from app.models.driver import Driver
from app.models.enums import DriverStatus, TripStatus, VehicleStatus
from app.models.fuel_log import FuelLog
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.trip import TripComplete, TripCreate
from app.services.audit import audit


def _now() -> datetime:
    return datetime.now(UTC)


def _num(d: Decimal) -> str:
    return f"{float(d):g}"


# --- business-rule guards (raise DomainError → 409) ---

def _assert_vehicle_dispatchable(vehicle: Vehicle) -> None:
    """BR-2 / BR-4: only an available vehicle may be assigned."""
    if vehicle.status == VehicleStatus.retired:
        raise DomainError(
            "VEHICLE_NOT_AVAILABLE", f"{vehicle.registration_number} is retired."
        )
    if vehicle.status == VehicleStatus.in_shop:
        raise DomainError(
            "VEHICLE_NOT_AVAILABLE", f"{vehicle.registration_number} is in the workshop."
        )
    if vehicle.status == VehicleStatus.on_trip:
        raise DomainError(
            "VEHICLE_NOT_AVAILABLE", f"{vehicle.registration_number} is already on a trip."
        )


def _assert_driver_assignable(driver: Driver) -> None:
    """BR-3 / BR-4: available, non-suspended driver with a valid licence."""
    if driver.status == DriverStatus.suspended:
        raise DomainError("DRIVER_SUSPENDED", f"{driver.full_name} is suspended.")
    if driver.license_expiry < date.today():
        raise DomainError(
            "DRIVER_LICENSE_EXPIRED",
            f"{driver.full_name}'s licence expired on {driver.license_expiry.isoformat()}.",
        )
    if driver.status == DriverStatus.on_trip:
        raise DomainError("DRIVER_NOT_AVAILABLE", f"{driver.full_name} is already on a trip.")
    if driver.status == DriverStatus.off_duty:
        raise DomainError("DRIVER_NOT_AVAILABLE", f"{driver.full_name} is off duty.")


def _assert_capacity(vehicle: Vehicle, cargo: Decimal) -> None:
    """BR-5: cargo must not exceed capacity (equal is allowed)."""
    if cargo > vehicle.max_load_capacity_kg:
        raise DomainError(
            "CARGO_EXCEEDS_CAPACITY",
            f"Cargo weight {_num(cargo)} kg exceeds {vehicle.name} capacity of "
            f"{_num(vehicle.max_load_capacity_kg)} kg.",
            field="cargo_weight_kg",
        )


def _next_trip_code(db: Session) -> str:
    from sqlalchemy import text

    n = db.execute(text("SELECT nextval('trip_code_seq')")).scalar_one()
    return f"TRP-{int(n):04d}"


# --- list ---

_SORTABLE = {
    "trip_code": Trip.trip_code,
    "status": Trip.status,
    "created_at": Trip.created_at,
    "cargo_weight_kg": Trip.cargo_weight_kg,
}


def list_trips(
    db: Session,
    pg: Pagination,
    *,
    status: TripStatus | None = None,
    vehicle_id: uuid.UUID | None = None,
    driver_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
) -> tuple[list[Trip], int]:
    stmt = select(Trip)
    if status is not None:
        stmt = stmt.where(Trip.status == status)
    if vehicle_id is not None:
        stmt = stmt.where(Trip.vehicle_id == vehicle_id)
    if driver_id is not None:
        stmt = stmt.where(Trip.driver_id == driver_id)
    if date_from is not None:
        stmt = stmt.where(Trip.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Trip.created_at <= date_to)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Trip.trip_code.ilike(like), Trip.source.ilike(like), Trip.destination.ilike(like))
        )
    return paginate(db, stmt, pg, _SORTABLE, Trip.created_at)


def get_trip(db: Session, trip_id: uuid.UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise NotFoundError("trip")
    return trip


# --- lifecycle ---

def create(db: Session, data: TripCreate, actor: User) -> Trip:
    """Create a draft trip; validates BR-2/3/4/5 already at draft time (docs/03)."""
    vehicle = db.get(Vehicle, data.vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")
    driver = db.get(Driver, data.driver_id)
    if driver is None:
        raise NotFoundError("driver")

    _assert_vehicle_dispatchable(vehicle)
    _assert_driver_assignable(driver)
    _assert_capacity(vehicle, data.cargo_weight_kg)

    trip = Trip(
        trip_code=_next_trip_code(db),
        source=data.source,
        destination=data.destination,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        cargo_weight_kg=data.cargo_weight_kg,
        planned_distance_km=data.planned_distance_km,
        revenue=data.revenue,
        notes=data.notes,
        status=TripStatus.draft,
        created_by=actor.id,
    )
    db.add(trip)
    db.flush()
    audit(db, actor, "trip.create", trip)
    db.commit()
    db.refresh(trip)
    return trip


def _lock_trip_vehicle_driver(db: Session, trip_id: uuid.UUID) -> tuple[Trip, Vehicle, Driver]:
    trip = db.execute(
        select(Trip).where(Trip.id == trip_id).with_for_update()
    ).scalar_one_or_none()
    if trip is None:
        raise NotFoundError("trip")
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.id == trip.vehicle_id).with_for_update()
    ).scalar_one()
    driver = db.execute(
        select(Driver).where(Driver.id == trip.driver_id).with_for_update()
    ).scalar_one()
    return trip, vehicle, driver


def dispatch(db: Session, trip_id: uuid.UUID, actor: User) -> Trip:
    """BR-2..BR-6. One transaction; locks trip → vehicle → driver in that order."""
    trip, vehicle, driver = _lock_trip_vehicle_driver(db, trip_id)
    if trip.status != TripStatus.draft:
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"Trip {trip.trip_code} is {trip.status.value} and cannot be dispatched.",
        )
    _assert_vehicle_dispatchable(vehicle)
    _assert_driver_assignable(driver)
    _assert_capacity(vehicle, trip.cargo_weight_kg)

    trip.status = TripStatus.dispatched
    trip.dispatched_at = _now()
    trip.start_odometer = vehicle.odometer_km
    vehicle.status = VehicleStatus.on_trip  # BR-6
    driver.status = DriverStatus.on_trip
    audit(db, actor, "trip.dispatch", trip)
    try:
        db.commit()
    except IntegrityError as exc:  # BR-4 race: partial unique index tripped
        db.rollback()
        detail = str(getattr(exc, "orig", exc))
        if "uq_trips_active_driver" in detail:
            raise DomainError(
                "DRIVER_NOT_AVAILABLE",
                f"{driver.full_name} was just assigned to another dispatched trip.",
            ) from exc
        raise DomainError(
            "VEHICLE_NOT_AVAILABLE",
            f"{vehicle.registration_number} was just dispatched on another trip.",
        ) from exc
    db.refresh(trip)
    return trip


def complete(db: Session, trip_id: uuid.UUID, data: TripComplete, actor: User) -> Trip:
    """BR-7: statuses back to available, odometer forward, optional linked fuel log."""
    trip, vehicle, driver = _lock_trip_vehicle_driver(db, trip_id)
    if trip.status != TripStatus.dispatched:
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"Trip {trip.trip_code} is {trip.status.value} and cannot be completed.",
        )
    if data.end_odometer < trip.start_odometer:
        raise DomainError(
            "END_ODOMETER_LT_START",
            f"End odometer {_num(data.end_odometer)} is less than start "
            f"{_num(trip.start_odometer)}.",
            field="end_odometer",
        )

    trip.status = TripStatus.completed
    trip.completed_at = _now()
    trip.end_odometer = data.end_odometer
    if data.revenue is not None:
        trip.revenue = data.revenue
    vehicle.status = VehicleStatus.available
    driver.status = DriverStatus.available
    vehicle.odometer_km = data.end_odometer

    if data.fuel_liters is not None and data.fuel_cost is not None:
        db.add(
            FuelLog(
                vehicle_id=vehicle.id,
                trip_id=trip.id,
                liters=data.fuel_liters,
                cost=data.fuel_cost,
                odometer_at_fill=data.end_odometer,
                created_by=actor.id,
            )
        )
    audit(db, actor, "trip.complete", trip)
    db.commit()
    db.refresh(trip)
    return trip


def cancel(db: Session, trip_id: uuid.UUID, actor: User, reason: str | None = None) -> Trip:
    """BR-8: restore vehicle+driver to available only if the trip was dispatched."""
    trip, vehicle, driver = _lock_trip_vehicle_driver(db, trip_id)
    if trip.status not in (TripStatus.draft, TripStatus.dispatched):
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"Trip {trip.trip_code} is {trip.status.value} and cannot be cancelled.",
        )
    was_dispatched = trip.status == TripStatus.dispatched
    trip.status = TripStatus.cancelled
    trip.cancelled_at = _now()
    if reason:
        trip.notes = (trip.notes + "\n" if trip.notes else "") + f"Cancelled: {reason}"
    if was_dispatched:
        vehicle.status = VehicleStatus.available
        driver.status = DriverStatus.available
    audit(db, actor, "trip.cancel", trip)
    db.commit()
    db.refresh(trip)
    return trip
