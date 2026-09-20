"""Notification request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_type: str
    title: str
    message: str
    job_id: UUID | None
    draft_id: UUID | None
    application_record_id: UUID | None
    read_at: datetime | None
    created_at: datetime | None
