"""
Integration test configuration.

Strategy: use a single SQLite in-memory database for the entire test session.
We patch app.db.session at import time using a pytest plugin hook so the
engine is replaced before any test module imports app code.
"""

import os

# ── Environment must be set before ANY app import ────────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")
os.environ.setdefault("SYNC_ADAPTER", "mock")
os.environ.setdefault("JIRA_BASE_URL", "https://mock.atlassian.net")
os.environ.setdefault("JIRA_USER_EMAIL", "test@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "mock-token")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("UPLOAD_DIR", "/tmp/test_uploads")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# ── Build a single shared in-memory engine ───────────────────────────────────
# Use a named in-memory DB so all connections share the same data
_TEST_DB_URL = "sqlite:///file::memory:?cache=shared&uri=true"
TEST_ENGINE = create_engine(
    _TEST_DB_URL,
    connect_args={"check_same_thread": False, "uri": True},
    echo=False,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=TEST_ENGINE
)

# ── Patch app.db.session BEFORE it is used anywhere ──────────────────────────
import app.db.session as _db_session
_db_session.engine = TEST_ENGINE
_db_session.SessionLocal = TestingSessionLocal

# ── Now safe to import app models and Base ────────────────────────────────────
import app.models  # noqa: F401 — registers all ORM models with Base.metadata
from app.db.base import Base
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.models.user import UserModel, DepartmentModel


# ── Create tables once for the whole session ─────────────────────────────────
Base.metadata.create_all(bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate all tables between tests for isolation."""
    yield
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture
def db(clean_tables):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    from app.main import app

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable background workers during tests
    import app.workers.sync_worker as sw
    sw.start_sync_worker = lambda: None
    sw.stop_sync_worker = lambda: None

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def dept(db):
    d = DepartmentModel(name="Engineering", is_active=True)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@pytest.fixture
def business_user(db, dept):
    u = UserModel(
        email="user@example.com",
        display_name="Business User",
        password_hash=hash_password("password123"),
        role="business_user",
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def manager_user(db, dept):
    u = UserModel(
        email="manager@example.com",
        display_name="Manager",
        password_hash=hash_password("password123"),
        role="it_manager",
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def it_triage_user(db, dept):
    u = UserModel(
        email="it@example.com",
        display_name="IT Triage",
        password_hash=hash_password("password123"),
        role="it_triage",
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def admin_user(db, dept):
    u = UserModel(
        email="admin@example.com",
        display_name="Admin",
        password_hash=hash_password("password123"),
        role="platform_admin",
        department_id=dept.id,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def login(client, email: str, password: str = "password123"):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp
