"""Job API and source validation schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator


class LocalJobRecord(BaseModel):
    """Validated source record used by the safe local adapter."""

    title: str = Field(..., min_length=1, max_length=300)
    company: str = Field(..., min_length=1, max_length=300)
    location: str | None = Field(default=None, max_length=300)
    description: str = Field(..., min_length=1, max_length=50000)
    employment_type: str | None = Field(default=None, max_length=100)
    external_job_id: str | None = Field(default=None, min_length=1, max_length=300)
    external_url: AnyHttpUrl | None = None
    posted_at: datetime | None = None

    @field_validator("title", "company", "description")
    @classmethod
    def reject_blank_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("location", "employment_type", "external_job_id")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    location: str | None
    description: str
    employment_type: str | None
    source: str
    external_job_id: str | None
    external_url: str | None
    posted_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    source_job_id: str | None = None
    url: str | None = None

    @model_validator(mode="after")
    def populate_search_aliases(self) -> "JobResponse":
        if self.source_job_id is None:
            self.source_job_id = self.external_job_id
        if self.url is None:
            self.url = self.external_url
        return self


class LocalJobIngestionRequest(BaseModel):
    jobs: list[LocalJobRecord] = Field(..., min_length=1, max_length=500)


class JobIngestionResponse(BaseModel):
    source: str
    jobs: list[JobResponse]
    created_count: int
    updated_count: int


class JobSearchResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    limit: int
    offset: int


class MatchCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: UUID
    location: str | None
    headline: str | None
    summary: str | None
    skills_count: int
    experience_count: int
    education_count: int
    project_count: int


class MatchJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    location: str | None
    description: str
    employment_type: str | None
    source: str
    external_job_id: str | None
    external_url: str | None
    posted_at: datetime | None


class MatchScoringBreakdown(BaseModel):
    skill_overlap: float
    title_relevance: float
    experience_relevance: float
    education_relevance: float
    location_compatibility: float
    weights: dict[str, float]


class MatchResponse(BaseModel):
    overall_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    positive_reasons: list[str]
    potential_concerns: list[str]
    scoring_breakdown: MatchScoringBreakdown
    candidate: MatchCandidateResponse
    job: MatchJobResponse


class AnalysisJobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    source: str
    external_job_id: str | None
    external_url: str | None


class JobAnalysisResponse(BaseModel):
    job: AnalysisJobResponse
    role: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_requirement: str | None
    education_requirement: str | None
    location: str | None
    work_mode: str
    employment_type: str | None
    important_requirements: list[str]
    unknowns: list[str]
    ambiguities: list[str]


class RankedJobResponse(BaseModel):
    rank: int
    ranking_score: float
    eligibility: str
    reasons: list[str]
    unknowns: list[str]
    match: MatchResponse


class JobRankingResponse(BaseModel):
    jobs: list[RankedJobResponse]
    total: int
    limit: int
    offset: int
    preference_state: str
