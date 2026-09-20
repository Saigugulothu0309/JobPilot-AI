"""Authenticated resume management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.auth.models import User
from app.modules.resume.parser import ResumeParser
from app.modules.resume.schemas import (
    ResumeProcessingResponse,
    ResumeResponse,
    ResumeReviewData,
    ResumeReviewResponse,
)
from app.modules.resume.service import (
    ResumeNotFoundError,
    ResumeProcessingService,
    ResumeReviewError,
    ResumeReviewService,
    ResumeService,
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeResponse:
    try:
        resume = ResumeService(session).create_for_profile(current_user.id, file)
    except ValueError as exc:
        detail = str(exc)
        if "exceeds" in detail:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=detail,
            ) from exc
        if (
            "Unsupported" in detail
            or "MIME" in detail
            or "filename" in detail
            or "format" in detail
        ):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=detail,
            ) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=list[ResumeResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[ResumeResponse]:
    resumes = ResumeService(session).list_for_profile(current_user.id)
    return [ResumeResponse.model_validate(resume) for resume in resumes]


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeResponse:
    try:
        resume = ResumeService(session).get_for_profile(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResumeResponse.model_validate(resume)


@router.post("/{resume_id}/process", response_model=ResumeProcessingResponse)
def process_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeProcessingResponse:
    try:
        result = ResumeProcessingService(session).process_for_profile(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResumeProcessingResponse(
        resume_id=resume_id,
        status=result.status,
        text=result.text,
        character_count=result.character_count,
        page_count=result.page_count,
        extractor=result.extractor,
        error_code=result.error_code,
        error_message=result.error_message,
    )


@router.post("/{resume_id}/parse")
def parse_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    try:
        ResumeService(session).get_for_profile(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    processing = ResumeProcessingService(session).process_for_profile(current_user.id, resume_id)
    if not processing.success or not processing.text:
        return {
            "basic_information": None,
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "warnings": [processing.error_message or "Resume text could not be extracted."],
        }

    return ResumeParser().parse(processing.text).to_dict()


@router.get("/{resume_id}/review", response_model=ResumeReviewResponse)
def get_resume_review(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeReviewResponse:
    try:
        review = ResumeReviewService(session).get_review(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ResumeReviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return ResumeReviewResponse.model_validate(review)


@router.put("/{resume_id}/review", response_model=ResumeReviewResponse)
def update_resume_review(
    resume_id: UUID,
    payload: ResumeReviewData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeReviewResponse:
    try:
        review = ResumeReviewService(session).update_review(
            current_user.id,
            resume_id,
            payload.model_dump(),
        )
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ResumeReviewError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ResumeReviewResponse.model_validate(review)


@router.post("/{resume_id}/approve", response_model=ResumeReviewResponse)
def approve_resume_review(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ResumeReviewResponse:
    try:
        review = ResumeReviewService(session).approve_review(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ResumeReviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return ResumeReviewResponse.model_validate(review)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={status.HTTP_204_NO_CONTENT: {"description": "Resume deleted"}},
)
def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> None:
    try:
        ResumeService(session).delete_for_profile(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
