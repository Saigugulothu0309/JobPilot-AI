from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import get_db_session
from app.main import app
from app.modules.job.models import Job
from app.modules.job.service import JobService
from app.modules.job.sources import JobSourceError, LocalJobSource


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


def register(client: TestClient, email: str = "user@example.com") -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201


def get_auth_header(client: TestClient, email: str = "user@example.com") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def ingest_jobs(
    client: TestClient,
    jobs: list[dict[str, object]],
) -> None:
    get_settings.cache_clear()
    response = client.post(
        "/api/v1/jobs/ingest/local",
        json={"jobs": jobs},
        headers=get_auth_header(client),
    )
    assert response.status_code == 200


def local_job(
    *,
    external_job_id: str | None = "job-1",
    title: str = "Backend Engineer",
    company: str = "Example Co",
    location: str | None = "Remote",
) -> dict[str, object]:
    return {
        "title": title,
        "company": company,
        "location": location,
        "description": "Build reliable backend services.",
        "employment_type": "FULL_TIME",
        "external_job_id": external_job_id,
        "external_url": "https://jobs.example.test/job-1",
        "posted_at": "2026-09-01T10:00:00Z",
    }


def test_local_source_produces_normalized_job_data() -> None:
    normalized = LocalJobSource([local_job()]).normalize_job(local_job())

    assert normalized.source == "local"
    assert normalized.title == "Backend Engineer"
    assert normalized.external_job_id == "job-1"
    assert normalized.dedupe_key


def test_local_source_rejects_malformed_source_data() -> None:
    with pytest.raises(JobSourceError):
        LocalJobSource([{"title": "Missing description"}]).normalize_job(
            {"title": "Missing description"}
        )


def test_job_service_persists_attribution_and_deduplicates() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        source = LocalJobSource([local_job(), local_job()])
        first = JobService(session).ingest(source)
        second = JobService(session).ingest(source)

        assert first.created_count == 1
        assert second.created_count == 0
        assert second.updated_count == 1
        jobs = session.scalars(select(Job)).all()
        assert len(jobs) == 1
        assert jobs[0].source == "local"
        assert jobs[0].external_job_id == "job-1"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_different_external_jobs_and_fallback_jobs_remain_distinct() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        jobs = [
            local_job(external_job_id="job-1"),
            local_job(external_job_id="job-2", title="Data Engineer"),
            local_job(external_job_id=None, title="Fallback Role", company="Other Co"),
            local_job(external_job_id=None, title="Fallback Role", company="Other Co"),
        ]
        result = JobService(session).ingest(LocalJobSource(jobs))

        assert result.created_count == 3
        assert len(session.scalars(select(Job)).all()) == 3
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_missing_optional_source_fields_are_persisted_as_none() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        record = local_job(external_job_id=None, location=None)
        record["employment_type"] = None
        record["external_url"] = None
        record["posted_at"] = None
        JobService(session).ingest(LocalJobSource([record]))
        job = session.scalar(select(Job))

        assert job is not None
        assert job.location is None
        assert job.external_job_id is None
        assert job.external_url is None
        assert job.posted_at is None
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_ingestion_api_requires_authentication_and_admin_access(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"jobs": [local_job()]}
    assert client.post("/api/v1/jobs/ingest/local", json=payload).status_code == 401

    register(client)
    headers = get_auth_header(client)
    assert (
        client.post("/api/v1/jobs/ingest/local", json=payload, headers=headers).status_code
        == 403
    )

    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    get_settings.cache_clear()
    response = client.post("/api/v1/jobs/ingest/local", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["source"] == "local"
    assert response.json()["created_count"] == 1
    assert response.json()["jobs"][0]["company"] == "Example Co"
    assert response.json()["jobs"][0]["source_job_id"] == "job-1"
    assert response.json()["jobs"][0]["url"] == "https://jobs.example.test/job-1"


def test_ingestion_api_rejects_malformed_jobs(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    get_settings.cache_clear()
    register(client)
    headers = get_auth_header(client)

    response = client.post(
        "/api/v1/jobs/ingest/local",
        json={"jobs": [{"title": "Missing description"}]},
        headers=headers,
    )

    assert response.status_code == 422


def test_job_search_returns_empty_database(client: TestClient) -> None:
    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert response.json() == {"jobs": [], "total": 0, "limit": 20, "offset": 0}


def test_job_search_supports_keyword_and_multiple_matches(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    ingest_jobs(
        client,
        [
            {
                **local_job(external_job_id="python-1", title="Python Engineer"),
                "description": "Build Python APIs.",
            },
            {
                **local_job(external_job_id="python-2", title="Data Engineer"),
                "description": "Use Python and SQL for analytics.",
            },
            local_job(external_job_id="other", title="Frontend Engineer"),
        ],
    )

    response = client.get("/api/v1/jobs", params={"keyword": "python"})

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["jobs"]) == 2


def test_job_search_supports_company_location_and_source_filters(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    ingest_jobs(
        client,
        [
            local_job(external_job_id="one", company="Acme", location="Remote"),
            local_job(external_job_id="two", company="Beta", location="London"),
        ],
    )

    assert client.get("/api/v1/jobs", params={"company": "acme"}).json()["total"] == 1
    assert client.get("/api/v1/jobs", params={"location": "london"}).json()["total"] == 1
    assert client.get("/api/v1/jobs", params={"source": "LOCAL"}).json()["total"] == 2
    assert client.get("/api/v1/jobs", params={"source": "missing"}).json()["jobs"] == []


def test_job_search_paginates_and_orders_deterministically(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    ingest_jobs(
        client,
        [
            local_job(external_job_id="one", title="First"),
            local_job(external_job_id="two", title="Second"),
            local_job(external_job_id="three", title="Third"),
        ],
    )

    first = client.get("/api/v1/jobs", params={"limit": 2, "offset": 0}).json()
    second = client.get("/api/v1/jobs", params={"limit": 2, "offset": 2}).json()
    repeated = client.get("/api/v1/jobs", params={"limit": 2, "offset": 0}).json()

    assert first["total"] == 3
    assert len(first["jobs"]) == 2
    assert len(second["jobs"]) == 1
    assert [job["id"] for job in first["jobs"]] == [job["id"] for job in repeated["jobs"]]
    assert set(job["id"] for job in first["jobs"]).isdisjoint(
        job["id"] for job in second["jobs"]
    )


def test_job_search_rejects_malformed_query_parameters(client: TestClient) -> None:
    assert client.get("/api/v1/jobs", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/jobs", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/jobs", params={"offset": -1}).status_code == 422
    assert client.get("/api/v1/jobs", params={"keyword": ""}).status_code == 422


def test_job_ranking_uses_preferences_and_keeps_hard_conflicts_separate(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    headers = get_auth_header(client)
    profile = client.put(
        "/api/v1/profile",
        json={"headline": "Backend Engineer", "location": "Boston, MA"},
        headers=headers,
    )
    assert profile.status_code == 200
    skill = client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=headers,
    )
    assert skill.status_code == 201
    preferences = client.put(
        "/api/v1/profile/preferences",
        json={
            "target_roles": ["Backend Engineer"],
            "work_modes": ["REMOTE"],
            "technologies": ["Python"],
            "hard_constraints": ["Remote only"],
        },
        headers=headers,
    )
    assert preferences.status_code == 200
    ingest_jobs(
        client,
        [
            {
                **local_job(external_job_id="remote-python", title="Backend Engineer"),
                "description": "Required Python APIs. Remote role.",
            },
            {
                **local_job(
                    external_job_id="onsite-java",
                    title="Java Engineer",
                    location="Boston, MA",
                ),
                "description": "Required Java services. On-site role.",
            },
        ],
    )

    response = client.get("/api/v1/jobs/rank", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["preference_state"] == "CONFIGURED"
    assert payload["total"] == 2
    assert payload["jobs"][0]["match"]["job"]["external_job_id"] == "remote-python"
    assert payload["jobs"][0]["rank"] == 1
    assert payload["jobs"][1]["eligibility"] == "NOT_RECOMMENDED"
    assert any("explicit user exclusion" in reason for reason in payload["jobs"][1]["reasons"])


def test_job_ranking_is_deterministic_and_read_only(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    headers = get_auth_header(client)
    profile = client.put(
        "/api/v1/profile",
        json={"headline": "Python Engineer", "location": "Remote"},
        headers=headers,
    )
    assert profile.status_code == 200
    skill = client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "backend", "proficiency": "ADVANCED"},
        headers=headers,
    )
    assert skill.status_code == 201
    ingest_jobs(
        client,
        [
            {
                **local_job(external_job_id="one", title="Python Engineer"),
                "description": "Build Python services.",
            },
            {
                **local_job(external_job_id="two", title="Data Engineer"),
                "description": "Build data services.",
            },
        ],
    )
    before = client.get("/api/v1/jobs").json()
    first = client.get("/api/v1/jobs/rank", headers=headers)
    second = client.get("/api/v1/jobs/rank", headers=headers)
    after = client.get("/api/v1/jobs").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert before == after


def test_job_ranking_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/jobs/rank").status_code == 401


def test_job_analysis_extracts_structured_requirements_and_uncertainty(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    ingest_jobs(
        client,
        [
            {
                **local_job(title="Backend Engineer", location="Boston, MA"),
                "description": (
                    "Required skills: Python and FastAPI. Preferred: Docker. "
                    "Must have 2+ years of experience. Bachelor's degree in Computer Science "
                    "or equivalent experience. Hybrid role with Boston office attendance."
                ),
            }
        ],
    )

    jobs = client.get("/api/v1/jobs").json()["jobs"]
    job_id = jobs[0]["id"]
    response = client.post(f"/api/v1/jobs/{job_id}/analyze", headers=get_auth_header(client))

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "Backend Engineer"
    assert "Python" in payload["required_skills"]
    assert "FastAPI" in payload["required_skills"]
    assert "Docker" in payload["preferred_skills"]
    assert payload["experience_requirement"] == "2+ years of experience"
    assert "Bachelor's degree in Computer Science" in payload["education_requirement"]
    assert payload["work_mode"] == "hybrid"
    assert payload["employment_type"] == "FULL_TIME"
    assert payload["important_requirements"]
    assert "The posting allows an equivalent qualification or experience path." in payload[
        "ambiguities"
    ]
    assert "The posting contains both required and preferred qualification language." in payload[
        "ambiguities"
    ]


def test_job_analysis_represents_missing_information_as_unknown(client: TestClient) -> None:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    try:
        register(client)
        ingest_jobs(
            client,
            [
                {
                    **local_job(title="General Assistant", location=None),
                    "description": "Support the team and learn on the job.",
                    "employment_type": None,
                }
            ],
        )
        job_id = client.get("/api/v1/jobs").json()["jobs"][0]["id"]
        response = client.post(
            f"/api/v1/jobs/{job_id}/analyze",
            headers=get_auth_header(client),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["work_mode"] == "unknown"
        assert payload["employment_type"] is None
        assert "Location is not provided." in payload["unknowns"]
        assert "Work mode is not specified." in payload["unknowns"]
        assert "Experience requirement is not clearly specified." in payload["unknowns"]
        assert "Education requirement is not clearly specified." in payload["unknowns"]
        assert "Required skills are not clearly specified." in payload["unknowns"]
    finally:
        monkeypatch.undo()


def test_job_analysis_requires_authentication_and_handles_missing_jobs(client: TestClient) -> None:
    missing_id = "12345678-1234-4234-8234-123456789abc"
    assert client.post(f"/api/v1/jobs/{missing_id}/analyze").status_code == 401

    register(client)
    response = client.post(
        f"/api/v1/jobs/{missing_id}/analyze",
        headers=get_auth_header(client),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_job_analysis_is_deterministic_and_read_only(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JOB_INGESTION_ADMIN_EMAILS", "user@example.com")
    register(client)
    ingest_jobs(
        client,
        [
            {
                **local_job(title="Python Engineer"),
                "description": "Required: Python. Preferred: Docker. Remote role.",
            }
        ],
    )
    headers = get_auth_header(client)
    before = client.get("/api/v1/jobs").json()
    job_id = before["jobs"][0]["id"]

    first = client.post(f"/api/v1/jobs/{job_id}/analyze", headers=headers)
    second = client.post(f"/api/v1/jobs/{job_id}/analyze", headers=headers)
    after = client.get("/api/v1/jobs").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert before == after
