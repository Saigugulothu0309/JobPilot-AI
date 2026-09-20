from __future__ import annotations

from collections.abc import Generator
from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db_session
from app.main import app
from app.modules.auth.models import User
from app.modules.job.models import Job
from app.modules.profile.models import Education, Experience, Profile, Project, Skill


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


def register(client: TestClient, email: str = "user@example.com") -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def login(client: TestClient, email: str = "user@example.com") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def get_session(client: TestClient) -> Session:
    return next(app.dependency_overrides[get_db_session]())


def build_profile(session: Session, user: User, *, location: str | None = "Boston, MA") -> Profile:
    existing = session.scalar(select(Profile).where(Profile.user_id == user.id))
    if existing is not None:
        return existing
    profile = Profile(
        user_id=user.id,
        full_name="Jane Doe",
        location=location,
        headline="Backend Engineer",
        summary="Builds reliable systems and APIs.",
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def add_skill(session: Session, profile: Profile, name: str) -> Skill:
    skill = Skill(profile_id=profile.id, name=name, category="backend", proficiency="ADVANCED")
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return skill


def add_experience(
    session: Session,
    profile: Profile,
    *,
    job_title: str,
    company: str = "Example Co",
    location: str | None = "Boston, MA",
) -> Experience:
    experience = Experience(
        profile_id=profile.id,
        company=company,
        job_title=job_title,
        location=location,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 1, 1),
        description="Built platform infrastructure.",
    )
    session.add(experience)
    session.commit()
    session.refresh(experience)
    return experience


def add_education(
    session: Session,
    profile: Profile,
    *,
    institution: str,
    degree: str,
    field_of_study: str = "Computer Science",
) -> Education:
    education = Education(
        profile_id=profile.id,
        institution=institution,
        degree=degree,
        field_of_study=field_of_study,
        start_date=date(2016, 9, 1),
        end_date=date(2020, 6, 1),
    )
    session.add(education)
    session.commit()
    session.refresh(education)
    return education


def add_project(session: Session, profile: Profile, *, name: str) -> Project:
    project = Project(
        profile_id=profile.id,
        name=name,
        description="Built a service using Python and FastAPI.",
        url="https://example.com/project",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 6, 1),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def add_job(
    session: Session,
    *,
    title: str,
    company: str,
    location: str | None = "Remote",
    description: str | None = None,
) -> Job:
    job = Job(
        title=title,
        company=company,
        location=location,
        description=description or "Build durable software for production workloads.",
        employment_type="FULL_TIME",
        source="local",
        external_job_id=str(uuid4()),
        external_url="https://jobs.example.test/role",
        dedupe_key=f"test-{uuid4().hex}",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_matching_strong_skill_match_and_explainability(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    for skill_name in ("Python", "FastAPI", "PostgreSQL", "SQL"):
        add_skill(session, profile, skill_name)
    job = add_job(
        session,
        title="Senior Python Engineer",
        company="Example Co",
        location="Boston, MA",
        description="Build APIs with Python, FastAPI, SQL, and PostgreSQL.",
    )
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_score"] >= 60
    assert "Python" in payload["matched_skills"]
    assert payload["positive_reasons"]
    assert payload["potential_concerns"]
    assert payload["job"]["title"] == "Senior Python Engineer"


def test_matching_handles_partial_skill_match(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    job = add_job(
        session,
        title="JavaScript Engineer",
        company="Example Co",
        location="Remote",
        description="Build Node.js and JavaScript services.",
    )
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_score"] < 75
    assert payload["missing_skills"]


def test_matching_handles_no_skill_match(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    job = add_job(
        session,
        title="Graphic Designer",
        company="Example Co",
        location="Remote",
        description="Create design systems and marketing visuals.",
    )
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_skills"] == []
    assert payload["overall_score"] < 20


def test_matching_normalizes_skill_variants(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "React.js")
    add_skill(session, profile, "PostgreSQL")
    job = add_job(
        session,
        title="Frontend Engineer",
        company="Example Co",
        location="Remote",
        description="Build React apps and use Postgres for data storage.",
    )
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_skills"]
    assert any(skill.startswith("React") or skill == "React" for skill in payload["matched_skills"])
    assert any(skill.startswith("Postgres") or skill.startswith("Postgre") for skill in payload["matched_skills"])


def test_matching_title_relevance_and_experience_are_used(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    add_skill(session, profile, "FastAPI")
    add_experience(session, profile, job_title="Senior Backend Engineer", company="Acme")
    job = add_job(
        session,
        title="Backend Engineer",
        company="Example Co",
        location="Boston, MA",
        description="Build Python APIs with FastAPI and data processing.",
    )
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200
    assert response.json()["overall_score"] >= 60


def test_matching_requires_approved_candidate_data(client: TestClient) -> None:
    register(client)
    headers = login(client)

    job = add_job(
        next(app.dependency_overrides[get_db_session]()),
        title="Platform Engineer",
        company="Example Co",
        location="Remote",
        description="Build APIs and deploy services.",
    )

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Approved candidate data not found for user"


def test_matching_missing_job_is_not_found(client: TestClient) -> None:
    register(client)
    headers = login(client)
    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    session.close()

    missing_id = "12345678-1234-4234-8234-123456789abc"
    response = client.post(f"/api/v1/jobs/{missing_id}/match", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_matching_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/jobs/12345678-1234-4234-8234-123456789abc/match")
    assert response.status_code == 401


def test_matching_isolated_between_users(client: TestClient) -> None:
    register(client, "first@example.com")
    register(client, "second@example.com")
    first_headers = login(client, "first@example.com")
    second_headers = login(client, "second@example.com")

    session = get_session(client)
    first_user = session.scalar(select(User).where(User.email == "first@example.com"))
    second_user = session.scalar(select(User).where(User.email == "second@example.com"))
    assert first_user is not None
    assert second_user is not None
    first_profile = build_profile(session, first_user)
    second_profile = build_profile(session, second_user)
    add_skill(session, first_profile, "Python")
    add_skill(session, second_profile, "Java")
    job = add_job(
        session,
        title="Backend Engineer",
        company="Example Co",
        location="Remote",
        description="Use Python APIs and backend services.",
    )
    session.close()

    first_response = client.post(f"/api/v1/jobs/{job.id}/match", headers=first_headers)
    second_response = client.post(f"/api/v1/jobs/{job.id}/match", headers=second_headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["overall_score"] > second_response.json()["overall_score"]


def test_matching_uses_approved_profile_data_not_unapproved_resume_review_data(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    job = add_job(
        session,
        title="Data Engineer",
        company="Example Co",
        location="Boston, MA",
        description="Use Python and SQL for analytics.",
    )
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "Python" in payload["matched_skills"]
    assert payload["overall_score"] > 0


def test_matching_is_deterministic_and_explainable(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    add_skill(session, profile, "FastAPI")
    add_experience(session, profile, job_title="Senior Backend Engineer", company="Acme")
    add_education(session, profile, institution="University of London", degree="BSc")
    add_project(session, profile, name="JobPilot AI")
    job = add_job(
        session,
        title="Backend Engineer",
        company="Example Co",
        location="Boston, MA",
        description="Build Python APIs with FastAPI and data processing.",
    )
    session.close()

    first = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    second = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["positive_reasons"]
    assert first.json()["potential_concerns"]
    assert "missing_skills" in first.json()


def test_matching_no_database_writes_are_triggered(client: TestClient) -> None:
    register(client)
    headers = login(client)

    session = get_session(client)
    user = session.scalar(select(User))
    assert user is not None
    profile = build_profile(session, user)
    add_skill(session, profile, "Python")
    job = add_job(
        session,
        title="Python Engineer",
        company="Example Co",
        location="Remote",
        description="Work with Python and APIs.",
    )
    before_jobs = session.scalar(select(func.count()).select_from(Job))
    before_skills = session.scalar(select(func.count()).select_from(Skill))
    session.close()

    response = client.post(f"/api/v1/jobs/{job.id}/match", headers=headers)
    assert response.status_code == 200

    session = get_session(client)
    after_jobs = session.scalar(select(func.count()).select_from(Job))
    after_skills = session.scalar(select(func.count()).select_from(Skill))
    session.close()

    assert before_jobs == after_jobs
    assert before_skills == after_skills
