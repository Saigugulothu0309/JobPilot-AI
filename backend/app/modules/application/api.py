"""Authenticated application preparation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.activity.service import ActivityService
from app.modules.application.schemas import (
    ApplicationDraftApprovalRequest,
    ApplicationDraftCreateRequest,
    ApplicationDraftResponse,
    ApplicationDraftUpdateRequest,
    ApplicationRecordCreateRequest,
    ApplicationRecordResponse,
    ApplicationRecordUpdateRequest,
)
from app.modules.application.service import (
    ApplicationDraftApprovalError,
    ApplicationDraftNotFoundError,
    ApplicationDraftPreparationError,
    ApplicationDraftService,
    ApplicationRecordError,
    ApplicationRecordNotFoundError,
    ApplicationRecordService,
)
from app.modules.auth.models import User
from app.modules.notification.service import NotificationService
from app.security.auth import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/drafts", response_model=ApplicationDraftResponse)
def prepare_application_draft(
    payload: ApplicationDraftCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationDraftResponse:
    try:
        draft = ApplicationDraftService(session).prepare(
            current_user.id,
            payload.job_id,
            payload.resume_id,
        )
    except ApplicationDraftPreparationError as exc:
        detail = str(exc)
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="FAILURE",
            state="FAILED",
            message="Application draft preparation could not be completed.",
            details={
                "reason": detail,
                "next_action": "Correct the issue and retry preparation, or continue manually.",
            },
        )
        NotificationService(session).create_if_profile_for_user(
            current_user.id,
            notification_type="ACTION_FAILURE",
            title="Draft preparation needs attention",
            message=detail,
            dedupe_key=f"draft-failure:{payload.job_id}:{detail}",
        )
        code = (
            status.HTTP_404_NOT_FOUND
            if detail.endswith("not found")
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=detail) from exc
    return ApplicationDraftResponse.model_validate(draft)


@router.get("/drafts/{draft_id}", response_model=ApplicationDraftResponse)
def get_application_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationDraftResponse:
    try:
        draft = ApplicationDraftService(session).get_for_user(current_user.id, draft_id)
    except ApplicationDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApplicationDraftResponse.model_validate(draft)


@router.put("/drafts/{draft_id}", response_model=ApplicationDraftResponse)
def update_application_draft(
    draft_id: UUID,
    payload: ApplicationDraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationDraftResponse:
    try:
        draft = ApplicationDraftService(session).update_for_user(
            current_user.id,
            draft_id,
            payload.content,
        )
    except ApplicationDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ApplicationDraftApprovalError as exc:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="PAUSED",
            state="REVIEW_REQUIRED",
            message=(
                "Application draft editing is paused because the approved revision is immutable."
            ),
            details={
                "reason": str(exc),
                "next_action": "Prepare a new draft version before making changes.",
            },
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApplicationDraftResponse.model_validate(draft)


@router.post("/drafts/{draft_id}/approve", response_model=ApplicationDraftResponse)
def approve_application_draft(
    draft_id: UUID,
    payload: ApplicationDraftApprovalRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationDraftResponse:
    try:
        draft = ApplicationDraftService(session).approve_for_user(
            current_user.id,
            draft_id,
            payload.confirm,
        )
    except ApplicationDraftNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ApplicationDraftApprovalError as exc:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="PAUSED",
            state="REVIEW_REQUIRED",
            message="Application draft approval is paused until explicit confirmation is provided.",
            details={
                "reason": str(exc),
                "next_action": "Review the draft and confirm approval only if it is accurate.",
            },
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApplicationDraftResponse.model_validate(draft)


@router.post("/records", response_model=ApplicationRecordResponse)
def create_application_record(
    payload: ApplicationRecordCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationRecordResponse:
    try:
        record = ApplicationRecordService(session).create(
            current_user.id,
            job_id=payload.job_id,
            draft_id=payload.draft_id,
            status=payload.status,
            notes=payload.notes,
            applied_at=payload.applied_at,
            interview_at=payload.interview_at,
            follow_up_at=payload.follow_up_at,
        )
    except ApplicationRecordError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if str(exc).endswith("not found")
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return ApplicationRecordResponse.model_validate(record)


@router.get("/records", response_model=list[ApplicationRecordResponse])
def list_application_records(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[ApplicationRecordResponse]:
    records = ApplicationRecordService(session).list_for_user(current_user.id)
    return [ApplicationRecordResponse.model_validate(record) for record in records]


@router.get("/records/{record_id}", response_model=ApplicationRecordResponse)
def get_application_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationRecordResponse:
    try:
        record = ApplicationRecordService(session).get_for_user(current_user.id, record_id)
    except (ApplicationRecordNotFoundError, ApplicationRecordError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApplicationRecordResponse.model_validate(record)


@router.put("/records/{record_id}", response_model=ApplicationRecordResponse)
def update_application_record(
    record_id: UUID,
    payload: ApplicationRecordUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApplicationRecordResponse:
    try:
        record = ApplicationRecordService(session).update(
            current_user.id,
            record_id,
            status=payload.status,
            notes=payload.notes,
            applied_at=payload.applied_at,
            interview_at=payload.interview_at,
            follow_up_at=payload.follow_up_at,
            draft_id=payload.draft_id,
        )
    except (ApplicationRecordNotFoundError, ApplicationRecordError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ApplicationRecordError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if payload.status is not None:
        notification_type = "UNCERTAIN_STATUS" if record.status == "UNKNOWN" else "STATUS_CHANGED"
        message = (
            "Submission status unknown — verify manually."
            if record.status == "UNKNOWN"
            else f"Application tracking status is now {record.status}. This is a manual record."
        )
        NotificationService(session).create_if_profile_for_user(
            current_user.id,
            notification_type=notification_type,
            title="Application status needs review"
            if record.status == "UNKNOWN"
            else "Application status updated",
            message=message,
            dedupe_key=f"record-status:{record.id}:{record.status}",
            job_id=record.job_id,
            application_record_id=record.id,
        )
    return ApplicationRecordResponse.model_validate(record)
