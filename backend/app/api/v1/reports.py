"""Report endpoints (docs/03 §4 Reports). Read: fleet_manager + financial_analyst only."""
from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.db.queries import get_vehicle_report_rows
from app.models.user import User
from app.schemas.report import VehicleReport

router = APIRouter(prefix="/reports", tags=["Reports"])
_reader = require_roles("fleet_manager", "financial_analyst")

_SUMMABLE_FIELDS = (
    "acquisition_cost",
    "total_distance_km",
    "total_liters",
    "fuel_cost",
    "maintenance_cost",
    "other_expenses",
    "operational_cost",
    "revenue",
)

_CSV_COLUMNS = (
    "id",
    "registration_number",
    "name",
    "type",
    "region",
    "acquisition_cost",
    "total_distance_km",
    "total_liters",
    "fuel_cost",
    "maintenance_cost",
    "other_expenses",
    "operational_cost",
    "revenue",
    "fuel_efficiency_km_l",
    "roi",
)


def _totals(rows: list[dict]) -> dict:
    return {field: sum(r[field] or 0 for r in rows) for field in _SUMMABLE_FIELDS}


@router.get("/vehicles", response_model=VehicleReport, summary="Vehicle analytics report")
def vehicle_report(
    db: Session = Depends(get_db),
    _: User = Depends(_reader),
) -> VehicleReport:
    rows = get_vehicle_report_rows(db)
    return VehicleReport(rows=rows, totals=_totals(rows))


@router.get("/vehicles.csv", summary="Vehicle analytics report (CSV export)")
def vehicle_report_csv(
    db: Session = Depends(get_db),
    _: User = Depends(_reader),
) -> StreamingResponse:
    rows = get_vehicle_report_rows(db)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow({col: row[col] for col in _CSV_COLUMNS})
    buffer.seek(0)

    filename = f"transitops_vehicle_report_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
