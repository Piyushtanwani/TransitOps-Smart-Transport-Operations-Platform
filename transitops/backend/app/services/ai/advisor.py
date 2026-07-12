"""AI Trip Advisor — deterministic risk checks + optional LLM summary (docs/06 §6, BE-15).

Step 1 reuses the trip-service guards (BR-2/3/4/5) as read-only checks (no mutation,
no locking) to produce `hard_failures`, then layers soft `risk_factors`. Step 2 derives
the verdict from those two lists. Step 3 asks the LLM for a 3-sentence summary when AI
is enabled and reachable, falling back to a deterministic template otherwise so the
advisor always responds — even with `OPENROUTER_API_KEY` unset.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DomainError, NotFoundError
from app.models.driver import Driver
from app.models.enums import MaintenanceStatus
from app.models.maintenance import MaintenanceLog
from app.models.vehicle import Vehicle
from app.services.ai.client import OpenRouterError, call_openrouter
from app.services.ai.settings import ensure_ai_enabled
from app.services.trip_service import (
    _assert_capacity,
    _assert_driver_assignable,
    _assert_vehicle_dispatchable,
)

_CAPACITY_UTIL_PCT_THRESHOLD = Decimal("90")
_SAFETY_SCORE_THRESHOLD = Decimal("60")
_LICENSE_EXPIRY_WINDOW_DAYS = 30
_MAINTENANCE_ODOMETER_KM_THRESHOLD = Decimal("10000")
_LONG_HAUL_DISTANCE_KM = Decimal("500")
_LONG_HAUL_SAFETY_SCORE = Decimal("70")


def _num(d: Decimal) -> str:
    return f"{float(d):g}"


def _load_vehicle_and_driver(
    db: Session, vehicle_id: uuid.UUID, driver_id: uuid.UUID
) -> tuple[Vehicle, Driver]:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise NotFoundError("vehicle")
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise NotFoundError("driver")
    return vehicle, driver


def _hard_failures(vehicle: Vehicle, driver: Driver, cargo_weight_kg: Decimal) -> list[str]:
    """BR-2/3/4/5 — reuse the trip-service guards read-only (no locking, no mutation)."""
    failures: list[str] = []
    for guard, args in (
        (_assert_vehicle_dispatchable, (vehicle,)),
        (_assert_driver_assignable, (driver,)),
        (_assert_capacity, (vehicle, cargo_weight_kg)),
    ):
        try:
            guard(*args)
        except DomainError as exc:
            failures.append(exc.message)
    return failures


def _has_closed_maintenance(db: Session, vehicle_id: uuid.UUID) -> bool:
    row = db.execute(
        select(MaintenanceLog.id)
        .where(
            MaintenanceLog.vehicle_id == vehicle_id,
            MaintenanceLog.status == MaintenanceStatus.closed,
        )
        .limit(1)
    ).first()
    return row is not None


def _risk_factors(
    db: Session,
    vehicle: Vehicle,
    driver: Driver,
    cargo_weight_kg: Decimal,
    planned_distance_km: Decimal,
) -> list[str]:
    factors: list[str] = []

    utilization = (cargo_weight_kg / vehicle.max_load_capacity_kg) * Decimal("100")
    if utilization > _CAPACITY_UTIL_PCT_THRESHOLD:
        factors.append(f"High capacity utilization ({utilization:.0f}%)")

    if driver.safety_score < _SAFETY_SCORE_THRESHOLD:
        factors.append(f"Low driver safety score ({_num(driver.safety_score)})")

    today = date.today()
    days_to_expiry = (driver.license_expiry - today).days
    if 0 <= days_to_expiry <= _LICENSE_EXPIRY_WINDOW_DAYS:
        factors.append(f"Licence expires in {days_to_expiry} days")

    if not _has_closed_maintenance(db, vehicle.id) and (
        vehicle.odometer_km > _MAINTENANCE_ODOMETER_KM_THRESHOLD
    ):
        km = _num(vehicle.odometer_km)
        factors.append(f"Overdue for maintenance ({km} km since last service)")

    if (
        planned_distance_km > _LONG_HAUL_DISTANCE_KM
        and driver.safety_score < _LONG_HAUL_SAFETY_SCORE
    ):
        factors.append(f"Long haul ({_num(planned_distance_km)} km) with a lower-scored driver")

    return factors


def _verdict(hard_failures: list[str], risk_factors: list[str]) -> str:
    if hard_failures:
        return "block"
    if risk_factors:
        return "caution"
    return "go"


def _template_summary(verdict: str, hard_failures: list[str], risk_factors: list[str]) -> str:
    """Deterministic fallback summary used when the LLM is disabled or unreachable."""
    sentences = [f"Verdict: {verdict}."]
    if hard_failures:
        sentences.append(
            f"{len(hard_failures)} hard blocker(s) prevent dispatch: {'; '.join(hard_failures)}."
        )
    if risk_factors:
        sentences.append(
            f"{len(risk_factors)} risk(s) flagged for review: {'; '.join(risk_factors)}."
        )
    if not hard_failures and not risk_factors:
        sentences.append(
            "No hard blockers or risk factors were found; the trip looks safe to dispatch."
        )
    return " ".join(sentences)


def _llm_summary(
    db: Session,
    vehicle: Vehicle,
    driver: Driver,
    verdict: str,
    hard_failures: list[str],
    risk_factors: list[str],
) -> str:
    """Raises DomainError (AI disabled, 503) or OpenRouterError on any failure."""
    settings_row = ensure_ai_enabled(db)
    prompt = (
        "You are a fleet dispatch advisor. Based on the structured trip-risk findings "
        "below, write a concise 3-sentence dispatch recommendation for a fleet manager.\n\n"
        f"Vehicle: {vehicle.registration_number} ({vehicle.name})\n"
        f"Driver: {driver.full_name}\n"
        f"Verdict: {verdict}\n"
        f"Hard failures: {hard_failures or 'none'}\n"
        f"Risk factors: {risk_factors or 'none'}\n"
    )
    messages = [
        {"role": "system", "content": "You are a concise, operational fleet dispatch advisor."},
        {"role": "user", "content": prompt},
    ]
    from app.services.ai.settings import resolve_api_key

    result = call_openrouter(
        messages,
        model=settings_row.model,
        temperature=float(settings_row.temperature),
        max_tokens=settings_row.max_tokens,
        api_key=resolve_api_key(settings_row),
    )
    return result["choices"][0]["message"]["content"].strip()


def evaluate(
    db: Session,
    vehicle_id: uuid.UUID,
    driver_id: uuid.UUID,
    cargo_weight_kg: Decimal,
    planned_distance_km: Decimal,
    *,
    use_llm: bool = True,
) -> dict:
    """Read-only trip risk evaluation — never mutates the vehicle, driver, or trip state."""
    vehicle, driver = _load_vehicle_and_driver(db, vehicle_id, driver_id)

    hard_failures = _hard_failures(vehicle, driver, cargo_weight_kg)
    risk_factors = _risk_factors(db, vehicle, driver, cargo_weight_kg, planned_distance_km)
    verdict = _verdict(hard_failures, risk_factors)

    summary: str | None = None
    if use_llm:
        try:
            summary = _llm_summary(db, vehicle, driver, verdict, hard_failures, risk_factors)
        except (DomainError, OpenRouterError):
            summary = None

    if summary is None:
        summary = _template_summary(verdict, hard_failures, risk_factors)

    return {
        "verdict": verdict,
        "hard_failures": hard_failures,
        "risk_factors": risk_factors,
        "summary": summary,
    }
