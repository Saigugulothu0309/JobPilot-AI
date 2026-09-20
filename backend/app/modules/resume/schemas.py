"""Resume API request and response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    original_filename: str
    stored_filename: str
    storage_key: str
    mime_type: str
    file_size: int


class ResumeProcessingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: UUID
    status: str
    text: str = ""
    character_count: int = 0
    page_count: int | None = None
    extractor: str = ""
    error_code: str | None = None
    error_message: str | None = None


class ReviewBasicInformation(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    location: str | None = Field(default=None, max_length=200)
    linkedin_url: str | None = Field(default=None, max_length=2048)
    github_url: str | None = Field(default=None, max_length=2048)
    portfolio_url: str | None = Field(default=None, max_length=2048)
    source: str | None = Field(default=None, max_length=100)


class ReviewSkill(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=100)


class ReviewEducation(BaseModel):
    institution: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=200)
    start_date: str | None = Field(default=None, max_length=32)
    end_date: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None, max_length=4000)
    source: str | None = Field(default=None, max_length=100)


class ReviewExperience(BaseModel):
    company: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    start_date: str | None = Field(default=None, max_length=32)
    end_date: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None, max_length=4000)
    source: str | None = Field(default=None, max_length=100)


class ReviewProject(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    technologies: list[str] = Field(default_factory=list, max_length=100)
    url: str | None = Field(default=None, max_length=2048)
    start_date: str | None = Field(default=None, max_length=32)
    end_date: str | None = Field(default=None, max_length=32)
    source: str | None = Field(default=None, max_length=100)


class ResumeReviewData(BaseModel):
    basic_information: ReviewBasicInformation | None = None
    skills: list[ReviewSkill] = Field(default_factory=list, max_length=200)
    education: list[ReviewEducation] = Field(default_factory=list, max_length=100)
    experience: list[ReviewExperience] = Field(default_factory=list, max_length=100)
    projects: list[ReviewProject] = Field(default_factory=list, max_length=100)
    warnings: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("warnings", mode="before")
    @classmethod
    def normalize_warnings(cls, value: list[str] | None) -> list[str]:
        return value or []


class ResumeReviewResponse(ResumeReviewData):
    resume_id: UUID
    status: str
