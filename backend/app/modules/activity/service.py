"""Activity event persistence and owner-scoped retrieval."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.activity.models import ActivityEvent
from app.modules.profile.models import Profile


class ActivityProfileNotFoundError(RuntimeError):
    """Raised when activity is requested for a user without a profile."""


class ActivityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_for_profile(
        self,
        profile_id: UUID,
        *,
        event_type: str,
        state: str,
        message: str,
        job_id: UUID | None = None,
        draft_id: UUID | None = None,
        application_record_id: UUID | None = None,
        details: dict[str, object] | None = None,
    ) -> ActivityEvent:
        event = ActivityEvent(
            profile_id=profile_id,
            event_type=event_type,
            state=state,
            message=message,
            job_id=job_id,
            draft_id=draft_id,
            application_record_id=application_record_id,
            details=details or {},
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def record_for_user(
        self,
        user_id: UUID,
        *,
        event_type: str,
        state: str,
        message: str,
        job_id: UUID | None = None,
        draft_id: UUID | None = None,
        application_record_id: UUID | None = None,
        details: dict[str, object] | None = None,
    ) -> ActivityEvent:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise ActivityProfileNotFoundError("Profile not found")
        return self.record_for_profile(
            profile.id,
            event_type=event_type,
            state=state,
            message=message,
            job_id=job_id,
            draft_id=draft_id,
            application_record_id=application_record_id,
            details=details,
        )

    def record_if_profile_for_user(
        self,
        user_id: UUID,
        **kwargs: object,
    ) -> ActivityEvent | None:
        """Record activity only when the actor has an owned profile.

        Some read-only job operations remain available before profile creation.  Their
        successful result must not become a failure merely because there is no private
        activity timeline to attach it to.
        """
        try:
            return self.record_for_user(user_id, **kwargs)  # type: ignore[arg-type]
        except ActivityProfileNotFoundError:
            return None

    def list_for_user(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[ActivityEvent], int]:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise ActivityProfileNotFoundError("Profile not found")
        base_query = select(ActivityEvent).where(ActivityEvent.profile_id == profile.id)
        total = self.session.scalar(
            select(func.count()).select_from(ActivityEvent).where(
                ActivityEvent.profile_id == profile.id
            )
        )
        events = list(
            self.session.scalars(
                base_query.order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.asc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return events, int(total or 0)
