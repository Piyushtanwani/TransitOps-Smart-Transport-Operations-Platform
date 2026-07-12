"""BE-09 tests: fuel logs + expenses endpoints (docs/03 §4, §3 RBAC)."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.models.enums import UserRole
from app.tests.factories import API, auth_headers, make_vehicle


def _fuel_body(vehicle_id, **kw) -> dict:
    body = {
        "vehicle_id": str(vehicle_id),
        "liters": "40.50",
        "cost": "3500.00",
    }
    body.update(kw)
    return body


def _expense_body(vehicle_id, **kw) -> dict:
    body = {
        "vehicle_id": str(vehicle_id),
        "type": "toll",
        "amount": "150.00",
    }
    body.update(kw)
    return body


def test_create_fuel_log_happy_path_fleet_manager(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.fleet_manager)

    resp = client.post(f"{API}/fuel-logs", json=_fuel_body(vehicle.id), headers=headers)

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["vehicle_id"] == str(vehicle.id)
    assert Decimal(data["liters"]) == Decimal("40.50")
    assert Decimal(data["cost"]) == Decimal("3500.00")


def test_create_expense_happy_path_financial_analyst(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.financial_analyst)

    resp = client.post(f"{API}/expenses", json=_expense_body(vehicle.id), headers=headers)

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["vehicle_id"] == str(vehicle.id)
    assert data["type"] == "toll"
    assert Decimal(data["amount"]) == Decimal("150.00")


def test_negative_liters_returns_422_on_liters_field(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.fleet_manager)

    resp = client.post(
        f"{API}/fuel-logs", json=_fuel_body(vehicle.id, liters="-1"), headers=headers
    )

    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["field"] == "liters"


def test_negative_amount_returns_422_on_amount_field(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.financial_analyst)

    resp = client.post(
        f"{API}/expenses", json=_expense_body(vehicle.id, amount="-1"), headers=headers
    )

    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["field"] == "amount"


def test_driver_can_create_fuel_log_but_not_expense(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.driver)

    fuel_resp = client.post(f"{API}/fuel-logs", json=_fuel_body(vehicle.id), headers=headers)
    assert fuel_resp.status_code == 201, fuel_resp.text

    expense_resp = client.post(
        f"{API}/expenses", json=_expense_body(vehicle.id), headers=headers
    )
    assert expense_resp.status_code == 403, expense_resp.text


def test_safety_officer_forbidden_on_all_four_endpoints(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.safety_officer)

    assert (
        client.post(f"{API}/fuel-logs", json=_fuel_body(vehicle.id), headers=headers).status_code
        == 403
    )
    assert (
        client.post(
            f"{API}/expenses", json=_expense_body(vehicle.id), headers=headers
        ).status_code
        == 403
    )
    assert client.get(f"{API}/fuel-logs", headers=headers).status_code == 403
    assert client.get(f"{API}/expenses", headers=headers).status_code == 403


def test_financial_analyst_full_access(client, db):
    vehicle = make_vehicle(db)
    headers = auth_headers(client, db, UserRole.financial_analyst)

    assert (
        client.post(f"{API}/fuel-logs", json=_fuel_body(vehicle.id), headers=headers).status_code
        == 201
    )
    assert (
        client.post(
            f"{API}/expenses", json=_expense_body(vehicle.id), headers=headers
        ).status_code
        == 201
    )
    assert client.get(f"{API}/fuel-logs", headers=headers).status_code == 200
    assert client.get(f"{API}/expenses", headers=headers).status_code == 200


def test_driver_forbidden_on_fuel_log_list(client, db):
    headers = auth_headers(client, db, UserRole.driver)

    resp = client.get(f"{API}/fuel-logs", headers=headers)

    assert resp.status_code == 403, resp.text


def test_date_from_filter_returns_only_newer_fuel_log(client, db):
    vehicle = make_vehicle(db)
    fm_headers = auth_headers(client, db, UserRole.fleet_manager)

    old_date = date.today() - timedelta(days=30)
    new_date = date.today()

    old_resp = client.post(
        f"{API}/fuel-logs",
        json=_fuel_body(vehicle.id, filled_at=old_date.isoformat()),
        headers=fm_headers,
    )
    assert old_resp.status_code == 201, old_resp.text

    new_resp = client.post(
        f"{API}/fuel-logs",
        json=_fuel_body(vehicle.id, filled_at=new_date.isoformat()),
        headers=fm_headers,
    )
    assert new_resp.status_code == 201, new_resp.text

    fa_headers = auth_headers(client, db, UserRole.financial_analyst)
    list_resp = client.get(
        f"{API}/fuel-logs",
        params={
            "vehicle_id": str(vehicle.id),
            "date_from": (date.today() - timedelta(days=1)).isoformat(),
        },
        headers=fa_headers,
    )

    assert list_resp.status_code == 200, list_resp.text
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["filled_at"] == new_date.isoformat()
