"""Shared FastAPI dependency providers."""

from app.core.config import Settings, get_settings


def get_application_settings() -> Settings:
    """Provide application configuration to routes that explicitly need it."""
    return get_settings()
