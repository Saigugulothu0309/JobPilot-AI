"""Candidate profile database entity."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.resume.models import Resume


class Profile(Base):
    """A private candidate profile owned by exactly one user."""

    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(32))
    location: Mapped[str | None] = mapped_column(String(200))
    headline: Mapped[str | None] = mapped_column(String(250))
    summary: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="profile")
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    education: Mapped[list["Education"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    experience: Mapped[list["Experience"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    career_preferences: Mapped["CareerPreferences | None"] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )


class CareerPreferences(Base):
    """User-controlled job-search preferences owned by one profile."""

    __tablename__ = "career_preferences"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    employment_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    locations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    work_modes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    industries: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    career_interests: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    exclusions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    hard_constraints: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ranking_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    optional_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    deal_breakers: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    relocation_preference: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NOT_SPECIFIED"
    )
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    available_from: Mapped[date | None] = mapped_column(Date(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    profile: Mapped["Profile"] = relationship(back_populates="career_preferences")


class Skill(Base):
    """A single candidate skill attached to one profile."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_skills_profile_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    profile: Mapped["Profile"] = relationship(back_populates="skills")


class Education(Base):
    """Academic history for a candidate profile."""

    __tablename__ = "education"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(150), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date(), nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    profile: Mapped["Profile"] = relationship(back_populates="education")


class Experience(Base):
    """Work history for a candidate profile."""

    __tablename__ = "experience"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date(), nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    profile: Mapped["Profile"] = relationship(back_populates="experience")


class Project(Base):
    """Candidate project history attached to a profile."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    start_date: Mapped[date] = mapped_column(Date(), nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    profile: Mapped["Profile"] = relationship(back_populates="projects")
