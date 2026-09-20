"""Grounded application draft preparation."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity.service import ActivityService
from app.modules.application.models import ApplicationDraft, ApplicationRecord
from app.modules.application.schemas import APPLICATION_STATUSES
from app.modules.job.models import Job
from app.modules.notification.service import NotificationService
from app.modules.profile.models import Education, Experience, Profile, Project, Skill
from app.modules.resume.models import Resume
from app.modules.resume.service import ResumeNotFoundError, ResumeService


class ApplicationDraftNotFoundError(RuntimeError):
    """Raised when an application draft is absent or not owned by the user."""


class ApplicationDraftPreparationError(RuntimeError):
    """Raised when a grounded draft cannot be prepared safely."""


class ApplicationDraftApprovalError(RuntimeError):
    """Raised when a draft cannot be reviewed or approved."""


class ApplicationRecordNotFoundError(RuntimeError):
    """Raised when an application record is absent or not owned by the user."""


class ApplicationRecordError(RuntimeError):
    """Raised when an application record cannot be changed safely."""


class ApplicationDraftService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def prepare(
        self,
        user_id: UUID,
        job_id: UUID,
        resume_id: UUID | None = None,
    ) -> ApplicationDraft:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise ApplicationDraftPreparationError("Approved candidate profile not found")
        job = self.session.get(Job, job_id)
        if job is None:
            raise ApplicationDraftPreparationError("Job not found")

        resume = self._resolve_resume(user_id, resume_id) if resume_id else None
        skills = list(
            self.session.scalars(
                select(Skill).where(Skill.profile_id == profile.id).order_by(Skill.name.asc())
            ).all()
        )
        education = list(
            self.session.scalars(
                select(Education)
                .where(Education.profile_id == profile.id)
                .order_by(Education.start_date.desc())
            ).all()
        )
        experience = list(
            self.session.scalars(
                select(Experience)
                .where(Experience.profile_id == profile.id)
                .order_by(Experience.start_date.desc())
            ).all()
        )
        projects = list(
            self.session.scalars(
                select(Project)
                .where(Project.profile_id == profile.id)
                .order_by(Project.start_date.desc())
            ).all()
        )

        job_text = f"{job.title} {job.description}".casefold()
        relevant_skills = [
            skill.name for skill in skills if _normalize(skill.name) in _normalize(job_text)
        ]
        content: dict[str, object] = {
            "application_summary": _application_summary(profile, job),
            "resume_focus": sorted(set(relevant_skills)),
            "experience_evidence": [
                {
                    "company": item.company,
                    "job_title": item.job_title,
                    "description": item.description,
                    "evidence_type": "approved_experience",
                }
                for item in experience
            ],
            "project_evidence": [
                {
                    "name": item.name,
                    "description": item.description,
                    "evidence_type": "approved_project",
                }
                for item in projects
            ],
            "education_evidence": [
                {
                    "institution": item.institution,
                    "degree": item.degree,
                    "field_of_study": item.field_of_study,
                    "evidence_type": "approved_education",
                }
                for item in education
            ],
            "unresolved_items": _unresolved_items(profile, relevant_skills, resume),
            "approval_required": True,
        }
        profile_snapshot: dict[str, object] = {
            "profile_id": str(profile.id),
            "headline": profile.headline,
            "summary": profile.summary,
            "location": profile.location,
            "skills": [skill.name for skill in skills],
        }
        job_snapshot: dict[str, object] = {
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "location": job.location,
            "external_url": job.external_url,
        }

        draft = self.session.scalar(
            select(ApplicationDraft).where(
                ApplicationDraft.profile_id == profile.id,
                ApplicationDraft.job_id == job.id,
            )
        )
        if draft is None:
            draft = ApplicationDraft(
                profile_id=profile.id,
                job_id=job.id,
                resume_id=resume.id if resume else None,
                status="DRAFT",
                revision=1,
                content=content,
                profile_snapshot=profile_snapshot,
                job_snapshot=job_snapshot,
            )
            self.session.add(draft)
        else:
            draft.resume_id = resume.id if resume else draft.resume_id
            draft.status = "DRAFT"
            draft.revision += 1
            draft.content = content
            draft.profile_snapshot = profile_snapshot
            draft.job_snapshot = job_snapshot
        self.session.commit()
        self.session.refresh(draft)
        ActivityService(self.session).record_for_profile(
            profile.id,
            event_type="DRAFTING",
            state="AWAITING_APPROVAL",
            message="Application draft is ready for your review and explicit approval.",
            job_id=job.id,
            draft_id=draft.id,
            details={
                "revision": draft.revision,
                "unresolved_items": content["unresolved_items"],
                "next_action": "Review the draft and explicitly approve it if it is accurate.",
            },
        )
        NotificationService(self.session).create_for_profile(
            profile.id,
            notification_type="DRAFT_READY",
            title="Draft ready for review",
            message="Your application draft requires review and explicit approval.",
            dedupe_key=f"draft-ready:{draft.id}:{draft.revision}",
            job_id=job.id,
            draft_id=draft.id,
        )
        return draft

    def get_for_user(self, user_id: UUID, draft_id: UUID) -> ApplicationDraft:
        draft = self.session.scalar(
            select(ApplicationDraft)
            .join(Profile, Profile.id == ApplicationDraft.profile_id)
            .where(ApplicationDraft.id == draft_id, Profile.user_id == user_id)
        )
        if draft is None:
            raise ApplicationDraftNotFoundError("Application draft not found")
        return draft

    def update_for_user(
        self,
        user_id: UUID,
        draft_id: UUID,
        content: dict[str, object],
    ) -> ApplicationDraft:
        draft = self.get_for_user(user_id, draft_id)
        if draft.status == "APPROVED":
            raise ApplicationDraftApprovalError("Approved draft cannot be edited")
        draft.content = content
        draft.revision += 1
        draft.status = "DRAFT"
        draft.approved_revision = None
        draft.approval_confirmed = False
        self.session.commit()
        self.session.refresh(draft)
        ActivityService(self.session).record_for_user(
            user_id,
            event_type="DRAFTING",
            state="AWAITING_APPROVAL",
            message="Edited application draft requires your review and explicit approval.",
            job_id=draft.job_id,
            draft_id=draft.id,
            details={
                "revision": draft.revision,
                "next_action": (
                    "Review the edited draft and explicitly approve it if it is accurate."
                ),
            },
        )
        NotificationService(self.session).create_if_profile_for_user(
            user_id,
            notification_type="DRAFT_READY",
            title="Updated draft ready for review",
            message="Your edited application draft requires review and explicit approval.",
            dedupe_key=f"draft-ready:{draft.id}:{draft.revision}",
            job_id=draft.job_id,
            draft_id=draft.id,
        )
        return draft

    def approve_for_user(
        self,
        user_id: UUID,
        draft_id: UUID,
        confirm: bool,
    ) -> ApplicationDraft:
        draft = self.get_for_user(user_id, draft_id)
        if not confirm:
            raise ApplicationDraftApprovalError("Explicit approval confirmation is required")
        if draft.status == "APPROVED" and draft.approved_revision == draft.revision:
            return draft
        draft.status = "APPROVED"
        draft.approved_revision = draft.revision
        draft.approval_confirmed = True
        self.session.commit()
        self.session.refresh(draft)
        ActivityService(self.session).record_for_user(
            user_id,
            event_type="APPROVAL",
            state="COMPLETED",
            message="Application draft approval was recorded for the current revision.",
            job_id=draft.job_id,
            draft_id=draft.id,
            details={
                "approved_revision": draft.approved_revision,
                "next_action": "Manually submit outside JobPilot, then update tracking if desired.",
            },
        )
        return draft

    def _resolve_resume(self, user_id: UUID, resume_id: UUID) -> Resume:
        try:
            resume = ResumeService(self.session).get_for_profile(user_id, resume_id)
        except ResumeNotFoundError as exc:
            raise ApplicationDraftPreparationError("Resume not found") from exc
        if resume.review_status != "APPROVED":
            raise ApplicationDraftPreparationError("Resume must be approved before use in a draft")
        return resume


class ApplicationRecordService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: UUID) -> list[ApplicationRecord]:
        profile = self._profile(user_id)
        return list(
            self.session.scalars(
                select(ApplicationRecord)
                .where(ApplicationRecord.profile_id == profile.id)
                .order_by(ApplicationRecord.updated_at.desc(), ApplicationRecord.id.asc())
            ).all()
        )

    def get_for_user(self, user_id: UUID, record_id: UUID) -> ApplicationRecord:
        profile = self._profile(user_id)
        record = self.session.scalar(
            select(ApplicationRecord).where(
                ApplicationRecord.id == record_id,
                ApplicationRecord.profile_id == profile.id,
            )
        )
        if record is None:
            raise ApplicationRecordNotFoundError("Application record not found")
        return record

    def create(
        self,
        user_id: UUID,
        *,
        job_id: UUID,
        draft_id: UUID | None,
        status: str,
        notes: str | None,
        applied_at: datetime | None,
        interview_at: datetime | None,
        follow_up_at: datetime | None,
    ) -> ApplicationRecord:
        profile = self._profile(user_id)
        job = self.session.get(Job, job_id)
        if job is None:
            raise ApplicationRecordError("Job not found")
        existing = self.session.scalar(
            select(ApplicationRecord).where(
                ApplicationRecord.profile_id == profile.id,
                ApplicationRecord.job_id == job.id,
            )
        )
        if existing is not None:
            raise ApplicationRecordError("Application record already exists for this job")
        draft, draft_revision = self._draft(user_id, draft_id)
        normalized_status, normalized_notes = _normalize_status(status, notes)
        record = ApplicationRecord(
            profile_id=profile.id,
            job_id=job.id,
            draft_id=draft.id if draft else None,
            status=normalized_status,
            notes=normalized_notes,
            applied_at=applied_at,
            interview_at=interview_at,
            follow_up_at=follow_up_at,
            draft_revision=draft_revision,
            job_snapshot=_job_snapshot(job),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def update(
        self,
        user_id: UUID,
        record_id: UUID,
        *,
        status: str | None,
        notes: str | None,
        applied_at: datetime | None,
        interview_at: datetime | None,
        follow_up_at: datetime | None,
        draft_id: UUID | None,
    ) -> ApplicationRecord:
        record = self.get_for_user(user_id, record_id)
        draft, draft_revision = self._draft(user_id, draft_id) if draft_id else (None, None)
        if status is not None:
            record.status, record.notes = _normalize_status(status, notes)
        elif notes is not None:
            record.notes = notes
        if applied_at is not None:
            record.applied_at = applied_at
        if interview_at is not None:
            record.interview_at = interview_at
        if follow_up_at is not None:
            record.follow_up_at = follow_up_at
        if draft_id is not None:
            record.draft_id = draft.id if draft else None
            record.draft_revision = draft_revision
        self.session.commit()
        self.session.refresh(record)
        return record

    def _profile(self, user_id: UUID) -> Profile:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise ApplicationRecordError("Profile not found")
        return profile

    def _draft(
        self, user_id: UUID, draft_id: UUID | None
    ) -> tuple[ApplicationDraft | None, int | None]:
        if draft_id is None:
            return None, None
        draft = ApplicationDraftService(self.session).get_for_user(user_id, draft_id)
        return draft, draft.revision


def _normalize_status(status: str, notes: str | None) -> tuple[str, str | None]:
    normalized = status.strip().upper().replace("-", "_").replace(" ", "_")
    if normalized not in APPLICATION_STATUSES:
        raise ApplicationRecordError("Unsupported application status")
    if normalized == "UNKNOWN":
        return normalized, "Submission status unknown — verify manually."
    return normalized, notes


def _job_snapshot(job: Job) -> dict[str, object]:
    return {
        "job_id": str(job.id),
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "external_url": job.external_url,
    }


def _application_summary(profile: Profile, job: Job) -> str:
    if profile.summary:
        return profile.summary
    if profile.headline:
        return (
            f"{profile.headline} candidate interested in the {job.title} opportunity "
            f"at {job.company}."
        )
    return "An application summary requires an approved profile headline or summary."


def _unresolved_items(
    profile: Profile,
    relevant_skills: list[str],
    resume: Resume | None,
) -> list[str]:
    unresolved: list[str] = []
    if not profile.full_name:
        unresolved.append("Candidate name is not provided in the approved profile.")
    if not profile.summary and not profile.headline:
        unresolved.append("No approved profile summary or headline is available.")
    if not relevant_skills:
        unresolved.append("No approved profile skill directly matches the job text.")
    if resume is None:
        unresolved.append("No approved resume version was selected for this draft.")
    return unresolved


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", value.casefold()).strip()
