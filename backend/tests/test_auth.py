from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import get_db_session
from app.main import app
from app.modules.auth.models import User
from app.security.auth import create_access_token


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("AUTH_SECRET", "test-only-auth-secret-with-32-bytes")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
    get_settings.cache_clear()


def register(client: TestClient, email: str = "user@example.com", password: str = "password123"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def test_registration_stores_only_a_password_hash(client: TestClient) -> None:
    response = register(client)

    assert response.status_code == 201
    assert "password_hash" not in response.json()

    session = next(app.dependency_overrides[get_db_session]())
    user = session.scalar(select(User))
    assert user is not None
    assert user.password_hash != "password123"
    session.close()


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    assert register(client).status_code == 201
    assert register(client).status_code == 409


def test_login_and_me_require_valid_authentication(client: TestClient) -> None:
    register(client)

    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong"}
        ).status_code
        == 401
    )

    login = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"
    assert "password_hash" not in me.json()


def test_invalid_and_expired_tokens_are_rejected(client: TestClient) -> None:
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code
        == 401
    )
    register(client)
    user_id = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "password123"}
    ).json()
    assert user_id["access_token"]
    session = next(app.dependency_overrides[get_db_session]())
    user = session.scalar(select(User))
    assert user is not None
    expired = create_access_token(user.id, expires_delta=timedelta(seconds=-1))
    session.close()
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code
        == 401
    )
