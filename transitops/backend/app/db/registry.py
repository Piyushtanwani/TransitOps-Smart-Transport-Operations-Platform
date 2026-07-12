"""Central import point for every ORM model, so `Base.metadata` is complete.

Alembic autogenerate and `create_all` rely on all mapped classes being imported.
Models are added here as each DB task lands (DB-03..DB-05).
"""
from __future__ import annotations

# DB-03: users, vehicles, drivers
# DB-04: trips, maintenance, fuel, expenses
# DB-05: ai_settings, chat, audit
