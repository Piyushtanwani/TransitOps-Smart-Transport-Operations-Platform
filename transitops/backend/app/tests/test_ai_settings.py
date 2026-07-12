"""BE-13 tests: AI settings RBAC/redaction + AI_DISABLED (503) graceful path."""
from __future__ import annotations

import pytest

from app.core.errors import DomainError
from app.services.ai.settings import ensure_ai_enabled, get_settings_row
from app.tests.factories import auth_headers

API = "/api/v1"


def test_ai_settings_full_for_fm(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    r = client.get(f"{API}/ai/settings", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "temperature" in body and "system_prompt" in body
    assert "role_tool_permissions" in body


def test_ai_settings_redacted_for_non_fm(client, db) -> None:
    for role in ("driver", "safety_officer", "financial_analyst"):
        headers = auth_headers(client, db, role)
        r = client.get(f"{API}/ai/settings", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert set(body.keys()) == {"chatbot_enabled", "model"}


def test_ai_settings_put_is_fm_only(client, db) -> None:
    for role in ("driver", "safety_officer", "financial_analyst"):
        headers = auth_headers(client, db, role)
        r = client.put(f"{API}/ai/settings", json={"model": "x/y"}, headers=headers)
        assert r.status_code == 403


def test_ai_settings_put_updates_and_validates(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    ok = client.put(
        f"{API}/ai/settings",
        json={"temperature": 0.5, "model": "openai/gpt-4o-mini", "chatbot_enabled": True},
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["model"] == "openai/gpt-4o-mini"
    assert float(ok.json()["temperature"]) == 0.5
    # out-of-range temperature rejected
    bad = client.put(f"{API}/ai/settings", json={"temperature": 5}, headers=headers)
    assert bad.status_code == 422


def test_ai_disabled_returns_503(client, db) -> None:
    # With OPENROUTER_API_KEY unset (dev default) OR chatbot switched off,
    # ensure_ai_enabled raises AI_DISABLED (503).
    row = get_settings_row(db)
    row.chatbot_enabled = False
    db.commit()
    with pytest.raises(DomainError) as exc:
        ensure_ai_enabled(db)
    assert exc.value.code == "AI_DISABLED"
    assert exc.value.status_code == 503
