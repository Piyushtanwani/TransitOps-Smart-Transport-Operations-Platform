"""BE-14 tests: tool RBAC, chat persistence, disabled path, session ownership.

OpenRouter is mocked (no network) by monkeypatching `call_openrouter`.
"""
from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.models.chat import ChatMessage
from app.models.enums import VehicleStatus
from app.services.ai.defaults import DEFAULT_ROLE_TOOL_PERMISSIONS
from app.services.ai.tools import TOOLS
from app.tests.factories import auth_headers, make_vehicle

API = "/api/v1"


def _enable_ai(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "OPENROUTER_API_KEY", "test-key")


def _script(*responses):
    """Return a fake call_openrouter yielding the given messages in order."""
    calls = iter(responses)

    def _fake(messages, **kwargs):
        return {"choices": [{"message": next(calls)}]}

    return _fake


def test_ai_tools_registry_and_driver_forbidden_costs() -> None:
    # get_vehicle_costs exists as a tool but is NOT in the driver's default allowlist.
    assert "get_vehicle_costs" in TOOLS
    assert "get_vehicle_costs" not in DEFAULT_ROLE_TOOL_PERMISSIONS["driver"]
    assert "get_vehicle_costs" in DEFAULT_ROLE_TOOL_PERMISSIONS["financial_analyst"]
    # all 9 tools present
    assert len(TOOLS) == 9


def test_ai_chat_disabled_returns_503(client, db) -> None:
    # Default dev env has no OPENROUTER_API_KEY → chat is unavailable.
    headers = auth_headers(client, db, "driver")
    r = client.post(f"{API}/ai/chat", json={"message": "hi"}, headers=headers)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "AI_DISABLED"


def test_ai_chat_tool_roundtrip_persists(client, db, monkeypatch) -> None:
    _enable_ai(monkeypatch)
    make_vehicle(db, status=VehicleStatus.available)
    fake = _script(
        {  # turn 1: model asks to call get_vehicles
            "content": None,
            "tool_calls": [
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "get_vehicles", "arguments": '{"status": "available"}'},
                }
            ],
        },
        {"content": "You have available vehicles ready to dispatch."},  # turn 2: final answer
    )
    monkeypatch.setattr("app.services.ai.chat.call_openrouter", fake)

    headers = auth_headers(client, db, "driver")
    r = client.post(
        f"{API}/ai/chat", json={"message": "Which vehicles can I dispatch?"}, headers=headers
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == "You have available vehicles ready to dispatch."
    assert body["tool_calls"][0]["tool"] == "get_vehicles"

    sid = uuid.UUID(body["session_id"])
    rows = db.query(ChatMessage).filter(ChatMessage.session_id == sid).all()
    assert len(rows) == 2  # user + assistant persisted
    assistant = [m for m in rows if m.role.value == "assistant"][0]
    assert assistant.tool_calls  # tool-call transparency persisted


def test_ai_chat_forbidden_tool_is_handled(client, db, monkeypatch) -> None:
    _enable_ai(monkeypatch)
    fake = _script(
        {  # driver's model tries a forbidden financial tool
            "content": None,
            "tool_calls": [
                {"id": "c1", "type": "function",
                 "function": {"name": "get_vehicle_costs", "arguments": "{}"}}
            ],
        },
        {"content": "Sorry, cost data is only available to Finance and Fleet Managers."},
    )
    monkeypatch.setattr("app.services.ai.chat.call_openrouter", fake)
    headers = auth_headers(client, db, "driver")
    r = client.post(f"{API}/ai/chat", json={"message": "What is the ROI?"}, headers=headers)
    assert r.status_code == 200  # handled gracefully, never 500
    assert "Finance" in r.json()["reply"]


def test_ai_chat_sessions_owner_only(client, db) -> None:
    owner = auth_headers(client, db, "driver")
    created = client.post(f"{API}/ai/sessions", headers=owner)
    assert created.status_code == 201
    sid = created.json()["id"]
    # a different user cannot read someone else's session
    other = auth_headers(client, db, "safety_officer")
    r = client.get(f"{API}/ai/sessions/{sid}/messages", headers=other)
    assert r.status_code == 404
    # owner can
    assert client.get(f"{API}/ai/sessions/{sid}/messages", headers=owner).status_code == 200
