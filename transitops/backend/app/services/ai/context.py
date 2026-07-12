"""Assemble the 4-part chatbot system prompt (docs/06 §2)."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.db import queries
from app.models.user import User
from app.services.ai.knowledge import PROJECT_KNOWLEDGE
from app.services.ai.settings import get_settings_row


def permitted_tools(db: Session, role: str) -> list[str]:
    row = get_settings_row(db)
    return list(row.role_tool_permissions.get(role, []))


def build_system_prompt(db: Session, user: User) -> str:
    """(1) static knowledge + (2) live KPI snapshot + (3) requester identity +
    (4) admin system_prompt, appended last."""
    row = get_settings_row(db)
    role = user.role.value
    tools = list(row.role_tool_permissions.get(role, []))

    kpis = {
        **queries.get_vehicle_kpis(db),
        **queries.get_trip_kpis(db),
        **queries.get_driver_kpis(db),
    }
    live = (
        f"LIVE SNAPSHOT (today {date.today().isoformat()}): "
        f"active_vehicles={kpis['active_vehicles']}, available={kpis['available_vehicles']}, "
        f"in_shop={kpis['in_maintenance']}, utilization={kpis['fleet_utilization_pct']}%, "
        f"active_trips={kpis['active_trips']}, pending_trips={kpis['pending_trips']}, "
        f"drivers_on_duty={kpis['drivers_on_duty']}."
    )
    identity = (
        f"REQUESTER: {user.full_name}, role={role}. You may only call these tools: "
        f"{', '.join(tools) or '(none)'}. If asked for data outside your role's scope "
        f"(a driver or safety officer asking for costs, revenue, ROI or expenses), refuse "
        f"politely and name the role that can access it (Financial Analysts and Fleet Managers)."
    )

    parts = [PROJECT_KNOWLEDGE, live, identity]
    if row.system_prompt:
        parts.append(f"ADMIN INSTRUCTIONS: {row.system_prompt}")
    return "\n\n".join(parts)
