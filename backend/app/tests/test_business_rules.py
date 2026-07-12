"""Suite A — one test per business rule (docs/07 §2, names cite BR ids).

BR-1/BR-2 land with BE-05; BR-3 with BE-06; BR-4..BR-8 + invalid transitions
with BE-07; BR-9/BR-10 with BE-08.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.models.enums import DriverStatus, VehicleStatus
from app.tests.factories import (
    auth_headers,
    make_driver,
    make_vehicle,
)

API = "/api/v1"


def _create_trip(client, headers, vehicle_id, driver_id, *, cargo=400, distance=100):
    return client.post(
        f"{API}/trips",
        json={
            "source": "Ahmedabad",
            "destination": "Surat",
            "vehicle_id": str(vehicle_id),
            "driver_id": str(driver_id),
            "cargo_weight_kg": cargo,
            "planned_distance_km": distance,
        },
        headers=headers,
    )


def test_br1_duplicate_registration_rejected(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    body = {
        "registration_number": "GJ-99-XX-0001",
        "name": "Truck",
        "type": "truck",
        "max_load_capacity_kg": 1000,
        "acquisition_cost": 500000,
        "region": "North",
    }
    assert client.post(f"{API}/vehicles", json=body, headers=headers).status_code == 201
    r = client.post(f"{API}/vehicles", json=body, headers=headers)
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "DUPLICATE_REGISTRATION"
    assert "GJ-99-XX-0001" in err["message"]
    assert err["field"] == "registration_number"


def test_br2_in_shop_and_retired_hidden_from_dispatchable(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    available = make_vehicle(db, status=VehicleStatus.available)
    in_shop = make_vehicle(db, status=VehicleStatus.in_shop)
    retired = make_vehicle(db, status=VehicleStatus.retired)

    r = client.get(f"{API}/vehicles?dispatchable=true&page_size=100", headers=headers)
    assert r.status_code == 200
    ids = {v["id"] for v in r.json()["items"]}
    assert str(available.id) in ids
    assert str(in_shop.id) not in ids
    assert str(retired.id) not in ids
    # BE-07 extends: creating a trip with an in_shop vehicle → 409 VEHICLE_NOT_AVAILABLE.


# --- BR-2 (create with in_shop) ---

def test_br2_create_trip_with_in_shop_vehicle_blocked(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db, status=VehicleStatus.in_shop)
    d = make_driver(db)
    r = _create_trip(client, headers, v.id, d.id)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_NOT_AVAILABLE"
    assert "workshop" in r.json()["error"]["message"]


# --- BR-3 ---

def test_br3_expired_license_blocked(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db)
    d = make_driver(db, license_expiry=date.today() - timedelta(days=1))
    r = _create_trip(client, headers, v.id, d.id)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DRIVER_LICENSE_EXPIRED"


def test_br3_suspended_driver_blocked(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db)
    d = make_driver(db, status=DriverStatus.suspended)
    r = _create_trip(client, headers, v.id, d.id)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DRIVER_SUSPENDED"


# --- BR-4 (double-dispatch, service + DB partial index) ---

def test_br4_double_dispatch_vehicle_blocked(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db)
    d1, d2 = make_driver(db), make_driver(db)
    t1 = _create_trip(client, headers, v.id, d1.id).json()["id"]
    t2 = _create_trip(client, headers, v.id, d2.id).json()["id"]
    assert client.post(f"{API}/trips/{t1}/dispatch", headers=headers).status_code == 200
    r = client.post(f"{API}/trips/{t2}/dispatch", headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_NOT_AVAILABLE"
    # DB-level partial-index proof (raw insert → IntegrityError) lives in Suite D
    # (test_schema_constraints.py); the shared-session harness cannot host an
    # intentional IntegrityError mid-transaction.


def test_br4_double_dispatch_driver_blocked(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v1, v2 = make_vehicle(db), make_vehicle(db)
    d = make_driver(db)
    t1 = _create_trip(client, headers, v1.id, d.id).json()["id"]
    t2 = _create_trip(client, headers, v2.id, d.id).json()["id"]
    assert client.post(f"{API}/trips/{t1}/dispatch", headers=headers).status_code == 200
    r = client.post(f"{API}/trips/{t2}/dispatch", headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DRIVER_NOT_AVAILABLE"


# --- BR-5 ---

def test_br5_cargo_exceeds_capacity(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db, max_load_capacity_kg=Decimal("500"), name="Van-05")
    d = make_driver(db)
    over = _create_trip(client, headers, v.id, d.id, cargo=620)
    assert over.status_code == 409
    err = over.json()["error"]
    assert err["code"] == "CARGO_EXCEEDS_CAPACITY"
    assert "620" in err["message"] and "500" in err["message"]
    assert err["field"] == "cargo_weight_kg"
    # boundary: exactly capacity is allowed
    ok = _create_trip(client, headers, v.id, make_driver(db).id, cargo=500)
    assert ok.status_code == 201


# --- BR-6 ---

def test_br6_dispatch_sets_on_trip(client, db) -> None:
    from app.models.driver import Driver
    from app.models.vehicle import Vehicle

    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db, odometer_km=Decimal("12345"))
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    trip = client.post(f"{API}/trips/{tid}/dispatch", headers=headers).json()
    assert trip["status"] == "dispatched"
    assert Decimal(str(trip["start_odometer"])) == Decimal("12345")
    db.expire_all()
    assert db.get(Vehicle, v.id).status == VehicleStatus.on_trip
    assert db.get(Driver, d.id).status == DriverStatus.on_trip


# --- BR-7 ---

def test_br7_complete_restores_and_rolls_odometer(client, db) -> None:
    from app.models.driver import Driver
    from app.models.fuel_log import FuelLog
    from app.models.vehicle import Vehicle

    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db, odometer_km=Decimal("1000"))
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    done = client.post(
        f"{API}/trips/{tid}/complete",
        json={"end_odometer": 1250, "fuel_liters": 20, "fuel_cost": 2000},
        headers=headers,
    )
    assert done.status_code == 200 and done.json()["status"] == "completed"
    db.expire_all()
    assert db.get(Vehicle, v.id).status == VehicleStatus.available
    assert db.get(Driver, d.id).status == DriverStatus.available
    assert db.get(Vehicle, v.id).odometer_km == Decimal("1250.00")
    linked = db.query(FuelLog).filter(FuelLog.trip_id == tid).all()
    assert len(linked) == 1 and linked[0].liters == Decimal("20.00")


def test_end_odometer_lt_start_rejected(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db, odometer_km=Decimal("5000"))
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    r = client.post(f"{API}/trips/{tid}/complete", json={"end_odometer": 4000}, headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "END_ODOMETER_LT_START"


def test_fuel_fields_both_or_neither(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db)
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    r = client.post(
        f"{API}/trips/{tid}/complete",
        json={"end_odometer": 1200, "fuel_liters": 10},  # missing fuel_cost
        headers=headers,
    )
    assert r.status_code == 422


# --- BR-8 ---

def test_br8_cancel_dispatched_restores(client, db) -> None:
    from app.models.driver import Driver
    from app.models.vehicle import Vehicle

    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db)
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    cancelled = client.post(f"{API}/trips/{tid}/cancel", json={"reason": "weather"}, headers=headers)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    db.expire_all()
    assert db.get(Vehicle, v.id).status == VehicleStatus.available
    assert db.get(Driver, d.id).status == DriverStatus.available


def test_br8_cancel_draft_leaves_others_untouched(client, db) -> None:
    from app.models.driver import Driver
    from app.models.vehicle import Vehicle

    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db)
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]  # draft, nothing reserved
    r = client.post(f"{API}/trips/{tid}/cancel", headers=headers)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    db.expire_all()
    assert db.get(Vehicle, v.id).status == VehicleStatus.available
    assert db.get(Driver, d.id).status == DriverStatus.available


# --- invalid transitions ---

def test_invalid_transitions_rejected(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    v = make_vehicle(db)
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    # complete a draft → 409
    bad = client.post(f"{API}/trips/{tid}/complete", json={"end_odometer": 100}, headers=headers)
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
    # dispatch, complete, then dispatch again → 409
    client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    client.post(f"{API}/trips/{tid}/complete", json={"end_odometer": 500}, headers=headers)
    again = client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    assert again.status_code == 409 and again.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


# --- BR-9 / BR-10 (maintenance) ---

def test_br9_open_maintenance_sets_in_shop(client, db) -> None:
    from app.models.vehicle import Vehicle

    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db, status=VehicleStatus.available)
    r = client.post(
        f"{API}/maintenance",
        json={"vehicle_id": str(v.id), "title": "Oil Change", "cost": 1200},
        headers=headers,
    )
    assert r.status_code == 201
    db.expire_all()
    assert db.get(Vehicle, v.id).status == VehicleStatus.in_shop
    disp = client.get(f"{API}/vehicles?dispatchable=true&page_size=100", headers=headers)
    assert str(v.id) not in {x["id"] for x in disp.json()["items"]}


def test_br10_close_maintenance_restores_unless_retired(client, db) -> None:
    from app.models.vehicle import Vehicle

    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db, status=VehicleStatus.available)
    mid = client.post(
        f"{API}/maintenance", json={"vehicle_id": str(v.id), "title": "svc"}, headers=headers
    ).json()["id"]
    closed = client.post(f"{API}/maintenance/{mid}/close", json={"cost": 5000}, headers=headers)
    assert closed.status_code == 200 and closed.json()["status"] == "closed"
    db.expire_all()
    assert db.get(Vehicle, v.id).status == VehicleStatus.available

    # a retired vehicle stays retired when its job closes (BR-10 exception)
    v2 = make_vehicle(db, status=VehicleStatus.available)
    mid2 = client.post(
        f"{API}/maintenance", json={"vehicle_id": str(v2.id), "title": "svc2"}, headers=headers
    ).json()["id"]
    veh2 = db.get(Vehicle, v2.id)
    veh2.status = VehicleStatus.retired
    db.commit()
    client.post(f"{API}/maintenance/{mid2}/close", headers=headers)
    db.expire_all()
    assert db.get(Vehicle, v2.id).status == VehicleStatus.retired


def test_open_maintenance_on_on_trip_vehicle_blocked(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db)
    d = make_driver(db)
    tid = _create_trip(client, headers, v.id, d.id).json()["id"]
    client.post(f"{API}/trips/{tid}/dispatch", headers=headers)
    code = client.get(f"{API}/trips/{tid}", headers=headers).json()["trip_code"]
    r = client.post(
        f"{API}/maintenance", json={"vehicle_id": str(v.id), "title": "svc"}, headers=headers
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_NOT_AVAILABLE"
    assert code in r.json()["error"]["message"]
