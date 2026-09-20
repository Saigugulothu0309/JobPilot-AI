"""Persisted, unapproved application preparation drafts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApplicationDraft(Base):
    """A revisioned, user-owned draft prepared for one normalized job."""

    __tablename__ = "application_drafts"
    __table_args__ = (
        UniqueConstraint("profile_id", "job_id", name="uq_application_drafts_profile_job"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approved_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approval_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    profile_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    job_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApplicationRecord(Base):
    """A user-maintained application tracking record for one normalized job."""

    __tablename__ = "application_records"
    __table_args__ = (
        UniqueConstraint("profile_id", "job_id", name="uq_application_records_profile_job"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("application_drafts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SAVED")
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    draft_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
