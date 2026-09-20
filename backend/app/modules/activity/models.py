"""Persisted user-visible activity events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ActivityEvent(Base):
    """A user-scoped event describing a meaningful workflow state or action."""

    __tablename__ = "activity_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("application_drafts.id", ondelete="SET NULL"), nullable=True
    )
    application_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("application_records.id", ondelete="SET NULL"), nullable=True
    )
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
