"""
Shared pytest fixtures for integration tests.
Uses an in-memory SQLite database — never touches the dev database.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point to in-memory SQLite before importing app
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")
os.environ.setdefault("SYNC_ADAPTER", "mock")
os.environ.setdefault("JIRA_BASE_URL", "https://mock.atlassian.net")
os.environ.setdefault("JIRA_USER_EMAIL", "test@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "mock-token")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.db.base import Base
from app.db.session import SessionLocal
from app.main import app
from app.core.dependencies import get_db
from app.core.security import hash_password
from app.models.user import UserModel, DepartmentModel


TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


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
    """Helper to log in and return authenticated client."""
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp
