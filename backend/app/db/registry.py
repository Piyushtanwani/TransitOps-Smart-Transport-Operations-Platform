"""Central import point for every ORM model, so `Base.metadata` is complete.

Alembic autogenerate and `create_all` rely on all mapped classes being imported.
Models are added here as each DB task lands (DB-03..DB-05).
"""
from __future__ import annotations

from app.models import (  # noqa: F401  (users/vehicles/drivers/trips/maint/fuel/expense/ai/chat/audit)
    ai_settings,
    audit,
    chat,
    driver,
    expense,
    fuel_log,
    maintenance,
    trip,
    user,
    vehicle,
)
