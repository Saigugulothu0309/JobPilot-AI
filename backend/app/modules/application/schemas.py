"""Application preparation request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

APPLICATION_STATUSES = (
    "SAVED",
    "PREPARING",
    "READY_FOR_REVIEW",
    "APPROVED",
    "SUBMITTED",
    "INTERVIEW",
    "REJECTED",
    "OFFER",
    "WITHDRAWN",
    "UNKNOWN",
)


class ApplicationDraftCreateRequest(BaseModel):
    job_id: UUID
    resume_id: UUID | None = None


class ApplicationDraftUpdateRequest(BaseModel):
    content: dict[str, object]


class ApplicationDraftApprovalRequest(BaseModel):
    confirm: bool


class ApplicationDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    job_id: UUID
    resume_id: UUID | None
    status: str
    revision: int
    approved_revision: int | None
    approval_confirmed: bool
    content: dict[str, object]
    profile_snapshot: dict[str, object]
    job_snapshot: dict[str, object]
    created_at: datetime | None
    updated_at: datetime | None


class ApplicationRecordCreateRequest(BaseModel):
    job_id: UUID
    draft_id: UUID | None = None
    status: str = "SAVED"
    notes: str | None = None
    applied_at: datetime | None = None
    interview_at: datetime | None = None
    follow_up_at: datetime | None = None


class ApplicationRecordUpdateRequest(BaseModel):
    status: str | None = None
    notes: str | None = None
    applied_at: datetime | None = None
    interview_at: datetime | None = None
    follow_up_at: datetime | None = None
    draft_id: UUID | None = None


class ApplicationRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    job_id: UUID
    draft_id: UUID | None
    status: str
    notes: str | None
    saved_at: datetime | None
    applied_at: datetime | None
    interview_at: datetime | None
    follow_up_at: datetime | None
    draft_revision: int | None
    job_snapshot: dict[str, object]
    created_at: datetime | None
    updated_at: datetime | None
