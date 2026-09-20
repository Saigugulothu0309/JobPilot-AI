import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app, create_application

client = TestClient(app)


def test_application_starts_with_expected_metadata() -> None:
    application = create_application()

    assert application.title == "JobPilot AI"
    assert application.version == "0.1.0"


def test_health_endpoint_returns_healthy() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "jobpilot-ai"}


def test_settings_load_optional_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "test-provider")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.ai_provider == "test-provider"
    assert settings.database_url is None
    get_settings.cache_clear()
