"""AI insights endpoints — briefing, maintenance risk, expense anomalies.

Deterministic cores always respond; LLM narratives activate when OpenRouter is
configured (DB key from AI Settings, or the env var).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.user import User
from app.services.ai import insights

router = APIRouter(prefix="/ai/insights", tags=["AI"])


@router.get("/briefing", summary="AI daily ops briefing (FM/FA)")
def briefing(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("fleet_manager", "financial_analyst")),
) -> dict:
    return insights.daily_briefing(db)


@router.get("/maintenance-risk", summary="AI maintenance risk ranking (FM/SO)")
def maintenance_risk(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("fleet_manager", "safety_officer")),
) -> dict:
    return insights.maintenance_risk(db)


@router.get("/expense-anomalies", summary="AI expense anomaly detection (FM/FA)")
def expense_anomalies(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("fleet_manager", "financial_analyst")),
) -> dict:
    return insights.expense_anomalies(db)
