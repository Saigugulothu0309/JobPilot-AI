"""Owner-scoped one-time feedback for normalized jobs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class JobFeedback(Base):
    """A user correction or signal that does not alter durable preferences."""

    __tablename__ = "job_feedback"
    __table_args__ = (
        UniqueConstraint("profile_id", "job_id", "feedback_type", name="uq_job_feedback_signal"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="USER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FeedbackProposal(Base):
    """A reviewed, explicit proposal derived from user feedback."""

    __tablename__ = "feedback_proposals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_feedback.id", ondelete="CASCADE"), index=True
    )
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_field: Mapped[str | None] = mapped_column(String(50), nullable=True)
    previous_value: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    proposed_value: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    applied_skill_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("skills.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
