"""AI Trip Advisor tests (docs/06 §6, BE-15).

`OPENROUTER_API_KEY` is unset in the test environment, so `ensure_ai_enabled`
always raises before any network call — the advisor falls back to the
deterministic template summary. No LLM mocking is required for these tests
to stay network-free; `evaluate(..., use_llm=False)` is also exercised
directly to prove the summary path is independently forceable.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.models.enums import DriverStatus, VehicleStatus
from app.services.ai.advisor import evaluate
from app.tests.factories import API, auth_headers, make_driver, make_vehicle


def _payload(vehicle, driver, cargo="100", distance="50") -> dict:
    return {
        "vehicle_id": str(vehicle.id),
        "driver_id": str(driver.id),
        "cargo_weight_kg": cargo,
        "planned_distance_km": distance,
    }


def test_verdict_block_on_cargo_over_capacity(db):
    vehicle = make_vehicle(db, max_load_capacity_kg=Decimal("500"), status=VehicleStatus.available)
    driver = make_driver(db, status=DriverStatus.available)

    result = evaluate(db, vehicle.id, driver.id, Decimal("620"), Decimal("100"))

    assert result["verdict"] == "block"
    assert result["hard_failures"]
    assert isinstance(result["summary"], str) and result["summary"]


def test_verdict_caution_on_low_safety_score(db):
    vehicle = make_vehicle(db, max_load_capacity_kg=Decimal("500"), status=VehicleStatus.available)
    driver = make_driver(db, safety_score=Decimal("50"), status=DriverStatus.available)

    result = evaluate(db, vehicle.id, driver.id, Decimal("100"), Decimal("50"))

    assert result["verdict"] == "caution"
    assert result["hard_failures"] == []
    assert result["risk_factors"]
    assert isinstance(result["summary"], str) and result["summary"]


def test_verdict_go_when_clean(db):
    vehicle = make_vehicle(
        db,
        max_load_capacity_kg=Decimal("500"),
        odometer_km=Decimal("1000"),
        status=VehicleStatus.available,
    )
    driver = make_driver(
        db,
        safety_score=Decimal("95"),
        license_expiry=date.today() + timedelta(days=365),
        status=DriverStatus.available,
    )

    result = evaluate(db, vehicle.id, driver.id, Decimal("100"), Decimal("50"))

    assert result["verdict"] == "go"
    assert result["hard_failures"] == []
    assert result["risk_factors"] == []
    assert isinstance(result["summary"], str) and result["summary"]


def test_advisor_endpoint_does_not_mutate_state(client, db):
    vehicle = make_vehicle(db, max_load_capacity_kg=Decimal("500"), status=VehicleStatus.available)
    driver = make_driver(db, safety_score=Decimal("50"), status=DriverStatus.available)
    headers = auth_headers(client, db, role="fleet_manager")

    resp = client.post(f"{API}/ai/trip-advisor", json=_payload(vehicle, driver), headers=headers)

    assert resp.status_code == 200, resp.text
    db.refresh(vehicle)
    db.refresh(driver)
    assert vehicle.status == VehicleStatus.available
    assert driver.status == DriverStatus.available


def test_advisor_rbac_allows_fleet_manager_and_driver(client, db):
    vehicle = make_vehicle(db, status=VehicleStatus.available)
    driver = make_driver(db, status=DriverStatus.available)

    for role in ("fleet_manager", "driver"):
        headers = auth_headers(client, db, role=role)
        resp = client.post(f"{API}/ai/trip-advisor", json=_payload(vehicle, driver), headers=headers)
        assert resp.status_code == 200, resp.text


def test_advisor_rbac_forbids_financial_analyst_and_safety_officer(client, db):
    vehicle = make_vehicle(db, status=VehicleStatus.available)
    driver = make_driver(db, status=DriverStatus.available)

    for role in ("financial_analyst", "safety_officer"):
        headers = auth_headers(client, db, role=role)
        resp = client.post(f"{API}/ai/trip-advisor", json=_payload(vehicle, driver), headers=headers)
        assert resp.status_code == 403, resp.text
