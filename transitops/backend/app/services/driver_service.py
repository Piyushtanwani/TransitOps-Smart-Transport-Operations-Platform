"""Driver management logic (docs/03 §4, docs/04 BR-3 + status guard §2/§4.6)."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError, NotFoundError
from app.core.pagination import Pagination, paginate
from app.models.driver import Driver
from app.models.enums import DriverStatus, TripStatus
from app.models.trip import Trip
from app.models.user import User
from app.schemas.driver import DriverCreate, DriverUpdate
from app.services.audit import audit

_SORTABLE = {
    "full_name": Driver.full_name,
    "license_number": Driver.license_number,
    "license_expiry": Driver.license_expiry,
    "safety_score": Driver.safety_score,
    "status": Driver.status,
    "created_at": Driver.created_at,
}

# Legal manual status edges (docs/04 §2); on_trip is never a manual target/source.
_ALLOWED: dict[DriverStatus, set[DriverStatus]] = {
    DriverStatus.available: {DriverStatus.off_duty, DriverStatus.suspended},
    DriverStatus.off_duty: {DriverStatus.available, DriverStatus.suspended},
    DriverStatus.suspended: {DriverStatus.available},
}


def list_drivers(
    db: Session,
    pg: Pagination,
    *,
    status: DriverStatus | None = None,
    license_valid: bool | None = None,
    q: str | None = None,
    assignable: bool = False,
) -> tuple[list[Driver], int]:
    today = date.today()
    stmt = select(Driver)
    if assignable:  # BR-3: available AND licence not expired
        stmt = stmt.where(
            Driver.status == DriverStatus.available, Driver.license_expiry >= today
        )
    elif status is not None:
        stmt = stmt.where(Driver.status == status)
    if license_valid is True:
        stmt = stmt.where(Driver.license_expiry >= today)
    elif license_valid is False:
        stmt = stmt.where(Driver.license_expiry < today)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Driver.full_name.ilike(like), Driver.license_number.ilike(like))
        )
    return paginate(db, stmt, pg, _SORTABLE, Driver.full_name)


def expiring_drivers(db: Session, days: int = 30) -> list[Driver]:
    today = date.today()
    stmt = (
        select(Driver)
        .where(
            Driver.license_expiry >= today,
            Driver.license_expiry <= today + timedelta(days=days),
        )
        .order_by(Driver.license_expiry.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_driver(db: Session, driver_id: uuid.UUID) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise NotFoundError("driver")
    return driver


def create_driver(db: Session, data: DriverCreate, actor: User) -> Driver:
    driver = Driver(
        full_name=data.full_name,
        license_number=data.license_number,
        license_category=data.license_category,
        license_expiry=data.license_expiry,
        contact_number=data.contact_number,
        safety_score=data.safety_score,
    )
    db.add(driver)
    try:
        db.flush()
    except IntegrityError as exc:  # BR-1 (license uniqueness)
        db.rollback()
        raise DomainError(
            "DUPLICATE_LICENSE",
            f"A driver with license {data.license_number} already exists.",
            field="license_number",
        ) from exc
    audit(db, actor, "driver.create", driver)
    db.commit()
    db.refresh(driver)
    return driver


def update_driver(db: Session, driver_id: uuid.UUID, data: DriverUpdate, actor: User) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise NotFoundError("driver")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(
            "DUPLICATE_LICENSE",
            f"A driver with license {data.license_number} already exists.",
            field="license_number",
        ) from exc
    audit(db, actor, "driver.update", driver)
    db.commit()
    db.refresh(driver)
    return driver


def set_driver_status(
    db: Session, driver_id: uuid.UUID, new_status: DriverStatus, actor: User
) -> Driver:
    """Manual status change under a row lock (docs/04 §2, §4.6)."""
    driver = db.execute(
        select(Driver).where(Driver.id == driver_id).with_for_update()
    ).scalar_one_or_none()
    if driver is None:
        raise NotFoundError("driver")

    if driver.status == DriverStatus.on_trip:
        code = db.execute(
            select(Trip.trip_code)
            .where(Trip.driver_id == driver_id, Trip.status == TripStatus.dispatched)
            .limit(1)
        ).scalar_one_or_none()
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"{driver.full_name} is on trip {code or '(dispatched)'}; "
            "complete or cancel it before changing status.",
        )

    if new_status != driver.status and new_status not in _ALLOWED.get(driver.status, set()):
        raise DomainError(
            "INVALID_STATUS_TRANSITION",
            f"{driver.full_name} cannot move from {driver.status.value} to {new_status.value}.",
        )

    driver.status = new_status
    audit(db, actor, "driver.status", driver, payload={"status": new_status.value})
    db.commit()
    db.refresh(driver)
    return driver
