"""Database access for candidate profiles."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.profile.models import (
    CareerPreferences,
    Education,
    Experience,
    Profile,
    Project,
    Skill,
)


class ProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_id(self, user_id: UUID) -> Profile | None:
        return self.session.scalar(select(Profile).where(Profile.user_id == user_id))

    def get_by_id(self, profile_id: UUID) -> Profile | None:
        return self.session.get(Profile, profile_id)

    def create(self, user_id: UUID, values: dict[str, str | None]) -> Profile:
        profile = Profile(user_id=user_id, **values)
        self.session.add(profile)
        return profile

    def save(self, profile: Profile) -> Profile:
        self.session.commit()
        self.session.refresh(profile)
        return profile


class CareerPreferencesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_profile_id(self, profile_id: UUID) -> CareerPreferences | None:
        return self.session.scalar(
            select(CareerPreferences).where(CareerPreferences.profile_id == profile_id)
        )

    def create(self, profile_id: UUID, values: dict[str, object]) -> CareerPreferences:
        preferences = CareerPreferences(profile_id=profile_id, **values)
        self.session.add(preferences)
        return preferences

    def save(self, preferences: CareerPreferences) -> CareerPreferences:
        self.session.commit()
        self.session.refresh(preferences)
        return preferences


class SkillRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_profile_id(self, profile_id: UUID) -> list[Skill]:
        return list(
            self.session.scalars(
                select(Skill).where(Skill.profile_id == profile_id).order_by(Skill.created_at.asc())
            ).all()
        )

    def get_by_id_and_profile_id(self, skill_id: UUID, profile_id: UUID) -> Skill | None:
        return self.session.scalar(
            select(Skill).where(Skill.id == skill_id, Skill.profile_id == profile_id)
        )

    def get_by_profile_and_name(
        self,
        profile_id: UUID,
        name: str,
        exclude_id: UUID | None = None,
    ) -> Skill | None:
        query = select(Skill).where(Skill.profile_id == profile_id, Skill.name == name)
        if exclude_id is not None:
            query = query.where(Skill.id != exclude_id)
        return self.session.scalar(query)

    def create(self, profile_id: UUID, values: dict[str, object]) -> Skill:
        skill = Skill(profile_id=profile_id, **values)
        self.session.add(skill)
        self.session.commit()
        self.session.refresh(skill)
        return skill

    def update(self, skill: Skill, values: dict[str, object]) -> Skill:
        for field, value in values.items():
            setattr(skill, field, value)
        self.session.commit()
        self.session.refresh(skill)
        return skill

    def delete(self, skill: Skill) -> None:
        self.session.delete(skill)
        self.session.commit()


class EducationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_profile_id(self, profile_id: UUID) -> list[Education]:
        return list(
            self.session.scalars(
                select(Education)
                .where(Education.profile_id == profile_id)
                .order_by(Education.start_date.desc())
            ).all()
        )

    def get_by_id_and_profile_id(
        self, education_id: UUID, profile_id: UUID
    ) -> Education | None:
        return self.session.scalar(
            select(Education).where(
                Education.id == education_id,
                Education.profile_id == profile_id,
            )
        )

    def create(self, profile_id: UUID, values: dict[str, object]) -> Education:
        education = Education(profile_id=profile_id, **values)
        self.session.add(education)
        self.session.commit()
        self.session.refresh(education)
        return education

    def update(self, education: Education, values: dict[str, object]) -> Education:
        for field, value in values.items():
            setattr(education, field, value)
        self.session.commit()
        self.session.refresh(education)
        return education

    def delete(self, education: Education) -> None:
        self.session.delete(education)
        self.session.commit()


class ExperienceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_profile_id(self, profile_id: UUID) -> list[Experience]:
        return list(
            self.session.scalars(
                select(Experience)
                .where(Experience.profile_id == profile_id)
                .order_by(Experience.start_date.desc())
            ).all()
        )

    def get_by_id_and_profile_id(
        self, experience_id: UUID, profile_id: UUID
    ) -> Experience | None:
        return self.session.scalar(
            select(Experience).where(
                Experience.id == experience_id,
                Experience.profile_id == profile_id,
            )
        )

    def create(self, profile_id: UUID, values: dict[str, object]) -> Experience:
        experience = Experience(profile_id=profile_id, **values)
        self.session.add(experience)
        self.session.commit()
        self.session.refresh(experience)
        return experience

    def update(self, experience: Experience, values: dict[str, object]) -> Experience:
        for field, value in values.items():
            setattr(experience, field, value)
        self.session.commit()
        self.session.refresh(experience)
        return experience

    def delete(self, experience: Experience) -> None:
        self.session.delete(experience)
        self.session.commit()


class ProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_profile_id(self, profile_id: UUID) -> list[Project]:
        return list(
            self.session.scalars(
                select(Project)
                .where(Project.profile_id == profile_id)
                .order_by(Project.start_date.desc())
            ).all()
        )

    def get_by_id_and_profile_id(
        self, project_id: UUID, profile_id: UUID
    ) -> Project | None:
        return self.session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.profile_id == profile_id,
            )
        )

    def create(self, profile_id: UUID, values: dict[str, object]) -> Project:
        project = Project(profile_id=profile_id, **values)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def update(self, project: Project, values: dict[str, object]) -> Project:
        for field, value in values.items():
            setattr(project, field, value)
        self.session.commit()
        self.session.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.session.delete(project)
        self.session.commit()
