"""Activity event response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    event_type: str
    state: str
    message: str
    job_id: UUID | None
    draft_id: UUID | None
    application_record_id: UUID | None
    details: dict[str, object]
    created_at: datetime | None
