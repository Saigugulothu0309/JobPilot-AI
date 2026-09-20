"""Environment-backed application configuration."""

from dataclasses import dataclass, field
from functools import lru_cache
from os import getenv


@dataclass(frozen=True)
class Settings:
    """Optional service configuration required by future integrations."""

    app_env: str = field(default_factory=lambda: getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: getenv("LOG_LEVEL", "INFO"))
    database_url: str | None = field(default_factory=lambda: getenv("DATABASE_URL"), repr=False)
    redis_url: str | None = field(default_factory=lambda: getenv("REDIS_URL"), repr=False)
    ai_provider: str | None = field(default_factory=lambda: getenv("AI_PROVIDER"))
    ai_api_key: str | None = field(default_factory=lambda: getenv("AI_API_KEY"), repr=False)
    auth_secret: str | None = field(default_factory=lambda: getenv("AUTH_SECRET"), repr=False)
    auth_token_expire_minutes: int = field(
        default_factory=lambda: int(getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))
    )
    resume_storage_path: str = field(
        default_factory=lambda: getenv("RESUME_STORAGE_PATH", "storage/resumes")
    )
    job_ingestion_admin_emails: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            email.strip().lower()
            for email in getenv("JOB_INGESTION_ADMIN_EMAILS", "").split(",")
            if email.strip()
        )
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached configuration without requiring optional services."""
    return Settings()
