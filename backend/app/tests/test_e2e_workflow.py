"""Suite C — end-to-end replay of the brief's scenario (docs/07 §4).

Run in front of judges:  pytest -q -k e2e -s
Single staged test with printed narration.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.tests.factories import auth_headers

API = "/api/v1"


def test_e2e_workflow(client, db) -> None:
    fm = auth_headers(client, db, "fleet_manager")
    print("\n── TransitOps E2E ─────────────────────────────")

    # 1. Register Van-05 (500 kg, odometer 41 000)
    van = client.post(
        f"{API}/vehicles",
        json={
            "registration_number": "GJ-01-AB-1234",
            "name": "Tata Ace Van-05",
            "type": "van",
            "max_load_capacity_kg": 500,
            "odometer_km": 41000,
            "acquisition_cost": 650000,
            "region": "North",
        },
        headers=fm,
    )
    assert van.status_code == 201, van.text
    van = van.json()
    print(f"1. Registered {van['registration_number']} (cap {van['max_load_capacity_kg']} kg)")

    # 2. Register Alex D'Souza with a valid licence
    alex = client.post(
        f"{API}/drivers",
        json={
            "full_name": "Alex D'Souza",
            "license_number": "GJ-LMV-2019-0001",
            "license_category": "LMV",
            "license_expiry": (date.today() + timedelta(days=400)).isoformat(),
            "contact_number": "9876543210",
        },
        headers=fm,
    )
    assert alex.status_code == 201, alex.text
    alex = alex.json()
    print(f"2. Registered driver {alex['full_name']}")

    # 3. Create a 450 kg trip (450 <= 500 passes)
    trip = client.post(
        f"{API}/trips",
        json={
            "source": "Ahmedabad",
            "destination": "Surat",
            "vehicle_id": van["id"],
            "driver_id": alex["id"],
            "cargo_weight_kg": 450,
            "planned_distance_km": 265,
            "revenue": 12000,
        },
        headers=fm,
    )
    assert trip.status_code == 201, trip.text
    tid = trip.json()["id"]
    print(f"3. Created trip {trip.json()['trip_code']} (450 kg ≤ 500 kg)")

    # 4. Dispatch → both on_trip, start odometer captured
    disp = client.post(f"{API}/trips/{tid}/dispatch", headers=fm)
    assert disp.status_code == 200 and disp.json()["status"] == "dispatched"
    assert Decimal(str(disp.json()["start_odometer"])) == Decimal("41000")
    assert client.get(f"{API}/vehicles/{van['id']}", headers=fm).json()["status"] == "on_trip"
    assert client.get(f"{API}/drivers/{alex['id']}", headers=fm).json()["status"] == "on_trip"
    print("4. Dispatched — vehicle & driver on_trip, start odometer 41000")

    # 5. Complete with end odometer + fuel → both available, odometer rolled, fuel log linked
    done = client.post(
        f"{API}/trips/{tid}/complete",
        json={"end_odometer": 41500, "fuel_liters": 40, "fuel_cost": 4000},
        headers=fm,
    )
    assert done.status_code == 200 and done.json()["status"] == "completed"
    vd = client.get(f"{API}/vehicles/{van['id']}", headers=fm).json()
    assert vd["status"] == "available"
    assert Decimal(str(vd["odometer_km"])) == Decimal("41500")
    assert client.get(f"{API}/drivers/{alex['id']}", headers=fm).json()["status"] == "available"
    fuel = client.get(f"{API}/fuel-logs?vehicle_id={van['id']}", headers=fm).json()
    assert fuel["total"] == 1 and float(fuel["items"][0]["liters"]) == 40.0
    print("5. Completed — odometer rolled to 41500, linked fuel log created")

    # 6. Open "Oil Change" maintenance → in_shop, hidden from dispatchable
    maint = client.post(
        f"{API}/maintenance",
        json={"vehicle_id": van["id"], "title": "Oil Change", "cost": 1200},
        headers=fm,
    )
    assert maint.status_code == 201
    mid = maint.json()["id"]
    assert client.get(f"{API}/vehicles/{van['id']}", headers=fm).json()["status"] == "in_shop"
    disp_pool = client.get(f"{API}/vehicles?dispatchable=true&page_size=100", headers=fm).json()
    assert van["id"] not in {x["id"] for x in disp_pool["items"]}
    print("6. Opened Oil Change — vehicle in_shop, removed from dispatch pool")

    # 7. Report reflects distance / fuel cost / efficiency
    rows = client.get(f"{API}/reports/vehicles", headers=fm).json()["rows"]
    row = next(r for r in rows if r["id"] == van["id"])
    assert row["total_distance_km"] == 500  # 41500 - 41000
    assert row["fuel_cost"] == 4000
    assert row["fuel_efficiency_km_l"] == 12.5  # 500 / 40
    print(f"7. Report: 500 km, ₹4000 fuel, {row['fuel_efficiency_km_l']} km/L")

    # 8. Close maintenance → available again
    assert client.post(f"{API}/maintenance/{mid}/close", headers=fm).status_code == 200
    assert client.get(f"{API}/vehicles/{van['id']}", headers=fm).json()["status"] == "available"
    print("8. Closed maintenance — vehicle available")
    print("── E2E complete ✔ ─────────────────────────────")
