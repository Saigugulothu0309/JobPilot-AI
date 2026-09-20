"""Persisted, owner-scoped in-app notifications."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Notification(Base):
    """A private notification about a meaningful workflow event."""

    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("profile_id", "dedupe_key", name="uq_notifications_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(200), nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("application_drafts.id", ondelete="SET NULL"), nullable=True
    )
    application_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("application_records.id", ondelete="SET NULL"), nullable=True
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
