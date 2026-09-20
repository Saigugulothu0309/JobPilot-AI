from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db_session
from app.main import app
from app.modules.auth.models import User
from app.modules.profile.models import Profile


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("AUTH_SECRET", "test-only-auth-secret-with-32-bytes")
    from app.core.config import get_settings

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


def login(client: TestClient, email: str = "user@example.com", password: str = "password123"):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response


def get_auth_header(client: TestClient, email: str = "user@example.com") -> dict[str, str]:
    login_response = login(client, email=email)
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_authenticated_user_can_create_and_retrieve_profile(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    create_response = client.put(
        "/api/v1/profile",
        json={
            "full_name": "Ada Lovelace",
            "phone": "+15551234567",
            "location": "London",
            "headline": "Mathematician",
            "summary": "Worked on the Analytical Engine.",
        },
        headers=headers,
    )

    assert create_response.status_code == 200
    body = create_response.json()
    assert body["full_name"] == "Ada Lovelace"
    assert body["headline"] == "Mathematician"

    get_response = client.get("/api/v1/profile", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == "Ada Lovelace"


def test_authenticated_user_can_update_profile(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    client.put(
        "/api/v1/profile",
        json={"full_name": "Ada Lovelace", "headline": "Mathematician"},
        headers=headers,
    )

    update_response = client.put(
        "/api/v1/profile",
        json={"full_name": "Ada Byron", "summary": "Updated summary"},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Ada Byron"
    assert update_response.json()["summary"] == "Updated summary"


def test_unauthenticated_profile_access_is_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/profile").status_code == 401
    assert client.put("/api/v1/profile", json={"full_name": "Ada"}).status_code == 401
    assert client.get("/api/v1/profile/preferences").status_code == 401
    assert client.put("/api/v1/profile/preferences", json={}).status_code == 401


def test_authenticated_user_can_create_and_retrieve_career_preferences(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    update = client.put(
        "/api/v1/profile/preferences",
        json={
            "target_roles": ["Backend Engineer", "Data Engineer"],
            "employment_types": ["full_time", "internship"],
            "locations": ["Boston, MA"],
            "work_modes": ["remote", "hybrid"],
            "technologies": ["Python", "FastAPI"],
            "hard_constraints": ["No relocation required"],
            "ranking_preferences": ["Prefer remote work"],
            "optional_preferences": ["Early-stage company"],
            "relocation_preference": "depends",
            "salary_min": 70000,
            "salary_max": 100000,
            "available_from": "2026-10-01",
        },
        headers=headers,
    )

    assert update.status_code == 200
    body = update.json()
    assert body["target_roles"] == ["Backend Engineer", "Data Engineer"]
    assert body["employment_types"] == ["FULL_TIME", "INTERNSHIP"]
    assert body["work_modes"] == ["REMOTE", "HYBRID"]
    assert body["relocation_preference"] == "DEPENDS"
    assert body["hard_constraints"] == ["No relocation required"]

    retrieved = client.get("/api/v1/profile/preferences", headers=headers)
    assert retrieved.status_code == 200
    assert retrieved.json() == body


def test_career_preferences_are_isolated_and_validated(client: TestClient) -> None:
    register(client, "owner@example.com")
    register(client, "other@example.com")
    owner_headers = get_auth_header(client, "owner@example.com")
    other_headers = get_auth_header(client, "other@example.com")

    created = client.put(
        "/api/v1/profile/preferences",
        json={"target_roles": ["Backend Engineer"]},
        headers=owner_headers,
    )
    assert created.status_code == 200

    missing = client.get("/api/v1/profile/preferences", headers=other_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Preferences not found"

    invalid_range = client.put(
        "/api/v1/profile/preferences",
        json={"salary_min": 100000, "salary_max": 70000},
        headers=owner_headers,
    )
    assert invalid_range.status_code == 422

    invalid_enum = client.put(
        "/api/v1/profile/preferences",
        json={"work_modes": ["commute-free"]},
        headers=owner_headers,
    )
    assert invalid_enum.status_code == 422


def test_profile_ownership_is_enforced(client: TestClient) -> None:
    register(client, "owner@example.com")
    register(client, "other@example.com")

    owner_headers = get_auth_header(client, "owner@example.com")
    other_headers = get_auth_header(client, "other@example.com")

    client.put(
        "/api/v1/profile",
        json={"full_name": "Owner Name"},
        headers=owner_headers,
    )

    response = client.get("/api/v1/profile", headers=other_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"


def test_user_cannot_create_multiple_profiles(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    first = client.put("/api/v1/profile", json={"full_name": "First Profile"}, headers=headers)
    second = client.put("/api/v1/profile", json={"full_name": "Second Profile"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200

    session = next(app.dependency_overrides[get_db_session]())
    profiles = session.scalars(select(Profile)).all()
    assert len(profiles) == 1
    assert profiles[0].full_name == "Second Profile"
    session.close()


def test_invalid_profile_input_is_rejected(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    response = client.put(
        "/api/v1/profile",
        json={"full_name": "x" * 201},
        headers=headers,
    )

    assert response.status_code == 422


def test_profile_is_not_associated_with_different_user_id(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    response = client.put(
        "/api/v1/profile",
        json={"full_name": "Ada Lovelace"},
        headers=headers,
    )
    assert response.status_code == 200

    session = next(app.dependency_overrides[get_db_session]())
    profile = session.scalar(select(Profile))
    assert profile is not None
    user = session.scalar(select(User))
    assert user is not None
    assert profile.user_id == user.id
    session.close()


def test_professional_data_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/profile/skills").status_code == 401
    assert client.post("/api/v1/profile/skills", json={"name": "Python"}).status_code == 401
    assert client.get("/api/v1/profile/education").status_code == 401
    assert client.get("/api/v1/profile/experience").status_code == 401
    assert client.get("/api/v1/profile/projects").status_code == 401


def test_skill_crud_and_duplicate_handling(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    create = client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=headers,
    )
    assert create.status_code == 201
    skill_id = create.json()["id"]

    list_response = client.get("/api/v1/profile/skills", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    duplicate = client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=headers,
    )
    assert duplicate.status_code == 409

    update = client.put(
        f"/api/v1/profile/skills/{skill_id}",
        json={"name": "Python", "category": "data", "proficiency": "EXPERT"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["category"] == "data"

    delete_response = client.delete(f"/api/v1/profile/skills/{skill_id}", headers=headers)
    assert delete_response.status_code == 204
    assert client.get("/api/v1/profile/skills", headers=headers).json() == []


def test_education_crud_and_date_handling(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    create = client.post(
        "/api/v1/profile/education",
        json={
            "institution": "University of London",
            "degree": "BSc",
            "field_of_study": "Computer Science",
            "start_date": "2020-09-01",
            "end_date": "2024-06-01",
            "description": "Graduated with honors.",
        },
        headers=headers,
    )
    assert create.status_code == 201
    education_id = create.json()["id"]

    invalid = client.post(
        "/api/v1/profile/education",
        json={
            "institution": "Bad School",
            "degree": "MSc",
            "field_of_study": "AI",
            "start_date": "2025-01-01",
            "end_date": "2024-12-01",
            "description": "Broken range",
        },
        headers=headers,
    )
    assert invalid.status_code == 422

    update = client.put(
        f"/api/v1/profile/education/{education_id}",
        json={"degree": "MEng", "description": "Updated description"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["degree"] == "MEng"

    delete_response = client.delete(f"/api/v1/profile/education/{education_id}", headers=headers)
    assert delete_response.status_code == 204


def test_experience_crud_and_current_employment(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    create = client.post(
        "/api/v1/profile/experience",
        json={
            "company": "OpenAI",
            "job_title": "Platform Engineer",
            "location": "Remote",
            "start_date": "2021-01-01",
            "end_date": None,
            "description": "Current role.",
        },
        headers=headers,
    )
    assert create.status_code == 201
    experience_id = create.json()["id"]

    invalid = client.post(
        "/api/v1/profile/experience",
        json={
            "company": "Bad Company",
            "job_title": "Engineer",
            "location": "Remote",
            "start_date": "2025-01-01",
            "end_date": "2024-12-01",
            "description": "Broken range",
        },
        headers=headers,
    )
    assert invalid.status_code == 422

    update = client.put(
        f"/api/v1/profile/experience/{experience_id}",
        json={"job_title": "Senior Platform Engineer"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["job_title"] == "Senior Platform Engineer"

    delete_response = client.delete(f"/api/v1/profile/experience/{experience_id}", headers=headers)
    assert delete_response.status_code == 204


def test_project_crud_and_url_validation(client: TestClient) -> None:
    register(client)
    headers = get_auth_header(client)

    create = client.post(
        "/api/v1/profile/projects",
        json={
            "name": "JobPilot AI",
            "description": "AI job matching platform.",
            "url": "https://example.com/project",
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
        },
        headers=headers,
    )
    assert create.status_code == 201
    project_id = create.json()["id"]

    invalid = client.post(
        "/api/v1/profile/projects",
        json={
            "name": "Broken project",
            "description": "Invalid URL",
            "url": "not-a-url",
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
        },
        headers=headers,
    )
    assert invalid.status_code == 422

    update = client.put(
        f"/api/v1/profile/projects/{project_id}",
        json={"name": "JobPilot AI v2"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "JobPilot AI v2"

    delete_response = client.delete(f"/api/v1/profile/projects/{project_id}", headers=headers)
    assert delete_response.status_code == 204


def test_users_cannot_access_another_users_professional_data(client: TestClient) -> None:
    register(client, "owner@example.com")
    register(client, "other@example.com")

    owner_headers = get_auth_header(client, "owner@example.com")
    other_headers = get_auth_header(client, "other@example.com")

    create = client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=owner_headers,
    )
    assert create.status_code == 201
    skill_id = create.json()["id"]

    other_list = client.get("/api/v1/profile/skills", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []

    other_update = client.put(
        f"/api/v1/profile/skills/{skill_id}",
        json={"name": "Hacking"},
        headers=other_headers,
    )
    assert other_update.status_code == 404

    other_delete = client.delete(f"/api/v1/profile/skills/{skill_id}", headers=other_headers)
    assert other_delete.status_code == 404
