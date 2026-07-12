"""Report schemas (docs/03 §4 Reports). Mirrors app.db.queries.get_vehicle_report_rows."""
from __future__ import annotations

from pydantic import BaseModel


class VehicleReportRow(BaseModel):
    id: str
    registration_number: str
    name: str
    type: str
    region: str
    acquisition_cost: float | None
    total_distance_km: float | None
    total_liters: float | None
    fuel_cost: float | None
    maintenance_cost: float | None
    other_expenses: float | None
    operational_cost: float | None
    revenue: float | None
    fuel_efficiency_km_l: float | None
    roi: float | None


class VehicleReport(BaseModel):
    rows: list[VehicleReportRow]
    totals: dict
