"""Authenticated owner-scoped opportunity feedback endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.auth.models import User
from app.modules.feedback.schemas import (
    FeedbackProposalCreateRequest,
    FeedbackProposalResponse,
    JobFeedbackCreateRequest,
    JobFeedbackResponse,
)
from app.modules.feedback.service import (
    FeedbackConflictError,
    FeedbackError,
    FeedbackNotFoundError,
    JobFeedbackService,
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=JobFeedbackResponse)
def create_job_feedback(
    payload: JobFeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobFeedbackResponse:
    try:
        feedback = JobFeedbackService(session).create_or_update(
            current_user.id,
            job_id=payload.job_id,
            feedback_type=payload.feedback_type,
            note=payload.note,
        )
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeedbackError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JobFeedbackResponse.model_validate(feedback)


@router.get("", response_model=list[JobFeedbackResponse])
def list_job_feedback(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[JobFeedbackResponse]:
    try:
        feedback = JobFeedbackService(session).list_for_user(current_user.id, limit, offset)
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [JobFeedbackResponse.model_validate(item) for item in feedback]


@router.get("/proposals", response_model=list[FeedbackProposalResponse])
def list_feedback_proposals(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[FeedbackProposalResponse]:
    try:
        proposals = JobFeedbackService(session).list_proposals_for_user(
            current_user.id, limit, offset
        )
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [FeedbackProposalResponse.model_validate(item) for item in proposals]


@router.post("/proposals", response_model=FeedbackProposalResponse)
def create_feedback_proposal(
    payload: FeedbackProposalCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FeedbackProposalResponse:
    try:
        proposal = JobFeedbackService(session).create_proposal(
            current_user.id,
            feedback_id=payload.feedback_id,
            target_type=payload.target_type,
            target_field=payload.target_field,
            proposed_value=payload.proposed_value,
        )
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (FeedbackConflictError, FeedbackError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return FeedbackProposalResponse.model_validate(proposal)


@router.post("/proposals/{proposal_id}/confirm", response_model=FeedbackProposalResponse)
def confirm_feedback_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FeedbackProposalResponse:
    try:
        proposal = JobFeedbackService(session).confirm_proposal(current_user.id, proposal_id)
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (FeedbackConflictError, FeedbackError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return FeedbackProposalResponse.model_validate(proposal)


@router.post("/proposals/{proposal_id}/reject", response_model=FeedbackProposalResponse)
def reject_feedback_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FeedbackProposalResponse:
    try:
        proposal = JobFeedbackService(session).reject_proposal(current_user.id, proposal_id)
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (FeedbackConflictError, FeedbackError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return FeedbackProposalResponse.model_validate(proposal)


@router.post("/proposals/{proposal_id}/revoke", response_model=FeedbackProposalResponse)
def revoke_feedback_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FeedbackProposalResponse:
    try:
        proposal = JobFeedbackService(session).revoke_proposal(current_user.id, proposal_id)
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (FeedbackConflictError, FeedbackError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return FeedbackProposalResponse.model_validate(proposal)


@router.post(
    "/proposals/{proposal_id}/{action}",
    response_model=FeedbackProposalResponse,
    include_in_schema=False,
)
def act_on_feedback_proposal(
    proposal_id: UUID,
    action: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FeedbackProposalResponse:
    if action == "confirm":
        return confirm_feedback_proposal(proposal_id, current_user, session)
    if action == "reject":
        return reject_feedback_proposal(proposal_id, current_user, session)
    if action == "revoke":
        return revoke_feedback_proposal(proposal_id, current_user, session)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported proposal action: {action}",
    )

