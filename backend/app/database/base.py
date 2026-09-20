"""SQLAlchemy declarative metadata for future database models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for future mapped entities."""
