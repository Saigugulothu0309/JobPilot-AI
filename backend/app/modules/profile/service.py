"""Candidate profile operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.profile.models import (
    CareerPreferences,
    Education,
    Experience,
    Profile,
    Project,
    Skill,
)
from app.modules.profile.repository import (
    CareerPreferencesRepository,
    EducationRepository,
    ExperienceRepository,
    ProfileRepository,
    ProjectRepository,
    SkillRepository,
)


class ProfileNotFoundError(RuntimeError):
    """Raised when a profile has not been created for the authenticated user."""


class ProfessionalRecordNotFoundError(RuntimeError):
    """Raised when a professional record is unavailable for the authenticated profile."""


class DuplicateProfessionalRecordError(RuntimeError):
    """Raised when a duplicate professional record is rejected."""


class ProfileService:
    def __init__(self, session: Session) -> None:
        self.repository = ProfileRepository(session)
        self.preferences_repository = CareerPreferencesRepository(session)
        self.skill_repository = SkillRepository(session)
        self.education_repository = EducationRepository(session)
        self.experience_repository = ExperienceRepository(session)
        self.project_repository = ProjectRepository(session)

    def get(self, user_id: UUID) -> Profile | None:
        return self.repository.get_by_user_id(user_id)

    def require_profile(self, user_id: UUID) -> Profile:
        profile = self.get(user_id)
        if profile is None:
            raise ProfileNotFoundError("Profile not found")
        return profile

    def get_or_create_profile(self, user_id: UUID) -> Profile:
        profile = self.get(user_id)
        if profile is None:
            profile = self.repository.create(user_id, {})
            self.repository.save(profile)
        return profile

    def upsert(self, user_id: UUID, values: dict[str, str | None]) -> Profile:
        profile = self.repository.get_by_user_id(user_id)
        if profile is None:
            profile = self.repository.create(user_id, values)
        else:
            for field, value in values.items():
                setattr(profile, field, value)
        return self.repository.save(profile)

    def get_preferences(self, user_id: UUID) -> CareerPreferences | None:
        profile = self.get(user_id)
        if profile is None:
            raise ProfileNotFoundError("Profile not found")
        return self.preferences_repository.get_by_profile_id(profile.id)

    def upsert_preferences(
        self, user_id: UUID, values: dict[str, object]
    ) -> CareerPreferences:
        profile = self.get_or_create_profile(user_id)
        preferences = self.preferences_repository.get_by_profile_id(profile.id)
        if preferences is None:
            preferences = self.preferences_repository.create(profile.id, values)
        else:
            for field, value in values.items():
                setattr(preferences, field, value)
        return self.preferences_repository.save(preferences)

    def list_skills(self, user_id: UUID) -> list[Skill]:
        profile = self.get_or_create_profile(user_id)
        return self.skill_repository.list_by_profile_id(profile.id)

    def create_skill(self, user_id: UUID, values: dict[str, object]) -> Skill:
        profile = self.get_or_create_profile(user_id)
        if (
            self.skill_repository.get_by_profile_and_name(profile.id, str(values["name"]))
            is not None
        ):
            raise DuplicateProfessionalRecordError("Skill already exists for this profile")
        return self.skill_repository.create(profile.id, values)

    def get_skill(self, user_id: UUID, skill_id: UUID) -> Skill:
        profile = self.get_or_create_profile(user_id)
        skill = self.skill_repository.get_by_id_and_profile_id(skill_id, profile.id)
        if skill is None:
            raise ProfessionalRecordNotFoundError("Skill not found")
        return skill

    def update_skill(self, user_id: UUID, skill_id: UUID, values: dict[str, object]) -> Skill:
        skill = self.get_skill(user_id, skill_id)
        if "name" in values:
            existing = self.skill_repository.get_by_profile_and_name(
                skill.profile_id, str(values["name"]), exclude_id=skill.id
            )
            if existing is not None:
                raise DuplicateProfessionalRecordError("Skill already exists for this profile")
        return self.skill_repository.update(skill, values)

    def delete_skill(self, user_id: UUID, skill_id: UUID) -> None:
        skill = self.get_skill(user_id, skill_id)
        self.skill_repository.delete(skill)

    def list_education(self, user_id: UUID) -> list[Education]:
        profile = self.get_or_create_profile(user_id)
        return self.education_repository.list_by_profile_id(profile.id)

    def create_education(self, user_id: UUID, values: dict[str, object]) -> Education:
        profile = self.get_or_create_profile(user_id)
        return self.education_repository.create(profile.id, values)

    def get_education(self, user_id: UUID, education_id: UUID) -> Education:
        profile = self.get_or_create_profile(user_id)
        education = self.education_repository.get_by_id_and_profile_id(education_id, profile.id)
        if education is None:
            raise ProfessionalRecordNotFoundError("Education not found")
        return education

    def update_education(
        self,
        user_id: UUID,
        education_id: UUID,
        values: dict[str, object],
    ) -> Education:
        education = self.get_education(user_id, education_id)
        return self.education_repository.update(education, values)

    def delete_education(self, user_id: UUID, education_id: UUID) -> None:
        education = self.get_education(user_id, education_id)
        self.education_repository.delete(education)

    def list_experience(self, user_id: UUID) -> list[Experience]:
        profile = self.get_or_create_profile(user_id)
        return self.experience_repository.list_by_profile_id(profile.id)

    def create_experience(self, user_id: UUID, values: dict[str, object]) -> Experience:
        profile = self.get_or_create_profile(user_id)
        return self.experience_repository.create(profile.id, values)

    def get_experience(self, user_id: UUID, experience_id: UUID) -> Experience:
        profile = self.get_or_create_profile(user_id)
        experience = self.experience_repository.get_by_id_and_profile_id(experience_id, profile.id)
        if experience is None:
            raise ProfessionalRecordNotFoundError("Experience not found")
        return experience

    def update_experience(
        self,
        user_id: UUID,
        experience_id: UUID,
        values: dict[str, object],
    ) -> Experience:
        experience = self.get_experience(user_id, experience_id)
        return self.experience_repository.update(experience, values)

    def delete_experience(self, user_id: UUID, experience_id: UUID) -> None:
        experience = self.get_experience(user_id, experience_id)
        self.experience_repository.delete(experience)

    def list_projects(self, user_id: UUID) -> list[Project]:
        profile = self.get_or_create_profile(user_id)
        return self.project_repository.list_by_profile_id(profile.id)

    def create_project(self, user_id: UUID, values: dict[str, object]) -> Project:
        profile = self.get_or_create_profile(user_id)
        return self.project_repository.create(profile.id, values)

    def get_project(self, user_id: UUID, project_id: UUID) -> Project:
        profile = self.get_or_create_profile(user_id)
        project = self.project_repository.get_by_id_and_profile_id(project_id, profile.id)
        if project is None:
            raise ProfessionalRecordNotFoundError("Project not found")
        return project

    def update_project(
        self,
        user_id: UUID,
        project_id: UUID,
        values: dict[str, object],
    ) -> Project:
        project = self.get_project(user_id, project_id)
        return self.project_repository.update(project, values)

    def delete_project(self, user_id: UUID, project_id: UUID) -> None:
        project = self.get_project(user_id, project_id)
        self.project_repository.delete(project)
