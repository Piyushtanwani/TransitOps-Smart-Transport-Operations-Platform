"""AI insights: deterministic cores always respond; LLM narrative when configured."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.enums import MaintenanceStatus
from app.models.expense import Expense
from app.models.fuel_log import FuelLog
from app.models.maintenance import MaintenanceLog
from app.services.ai.settings import get_settings_row
from app.tests.factories import auth_headers, make_user, make_vehicle

API = "/api/v1"


def test_briefing_template_path_and_rbac(client, db) -> None:
    make_vehicle(db)
    fm = auth_headers(client, db, "fleet_manager")
    r = client.get(f"{API}/ai/insights/briefing", headers=fm)
    assert r.status_code == 200
    body = r.json()
    assert body["llm_used"] is False  # no key configured → rule-built narrative
    assert body["narrative"]
    assert "kpis" in body and "expiring_licenses" in body and "worst_roi" in body
    # FA allowed, driver/safety blocked (contains cost/ROI data)
    assert client.get(f"{API}/ai/insights/briefing",
                      headers=auth_headers(client, db, "financial_analyst")).status_code == 200
    assert client.get(f"{API}/ai/insights/briefing",
                      headers=auth_headers(client, db, "driver")).status_code == 403


def test_maintenance_risk_flags_unserviced_high_km(client, db) -> None:
    v = make_vehicle(db, odometer_km=Decimal("15000"))  # never serviced, >10k km
    serviced = make_vehicle(db, odometer_km=Decimal("15000"))
    actor = make_user(db, "fleet_manager")
    db.add(MaintenanceLog(vehicle_id=serviced.id, title="svc", status=MaintenanceStatus.closed,
                          opened_at=datetime.now(UTC) - timedelta(days=2),
                          closed_at=datetime.now(UTC) - timedelta(days=1),
                          created_by=actor.id))
    db.commit()

    so = auth_headers(client, db, "safety_officer")
    r = client.get(f"{API}/ai/insights/maintenance-risk", headers=so)
    assert r.status_code == 200
    rows = {x["registration_number"]: x for x in r.json()["vehicles"]}
    assert rows[v.registration_number]["risk_score"] >= 50
    assert any("never serviced" in reason for reason in rows[v.registration_number]["reasons"])
    assert rows[serviced.registration_number]["risk_score"] < rows[v.registration_number]["risk_score"]
    # FA blocked on this one
    assert client.get(f"{API}/ai/insights/maintenance-risk",
                      headers=auth_headers(client, db, "financial_analyst")).status_code == 403


def test_expense_anomalies_detects_outlier_and_duplicate(client, db) -> None:
    v = make_vehicle(db)
    actor = make_user(db, "fleet_manager")
    # 4 normal fuel prices ~100/L + 1 wild outlier at 400/L
    for cost in (2000, 2100, 1950, 2050):
        db.add(FuelLog(vehicle_id=v.id, liters=Decimal("20"), cost=Decimal(cost),
                       created_by=actor.id))
    db.add(FuelLog(vehicle_id=v.id, liters=Decimal("20"), cost=Decimal("8000"),
                   created_by=actor.id))
    # duplicate same-day toll
    for _ in range(2):
        db.add(Expense(vehicle_id=v.id, type="toll", amount=Decimal("450"),
                       created_by=actor.id))
    db.commit()

    fm = auth_headers(client, db, "fleet_manager")
    r = client.get(f"{API}/ai/insights/expense-anomalies", headers=fm)
    assert r.status_code == 200
    kinds = {a["kind"] for a in r.json()["anomalies"]}
    assert "fuel_price_outlier" in kinds
    assert "possible_duplicate" in kinds
    assert r.json()["llm_used"] is False
    assert client.get(f"{API}/ai/insights/expense-anomalies",
                      headers=auth_headers(client, db, "driver")).status_code == 403


def test_insights_use_llm_when_configured(client, db, monkeypatch) -> None:
    make_vehicle(db)
    row = get_settings_row(db)
    row.openrouter_api_key = "sk-or-db-key"
    row.chatbot_enabled = True
    db.commit()
    monkeypatch.setattr(
        "app.services.ai.insights.call_openrouter",
        lambda *a, **k: {"choices": [{"message": {"content": "LLM briefing text."}}]},
    )
    fm = auth_headers(client, db, "fleet_manager")
    body = client.get(f"{API}/ai/insights/briefing", headers=fm).json()
    assert body["llm_used"] is True
    assert body["narrative"] == "LLM briefing text."
