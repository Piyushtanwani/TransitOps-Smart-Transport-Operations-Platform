"""Suite B (auth half) — login, refresh rotation, me, token expiry (docs/07 §3).

The parametrized RBAC sweep is appended by BE-04 onward.
"""
from __future__ import annotations

from freezegun import freeze_time

from app.core.security import create_access_token
from app.models.enums import UserRole
from app.tests.factories import PASSWORD, auth_headers, login, make_user

API = "/api/v1"


def test_login_ok_returns_pair_and_user(client, db) -> None:
    user = make_user(db, UserRole.fleet_manager, email="fm@test.in")
    r = login(client, "fm@test.in")
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == "fm@test.in"
    assert body["user"]["role"] == "fleet_manager"


def test_login_wrong_password_401(client, db) -> None:
    make_user(db, UserRole.driver, email="d@test.in")
    r = login(client, "d@test.in", "not-the-password")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_unknown_email_same_message_as_wrong_password(client, db) -> None:
    make_user(db, UserRole.driver, email="known@test.in")
    unknown = login(client, "nobody@test.in", "whatever")
    wrong = login(client, "known@test.in", "whatever")
    # No user enumeration: identical status + message.
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_inactive_user_401(client, db) -> None:
    make_user(db, UserRole.safety_officer, email="off@test.in", is_active=False)
    r = login(client, "off@test.in")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_roundtrip(client, db) -> None:
    user = make_user(db, UserRole.financial_analyst, email="fa@test.in")
    token = login(client, "fa@test.in").json()["access_token"]
    r = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "fa@test.in"
    assert r.json()["role"] == "financial_analyst"


def test_me_without_token_401(client, db) -> None:
    r = client.get(f"{API}/auth/me")
    assert r.status_code == 401


def test_refresh_returns_new_pair(client, db) -> None:
    make_user(db, UserRole.driver, email="r@test.in")
    tokens = login(client, "r@test.in").json()
    r = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    fresh = r.json()
    assert fresh["access_token"] and fresh["refresh_token"]
    # New access token is usable.
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {fresh['access_token']}"})
    assert me.status_code == 200


def test_access_token_cannot_be_used_as_refresh(client, db) -> None:
    make_user(db, UserRole.driver, email="a@test.in")
    tokens = login(client, "a@test.in").json()
    r = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_TOKEN"


def test_expired_access_token_401_token_expired(client, db) -> None:
    user = make_user(db, UserRole.fleet_manager, email="exp@test.in")
    with freeze_time("2026-01-01 00:00:00"):
        token = create_access_token(user)
    with freeze_time("2026-01-01 02:00:00"):  # 30-min TTL → expired
        r = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_EXPIRED"
