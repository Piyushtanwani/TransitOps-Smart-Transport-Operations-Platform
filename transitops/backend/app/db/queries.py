"""Aggregate KPI + report SQL (verbatim from docs/02 §5), parameterized via text().

Consumed by BE-10 (dashboard) and BE-11 (reports). Definitions per docs/01 §5.
Do not rename these functions without a TASKS-OVERVIEW Change Log entry.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _num(x: Any) -> float | None:
    return float(x) if x is not None else None


def get_vehicle_kpis(
    db: Session,
    type_: str | None = None,
    region: str | None = None,
    status: str | None = None,
) -> dict:
    """Active/available/in-shop counts + fleet utilization %% (docs/01 §5).

    Optional type/region/status narrow the vehicle set (enum columns cast to text
    so string params compare cleanly).
    """
    where, params = [], {}
    if type_:
        where.append("type::text = :type")
        params["type"] = type_
    if region:
        where.append("region = :region")
        params["region"] = region
    if status:
        where.append("status::text = :status")
        params["status"] = status
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    row = db.execute(
        text(
            f"""
            SELECT
              COUNT(*) FILTER (WHERE status <> 'retired')   AS active_vehicles,
              COUNT(*) FILTER (WHERE status = 'available')  AS available_vehicles,
              COUNT(*) FILTER (WHERE status = 'in_shop')    AS in_maintenance,
              ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'on_trip')
                    / NULLIF(COUNT(*) FILTER (WHERE status <> 'retired'), 0), 1)
                    AS fleet_utilization_pct
            FROM vehicles {clause}
            """
        ),
        params,
    ).mappings().one()
    return {
        "active_vehicles": int(row["active_vehicles"] or 0),
        "available_vehicles": int(row["available_vehicles"] or 0),
        "in_maintenance": int(row["in_maintenance"] or 0),
        "fleet_utilization_pct": float(row["fleet_utilization_pct"] or 0.0),
    }


def get_trip_kpis(db: Session) -> dict:
    """Active trips = dispatched; pending trips = draft (docs/01 §5)."""
    row = db.execute(
        text(
            """
            SELECT COUNT(*) FILTER (WHERE status = 'dispatched') AS active_trips,
                   COUNT(*) FILTER (WHERE status = 'draft')      AS pending_trips
            FROM trips
            """
        )
    ).mappings().one()
    return {
        "active_trips": int(row["active_trips"] or 0),
        "pending_trips": int(row["pending_trips"] or 0),
    }


def get_driver_kpis(db: Session) -> dict:
    """Drivers on duty = available + on_trip (docs/01 §5)."""
    row = db.execute(
        text(
            """
            SELECT COUNT(*) FILTER (WHERE status IN ('available', 'on_trip'))
                   AS drivers_on_duty
            FROM drivers
            """
        )
    ).mappings().one()
    return {"drivers_on_duty": int(row["drivers_on_duty"] or 0)}


def get_expiring_license_count(db: Session, days: int = 30) -> int:
    """Drivers whose licence expires within `days` (dashboard alert)."""
    return int(
        db.execute(
            text(
                "SELECT COUNT(*) FROM drivers "
                "WHERE license_expiry <= CURRENT_DATE + (:days || ' days')::interval "
                "AND license_expiry >= CURRENT_DATE"
            ),
            {"days": days},
        ).scalar_one()
    )


def get_vehicle_report_rows(db: Session) -> list[dict]:
    """Per-vehicle fuel efficiency, operational cost, ROI (verbatim docs/02 §5)."""
    rows = db.execute(
        text(
            """
            SELECT v.id, v.registration_number, v.name, v.type, v.region, v.acquisition_cost,
                   COALESCE(t.total_distance,0) AS total_distance_km,
                   COALESCE(f.total_liters,0)   AS total_liters,
                   COALESCE(f.total_fuel_cost,0) AS fuel_cost,
                   COALESCE(m.total_maint_cost,0) AS maintenance_cost,
                   COALESCE(e.total_other,0)    AS other_expenses,
                   COALESCE(f.total_fuel_cost,0)+COALESCE(m.total_maint_cost,0) AS operational_cost,
                   COALESCE(t.total_revenue,0)  AS revenue,
                   CASE WHEN COALESCE(f.total_liters,0) > 0
                        THEN ROUND(COALESCE(t.total_distance,0)/f.total_liters, 2) END
                        AS fuel_efficiency_km_l,
                   ROUND((COALESCE(t.total_revenue,0)
                         - (COALESCE(f.total_fuel_cost,0)+COALESCE(m.total_maint_cost,0)))
                         / v.acquisition_cost, 4) AS roi
            FROM vehicles v
            LEFT JOIN (SELECT vehicle_id, SUM(end_odometer-start_odometer) AS total_distance,
                              SUM(revenue) AS total_revenue
                       FROM trips WHERE status='completed' GROUP BY vehicle_id) t ON t.vehicle_id=v.id
            LEFT JOIN (SELECT vehicle_id, SUM(liters) total_liters, SUM(cost) total_fuel_cost
                       FROM fuel_logs GROUP BY vehicle_id) f ON f.vehicle_id=v.id
            LEFT JOIN (SELECT vehicle_id, SUM(cost) total_maint_cost
                       FROM maintenance_logs GROUP BY vehicle_id) m ON m.vehicle_id=v.id
            LEFT JOIN (SELECT vehicle_id, SUM(amount) total_other
                       FROM expenses GROUP BY vehicle_id) e ON e.vehicle_id=v.id
            ORDER BY v.registration_number
            """
        )
    ).mappings().all()

    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": str(r["id"]),
                "registration_number": r["registration_number"],
                "name": r["name"],
                "type": r["type"],
                "region": r["region"],
                "acquisition_cost": _num(r["acquisition_cost"]),
                "total_distance_km": _num(r["total_distance_km"]),
                "total_liters": _num(r["total_liters"]),
                "fuel_cost": _num(r["fuel_cost"]),
                "maintenance_cost": _num(r["maintenance_cost"]),
                "other_expenses": _num(r["other_expenses"]),
                "operational_cost": _num(r["operational_cost"]),
                "revenue": _num(r["revenue"]),
                "fuel_efficiency_km_l": _num(r["fuel_efficiency_km_l"]),
                "roi": _num(r["roi"]),
            }
        )
    return out


def get_trips_last_14_days(db: Session) -> list[dict]:
    """14-day series of completed vs dispatched trip counts (dashboard chart)."""
    rows = db.execute(
        text(
            """
            SELECT d::date AS date,
                   COALESCE(c.cnt,0) AS completed,
                   COALESCE(x.cnt,0) AS dispatched
            FROM generate_series(CURRENT_DATE - INTERVAL '13 days', CURRENT_DATE,
                                 INTERVAL '1 day') d
            LEFT JOIN (SELECT completed_at::date dt, COUNT(*) cnt FROM trips
                       WHERE status='completed'
                         AND completed_at >= CURRENT_DATE - INTERVAL '13 days'
                       GROUP BY 1) c ON c.dt = d::date
            LEFT JOIN (SELECT dispatched_at::date dt, COUNT(*) cnt FROM trips
                       WHERE dispatched_at >= CURRENT_DATE - INTERVAL '13 days'
                       GROUP BY 1) x ON x.dt = d::date
            ORDER BY d
            """
        )
    ).mappings().all()
    return [
        {"date": r["date"].isoformat(), "completed": int(r["completed"]), "dispatched": int(r["dispatched"])}
        for r in rows
    ]


def get_cost_breakdown_top8(db: Session) -> list[dict]:
    """Top-8 vehicles by fuel + maintenance spend (dashboard chart)."""
    rows = db.execute(
        text(
            """
            SELECT v.registration_number AS vehicle,
                   COALESCE(f.fuel,0) AS fuel,
                   COALESCE(m.maint,0) AS maintenance
            FROM vehicles v
            LEFT JOIN (SELECT vehicle_id, SUM(cost) fuel FROM fuel_logs GROUP BY 1) f
                   ON f.vehicle_id=v.id
            LEFT JOIN (SELECT vehicle_id, SUM(cost) maint FROM maintenance_logs GROUP BY 1) m
                   ON m.vehicle_id=v.id
            ORDER BY (COALESCE(f.fuel,0)+COALESCE(m.maint,0)) DESC
            LIMIT 8
            """
        )
    ).mappings().all()
    return [
        {"vehicle": r["vehicle"], "fuel": _num(r["fuel"]), "maintenance": _num(r["maintenance"])}
        for r in rows
    ]


def get_status_distribution(db: Session) -> list[dict]:
    """Vehicle status distribution (dashboard chart)."""
    rows = db.execute(
        text("SELECT status::text AS status, COUNT(*) AS count FROM vehicles GROUP BY status ORDER BY status")
    ).mappings().all()
    return [{"status": r["status"], "count": int(r["count"])} for r in rows]
