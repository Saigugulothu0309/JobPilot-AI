"""Authenticated, admin-controlled local job ingestion endpoint."""

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db_session
from app.modules.activity.service import ActivityService
from app.modules.auth.models import User
from app.modules.job.analysis import JobAnalysisService
from app.modules.job.matching import CandidateDataNotFoundError, JobMatchingService
from app.modules.job.ranking import JobRankingService
from app.modules.job.schemas import (
    JobAnalysisResponse,
    JobIngestionResponse,
    JobRankingResponse,
    JobResponse,
    JobSearchResponse,
    LocalJobIngestionRequest,
    MatchResponse,
    RankedJobResponse,
)
from app.modules.job.service import JobService
from app.modules.job.sources import JobSourceError, LocalJobSource
from app.modules.profile.service import ProfileNotFoundError, ProfileService
from app.security.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobSearchResponse)
def search_jobs(
    keyword: str | None = Query(default=None, min_length=1, max_length=200),
    q: str | None = Query(default=None, min_length=1, max_length=200),
    company: str | None = Query(default=None, min_length=1, max_length=300),
    location: str | None = Query(default=None, min_length=1, max_length=300),
    source: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
) -> JobSearchResponse:
    result = JobService(session).search(
        keyword=keyword or q,
        company=company,
        location=location,
        source=source,
        limit=limit,
        offset=offset,
    )
    return JobSearchResponse(
        jobs=[JobResponse.model_validate(job) for job in result.jobs],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def _require_ingestion_admin(current_user: User) -> None:
    if current_user.email.casefold() not in get_settings().job_ingestion_admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job ingestion is not permitted",
        )


@router.post("/ingest/local", response_model=JobIngestionResponse)
def ingest_local_jobs(
    payload: LocalJobIngestionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobIngestionResponse:
    _require_ingestion_admin(current_user)
    try:
        result = JobService(session).ingest(LocalJobSource(payload.jobs))
    except JobSourceError as exc:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="FAILURE",
            state="FAILED",
            message="Opportunity input could not be normalized.",
            details={
                "reason": str(exc),
                "next_action": "Correct the opportunity input and try again.",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    ActivityService(session).record_if_profile_for_user(
        current_user.id,
        event_type="OPPORTUNITY_INPUT",
        state="COMPLETED",
        message="Opportunity input was normalized and saved.",
        details={
            "source": result.source,
            "created_count": result.created_count,
            "updated_count": result.updated_count,
            "next_action": "Review the saved opportunities before matching or drafting.",
        },
    )
    return JobIngestionResponse(
        source=result.source,
        jobs=[JobResponse.model_validate(job) for job in result.jobs],
        created_count=result.created_count,
        updated_count=result.updated_count,
    )


@router.post("/{job_id}/match", response_model=MatchResponse)
def evaluate_job_match(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> MatchResponse:
    job = JobService(session).get_by_id(job_id)
    if job is None:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="FAILURE",
            state="FAILED",
            message="Job matching could not start because the opportunity was not found.",
            details={"next_action": "Choose an available opportunity and try again."},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    try:
        result = JobMatchingService(session).match_user_to_job(current_user.id, job)
    except CandidateDataNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approved candidate data not found for user",
        ) from exc

    ActivityService(session).record_if_profile_for_user(
        current_user.id,
        event_type="MATCHING",
        state="COMPLETED",
        message="Job match analysis is ready for review.",
        job_id=job.id,
        details={
            "overall_score": result.overall_score,
            "next_action": "Review match reasons, concerns, and missing skills.",
        },
    )
    if result.potential_concerns or result.missing_skills:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="WARNING",
            state="REVIEW_REQUIRED",
            message="The job match includes concerns or missing evidence that need review.",
            job_id=job.id,
            details={
                "potential_concerns": result.potential_concerns,
                "missing_skills": result.missing_skills,
                "next_action": "Review the concerns; do not treat them as disqualifying facts.",
            },
        )

    return MatchResponse.model_validate(asdict(result))


@router.post("/{job_id}/analyze", response_model=JobAnalysisResponse)
def analyze_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobAnalysisResponse:
    job = JobService(session).get_by_id(job_id)
    if job is None:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="FAILURE",
            state="FAILED",
            message="Job analysis could not start because the opportunity was not found.",
            details={"next_action": "Choose an available opportunity and try again."},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    result = JobAnalysisService().analyze(job)
    ActivityService(session).record_if_profile_for_user(
        current_user.id,
        event_type="ANALYSIS",
        state="COMPLETED",
        message="Job requirement analysis is ready for review.",
        job_id=job.id,
        details={
            "unknowns": result.unknowns,
            "ambiguities": result.ambiguities,
            "next_action": "Review requirements and uncertainty before relying on the analysis.",
        },
    )
    if result.unknowns or result.ambiguities:
        ActivityService(session).record_if_profile_for_user(
            current_user.id,
            event_type="WARNING",
            state="REVIEW_REQUIRED",
            message="Job analysis contains unknown or ambiguous information.",
            job_id=job.id,
            details={
                "unknowns": result.unknowns,
                "ambiguities": result.ambiguities,
                "next_action": "Verify unclear job details from the original posting.",
            },
        )
    return JobAnalysisResponse.model_validate(asdict(result))


@router.get("/rank", response_model=JobRankingResponse)
def rank_jobs(
    keyword: str | None = Query(default=None, min_length=1, max_length=200),
    company: str | None = Query(default=None, min_length=1, max_length=300),
    location: str | None = Query(default=None, min_length=1, max_length=300),
    source: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> JobRankingResponse:
    result = JobService(session).search(
        keyword=keyword,
        company=company,
        location=location,
        source=source,
        limit=100,
        offset=0,
    )
    try:
        preferences = ProfileService(session).get_preferences(current_user.id)
    except ProfileNotFoundError:
        preferences = None
    ranked = JobRankingService(JobMatchingService(session)).rank_jobs(
        current_user.id, result.jobs, preferences
    )
    page = ranked[offset : offset + limit]
    return JobRankingResponse(
        jobs=[
            RankedJobResponse(
                rank=item.rank,
                ranking_score=item.ranking_score,
                eligibility=item.eligibility,
                reasons=item.reasons,
                unknowns=item.unknowns,
                match=MatchResponse.model_validate(asdict(item.match)),
            )
            for item in page
        ],
        total=len(ranked),
        limit=limit,
        offset=offset,
        preference_state="CONFIGURED" if preferences is not None else "NOT_CONFIGURED",
    )
