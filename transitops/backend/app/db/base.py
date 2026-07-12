"""Declarative base + eager import of every model module.

Alembic autogenerate depends on this file: all model modules must be
imported here so that ``Base.metadata`` contains every table before
``alembic revision --autogenerate`` runs.

Models import Base from app.db.base_class to avoid circular imports.
"""
from app.db.base_class import Base  # noqa: F401 — re-exported

# --- Import every model module so metadata is fully populated ---
# Order does not matter for metadata; FK references resolve by name.
from app.models import enums  # noqa: F401

from app.models.user import User  # noqa: F401
from app.models.vehicle import Vehicle  # noqa: F401
from app.models.driver import Driver  # noqa: F401
from app.models.trip import Trip  # noqa: F401
from app.models.maintenance import MaintenanceLog  # noqa: F401
from app.models.fuel_log import FuelLog  # noqa: F401
from app.models.expense import Expense  # noqa: F401
from app.models.ai_settings import AISettings  # noqa: F401
from app.models.chat import ChatSession, ChatMessage  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
