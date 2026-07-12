"""AI tool registry (docs/06 §4). Read-only executors; row caps; role-aware field stripping.

Each tool is MCP-shaped (name + JSON schema + executor) so BE-16 can expose the same
registry over MCP. Executors never mutate state.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import queries
from app.models.driver import Driver
from app.models.enums import DriverStatus, MaintenanceStatus, TripStatus, VehicleStatus, VehicleType
from app.models.maintenance import MaintenanceLog
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.ai.knowledge import PROJECT_KNOWLEDGE

_MAX = 50
_COST_ROLES = {"fleet_manager", "financial_analyst"}


def _cap(limit: Any) -> int:
    try:
        return max(1, min(int(limit), _MAX))
    except (TypeError, ValueError):
        return 20


def _enum(cls, value):
    try:
        return cls(value)
    except (ValueError, KeyError):
        return None


# --- executors ---

def _get_kpis(db: Session, user: User) -> dict:
    return {
        **queries.get_vehicle_kpis(db),
        **queries.get_trip_kpis(db),
        **queries.get_driver_kpis(db),
        "expiring_licenses": queries.get_expiring_license_count(db, 30),
    }


def _get_vehicles(db, user, status=None, type=None, region=None, q=None, limit=20):
    stmt = select(Vehicle)
    st = _enum(VehicleStatus, status) if status else None
    ty = _enum(VehicleType, type) if type else None
    if st:
        stmt = stmt.where(Vehicle.status == st)
    if ty:
        stmt = stmt.where(Vehicle.type == ty)
    if region:
        stmt = stmt.where(Vehicle.region == region)
    if q:
        stmt = stmt.where(Vehicle.registration_number.ilike(f"%{q}%"))
    show_cost = user.role.value in _COST_ROLES
    out = []
    for v in db.execute(stmt.limit(_cap(limit))).scalars():
        row = {
            "registration_number": v.registration_number,
            "name": v.name,
            "type": v.type.value,
            "max_load_capacity_kg": float(v.max_load_capacity_kg),
            "odometer_km": float(v.odometer_km),
            "region": v.region,
            "status": v.status.value,
        }
        if show_cost:  # strip acquisition_cost for driver / safety_officer
            row["acquisition_cost"] = float(v.acquisition_cost)
        out.append(row)
    return out


def _get_drivers(db, user, status=None, license_valid=None, q=None, limit=20):
    stmt = select(Driver)
    st = _enum(DriverStatus, status) if status else None
    if st:
        stmt = stmt.where(Driver.status == st)
    if license_valid is True:
        stmt = stmt.where(Driver.license_expiry >= date.today())
    elif license_valid is False:
        stmt = stmt.where(Driver.license_expiry < date.today())
    if q:
        stmt = stmt.where(Driver.full_name.ilike(f"%{q}%"))
    return [
        {
            "full_name": d.full_name,
            "license_number": d.license_number,
            "license_category": d.license_category,
            "license_expiry": d.license_expiry.isoformat(),
            "safety_score": float(d.safety_score),
            "status": d.status.value,
        }
        for d in db.execute(stmt.limit(_cap(limit))).scalars()
    ]


def _resolve_vehicle_id(db, vehicle_reg):
    if not vehicle_reg:
        return None
    return db.execute(
        select(Vehicle.id).where(Vehicle.registration_number == vehicle_reg)
    ).scalar_one_or_none()


def _get_trips(db, user, status=None, vehicle_reg=None, driver_name=None,
               date_from=None, date_to=None, limit=20):
    stmt = select(Trip)
    st = _enum(TripStatus, status) if status else None
    if st:
        stmt = stmt.where(Trip.status == st)
    vid = _resolve_vehicle_id(db, vehicle_reg)
    if vid:
        stmt = stmt.where(Trip.vehicle_id == vid)
    if driver_name:
        stmt = stmt.where(
            Trip.driver_id.in_(select(Driver.id).where(Driver.full_name.ilike(f"%{driver_name}%")))
        )
    stmt = stmt.order_by(Trip.created_at.desc())
    out = []
    for t in db.execute(stmt.limit(_cap(limit))).scalars():
        out.append({
            "trip_code": t.trip_code,
            "source": t.source,
            "destination": t.destination,
            "vehicle": t.vehicle.registration_number,
            "driver": t.driver.full_name,
            "cargo_weight_kg": float(t.cargo_weight_kg),
            "status": t.status.value,
            "dispatched_at": t.dispatched_at.isoformat() if t.dispatched_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        })
    return out


def _get_maintenance(db, user, status=None, vehicle_reg=None):
    stmt = select(MaintenanceLog)
    st = _enum(MaintenanceStatus, status) if status else None
    if st:
        stmt = stmt.where(MaintenanceLog.status == st)
    vid = _resolve_vehicle_id(db, vehicle_reg)
    if vid:
        stmt = stmt.where(MaintenanceLog.vehicle_id == vid)
    return [
        {
            "vehicle": m.vehicle.registration_number,
            "title": m.title,
            "cost": float(m.cost),
            "status": m.status.value,
            "opened_at": m.opened_at.isoformat(),
            "closed_at": m.closed_at.isoformat() if m.closed_at else None,
        }
        for m in db.execute(stmt.limit(_MAX)).scalars()
    ]


def _get_expiring_licenses(db, user, days=30):
    horizon = date.today() + timedelta(days=_cap_days(days))
    rows = db.execute(
        select(Driver)
        .where(Driver.license_expiry >= date.today(), Driver.license_expiry <= horizon)
        .order_by(Driver.license_expiry.asc())
        .limit(_MAX)
    ).scalars()
    return [
        {
            "full_name": d.full_name,
            "license_number": d.license_number,
            "license_expiry": d.license_expiry.isoformat(),
        }
        for d in rows
    ]


def _cap_days(days: Any) -> int:
    try:
        return max(1, min(int(days), 365))
    except (TypeError, ValueError):
        return 30


def _get_vehicle_costs(db, user, vehicle_reg=None):
    rows = queries.get_vehicle_report_rows(db)
    if vehicle_reg:
        rows = [r for r in rows if r["registration_number"] == vehicle_reg]
    return [
        {
            "registration_number": r["registration_number"],
            "fuel_cost": r["fuel_cost"],
            "maintenance_cost": r["maintenance_cost"],
            "operational_cost": r["operational_cost"],
            "revenue": r["revenue"],
            "roi": r["roi"],
        }
        for r in rows[:_MAX]
    ]


def _get_fuel_efficiency(db, user, vehicle_reg=None):
    rows = queries.get_vehicle_report_rows(db)
    if vehicle_reg:
        rows = [r for r in rows if r["registration_number"] == vehicle_reg]
    return [
        {
            "registration_number": r["registration_number"],
            "fuel_efficiency_km_l": r["fuel_efficiency_km_l"],
        }
        for r in rows[:_MAX]
    ]


def _explain_business_rule(db, user, topic=""):
    block = PROJECT_KNOWLEDGE.split("BUSINESS RULES")[1].split("METRIC DEFINITIONS")[0]
    lines = [ln.strip() for ln in block.replace("\n", " ").split("BR-") if ln.strip()]
    topic_l = (topic or "").lower()
    matches = [f"BR-{ln}" for ln in lines if topic_l in ln.lower()] if topic_l else []
    return {"topic": topic, "matches": matches or [f"BR-{ln}" for ln in lines]}


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    allowed_roles: set[str]
    executor: Callable[..., Any]
    _f: dict = field(default_factory=dict)

    def openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def _params(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or []}


_ALL = {"fleet_manager", "driver", "safety_officer", "financial_analyst"}

TOOLS: dict[str, Tool] = {
    "get_kpis": Tool(
        "get_kpis", "Current dashboard KPI snapshot.", _params({}), set(_ALL), _get_kpis
    ),
    "get_vehicles": Tool(
        "get_vehicles", "List vehicles with optional filters.",
        _params({
            "status": {"type": "string"}, "type": {"type": "string"},
            "region": {"type": "string"}, "q": {"type": "string"},
            "limit": {"type": "integer"},
        }), set(_ALL), _get_vehicles,
    ),
    "get_drivers": Tool(
        "get_drivers", "List drivers with optional filters.",
        _params({
            "status": {"type": "string"}, "license_valid": {"type": "boolean"},
            "q": {"type": "string"}, "limit": {"type": "integer"},
        }), set(_ALL), _get_drivers,
    ),
    "get_trips": Tool(
        "get_trips", "List trips with optional filters.",
        _params({
            "status": {"type": "string"}, "vehicle_reg": {"type": "string"},
            "driver_name": {"type": "string"}, "date_from": {"type": "string"},
            "date_to": {"type": "string"}, "limit": {"type": "integer"},
        }), set(_ALL), _get_trips,
    ),
    "get_maintenance": Tool(
        "get_maintenance", "List maintenance jobs and costs.",
        _params({"status": {"type": "string"}, "vehicle_reg": {"type": "string"}}),
        set(_ALL), _get_maintenance,
    ),
    "get_expiring_licenses": Tool(
        "get_expiring_licenses", "Drivers whose licence expires within N days.",
        _params({"days": {"type": "integer"}}),
        {"fleet_manager", "safety_officer"}, _get_expiring_licenses,
    ),
    "get_vehicle_costs": Tool(
        "get_vehicle_costs", "Per-vehicle fuel/maintenance/operational cost, revenue and ROI.",
        _params({"vehicle_reg": {"type": "string"}}),
        {"fleet_manager", "financial_analyst"}, _get_vehicle_costs,
    ),
    "get_fuel_efficiency": Tool(
        "get_fuel_efficiency", "Fuel efficiency (km/L) per vehicle.",
        _params({"vehicle_reg": {"type": "string"}}),
        {"fleet_manager", "driver", "financial_analyst"}, _get_fuel_efficiency,
    ),
    "explain_business_rule": Tool(
        "explain_business_rule", "Explain a business rule (BR-1..BR-10) by topic.",
        _params({"topic": {"type": "string"}}), set(_ALL), _explain_business_rule,
    ),
}
