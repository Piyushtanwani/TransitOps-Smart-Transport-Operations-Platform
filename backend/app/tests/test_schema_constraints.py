"""Suite D — DB-level constraint proofs (docs/07 §5).

Each intentional failure runs inside a SAVEPOINT (`db.begin_nested()`) so the
IntegrityError rolls back only that savepoint and the shared test transaction stays
usable. These prove the schema itself enforces the rules (not just the services).
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.enums import MaintenanceStatus, TripStatus, UserRole, VehicleType
from app.models.maintenance import MaintenanceLog
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.tests.factories import make_driver, make_user, make_vehicle


def _trip(db, vehicle, driver, user, **kw) -> Trip:
    seq = db.execute(text("SELECT nextval('trip_code_seq')")).scalar_one()
    fields = dict(
        trip_code=f"TRP-{int(seq):04d}",
        source="A",
        destination="B",
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        cargo_weight_kg=Decimal("100"),
        planned_distance_km=Decimal("100"),
        created_by=user.id,
        status=TripStatus.draft,
    )
    fields.update(kw)
    return Trip(**fields)


def test_negative_capacity_check(client, db) -> None:
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(
                Vehicle(
                    registration_number="NEG-1",
                    name="x",
                    type=VehicleType.van,
                    max_load_capacity_kg=Decimal("-5"),
                    acquisition_cost=Decimal("100"),
                    region="North",
                )
            )
            db.flush()


def test_invalid_email_check(client, db) -> None:
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(
                User(
                    email="not-an-email",
                    hashed_password="x",
                    full_name="X",
                    role=UserRole.driver,
                )
            )
            db.flush()


def test_duplicate_registration_unique(client, db) -> None:
    make_vehicle(db, registration_number="DUP-REG-1")
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(
                Vehicle(
                    registration_number="DUP-REG-1",
                    name="y",
                    type=VehicleType.truck,
                    max_load_capacity_kg=Decimal("1000"),
                    acquisition_cost=Decimal("100"),
                    region="North",
                )
            )
            db.flush()


def test_second_dispatched_trip_same_vehicle_blocked(client, db) -> None:
    """uq_trips_active_vehicle — the DB-level BR-4 proof."""
    user, vehicle = make_user(db), make_vehicle(db)
    d1, d2 = make_driver(db), make_driver(db)
    db.add(_trip(db, vehicle, d1, user, status=TripStatus.dispatched))
    db.flush()
    second = _trip(db, vehicle, d2, user, status=TripStatus.dispatched)  # built outside savepoint
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(second)
            db.flush()


def test_second_dispatched_trip_same_driver_blocked(client, db) -> None:
    user, driver = make_user(db), make_driver(db)
    v1, v2 = make_vehicle(db), make_vehicle(db)
    db.add(_trip(db, v1, driver, user, status=TripStatus.dispatched))
    db.flush()
    second = _trip(db, v2, driver, user, status=TripStatus.dispatched)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(second)
            db.flush()


def test_duplicate_open_maintenance_per_vehicle_blocked(client, db) -> None:
    user, vehicle = make_user(db), make_vehicle(db)
    db.add(MaintenanceLog(vehicle_id=vehicle.id, title="a", status=MaintenanceStatus.open, created_by=user.id))
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(
                MaintenanceLog(
                    vehicle_id=vehicle.id, title="b", status=MaintenanceStatus.open, created_by=user.id
                )
            )
            db.flush()


def test_ck_trips_completed_fields(client, db) -> None:
    """A completed trip must carry both odometers."""
    user, vehicle, driver = make_user(db), make_vehicle(db), make_driver(db)
    bad = _trip(
        db, vehicle, driver, user,
        status=TripStatus.completed, start_odometer=None, end_odometer=None,
    )
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(bad)
            db.flush()


def test_fk_restrict_on_vehicle_delete(client, db) -> None:
    user, vehicle, driver = make_user(db), make_vehicle(db), make_driver(db)
    db.add(_trip(db, vehicle, driver, user))
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.delete(vehicle)
            db.flush()
