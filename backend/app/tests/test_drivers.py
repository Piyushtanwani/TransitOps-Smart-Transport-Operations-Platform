"""Driver endpoint behavior: assignable filter, status guard, expiring, duplicate licence."""
from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import DriverStatus, TripStatus
from app.tests.factories import auth_headers, make_driver, make_trip, make_user, make_vehicle

API = "/api/v1"


def test_driver_assignable_excludes_expired_and_suspended(client, db) -> None:
    headers = auth_headers(client, db, "driver")
    good = make_driver(db)  # available, valid licence
    expired = make_driver(db, license_expiry=date.today() - timedelta(days=1))
    suspended = make_driver(db, status=DriverStatus.suspended)

    r = client.get(f"{API}/drivers?assignable=true&page_size=100", headers=headers)
    assert r.status_code == 200
    ids = {d["id"] for d in r.json()["items"]}
    assert str(good.id) in ids
    assert str(expired.id) not in ids
    assert str(suspended.id) not in ids


def test_driver_license_valid_filter(client, db) -> None:
    headers = auth_headers(client, db, "safety_officer")
    valid = make_driver(db)
    expired = make_driver(db, license_expiry=date.today() - timedelta(days=5))
    r = client.get(f"{API}/drivers?license_valid=false&page_size=100", headers=headers)
    ids = {d["id"] for d in r.json()["items"]}
    assert str(expired.id) in ids and str(valid.id) not in ids


def test_driver_duplicate_license_409(client, db) -> None:
    headers = auth_headers(client, db, "safety_officer")
    body = {
        "full_name": "Test D",
        "license_number": "GJ-DUP-0001",
        "license_category": "LMV",
        "license_expiry": (date.today() + timedelta(days=365)).isoformat(),
        "contact_number": "9876500000",
    }
    assert client.post(f"{API}/drivers", json=body, headers=headers).status_code == 201
    r = client.post(f"{API}/drivers", json=body, headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DUPLICATE_LICENSE"
    assert r.json()["error"]["field"] == "license_number"


def test_driver_status_transitions(client, db) -> None:
    headers = auth_headers(client, db, "safety_officer")
    d = make_driver(db, status=DriverStatus.available)
    assert client.post(f"{API}/drivers/{d.id}/status", json={"status": "off_duty"}, headers=headers).json()["status"] == "off_duty"
    assert client.post(f"{API}/drivers/{d.id}/status", json={"status": "suspended"}, headers=headers).json()["status"] == "suspended"
    assert client.post(f"{API}/drivers/{d.id}/status", json={"status": "available"}, headers=headers).json()["status"] == "available"


def test_driver_suspend_while_on_trip_409_names_trip(client, db) -> None:
    headers = auth_headers(client, db, "safety_officer")
    actor = make_user(db, "fleet_manager")
    vehicle = make_vehicle(db)
    driver = make_driver(db, status=DriverStatus.on_trip)
    trip = make_trip(
        db, vehicle=vehicle, driver=driver, created_by=actor.id, status=TripStatus.dispatched
    )
    r = client.post(f"{API}/drivers/{driver.id}/status", json={"status": "suspended"}, headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
    assert trip.trip_code in r.json()["error"]["message"]


def test_driver_cannot_set_on_trip_manually(client, db) -> None:
    headers = auth_headers(client, db, "safety_officer")
    d = make_driver(db)
    r = client.post(f"{API}/drivers/{d.id}/status", json={"status": "on_trip"}, headers=headers)
    assert r.status_code == 422  # Literal rejects on_trip


def test_driver_expiring_endpoint(client, db) -> None:
    headers = auth_headers(client, db, "safety_officer")
    soon = make_driver(db, license_expiry=date.today() + timedelta(days=10))
    far = make_driver(db, license_expiry=date.today() + timedelta(days=200))
    r = client.get(f"{API}/drivers/expiring?days=30", headers=headers)
    assert r.status_code == 200
    ids = {d["id"] for d in r.json()}
    assert str(soon.id) in ids and str(far.id) not in ids
