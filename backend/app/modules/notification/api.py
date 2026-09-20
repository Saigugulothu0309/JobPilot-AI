"""Authenticated private in-app notification endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.auth.models import User
from app.modules.notification.schemas import NotificationResponse
from app.modules.notification.service import NotificationNotFoundError, NotificationService
from app.security.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[NotificationResponse]:
    notifications = NotificationService(session).list_for_user(current_user.id, limit, offset)
    return [NotificationResponse.model_validate(item) for item in notifications]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> NotificationResponse:
    try:
        notification = NotificationService(session).mark_read_for_user(
            current_user.id, notification_id
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return NotificationResponse.model_validate(notification)
