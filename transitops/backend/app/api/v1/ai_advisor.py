"""AI Trip Advisor endpoint (docs/06 §6, BE-15). Read-only — never mutates state."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.user import User
from app.schemas.ai import TripAdvisorRequest, TripAdvisorResponse
from app.services.ai.advisor import evaluate

router = APIRouter(prefix="/ai", tags=["AI"])
_advisor_roles = require_roles("fleet_manager", "driver")


@router.post(
    "/trip-advisor",
    response_model=TripAdvisorResponse,
    summary="AI trip risk advisor (FM, driver)",
)
def trip_advisor(
    body: TripAdvisorRequest,
    db: Session = Depends(get_db),
    _: User = Depends(_advisor_roles),
) -> TripAdvisorResponse:
    result = evaluate(
        db,
        body.vehicle_id,
        body.driver_id,
        body.cargo_weight_kg,
        body.planned_distance_km,
    )
    return TripAdvisorResponse(**result)
