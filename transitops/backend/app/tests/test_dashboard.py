"""Dashboard KPI/chart endpoint tests (BE-10, docs/07 §1)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.enums import DriverStatus, UserRole, VehicleStatus
from app.tests.factories import API, auth_headers, make_driver, make_vehicle

pytestmark = pytest.mark.usefixtures("client")


def test_kpi_math(client, db: Session) -> None:
    make_vehicle(db, status=VehicleStatus.available)
    make_vehicle(db, status=VehicleStatus.available)
    make_vehicle(db, status=VehicleStatus.available)
    make_vehicle(db, status=VehicleStatus.on_trip)
    make_vehicle(db, status=VehicleStatus.in_shop)
    make_vehicle(db, status=VehicleStatus.retired)

    headers = auth_headers(client, db, role=UserRole.fleet_manager)
    resp = client.get(f"{API}/dashboard/kpis", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["active_vehicles"] == 5
    assert body["available_vehicles"] == 3
    assert body["in_maintenance"] == 1
    assert body["fleet_utilization_pct"] == round(100 * 1 / 5, 1) == 20.0
    assert "alerts" in body
    assert "expiring_licenses" in body["alerts"]


def test_zero_active_guard(client, db: Session) -> None:
    make_vehicle(db, status=VehicleStatus.retired)

    headers = auth_headers(client, db, role=UserRole.fleet_manager)
    resp = client.get(f"{API}/dashboard/kpis", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["active_vehicles"] == 0
    assert body["fleet_utilization_pct"] == 0.0


def test_alerts_expiring_licenses(client, db: Session) -> None:
    make_driver(db, license_expiry=date.today() + timedelta(days=15))
    make_driver(db, status=DriverStatus.available, license_expiry=date.today() + timedelta(days=400))

    headers = auth_headers(client, db, role=UserRole.fleet_manager)
    resp = client.get(f"{API}/dashboard/kpis", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["alerts"]["expiring_licenses"] == 1


def test_charts_endpoint(client, db: Session) -> None:
    headers = auth_headers(client, db, role=UserRole.fleet_manager)
    resp = client.get(f"{API}/dashboard/charts", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert set(body.keys()) == {"trips_last_14d", "cost_breakdown", "status_distribution"}
    assert len(body["trips_last_14d"]) == 14


@pytest.mark.parametrize(
    "role",
    [
        UserRole.fleet_manager,
        UserRole.driver,
        UserRole.safety_officer,
        UserRole.financial_analyst,
    ],
)
def test_kpis_all_roles(client, db: Session, role: UserRole) -> None:
    headers = auth_headers(client, db, role=role)
    resp = client.get(f"{API}/dashboard/kpis", headers=headers)
    assert resp.status_code == 200, resp.text
