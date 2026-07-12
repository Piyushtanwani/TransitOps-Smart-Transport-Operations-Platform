"""API v1 router aggregation. Sub-routers are mounted as each BE task lands."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, users, vehicles

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(vehicles.router)
