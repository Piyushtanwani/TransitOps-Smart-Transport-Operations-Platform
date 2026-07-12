"""Test data factories + auth helpers (docs/07 §1)."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.driver import Driver
from app.models.enums import DriverStatus, TripStatus, UserRole, VehicleStatus, VehicleType
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle

PASSWORD = "Transit@123"
API = "/api/v1"


def _uniq() -> str:
    return uuid.uuid4().hex[:8]


def make_user(
    db: Session,
    role: str | UserRole = UserRole.fleet_manager,
    *,
    email: str | None = None,
    password: str = PASSWORD,
    full_name: str | None = None,
    is_active: bool = True,
) -> User:
    role_val = role.value if isinstance(role, UserRole) else role
    user = User(
        email=email or f"{role_val}_{_uniq()}@test.in",
        hashed_password=hash_password(password),
        full_name=full_name or f"Test {role_val}",
        role=UserRole(role_val),
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_vehicle(db: Session, **kw: Any) -> Vehicle:
    defaults: dict[str, Any] = dict(
        registration_number=f"TS-01-XX-{uuid.uuid4().int % 10000:04d}",
        name="Test Vehicle",
        type=VehicleType.van,
        max_load_capacity_kg=Decimal("500"),
        odometer_km=Decimal("1000"),
        acquisition_cost=Decimal("500000"),
        region="North",
        status=VehicleStatus.available,
    )
    defaults.update(kw)
    v = Vehicle(**defaults)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def make_driver(db: Session, **kw: Any) -> Driver:
    defaults: dict[str, Any] = dict(
        full_name="Test Driver",
        license_number=f"TS-LIC-{_uniq()}",
        license_category="LMV",
        license_expiry=date.today() + timedelta(days=365),
        contact_number="9876500000",
        safety_score=Decimal("90"),
        status=DriverStatus.available,
    )
    defaults.update(kw)
    d = Driver(**defaults)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def make_trip(
    db: Session,
    *,
    vehicle: Vehicle,
    driver: Driver,
    created_by: uuid.UUID,
    status: TripStatus = TripStatus.draft,
    cargo_weight_kg: Any = "400",
    planned_distance_km: Any = "100",
    **kw: Any,
) -> Trip:
    code = "TRP-%04d" % db.execute(text("SELECT nextval('trip_code_seq')")).scalar_one()
    t = Trip(
        trip_code=code,
        source=kw.pop("source", "Ahmedabad"),
        destination=kw.pop("destination", "Surat"),
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        cargo_weight_kg=Decimal(str(cargo_weight_kg)),
        planned_distance_km=Decimal(str(planned_distance_km)),
        created_by=created_by,
        status=status,
        **kw,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def login(client, email: str, password: str = PASSWORD):
    return client.post(f"{API}/auth/login", json={"email": email, "password": password})


def auth_headers(client, db: Session, role: str | UserRole = UserRole.fleet_manager, **kw: Any) -> dict:
    """Create a user of `role`, log in, return the Bearer auth header."""
    user = make_user(db, role=role, **kw)
    resp = login(client, user.email)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
