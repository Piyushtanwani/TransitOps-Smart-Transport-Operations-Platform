"""Suite A — one test per business rule (docs/07 §2, names cite BR ids).

BR-1/BR-2 land with BE-05; BR-3 with BE-06; BR-4..BR-8 + invalid transitions
with BE-07; BR-9/BR-10 with BE-08.
"""
from __future__ import annotations

from app.models.enums import VehicleStatus
from app.tests.factories import auth_headers, make_vehicle

API = "/api/v1"


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
