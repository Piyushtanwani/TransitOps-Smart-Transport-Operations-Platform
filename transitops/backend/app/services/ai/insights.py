"""AI operational insights: daily briefing, maintenance risk, expense anomalies.

Each insight has a deterministic core that always works; when OpenRouter is
configured (DB key or env — see ai/settings.resolve_api_key) an LLM narrative
is layered on top. With no key the narrative falls back to a rule-built text,
so the endpoints never 503.
"""
from __future__ import annotations

import statistics
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.db import queries
from app.models.enums import MaintenanceStatus, TripStatus, VehicleStatus
from app.models.fuel_log import FuelLog
from app.models.maintenance import MaintenanceLog
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.services.ai.client import OpenRouterError, call_openrouter
from app.services.ai.settings import ensure_ai_enabled, resolve_api_key
from app.services.driver_service import expiring_drivers


def _narrate(db: Session, system: str, payload: str, fallback: str) -> tuple[str, bool]:
    """LLM narrative when configured; deterministic fallback otherwise."""
    try:
        row = ensure_ai_enabled(db)
        result = call_openrouter(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": payload},
            ],
            model=row.model,
            temperature=float(row.temperature),
            max_tokens=min(row.max_tokens, 600),
            api_key=resolve_api_key(row),
        )
        text = (result["choices"][0]["message"]["content"] or "").strip()
        if text:
            return text, True
    except (DomainError, OpenRouterError, KeyError, IndexError):
        pass
    return fallback, False


# ---------------------------------------------------------------- briefing

def daily_briefing(db: Session, *, use_llm: bool = True) -> dict:
    """One-screen morning ops summary for FM/FA."""
    kpis = {
        **queries.get_vehicle_kpis(db),
        **queries.get_trip_kpis(db),
        **queries.get_driver_kpis(db),
    }
    expiring = [
        {
            "full_name": d.full_name,
            "license_expiry": d.license_expiry.isoformat(),
            "days_left": (d.license_expiry - date.today()).days,
        }
        for d in expiring_drivers(db, 30)
    ]
    open_jobs = [
        {"vehicle": m.vehicle.registration_number, "title": m.title,
         "days_open": (datetime.now(UTC) - m.opened_at).days}
        for m in db.execute(
            select(MaintenanceLog).where(MaintenanceLog.status == MaintenanceStatus.open)
        ).scalars()
    ]
    report = queries.get_vehicle_report_rows(db)
    with_roi = [r for r in report if r["roi"] is not None]
    worst_roi = sorted(with_roi, key=lambda r: r["roi"])[:3]
    worst_roi = [
        {"vehicle": r["registration_number"], "roi": r["roi"],
         "operational_cost": r["operational_cost"], "revenue": r["revenue"]}
        for r in worst_roi
    ]
    active = [
        {"trip_code": t.trip_code, "route": f"{t.source} → {t.destination}",
         "vehicle": t.vehicle.registration_number, "driver": t.driver.full_name}
        for t in db.execute(
            select(Trip).where(Trip.status == TripStatus.dispatched)
        ).scalars()
    ]

    fallback = (
        f"Fleet status: {kpis['available_vehicles']} of {kpis['active_vehicles']} vehicles "
        f"available ({kpis['fleet_utilization_pct']}% utilization), "
        f"{kpis['in_maintenance']} in the workshop. "
        f"{kpis['active_trips']} trips on the road, {kpis['pending_trips']} drafts waiting. "
        f"{len(expiring)} licence(s) expire within 30 days. "
        f"{len(open_jobs)} maintenance job(s) open. "
        + (
            "Worst ROI: "
            + ", ".join(f"{r['vehicle']} ({r['roi']})" for r in worst_roi)
            + "."
            if worst_roi
            else ""
        )
    ).strip()

    narrative, llm_used = (fallback, False)
    if use_llm:
        narrative, llm_used = _narrate(
            db,
            "You are a fleet operations chief writing the morning briefing. Be concrete, "
            "cite registration numbers/names/numbers, max 6 sentences, end with the single "
            "most important action for today.",
            f"KPIs: {kpis}\nExpiring licences: {expiring}\nOpen maintenance: {open_jobs}\n"
            f"Worst ROI vehicles: {worst_roi}\nTrips on the road: {active}",
            fallback,
        )
    return {
        "narrative": narrative,
        "llm_used": llm_used,
        "kpis": kpis,
        "expiring_licenses": expiring,
        "open_maintenance": open_jobs,
        "worst_roi": worst_roi,
        "active_trips": active,
    }


# ---------------------------------------------------------- maintenance risk

def maintenance_risk(db: Session, *, use_llm: bool = True) -> dict:
    """Rank non-retired vehicles by service risk (deterministic, explainable)."""
    vehicles = db.execute(
        select(Vehicle).where(Vehicle.status != VehicleStatus.retired)
    ).scalars().all()
    closed = db.execute(
        select(MaintenanceLog).where(MaintenanceLog.status == MaintenanceStatus.closed)
    ).scalars().all()
    last_service: dict = {}
    for m in closed:
        prev = last_service.get(m.vehicle_id)
        when = m.closed_at or m.opened_at
        if prev is None or when > prev:
            last_service[m.vehicle_id] = when

    now = datetime.now(UTC)
    ranked = []
    for v in vehicles:
        score = 0
        reasons: list[str] = []
        odo = float(v.odometer_km)
        serviced_at = last_service.get(v.id)
        if serviced_at is None:
            if odo > 10000:
                score += 50
                reasons.append(f"never serviced with {odo:,.0f} km on the clock")
            elif odo > 0:
                score += 15
                reasons.append("no service history")
        else:
            days = (now - serviced_at).days
            if days > 90:
                score += 40
                reasons.append(f"last serviced {days} days ago")
            elif days > 45:
                score += 20
                reasons.append(f"{days} days since last service")
        if odo > 150000:
            score += 30
            reasons.append(f"high-mileage vehicle ({odo:,.0f} km)")
        elif odo > 80000:
            score += 15
            reasons.append(f"{odo:,.0f} km total mileage")
        if v.status == VehicleStatus.in_shop:
            score = max(score - 40, 0)
            reasons.append("currently in the workshop")
        ranked.append(
            {
                "registration_number": v.registration_number,
                "name": v.name,
                "status": v.status.value,
                "odometer_km": odo,
                "risk_score": min(score, 100),
                "reasons": reasons or ["no risk indicators"],
            }
        )
    ranked.sort(key=lambda r: r["risk_score"], reverse=True)

    top = [r for r in ranked if r["risk_score"] >= 40][:5]
    top_lines = "; ".join(
        f"{r['registration_number']} ({r['risk_score']}: {r['reasons'][0]})" for r in top
    )
    fallback = (
        f"Highest service risk: {top_lines}."
        if top
        else "No vehicles currently show elevated maintenance risk."
    )
    narrative, llm_used = (fallback, False)
    if use_llm:
        narrative, llm_used = _narrate(
            db,
            "You are a fleet maintenance planner. Given risk-ranked vehicles, recommend "
            "which to book into the workshop this week and why. Max 4 sentences.",
            f"Ranked vehicles: {ranked[:8]}",
            fallback,
        )
    return {"narrative": narrative, "llm_used": llm_used, "vehicles": ranked}


# ---------------------------------------------------------- expense anomalies

def expense_anomalies(db: Session, *, use_llm: bool = True) -> dict:
    """Flag fuel-price outliers and duplicate same-day expenses (deterministic)."""
    anomalies: list[dict] = []

    fuel = db.execute(select(FuelLog)).scalars().all()
    prices = [float(f.cost) / float(f.liters) for f in fuel if float(f.liters) > 0]
    if len(prices) >= 4:
        # Median-based band: robust against the outlier inflating its own threshold.
        med = statistics.median(prices)
        for f in fuel:
            liters = float(f.liters)
            if liters <= 0:
                continue
            price = float(f.cost) / liters
            if price > med * 1.5 or price < med * 0.5:
                anomalies.append(
                    {
                        "kind": "fuel_price_outlier",
                        "vehicle": f.vehicle.registration_number,
                        "detail": f"₹{price:,.1f}/L vs fleet median ₹{med:,.1f}/L",
                        "amount": float(f.cost),
                        "date": f.filled_at.isoformat(),
                    }
                )

    from app.models.expense import Expense

    expenses = db.execute(select(Expense)).scalars().all()
    seen: dict = {}
    for e in expenses:
        key = (e.vehicle_id, e.type.value, Decimal(e.amount), e.incurred_at)
        if key in seen:
            anomalies.append(
                {
                    "kind": "possible_duplicate",
                    "vehicle": e.vehicle.registration_number,
                    "detail": (
                        f"duplicate {e.type.value} of ₹{float(e.amount):,.0f} "
                        "on the same day"
                    ),
                    "amount": float(e.amount),
                    "date": e.incurred_at.isoformat(),
                }
            )
        seen[key] = True
    amounts = sorted(float(e.amount) for e in expenses)
    if len(amounts) >= 5:
        p90 = amounts[int(len(amounts) * 0.9) - 1]
        for e in expenses:
            if float(e.amount) > p90 * 1.5:
                anomalies.append(
                    {
                        "kind": "unusually_large",
                        "vehicle": e.vehicle.registration_number,
                        "detail": f"{e.type.value} of ₹{float(e.amount):,.0f} far above the "
                                  f"90th percentile (₹{p90:,.0f})",
                        "amount": float(e.amount),
                        "date": e.incurred_at.isoformat(),
                    }
                )

    fallback = (
        f"{len(anomalies)} spending anomal{'y' if len(anomalies) == 1 else 'ies'} detected: "
        + "; ".join(f"{a['vehicle']} — {a['detail']}" for a in anomalies[:4])
        if anomalies
        else "No spending anomalies detected across fuel logs and expenses."
    )
    narrative, llm_used = (fallback, False)
    if use_llm and anomalies:
        narrative, llm_used = _narrate(
            db,
            "You are a fleet financial controller. Summarize these spending anomalies and "
            "what to verify with the drivers/vendors. Max 4 sentences.",
            f"Anomalies: {anomalies[:10]}",
            fallback,
        )
    return {"narrative": narrative, "llm_used": llm_used, "anomalies": anomalies}
