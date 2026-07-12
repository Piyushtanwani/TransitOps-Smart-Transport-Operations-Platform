"""Pytest harness (docs/07 §1): migrated test DB, per-test rollback, client override."""
from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.core.deps import get_db
from app.main import app

_BACKEND = Path(__file__).resolve().parents[2]  # tests -> app -> backend
_settings = get_settings()
TEST_URL = _settings.DATABASE_URL_TEST or _settings.DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_db() -> None:
    """Bring `transitops_test` to head once per session."""
    cfg = Config(str(_BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_URL)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def _engine(_migrate_test_db):
    engine = create_engine(TEST_URL, pool_pre_ping=True, future=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(_engine) -> Session:
    """Each test runs inside a transaction rolled back at teardown.

    `join_transaction_mode='create_savepoint'` lets service code call `commit()`
    (releasing a savepoint) while the outer transaction still rolls everything back.
    """
    connection = _engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db) -> TestClient:
    """TestClient whose `get_db` yields the test-scoped session."""

    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
