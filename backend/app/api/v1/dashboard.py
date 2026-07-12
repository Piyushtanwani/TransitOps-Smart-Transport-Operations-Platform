"""Dashboard endpoints (docs/03 §4 Dashboard). Read: all four roles."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.enums import VehicleStatus, VehicleType
from app.models.user import User
from app.schemas.dashboard import ChartsResponse, KpisResponse
from app.services import report_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=KpisResponse, summary="Dashboard KPIs")
def get_kpis(
    type: VehicleType | None = Query(None),
    region: str | None = Query(None),
    status: VehicleStatus | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KpisResponse:
    data = report_service.get_dashboard_kpis(
        db,
        type_=type.value if type else None,
        region=region,
        status=status.value if status else None,
    )
    return KpisResponse(**data)


@router.get("/charts", response_model=ChartsResponse, summary="Dashboard charts")
def get_charts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ChartsResponse:
    data = report_service.get_dashboard_charts(db)
    return ChartsResponse(**data)
