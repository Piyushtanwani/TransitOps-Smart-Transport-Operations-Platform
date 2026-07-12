"""Maintenance endpoint behavior: duplicate-open guard + RBAC (docs/03 §4)."""
from __future__ import annotations

from app.tests.factories import auth_headers, make_vehicle

API = "/api/v1"


def test_duplicate_open_maintenance_blocked(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    v = make_vehicle(db)
    first = client.post(
        f"{API}/maintenance", json={"vehicle_id": str(v.id), "title": "a"}, headers=headers
    )
    assert first.status_code == 201
    second = client.post(
        f"{API}/maintenance", json={"vehicle_id": str(v.id), "title": "b"}, headers=headers
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "VEHICLE_HAS_OPEN_MAINTENANCE"


def test_maintenance_create_is_fm_only_read_is_all(client, db) -> None:
    v = make_vehicle(db)
    body = {"vehicle_id": str(v.id), "title": "x"}
    for role in ("driver", "safety_officer", "financial_analyst"):
        h = auth_headers(client, db, role)
        assert client.post(f"{API}/maintenance", json=body, headers=h).status_code == 403
    for role in ("driver", "safety_officer", "financial_analyst", "fleet_manager"):
        h = auth_headers(client, db, role)
        assert client.get(f"{API}/maintenance", headers=h).status_code == 200
