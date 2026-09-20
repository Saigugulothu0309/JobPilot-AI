"""Synchronous SQLAlchemy engine and session infrastructure."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine(database_url: str) -> Engine:
    """Create a reusable engine without opening a database connection."""
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory() -> sessionmaker[Session]:
    """Build the session factory when database-backed functionality is requested."""
    database_url = get_settings().database_url
    if database_url is None:
        raise RuntimeError("DATABASE_URL must be configured for database operations.")

    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a request-scoped database session for future API dependencies."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
