"""BE-02 unit tests: password hashing, JWT lifecycle, error-envelope shape."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from freezegun import freeze_time
from pydantic import BaseModel

from app.core.errors import DomainError, NotFoundError, register_exception_handlers
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole


class _CargoBody(BaseModel):
    # Module-level so `from __future__ import annotations` string hints resolve.
    cargo_weight_kg: float


def _fake_user(role: UserRole = UserRole.fleet_manager) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), role=role)


def test_password_hash_roundtrip() -> None:
    h = hash_password("Transit@123")
    assert h != "Transit@123"
    assert verify_password("Transit@123", h) is True
    assert verify_password("wrong-password", h) is False


def test_access_token_carries_sub_and_role() -> None:
    user = _fake_user(UserRole.driver)
    payload = decode_token(create_access_token(user))
    assert payload["sub"] == str(user.id)
    assert payload["role"] == "driver"
    assert payload["type"] == "access"


def test_refresh_token_has_jti_and_type() -> None:
    payload = decode_token(create_refresh_token(_fake_user()))
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_expired_access_token_raises_token_expired() -> None:
    user = _fake_user()
    with freeze_time("2026-01-01 00:00:00"):
        token = create_access_token(user)
    with freeze_time("2026-01-01 02:00:00"):  # TTL is 30 min → expired
        with pytest.raises(TokenError) as exc:
            decode_token(token)
    assert exc.value.code == "TOKEN_EXPIRED"


def test_tampered_token_rejected() -> None:
    with pytest.raises(TokenError) as exc:
        decode_token("not.a.jwt")
    assert exc.value.code == "INVALID_TOKEN"


# --- error envelope shape through a dummy app ---

def _envelope_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/boom")
    def boom() -> None:
        raise DomainError(
            "CARGO_EXCEEDS_CAPACITY",
            "Cargo weight 620 kg exceeds Van-05 capacity of 500 kg.",
            field="cargo_weight_kg",
        )

    @app.get("/missing")
    def missing() -> None:
        raise NotFoundError("trip")

    @app.post("/validate")
    def validate(body: _CargoBody) -> dict:
        return {"ok": body.cargo_weight_kg}

    return app


def test_domain_error_envelope() -> None:
    client = TestClient(_envelope_app())
    r = client.post("/boom")
    assert r.status_code == 409
    assert r.json() == {
        "error": {
            "code": "CARGO_EXCEEDS_CAPACITY",
            "message": "Cargo weight 620 kg exceeds Van-05 capacity of 500 kg.",
            "field": "cargo_weight_kg",
        }
    }


def test_not_found_envelope() -> None:
    client = TestClient(_envelope_app())
    r = client.get("/missing")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_maps_field() -> None:
    client = TestClient(_envelope_app())
    r = client.post("/validate", json={})  # missing cargo_weight_kg
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["field"] == "cargo_weight_kg"
    assert body["error"]["code"] == "VALIDATION_ERROR"
