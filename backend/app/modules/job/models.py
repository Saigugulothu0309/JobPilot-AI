"""Shared normalized job database entity."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Job(Base):
    """A normalized job listing shared across the application."""

    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_jobs_dedupe_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(300), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    external_job_id: Mapped[str | None] = mapped_column(String(300), index=True, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
