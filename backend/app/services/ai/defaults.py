"""Default AI configuration — role→tool permission matrix (docs/06 §4)."""
from __future__ import annotations

DEFAULT_ROLE_TOOL_PERMISSIONS: dict[str, list[str]] = {
    "fleet_manager": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_expiring_licenses", "get_vehicle_costs", "get_fuel_efficiency",
        "explain_business_rule",
    ],
    "driver": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_fuel_efficiency", "explain_business_rule",
    ],
    "safety_officer": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_expiring_licenses", "explain_business_rule",
    ],
    "financial_analyst": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_vehicle_costs", "get_fuel_efficiency", "explain_business_rule",
    ],
}

DEFAULT_SYSTEM_PROMPT = (
    "Be concise, professional and operational. Cite concrete numbers and identifiers "
    "from tool results. Never expose data a user's role may not access."
)
