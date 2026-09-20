from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import get_db_session
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("AUTH_SECRET", "test-only-auth-secret-with-32-bytes")
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com,other@example.com")
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


def register(client: TestClient, email: str) -> dict[str, str]:
    assert client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    ).status_code == 201
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_profile(client: TestClient, headers: dict[str, str]) -> None:
    assert client.put(
        "/api/v1/profile",
        json={"full_name": "Jane Doe", "headline": "Backend Engineer", "location": "Remote"},
        headers=headers,
    ).status_code == 200
    assert client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=headers,
    ).status_code == 201


def create_job(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/jobs/ingest/local",
        json={
            "jobs": [
                {
                    "title": "Backend Engineer",
                    "company": "Example Co",
                    "location": "Remote",
                    "description": "Required: Python. Experience requirement is unclear.",
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


def test_activity_shows_analysis_warning_draft_and_approval_next_actions(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    assert client.post(f"/api/v1/jobs/{job_id}/analyze", headers=headers).status_code == 200
    draft = client.post("/api/v1/applications/drafts", json={"job_id": job_id}, headers=headers)
    assert draft.status_code == 200
    assert client.post(
        f"/api/v1/applications/drafts/{draft.json()['id']}/approve",
        json={"confirm": False},
        headers=headers,
    ).status_code == 409
    assert client.post(
        f"/api/v1/applications/drafts/{draft.json()['id']}/approve",
        json={"confirm": True},
        headers=headers,
    ).status_code == 200

    activity = client.get("/api/v1/activity", headers=headers)

    assert activity.status_code == 200
    events = activity.json()
    assert {event["event_type"] for event in events} >= {
        "OPPORTUNITY_INPUT",
        "ANALYSIS",
        "WARNING",
        "DRAFTING",
        "PAUSED",
        "APPROVAL",
    }
    draft_event = next(event for event in events if event["event_type"] == "DRAFTING")
    assert draft_event["state"] == "AWAITING_APPROVAL"
    assert "next_action" in draft_event["details"]
    approval_event = next(event for event in events if event["event_type"] == "APPROVAL")
    assert approval_event["details"]["approved_revision"] == 1


def test_activity_is_authenticated_and_owner_scoped(client: TestClient) -> None:
    assert client.get("/api/v1/activity").status_code == 401

    owner_headers = register(client, "user@example.com")
    create_profile(client, owner_headers)
    job_id = create_job(client, owner_headers)
    assert client.post(f"/api/v1/jobs/{job_id}/match", headers=owner_headers).status_code == 200

    other_headers = register(client, "other@example.com")
    create_profile(client, other_headers)
    response = client.get("/api/v1/activity", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_in_app_notifications_are_private_readable_and_truthful(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)
    draft = client.post("/api/v1/applications/drafts", json={"job_id": job_id}, headers=headers)
    assert draft.status_code == 200

    notifications = client.get("/api/v1/notifications", headers=headers)
    assert notifications.status_code == 200
    draft_notification = notifications.json()[0]
    assert draft_notification["notification_type"] == "DRAFT_READY"
    assert draft_notification["read_at"] is None

    marked_read = client.post(
        f"/api/v1/notifications/{draft_notification['id']}/read", headers=headers
    )
    assert marked_read.status_code == 200
    assert marked_read.json()["read_at"] is not None

    record = client.post(
        "/api/v1/applications/records", json={"job_id": job_id}, headers=headers
    )
    assert record.status_code == 200
    assert client.put(
        f"/api/v1/applications/records/{record.json()['id']}",
        json={"status": "unknown"},
        headers=headers,
    ).status_code == 200
    notifications = client.get("/api/v1/notifications", headers=headers).json()
    unknown = next(
        item for item in notifications if item["notification_type"] == "UNCERTAIN_STATUS"
    )
    assert unknown["message"] == "Submission status unknown — verify manually."

    other_headers = register(client, "other@example.com")
    create_profile(client, other_headers)
    assert client.get("/api/v1/notifications", headers=other_headers).json() == []
    assert client.post(
        f"/api/v1/notifications/{draft_notification['id']}/read", headers=other_headers
    ).status_code == 404


def test_user_feedback_is_private_and_does_not_change_tracking_or_preferences(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    feedback = client.post(
        "/api/v1/feedback",
        json={
            "job_id": job_id,
            "feedback_type": "WRONG_PREFERENCE",
            "note": "Remote preference was interpreted incorrectly.",
        },
        headers=headers,
    )

    assert feedback.status_code == 200
    payload = feedback.json()
    assert payload["source"] == "USER"
    assert payload["feedback_type"] == "WRONG_PREFERENCE"
    assert client.get("/api/v1/applications/records", headers=headers).json() == []
    assert client.get("/api/v1/profile/preferences", headers=headers).status_code == 404
    activity = client.get("/api/v1/activity", headers=headers).json()
    assert any(
        event["event_type"] == "USER_FEEDBACK" and event["details"]["source"] == "USER"
        for event in activity
    )

    other_headers = register(client, "other@example.com")
    create_profile(client, other_headers)
    assert client.get("/api/v1/feedback", headers=other_headers).json() == []
    assert client.get("/api/v1/feedback", headers=headers).json()[0]["id"] == payload["id"]


def test_feedback_accepts_all_documented_types_and_updates_same_user_signal(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)
    types = [
        "INTERESTED",
        "NOT_INTERESTED",
        "INCORRECT",
        "MISSING_SKILL",
        "WRONG_PREFERENCE",
        "ALREADY_APPLIED",
    ]
    for feedback_type in types:
        assert client.post(
            "/api/v1/feedback",
            json={"job_id": job_id, "feedback_type": feedback_type},
            headers=headers,
        ).status_code == 200
    updated = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "MISSING_SKILL", "note": "Docker"},
        headers=headers,
    )
    assert updated.status_code == 200
    feedback = client.get("/api/v1/feedback", headers=headers).json()
    assert len(feedback) == len(types)
    missing_skill = next(item for item in feedback if item["feedback_type"] == "MISSING_SKILL")
    assert missing_skill["note"] == "Docker"


def test_feedback_proposal_creation_wrong_preference(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    client.put(
        "/api/v1/profile/preferences",
        json={"target_roles": ["Junior Developer"]},
        headers=headers,
    )

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE", "note": "Wrong role"},
        headers=headers,
    ).json()

    proposal_resp = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "target_roles",
            "proposed_value": {"value": ["Backend Engineer", "Platform Engineer"]},
        },
        headers=headers,
    )
    assert proposal_resp.status_code == 200
    proposal = proposal_resp.json()
    assert proposal["status"] == "PENDING"
    assert proposal["target_type"] == "PREFERENCE"
    assert proposal["target_field"] == "target_roles"
    assert proposal["previous_value"] == {"value": ["Junior Developer"]}
    assert proposal["proposed_value"] == {"value": ["Backend Engineer", "Platform Engineer"]}

    # Verify preferences NOT mutated before confirmation
    prefs = client.get("/api/v1/profile/preferences", headers=headers).json()
    assert prefs["target_roles"] == ["Junior Developer"]


def test_feedback_proposal_creation_missing_skill(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "MISSING_SKILL", "note": "Missing Go"},
        headers=headers,
    ).json()

    proposal_resp = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "SKILL",
            "proposed_value": {"name": "Go", "category": "backend", "proficiency": "INTERMEDIATE"},
        },
        headers=headers,
    )
    assert proposal_resp.status_code == 200
    proposal = proposal_resp.json()
    assert proposal["status"] == "PENDING"
    assert proposal["target_type"] == "SKILL"
    assert proposal["applied_skill_id"] is None

    # Verify skill NOT added before confirmation
    skills = client.get("/api/v1/profile/skills", headers=headers).json()
    assert not any(s["name"] == "Go" for s in skills)


def test_feedback_proposal_creation_incorrect(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "INCORRECT", "note": "Title is wrong"},
        headers=headers,
    ).json()

    proposal_resp = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "JOB_CORRECTION",
            "proposed_value": {"correction": "Job requires senior experience"},
        },
        headers=headers,
    )
    assert proposal_resp.status_code == 200
    proposal = proposal_resp.json()
    assert proposal["status"] == "PENDING"
    assert proposal["target_type"] == "JOB_CORRECTION"

    # Verify shared job was NOT mutated
    job = client.get("/api/v1/jobs", headers=headers).json()["jobs"][0]
    assert job["title"] == "Backend Engineer"


def test_informational_feedback_cannot_create_proposal(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    for fb_type in ["INTERESTED", "NOT_INTERESTED", "ALREADY_APPLIED"]:
        fb = client.post(
            "/api/v1/feedback",
            json={"job_id": job_id, "feedback_type": fb_type},
            headers=headers,
        ).json()
        resp = client.post(
            "/api/v1/feedback/proposals",
            json={
                "feedback_id": fb["id"],
                "target_type": "PREFERENCE",
                "target_field": "target_roles",
                "proposed_value": {"value": ["Lead"]},
            },
            headers=headers,
        )
        assert resp.status_code == 409


def test_feedback_proposal_confirmation_updates_preferences_and_records_activity(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    client.put(
        "/api/v1/profile/preferences",
        json={"target_roles": ["Intern"]},
        headers=headers,
    )

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE"},
        headers=headers,
    ).json()

    proposal = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "preferred_roles",
            "proposed_value": {"value": ["Full Stack Engineer"]},
        },
        headers=headers,
    ).json()

    confirm_resp = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/confirm",
        headers=headers,
    )
    assert confirm_resp.status_code == 200
    confirmed = confirm_resp.json()
    assert confirmed["status"] == "CONFIRMED"
    assert confirmed["confirmed_at"] is not None

    prefs = client.get("/api/v1/profile/preferences", headers=headers).json()
    assert prefs["target_roles"] == ["Full Stack Engineer"]

    activity = client.get("/api/v1/activity", headers=headers).json()
    conf_event = next(e for e in activity if e["event_type"] == "FEEDBACK_CONFIRMED")
    assert conf_event["details"]["proposal_id"] == proposal["id"]


def test_feedback_proposal_confirmation_adds_skill_and_revocation_removes_it(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "MISSING_SKILL"},
        headers=headers,
    ).json()

    proposal = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "SKILL",
            "proposed_value": {"name": "Rust", "proficiency": "ADVANCED", "category": "backend"},
        },
        headers=headers,
    ).json()

    confirm_resp = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/confirm",
        headers=headers,
    )
    assert confirm_resp.status_code == 200
    confirmed = confirm_resp.json()
    assert confirmed["status"] == "CONFIRMED"
    assert confirmed["applied_skill_id"] is not None

    skills = client.get("/api/v1/profile/skills", headers=headers).json()
    assert any(s["name"] == "Rust" for s in skills)

    revoke_resp = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/revoke",
        headers=headers,
    )
    assert revoke_resp.status_code == 200
    revoked = revoke_resp.json()
    assert revoked["status"] == "REVOKED"
    assert revoked["revoked_at"] is not None

    skills_after = client.get("/api/v1/profile/skills", headers=headers).json()
    assert not any(s["name"] == "Rust" for s in skills_after)

    activity = client.get("/api/v1/activity", headers=headers).json()
    assert any(e["event_type"] == "FEEDBACK_REVOKED" for e in activity)


def test_feedback_proposal_rejection_leaves_data_unchanged(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    client.put(
        "/api/v1/profile/preferences",
        json={"locations": ["New York"]},
        headers=headers,
    )

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE"},
        headers=headers,
    ).json()

    proposal = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "locations",
            "proposed_value": {"value": ["San Francisco"]},
        },
        headers=headers,
    ).json()

    reject_resp = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/reject",
        headers=headers,
    )
    assert reject_resp.status_code == 200
    rejected = reject_resp.json()
    assert rejected["status"] == "REJECTED"
    assert rejected["rejected_at"] is not None

    prefs = client.get("/api/v1/profile/preferences", headers=headers).json()
    assert prefs["locations"] == ["New York"]

    feedback_list = client.get("/api/v1/feedback", headers=headers).json()
    assert any(item["id"] == fb["id"] for item in feedback_list)


def test_feedback_proposal_preference_revocation_restores_prior_value(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    client.put(
        "/api/v1/profile/preferences",
        json={"technologies": ["Python", "Django"]},
        headers=headers,
    )

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE"},
        headers=headers,
    ).json()

    proposal = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "technologies",
            "proposed_value": {"value": ["FastAPI", "SQLAlchemy"]},
        },
        headers=headers,
    ).json()

    client.post(f"/api/v1/feedback/proposals/{proposal['id']}/confirm", headers=headers)
    prefs_confirmed = client.get("/api/v1/profile/preferences", headers=headers).json()
    assert prefs_confirmed["technologies"] == ["FastAPI", "SQLAlchemy"]

    client.post(f"/api/v1/feedback/proposals/{proposal['id']}/revoke", headers=headers)
    prefs_revoked = client.get("/api/v1/profile/preferences", headers=headers).json()
    assert prefs_revoked["technologies"] == ["Python", "Django"]


def test_feedback_proposal_incorrect_confirm_preserves_review_without_mutating_job(
    client: TestClient,
) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "INCORRECT"},
        headers=headers,
    ).json()

    proposal = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "JOB_CORRECTION",
            "proposed_value": {"correction": "Company name is mislabeled"},
        },
        headers=headers,
    ).json()

    confirm_resp = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/confirm",
        headers=headers,
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "CONFIRMED"

    job = client.get("/api/v1/jobs", headers=headers).json()["jobs"][0]
    assert job["company"] == "Example Co"

    revoke_resp = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/revoke",
        headers=headers,
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "REVOKED"


def test_feedback_proposal_idempotency(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE"},
        headers=headers,
    ).json()

    proposal = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "work_modes",
            "proposed_value": {"value": ["REMOTE"]},
        },
        headers=headers,
    ).json()

    first_confirm = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/confirm", headers=headers
    )
    assert first_confirm.status_code == 200
    second_confirm = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/confirm", headers=headers
    )
    assert second_confirm.status_code == 200
    assert second_confirm.json()["status"] == "CONFIRMED"

    first_revoke = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/revoke", headers=headers
    )
    assert first_revoke.status_code == 200
    second_revoke = client.post(
        f"/api/v1/feedback/proposals/{proposal['id']}/revoke", headers=headers
    )
    assert second_revoke.status_code == 200
    assert second_revoke.json()["status"] == "REVOKED"


def test_feedback_proposal_owner_isolation(client: TestClient) -> None:
    user1_headers = register(client, "user@example.com")
    create_profile(client, user1_headers)
    job_id = create_job(client, user1_headers)

    fb1 = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE"},
        headers=user1_headers,
    ).json()

    prop1 = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb1["id"],
            "target_type": "PREFERENCE",
            "target_field": "target_roles",
            "proposed_value": {"value": ["Engineer"]},
        },
        headers=user1_headers,
    ).json()

    user2_headers = register(client, "other@example.com")
    create_profile(client, user2_headers)

    assert client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb1["id"],
            "target_type": "PREFERENCE",
            "target_field": "target_roles",
            "proposed_value": {"value": ["Hacker"]},
        },
        headers=user2_headers,
    ).status_code == 404

    assert client.post(
        f"/api/v1/feedback/proposals/{prop1['id']}/confirm", headers=user2_headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/feedback/proposals/{prop1['id']}/reject", headers=user2_headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/feedback/proposals/{prop1['id']}/revoke", headers=user2_headers
    ).status_code == 404


def test_feedback_proposal_invalid_actions_and_payloads(client: TestClient) -> None:
    headers = register(client, "user@example.com")
    create_profile(client, headers)
    job_id = create_job(client, headers)

    fb = client.post(
        "/api/v1/feedback",
        json={"job_id": job_id, "feedback_type": "WRONG_PREFERENCE"},
        headers=headers,
    ).json()

    assert client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "SKILL",
            "proposed_value": {"name": "Python", "proficiency": "ADVANCED"},
        },
        headers=headers,
    ).status_code == 409

    assert client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "nonexistent_field",
            "proposed_value": {"value": ["A"]},
        },
        headers=headers,
    ).status_code == 409

    assert client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "target_roles",
            "proposed_value": {"value": "NotAList"},
        },
        headers=headers,
    ).status_code == 409

    prop = client.post(
        "/api/v1/feedback/proposals",
        json={
            "feedback_id": fb["id"],
            "target_type": "PREFERENCE",
            "target_field": "target_roles",
            "proposed_value": {"value": ["Engineer"]},
        },
        headers=headers,
    ).json()
    assert client.post(
        f"/api/v1/feedback/proposals/{prop['id']}/revoke", headers=headers
    ).status_code == 409

    client.post(f"/api/v1/feedback/proposals/{prop['id']}/reject", headers=headers)
    assert client.post(
        f"/api/v1/feedback/proposals/{prop['id']}/confirm", headers=headers
    ).status_code == 409
