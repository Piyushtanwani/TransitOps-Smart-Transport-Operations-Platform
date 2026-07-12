"""Dashboard KPI/chart assembly (BE-10). Thin wrappers over app.db.queries.

KPI + chart definitions per docs/01 §5.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import queries


def get_dashboard_kpis(
    db: Session,
    type_: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> dict:
    """Combine vehicle/trip/driver KPIs + the expiring-license alert (docs/01 §5).

    `type_`/`region`/`status` narrow only the vehicle-derived KPIs; trip and
    driver KPIs are always computed globally.
    """
    vehicle_kpis = queries.get_vehicle_kpis(db, type_=type_, region=region, status=status)
    trip_kpis = queries.get_trip_kpis(db)
    driver_kpis = queries.get_driver_kpis(db)
    expiring_licenses = queries.get_expiring_license_count(db, days=30)

    return {
        **vehicle_kpis,
        **trip_kpis,
        **driver_kpis,
        "alerts": {"expiring_licenses": expiring_licenses},
    }


def get_dashboard_charts(db: Session) -> dict:
    """Assemble the three dashboard chart series (docs/01 §5)."""
    return {
        "trips_last_14d": queries.get_trips_last_14_days(db),
        "cost_breakdown": queries.get_cost_breakdown_top8(db),
        "status_distribution": queries.get_status_distribution(db),
    }
