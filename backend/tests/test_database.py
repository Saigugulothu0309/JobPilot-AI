import pytest

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import get_engine, get_session_factory


def test_database_configuration_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user@localhost:5432/jobpilot")
    get_settings.cache_clear()

    assert get_settings().database_url is not None

    get_settings.cache_clear()


def test_metadata_initializes_with_user_and_profile_tables() -> None:
    expected = {
        "profiles",
        "users",
        "skills",
        "education",
        "experience",
        "projects",
        "resumes",
        "jobs",
        "career_preferences",
        "application_drafts",
        "application_records",
        "activity_events",
        "notifications",
        "job_feedback",
        "feedback_proposals",
    }
    assert set(Base.metadata.tables) == expected


def test_session_factory_constructs_without_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = "postgresql+psycopg://user@localhost:5432/jobpilot"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    get_engine.cache_clear()

    session_factory = get_session_factory()
    session = session_factory()

    assert str(session.bind.url) == database_url
    session.close()
    get_engine.cache_clear()
    get_settings.cache_clear()
