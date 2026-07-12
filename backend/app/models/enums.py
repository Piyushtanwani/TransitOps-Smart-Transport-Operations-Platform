"""Domain enums mirroring `docs/02 §2` PostgreSQL ENUM types (values are lowercase strings)."""
from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum


class UserRole(str, Enum):
    fleet_manager = "fleet_manager"
    driver = "driver"
    safety_officer = "safety_officer"
    financial_analyst = "financial_analyst"


class VehicleType(str, Enum):
    truck = "truck"
    van = "van"
    mini_truck = "mini_truck"
    trailer = "trailer"


class VehicleStatus(str, Enum):
    available = "available"
    on_trip = "on_trip"
    in_shop = "in_shop"
    retired = "retired"


class DriverStatus(str, Enum):
    available = "available"
    on_trip = "on_trip"
    off_duty = "off_duty"
    suspended = "suspended"


class TripStatus(str, Enum):
    draft = "draft"
    dispatched = "dispatched"
    completed = "completed"
    cancelled = "cancelled"


class MaintenanceStatus(str, Enum):
    open = "open"
    closed = "closed"


class ExpenseType(str, Enum):
    toll = "toll"
    parking = "parking"
    fine = "fine"
    loading = "loading"
    other = "other"


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    tool = "tool"


def pg_enum(py_enum: type[Enum], name: str) -> SAEnum:
    """Build a SQLAlchemy ENUM whose PostgreSQL values are the member *values*.

    `values_callable` ensures PostgreSQL stores the lowercase strings
    (e.g. 'fleet_manager') rather than the Python member names.
    """
    return SAEnum(py_enum, name=name, values_callable=lambda e: [m.value for m in e])
