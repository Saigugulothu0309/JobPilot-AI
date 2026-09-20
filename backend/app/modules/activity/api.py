"""Authenticated activity and audit history endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.activity.schemas import ActivityEventResponse
from app.modules.activity.service import ActivityProfileNotFoundError, ActivityService
from app.modules.auth.models import User
from app.security.auth import get_current_user

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityEventResponse])
def list_activity(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[ActivityEventResponse]:
    try:
        events, _ = ActivityService(session).list_for_user(current_user.id, limit, offset)
    except ActivityProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [ActivityEventResponse.model_validate(event) for event in events]
