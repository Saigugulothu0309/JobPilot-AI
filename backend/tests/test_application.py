from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import get_db_session
from app.main import app
from app.modules.application.models import ApplicationDraft


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("AUTH_SECRET", "test-only-auth-secret-with-32-bytes")
    monkeypatch.setenv(
        "JOB_INGESTION_ADMIN_EMAILS",
        "user@example.com,owner@example.com,other@example.com",
    )
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


def register(client: TestClient, email: str = "user@example.com") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_job(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/jobs/ingest/local",
        json={
            "jobs": [
                {
                    "title": "Backend Engineer",
                    "company": "Example Co",
                    "location": "Remote",
                    "description": "Build Python APIs.",
                    "employment_type": "FULL_TIME",
                    "external_job_id": str(uuid4()),
                    "external_url": "https://jobs.example.test/backend",
                }
            ]
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["jobs"][0]["id"]


def create_profile(client: TestClient, headers: dict[str, str]) -> None:
    response = client.put(
        "/api/v1/profile",
        json={
            "full_name": "Jane Doe",
            "headline": "Backend Engineer",
            "summary": "Builds reliable APIs.",
            "location": "Remote",
        },
        headers=headers,
    )
    assert response.status_code == 200
    skill = client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=headers,
    )
    assert skill.status_code == 201


def test_authenticated_user_can_prepare_and_retrieve_grounded_draft(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)

    response = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DRAFT"
    assert payload["revision"] == 1
    assert payload["content"]["approval_required"] is True
    assert payload["content"]["application_summary"] == "Builds reliable APIs."
    assert payload["content"]["resume_focus"] == ["Python"]
    assert payload["content"]["experience_evidence"] == []
    assert payload["profile_snapshot"]["profile_id"]
    assert payload["job_snapshot"]["job_id"] == job_id

    retrieved = client.get(
        f"/api/v1/applications/drafts/{payload['id']}",
        headers=headers,
    )
    assert retrieved.status_code == 200
    assert retrieved.json() == payload


def test_repeating_preparation_updates_one_draft_revision(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)

    first = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=headers,
    )
    second = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["revision"] == 2
    session = next(app.dependency_overrides[get_db_session]())
    assert len(session.scalars(select(ApplicationDraft)).all()) == 1
    session.close()


def test_draft_ownership_and_authentication_are_enforced(client: TestClient) -> None:
    unauthenticated = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": str(uuid4())},
    )
    assert unauthenticated.status_code == 401

    owner_headers = register(client, "owner@example.com")
    create_profile(client, owner_headers)
    job_id = create_job(client, owner_headers)
    draft = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=owner_headers,
    ).json()

    other_headers = register(client, "other@example.com")
    response = client.get(
        f"/api/v1/applications/drafts/{draft['id']}",
        headers=other_headers,
    )
    assert response.status_code == 404


def test_draft_rejects_missing_job(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    response = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": str(uuid4())},
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_draft_requires_explicit_approval_and_resets_after_edit(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)
    draft = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=headers,
    ).json()

    rejected = client.post(
        f"/api/v1/applications/drafts/{draft['id']}/approve",
        json={"confirm": False},
        headers=headers,
    )
    assert rejected.status_code == 409
    assert "Explicit approval" in rejected.json()["detail"]

    approved = client.post(
        f"/api/v1/applications/drafts/{draft['id']}/approve",
        json={"confirm": True},
        headers=headers,
    )
    assert approved.status_code == 200
    approved_payload = approved.json()
    assert approved_payload["status"] == "APPROVED"
    assert approved_payload["approved_revision"] == approved_payload["revision"]
    assert approved_payload["approval_confirmed"] is True

    edited = client.put(
        f"/api/v1/applications/drafts/{draft['id']}",
        json={"content": {"application_summary": "User-reviewed summary."}},
        headers=headers,
    )
    assert edited.status_code == 409


def test_draft_edit_is_reviewable_before_approval(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)
    draft = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=headers,
    ).json()

    edited = client.put(
        f"/api/v1/applications/drafts/{draft['id']}",
        json={"content": {"application_summary": "User-reviewed summary."}},
        headers=headers,
    )
    assert edited.status_code == 200
    payload = edited.json()
    assert payload["status"] == "DRAFT"
    assert payload["revision"] == 2
    assert payload["approved_revision"] is None
    assert payload["approval_confirmed"] is False
    assert payload["content"] == {"application_summary": "User-reviewed summary."}


def test_application_tracking_preserves_job_and_draft_revision(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)
    draft = client.post(
        "/api/v1/applications/drafts",
        json={"job_id": job_id},
        headers=headers,
    ).json()

    created = client.post(
        "/api/v1/applications/records",
        json={
            "job_id": job_id,
            "draft_id": draft["id"],
            "status": "preparing",
            "notes": "Review before submission.",
            "follow_up_at": "2026-09-20T09:00:00Z",
        },
        headers=headers,
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "PREPARING"
    assert payload["draft_id"] == draft["id"]
    assert payload["draft_revision"] == draft["revision"]
    assert payload["job_snapshot"]["job_id"] == job_id
    assert payload["notes"] == "Review before submission."

    listed = client.get("/api/v1/applications/records", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_application_tracking_unknown_status_requires_manual_verification_message(
    client: TestClient,
) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)

    created = client.post(
        "/api/v1/applications/records",
        json={"job_id": job_id, "status": "unknown", "notes": "Network interrupted."},
        headers=headers,
    )

    assert created.status_code == 200
    assert created.json()["status"] == "UNKNOWN"
    assert created.json()["notes"] == "Submission status unknown — verify manually."


def test_application_tracking_updates_manually_and_rejects_duplicates(client: TestClient) -> None:
    headers = register(client)
    create_profile(client, headers)
    job_id = create_job(client, headers)
    created = client.post(
        "/api/v1/applications/records",
        json={"job_id": job_id},
        headers=headers,
    )
    assert created.status_code == 200
    record_id = created.json()["id"]

    duplicate = client.post(
        "/api/v1/applications/records",
        json={"job_id": job_id},
        headers=headers,
    )
    assert duplicate.status_code == 409

    updated = client.put(
        f"/api/v1/applications/records/{record_id}",
        json={"status": "interview", "notes": "Interview scheduled."},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "INTERVIEW"
    assert updated.json()["notes"] == "Interview scheduled."


def test_application_tracking_is_owner_scoped_and_requires_authentication(
    client: TestClient,
) -> None:
    unauthenticated = client.get("/api/v1/applications/records")
    assert unauthenticated.status_code == 401

    owner_headers = register(client, "owner@example.com")
    create_profile(client, owner_headers)
    job_id = create_job(client, owner_headers)
    record = client.post(
        "/api/v1/applications/records",
        json={"job_id": job_id},
        headers=owner_headers,
    ).json()

    other_headers = register(client, "other@example.com")
    response = client.get(
        f"/api/v1/applications/records/{record['id']}",
        headers=other_headers,
    )
    assert response.status_code == 404
