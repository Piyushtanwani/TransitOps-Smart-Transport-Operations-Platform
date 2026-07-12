"""Dashboard response schemas (docs/03 §4 Dashboard). Keys must match the contract exactly."""
from __future__ import annotations

from pydantic import BaseModel


class Alerts(BaseModel):
    expiring_licenses: int


class KpisResponse(BaseModel):
    active_vehicles: int
    available_vehicles: int
    in_maintenance: int
    active_trips: int
    pending_trips: int
    drivers_on_duty: int
    fleet_utilization_pct: float
    alerts: Alerts


class TripsLast14dPoint(BaseModel):
    date: str
    completed: int
    dispatched: int


class CostBreakdownItem(BaseModel):
    vehicle: str
    fuel: float | None
    maintenance: float | None


class StatusDistributionItem(BaseModel):
    status: str
    count: int


class ChartsResponse(BaseModel):
    trips_last_14d: list[TripsLast14dPoint]
    cost_breakdown: list[CostBreakdownItem]
    status_distribution: list[StatusDistributionItem]
