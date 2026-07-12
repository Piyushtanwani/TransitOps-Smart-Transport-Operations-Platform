"""Vehicle analytics report endpoint tests (BE-11, docs/07 §6 golden math)."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.enums import MaintenanceStatus, TripStatus, UserRole
from app.models.fuel_log import FuelLog
from app.models.maintenance import MaintenanceLog
from app.tests.factories import API, auth_headers, make_driver, make_trip, make_user, make_vehicle

pytestmark = pytest.mark.usefixtures("client")


def _build_golden_fixture(db: Session):
    user = make_user(db, "fleet_manager")
    vehicle = make_vehicle(db, acquisition_cost=Decimal("100000"))
    driver = make_driver(db)

    make_trip(
        db,
        vehicle=vehicle,
        driver=driver,
        created_by=user.id,
        status=TripStatus.completed,
        start_odometer=Decimal("0"),
        end_odometer=Decimal("100"),
        revenue=Decimal("6000"),
    )
    make_trip(
        db,
        vehicle=vehicle,
        driver=driver,
        created_by=user.id,
        status=TripStatus.completed,
        start_odometer=Decimal("100"),
        end_odometer=Decimal("250"),
        revenue=Decimal("4000"),
    )

    db.add(
        FuelLog(
            vehicle_id=vehicle.id,
            liters=Decimal("20"),
            cost=Decimal("2000"),
            created_by=user.id,
        )
    )
    db.add(
        MaintenanceLog(
            vehicle_id=vehicle.id,
            title="svc",
            cost=Decimal("1000"),
            status=MaintenanceStatus.closed,
            closed_at=datetime.now(UTC),
            created_by=user.id,
        )
    )
    db.commit()
    return vehicle


def test_vehicle_report_golden_math(client, db: Session) -> None:
    vehicle = _build_golden_fixture(db)
    headers = auth_headers(client, db, role=UserRole.fleet_manager)

    resp = client.get(f"{API}/reports/vehicles", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    row = next(r for r in body["rows"] if r["id"] == str(vehicle.id))
    assert row["total_distance_km"] == 250
    assert row["total_liters"] == 20
    assert row["fuel_cost"] == 2000
    assert row["maintenance_cost"] == 1000
    assert row["operational_cost"] == 3000
    assert row["revenue"] == 10000
    assert row["fuel_efficiency_km_l"] == 12.5
    assert row["roi"] == 0.07

    assert "totals" in body
    assert body["totals"]["fuel_cost"] >= 2000
    assert body["totals"]["maintenance_cost"] >= 1000
    assert body["totals"]["operational_cost"] >= 3000
    assert body["totals"]["revenue"] >= 10000


def test_vehicle_report_csv(client, db: Session) -> None:
    _build_golden_fixture(db)
    headers = auth_headers(client, db, role=UserRole.fleet_manager)

    resp = client.get(f"{API}/reports/vehicles.csv", headers=headers)
    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers["content-type"]
    assert resp.headers["content-disposition"].startswith(
        "attachment; filename=transitops_vehicle_report_"
    )

    first_line = resp.text.splitlines()[0]
    assert first_line.split(",")[0] == "id"
    assert "registration_number" in first_line


@pytest.mark.parametrize(
    "role, expected_status",
    [
        (UserRole.fleet_manager, 200),
        (UserRole.financial_analyst, 200),
        (UserRole.driver, 403),
        (UserRole.safety_officer, 403),
    ],
)
def test_vehicle_report_rbac(client, db: Session, role: UserRole, expected_status: int) -> None:
    headers = auth_headers(client, db, role=role)
    resp = client.get(f"{API}/reports/vehicles", headers=headers)
    assert resp.status_code == expected_status, resp.text
