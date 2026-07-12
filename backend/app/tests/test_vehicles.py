"""Vehicle endpoint behavior: detail rollups, retire/unretire, delete-with-history."""
from __future__ import annotations

from app.models.enums import MaintenanceStatus, VehicleStatus
from app.models.maintenance import MaintenanceLog
from app.tests.factories import auth_headers, make_driver, make_trip, make_user, make_vehicle

API = "/api/v1"


def test_vehicle_create_and_detail_rollups(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    body = {
        "registration_number": "GJ-01-DET-9",
        "name": "Detail Van",
        "type": "van",
        "max_load_capacity_kg": 500,
        "acquisition_cost": 650000,
        "region": "North",
    }
    created = client.post(f"{API}/vehicles", json=body, headers=headers).json()
    r = client.get(f"{API}/vehicles/{created['id']}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["open_maintenance"] is False
    assert detail["active_trip_code"] is None


def test_vehicle_retire_and_unretire(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db, status=VehicleStatus.available)
    retired = client.post(f"{API}/vehicles/{v.id}/retire", headers=headers)
    assert retired.status_code == 200 and retired.json()["status"] == "retired"
    back = client.post(f"{API}/vehicles/{v.id}/unretire", headers=headers)
    assert back.status_code == 200 and back.json()["status"] == "available"


def test_vehicle_retire_blocked_by_open_maintenance(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    actor = make_user(db, "fleet_manager")
    v = make_vehicle(db, status=VehicleStatus.in_shop)
    db.add(
        MaintenanceLog(
            vehicle_id=v.id, title="Gearbox", status=MaintenanceStatus.open, created_by=actor.id
        )
    )
    db.commit()
    r = client.post(f"{API}/vehicles/{v.id}/retire", headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_HAS_OPEN_MAINTENANCE"


def test_vehicle_retire_invalid_from_on_trip(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db, status=VehicleStatus.on_trip)
    r = client.post(f"{API}/vehicles/{v.id}/retire", headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_vehicle_delete_with_history_blocked(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    actor = make_user(db, "fleet_manager")
    v = make_vehicle(db)
    d = make_driver(db)
    make_trip(db, vehicle=v, driver=d, created_by=actor.id)
    r = client.delete(f"{API}/vehicles/{v.id}", headers=headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VEHICLE_HAS_HISTORY"


def test_vehicle_delete_without_history_ok(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db)
    assert client.delete(f"{API}/vehicles/{v.id}", headers=headers).status_code == 204
