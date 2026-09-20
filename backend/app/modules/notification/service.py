"""Owner-scoped in-app notification persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.notification.models import Notification
from app.modules.profile.models import Profile


class NotificationNotFoundError(RuntimeError):
    """Raised when a notification is not owned by the requesting user."""


class NotificationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_for_profile(
        self,
        profile_id: UUID,
        *,
        notification_type: str,
        title: str,
        message: str,
        dedupe_key: str,
        job_id: UUID | None = None,
        draft_id: UUID | None = None,
        application_record_id: UUID | None = None,
    ) -> Notification:
        existing = self.session.scalar(
            select(Notification).where(
                Notification.profile_id == profile_id,
                Notification.dedupe_key == dedupe_key,
            )
        )
        if existing is not None:
            return existing
        notification = Notification(
            profile_id=profile_id,
            notification_type=notification_type,
            title=title,
            message=message,
            dedupe_key=dedupe_key,
            job_id=job_id,
            draft_id=draft_id,
            application_record_id=application_record_id,
        )
        self.session.add(notification)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(
                select(Notification).where(
                    Notification.profile_id == profile_id,
                    Notification.dedupe_key == dedupe_key,
                )
            )
            if existing is None:
                raise
            return existing
        self.session.refresh(notification)
        return notification

    def create_if_profile_for_user(self, user_id: UUID, **kwargs: object) -> Notification | None:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            return None
        return self.create_for_profile(profile.id, **kwargs)  # type: ignore[arg-type]

    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> list[Notification]:
        profile = self._profile(user_id)
        return list(
            self.session.scalars(
                select(Notification)
                .where(Notification.profile_id == profile.id)
                .order_by(Notification.created_at.desc(), Notification.id.asc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def mark_read_for_user(self, user_id: UUID, notification_id: UUID) -> Notification:
        profile = self._profile(user_id)
        notification = self.session.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.profile_id == profile.id,
            )
        )
        if notification is None:
            raise NotificationNotFoundError("Notification not found")
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(notification)
        return notification

    def _profile(self, user_id: UUID) -> Profile:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise NotificationNotFoundError("Notification not found")
        return profile
