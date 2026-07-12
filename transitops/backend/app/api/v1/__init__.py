"""API v1 router aggregation. Sub-routers are mounted as each BE task lands."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    ai_advisor,
    auth,
    dashboard,
    drivers,
    expenses,
    fuel_logs,
    maintenance,
    reports,
    trips,
    users,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
api_router.include_router(trips.router)
api_router.include_router(maintenance.router)
api_router.include_router(fuel_logs.router)
api_router.include_router(expenses.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(ai.router)
api_router.include_router(ai_advisor.router)
