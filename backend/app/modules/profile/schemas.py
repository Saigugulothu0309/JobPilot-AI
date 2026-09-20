"""Candidate profile API schemas."""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

EMPLOYMENT_TYPES = Literal["INTERNSHIP", "FULL_TIME", "PART_TIME", "APPRENTICESHIP", "TRAINEE"]
WORK_MODES = Literal["REMOTE", "HYBRID", "ON_SITE"]
RELOCATION_PREFERENCES = Literal["NOT_SPECIFIED", "NOT_WILLING", "WILLING", "DEPENDS"]


class CareerPreferencesUpdateRequest(BaseModel):
    target_roles: list[str] = Field(default_factory=list, max_length=20)
    employment_types: list[EMPLOYMENT_TYPES] = Field(default_factory=list, max_length=10)
    locations: list[str] = Field(default_factory=list, max_length=20)
    work_modes: list[WORK_MODES] = Field(default_factory=list, max_length=5)
    industries: list[str] = Field(default_factory=list, max_length=20)
    technologies: list[str] = Field(default_factory=list, max_length=30)
    career_interests: list[str] = Field(default_factory=list, max_length=20)
    exclusions: list[str] = Field(default_factory=list, max_length=20)
    hard_constraints: list[str] = Field(default_factory=list, max_length=20)
    ranking_preferences: list[str] = Field(default_factory=list, max_length=20)
    optional_preferences: list[str] = Field(default_factory=list, max_length=20)
    deal_breakers: list[str] = Field(default_factory=list, max_length=20)
    relocation_preference: RELOCATION_PREFERENCES = "NOT_SPECIFIED"
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    available_from: date | None = None

    @field_validator(
        "target_roles",
        "locations",
        "industries",
        "technologies",
        "career_interests",
        "exclusions",
        "hard_constraints",
        "ranking_preferences",
        "optional_preferences",
        "deal_breakers",
        mode="before",
    )
    @classmethod
    def normalize_text_lists(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("preference values must not be blank")
        return normalized

    @field_validator("employment_types", "work_modes", mode="before")
    @classmethod
    def normalize_enum_lists(cls, values: list[str]) -> list[str]:
        return [value.strip().upper().replace("-", "_") for value in values]

    @field_validator("relocation_preference", mode="before")
    @classmethod
    def normalize_relocation_preference(cls, value: str) -> str:
        return value.strip().upper().replace("-", "_")

    @model_validator(mode="after")
    def validate_salary_range(self) -> "CareerPreferencesUpdateRequest":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_max < self.salary_min:
                raise ValueError("salary_max must be greater than or equal to salary_min")
        return self


class CareerPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    target_roles: list[str]
    employment_types: list[str]
    locations: list[str]
    work_modes: list[str]
    industries: list[str]
    technologies: list[str]
    career_interests: list[str]
    exclusions: list[str]
    hard_constraints: list[str]
    ranking_preferences: list[str]
    optional_preferences: list[str]
    deal_breakers: list[str]
    relocation_preference: str
    salary_min: int | None
    salary_max: int | None
    available_from: date | None


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    location: str | None = Field(default=None, max_length=200)
    headline: str | None = Field(default=None, max_length=250)
    summary: str | None = Field(default=None, max_length=4000)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str | None
    phone: str | None
    location: str | None
    headline: str | None
    summary: str | None


class SkillCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    proficiency: str = Field(..., min_length=1, max_length=20)

    @field_validator("proficiency")
    @classmethod
    def validate_proficiency(cls, value: str) -> str:
        allowed = {"BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"}
        if value.upper() not in allowed:
            raise ValueError("proficiency must be BEGINNER, INTERMEDIATE, ADVANCED, or EXPERT")
        return value.upper()


class SkillUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    proficiency: str | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("proficiency")
    @classmethod
    def validate_proficiency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"}
        if value.upper() not in allowed:
            raise ValueError("proficiency must be BEGINNER, INTERMEDIATE, ADVANCED, or EXPERT")
        return value.upper()


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    name: str
    category: str | None
    proficiency: str


class EducationCreateRequest(BaseModel):
    institution: str = Field(..., min_length=1, max_length=200)
    degree: str | None = Field(default=None, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self) -> "EducationCreateRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class EducationUpdateRequest(BaseModel):
    institution: str | None = Field(default=None, min_length=1, max_length=200)
    degree: str | None = Field(default=None, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self) -> "EducationUpdateRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class EducationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    institution: str
    degree: str | None
    field_of_study: str | None
    start_date: date
    end_date: date | None
    description: str | None


class ExperienceCreateRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    job_title: str = Field(..., min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceCreateRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ExperienceUpdateRequest(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=200)
    job_title: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceUpdateRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class ExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    company: str
    job_title: str
    location: str | None
    start_date: date
    end_date: date | None
    description: str | None


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    url: str | None = None
    start_date: date
    end_date: date | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = AnyHttpUrl(value)
        return str(parsed)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectCreateRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    url: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = AnyHttpUrl(value)
        return str(parsed)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectUpdateRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    name: str
    description: str | None
    url: str | None
    start_date: date
    end_date: date | None
