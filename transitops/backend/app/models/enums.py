"""Domain ENUM types — mirrors docs/02-DATABASE.md §2 exactly.

Each class is both a Python str-Enum and a PostgreSQL ENUM type.
SQLAlchemy columns use SAEnum(PyEnum, name="<pg_type_name>",
values_callable=...) so that PostgreSQL stores the lowercase string values,
not the Python member names.
"""
import enum


class UserRole(str, enum.Enum):
    """Maps to PostgreSQL ENUM user_role."""
    fleet_manager     = "fleet_manager"
    driver            = "driver"
    safety_officer    = "safety_officer"
    financial_analyst = "financial_analyst"


class VehicleType(str, enum.Enum):
    """Maps to PostgreSQL ENUM vehicle_type."""
    truck      = "truck"
    van        = "van"
    mini_truck = "mini_truck"
    trailer    = "trailer"


class VehicleStatus(str, enum.Enum):
    """Maps to PostgreSQL ENUM vehicle_status."""
    available = "available"
    on_trip   = "on_trip"
    in_shop   = "in_shop"
    retired   = "retired"


class DriverStatus(str, enum.Enum):
    """Maps to PostgreSQL ENUM driver_status."""
    available = "available"
    on_trip   = "on_trip"
    off_duty  = "off_duty"
    suspended = "suspended"


class TripStatus(str, enum.Enum):
    """Maps to PostgreSQL ENUM trip_status."""
    draft      = "draft"
    dispatched = "dispatched"
    completed  = "completed"
    cancelled  = "cancelled"


class MaintenanceStatus(str, enum.Enum):
    """Maps to PostgreSQL ENUM maintenance_status."""
    open   = "open"
    closed = "closed"


class ExpenseType(str, enum.Enum):
    """Maps to PostgreSQL ENUM expense_type."""
    toll    = "toll"
    parking = "parking"
    fine    = "fine"
    loading = "loading"
    other   = "other"


class ChatRole(str, enum.Enum):
    """Maps to PostgreSQL ENUM chat_role."""
    user      = "user"
    assistant = "assistant"
    tool      = "tool"
