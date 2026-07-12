"""Suite B (auth half) — login, refresh rotation, me, token expiry (docs/07 §3).

The parametrized RBAC sweep is appended by BE-04 onward.
"""
from __future__ import annotations

import uuid

import pytest
from freezegun import freeze_time

from app.core.security import create_access_token
from app.models.enums import UserRole
from app.tests.factories import auth_headers, login, make_user

API = "/api/v1"
ROLES = ["fleet_manager", "driver", "safety_officer", "financial_analyst"]


def test_login_ok_returns_pair_and_user(client, db) -> None:
    make_user(db, UserRole.fleet_manager, email="fm@test.in")
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
    make_user(db, UserRole.financial_analyst, email="fa@test.in")
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


# ---------------------------------------------------------------------------
# Parametrized RBAC sweep (docs/03 §3). ONE growing table: each BE task appends
# its rows here. The path appears in the test id, so `pytest -k <resource>`
# selects that resource's rows.
# ---------------------------------------------------------------------------

def _sweep_body(key: str | None) -> dict | None:
    if key == "user":
        return {
            "email": f"sweep_{uuid.uuid4().hex[:8]}@test.in",
            "full_name": "Sweep User",
            "role": "driver",
            "password": "passw0rd1",
        }
    if key == "vehicle":
        return {
            "registration_number": f"TS-{uuid.uuid4().hex[:6]}",
            "name": "Sweep Truck",
            "type": "truck",
            "max_load_capacity_kg": 1000,
            "acquisition_cost": 500000,
            "region": "North",
        }
    if key == "driver":
        return {
            "full_name": "Sweep Driver",
            "license_number": f"LIC-{uuid.uuid4().hex[:8]}",
            "license_category": "LMV",
            "license_expiry": "2030-01-01",
            "contact_number": "9876500000",
        }
    return None


_ALL_READ = {"fleet_manager": 200, "driver": 200, "safety_officer": 200, "financial_analyst": 200}
_FM_ONLY_CREATE = {"fleet_manager": 201, "driver": 403, "safety_officer": 403, "financial_analyst": 403}
_FM_ONLY_LIST = {"fleet_manager": 200, "driver": 403, "safety_officer": 403, "financial_analyst": 403}
_FM_SO_CREATE = {"fleet_manager": 201, "driver": 403, "safety_officer": 201, "financial_analyst": 403}

# (path, method, body_key, {role: expected_status})
RBAC_MATRIX: list[tuple] = [
    ("/users", "GET", None, _FM_ONLY_LIST),
    ("/users", "POST", "user", _FM_ONLY_CREATE),
    ("/vehicles", "GET", None, _ALL_READ),
    ("/vehicles", "POST", "vehicle", _FM_ONLY_CREATE),
    ("/drivers", "GET", None, _ALL_READ),
    ("/drivers", "POST", "driver", _FM_SO_CREATE),
]

_SWEEP_IDS = [f"{m}{p}" for (p, m, _, _) in RBAC_MATRIX]


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("path,method,body_key,expected", RBAC_MATRIX, ids=_SWEEP_IDS)
def test_rbac_sweep(client, db, role, path, method, body_key, expected) -> None:
    headers = auth_headers(client, db, role)
    resp = client.request(method, f"{API}{path}", headers=headers, json=_sweep_body(body_key))
    assert resp.status_code == expected[role], f"{role} {method} {path}: {resp.status_code} {resp.text}"


# --- Users CRUD (FM) dedicated cases ---

def test_users_create_duplicate_email_409(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    body = {"email": "dupe@test.in", "full_name": "A", "role": "driver", "password": "passw0rd1"}
    assert client.post(f"{API}/users", json=body, headers=headers).status_code == 201
    r = client.post(f"{API}/users", json=body, headers=headers)
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "DUPLICATE_EMAIL"
    assert err["field"] == "email"


def test_users_password_policy_422(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    body = {"email": "weak@test.in", "full_name": "A", "role": "driver", "password": "short"}
    r = client.post(f"{API}/users", json=body, headers=headers)
    assert r.status_code == 422
    assert r.json()["error"]["field"] == "password"


def test_users_patch_and_deactivate(client, db) -> None:
    headers = auth_headers(client, db, "fleet_manager")
    created = client.post(
        f"{API}/users",
        json={"email": "life@test.in", "full_name": "Life", "role": "driver", "password": "passw0rd1"},
        headers=headers,
    ).json()
    uid = created["id"]
    patched = client.patch(f"{API}/users/{uid}", json={"full_name": "Renamed"}, headers=headers)
    assert patched.status_code == 200 and patched.json()["full_name"] == "Renamed"
    # DELETE deactivates (never hard-deletes)
    assert client.delete(f"{API}/users/{uid}", headers=headers).status_code == 204
    deactivated = login(client, "life@test.in")
    assert deactivated.status_code == 401  # inactive user cannot log in
