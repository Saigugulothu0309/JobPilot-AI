"""Feedback request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FeedbackType = Literal[
    "INTERESTED",
    "NOT_INTERESTED",
    "INCORRECT",
    "MISSING_SKILL",
    "WRONG_PREFERENCE",
    "ALREADY_APPLIED",
]


class JobFeedbackCreateRequest(BaseModel):
    job_id: UUID
    feedback_type: FeedbackType
    note: str | None = Field(default=None, max_length=2000)


class JobFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    feedback_type: FeedbackType
    note: str | None
    source: Literal["USER"]
    created_at: datetime | None
    updated_at: datetime | None


class FeedbackProposalCreateRequest(BaseModel):
    feedback_id: UUID
    target_type: Literal["PREFERENCE", "SKILL", "JOB_CORRECTION"]
    target_field: str | None = Field(default=None, max_length=50)
    proposed_value: dict[str, object]


class FeedbackProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    feedback_id: UUID
    target_type: str
    target_field: str | None
    previous_value: dict[str, object]
    proposed_value: dict[str, object]
    status: str
    applied_skill_id: UUID | None = None
    confirmed_at: datetime | None
    rejected_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime | None = None
