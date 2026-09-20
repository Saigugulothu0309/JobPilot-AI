"""User feedback persistence and confirmation-gated proposal workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity.service import ActivityService
from app.modules.feedback.models import FeedbackProposal, JobFeedback
from app.modules.job.models import Job
from app.modules.profile.models import CareerPreferences, Profile, Skill

CANONICAL_PREFERENCE_FIELDS: set[str] = {
    "target_roles",
    "employment_types",
    "locations",
    "work_modes",
    "industries",
    "technologies",
    "career_interests",
    "exclusions",
    "hard_constraints",
    "ranking_preferences",
    "optional_preferences",
    "deal_breakers",
}

PREFERENCE_FIELD_ALIASES: dict[str, str] = {
    "preferred_locations": "locations",
    "preferred_work_modes": "work_modes",
    "preferred_industries": "industries",
    "preferred_technologies": "technologies",
    "preferred_roles": "target_roles",
}


class FeedbackError(RuntimeError):
    """Raised when feedback cannot be safely recorded or processed."""


class FeedbackNotFoundError(FeedbackError):
    """Raised when a requested feedback or proposal resource is not found."""


class FeedbackConflictError(FeedbackError):
    """Raised when a proposal action or payload is in an invalid state."""


class JobFeedbackService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_or_update(
        self, user_id: UUID, *, job_id: UUID, feedback_type: str, note: str | None
    ) -> JobFeedback:
        profile = self._profile(user_id)
        if self.session.get(Job, job_id) is None:
            raise FeedbackNotFoundError("Job not found")
        feedback = self.session.scalar(
            select(JobFeedback).where(
                JobFeedback.profile_id == profile.id,
                JobFeedback.job_id == job_id,
                JobFeedback.feedback_type == feedback_type,
            )
        )
        if feedback is None:
            feedback = JobFeedback(
                profile_id=profile.id,
                job_id=job_id,
                feedback_type=feedback_type,
                note=note,
                source="USER",
            )
            self.session.add(feedback)
        else:
            feedback.note = note
        self.session.commit()
        self.session.refresh(feedback)
        ActivityService(self.session).record_for_profile(
            profile.id,
            event_type="USER_FEEDBACK",
            state="COMPLETED",
            message=(
                "Your opportunity feedback was recorded without changing preferences or ranking."
            ),
            job_id=job_id,
            details={
                "feedback_type": feedback_type,
                "source": "USER",
                "next_action": (
                    "Review or update your profile and preferences separately if needed."
                ),
            },
        )
        return feedback

    def list_for_user(self, user_id: UUID, limit: int, offset: int) -> list[JobFeedback]:
        profile = self._profile(user_id)
        return list(
            self.session.scalars(
                select(JobFeedback)
                .where(JobFeedback.profile_id == profile.id)
                .order_by(JobFeedback.updated_at.desc(), JobFeedback.id.asc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def create_proposal(
        self,
        user_id: UUID,
        *,
        feedback_id: UUID,
        target_type: str,
        target_field: str | None,
        proposed_value: dict[str, object],
    ) -> FeedbackProposal:
        profile = self._profile(user_id)
        feedback = self.session.scalar(
            select(JobFeedback).where(
                JobFeedback.id == feedback_id,
                JobFeedback.profile_id == profile.id,
            )
        )
        if feedback is None:
            raise FeedbackNotFoundError("Feedback not found")

        if feedback.feedback_type in {"INTERESTED", "NOT_INTERESTED", "ALREADY_APPLIED"}:
            raise FeedbackConflictError(
                f"Feedback type {feedback.feedback_type} cannot create durable-learning proposals"
            )

        if (feedback.feedback_type, target_type) not in {
            ("WRONG_PREFERENCE", "PREFERENCE"),
            ("MISSING_SKILL", "SKILL"),
            ("INCORRECT", "JOB_CORRECTION"),
        }:
            raise FeedbackConflictError(
                f"Feedback type {feedback.feedback_type} cannot create a {target_type} proposal"
            )

        previous: dict[str, object] = {}
        resolved_target_field = target_field

        if target_type == "PREFERENCE":
            if not target_field:
                raise FeedbackConflictError("Preference proposal requires a target field")

            canonical_field = PREFERENCE_FIELD_ALIASES.get(target_field, target_field)
            if canonical_field not in CANONICAL_PREFERENCE_FIELDS:
                raise FeedbackConflictError(f"Invalid preference target field: {target_field}")

            raw_value = proposed_value.get("value")
            if not isinstance(raw_value, list) or not all(isinstance(v, str) for v in raw_value):
                raise FeedbackConflictError("Preference proposal requires a list of string values")

            resolved_target_field = canonical_field
            preferences = self.session.scalar(
                select(CareerPreferences).where(CareerPreferences.profile_id == profile.id)
            )
            existing_list = (
                list(getattr(preferences, canonical_field))
                if preferences and getattr(preferences, canonical_field, None) is not None
                else []
            )
            previous = {"value": existing_list}

        elif target_type == "SKILL":
            name = proposed_value.get("name")
            proficiency = proposed_value.get("proficiency")
            if not isinstance(name, str) or not name.strip():
                raise FeedbackConflictError("Skill proposal requires a non-empty name")
            if not isinstance(proficiency, str) or not proficiency.strip():
                raise FeedbackConflictError("Skill proposal requires a valid proficiency")

        elif target_type == "JOB_CORRECTION":
            correction = proposed_value.get("correction")
            if not isinstance(correction, str) or not correction.strip():
                raise FeedbackConflictError("Job correction proposal requires correction text")

        proposal = FeedbackProposal(
            profile_id=profile.id,
            feedback_id=feedback.id,
            target_type=target_type,
            target_field=resolved_target_field,
            previous_value=previous,
            proposed_value=proposed_value,
            status="PENDING",
        )
        self.session.add(proposal)
        self.session.commit()
        self.session.refresh(proposal)
        return proposal

    def get_proposal(self, user_id: UUID, proposal_id: UUID) -> FeedbackProposal:
        profile = self._profile(user_id)
        proposal = self.session.scalar(
            select(FeedbackProposal).where(
                FeedbackProposal.id == proposal_id,
                FeedbackProposal.profile_id == profile.id,
            )
        )
        if proposal is None:
            raise FeedbackNotFoundError("Feedback proposal not found")
        return proposal

    def confirm_proposal(self, user_id: UUID, proposal_id: UUID) -> FeedbackProposal:
        proposal = self.get_proposal(user_id, proposal_id)
        if proposal.status == "CONFIRMED":
            return proposal
        if proposal.status != "PENDING":
            raise FeedbackConflictError(
                f"Only pending proposals can be confirmed (status: {proposal.status})"
            )

        profile = self._profile(user_id)
        feedback = self.session.get(JobFeedback, proposal.feedback_id)
        job_id = feedback.job_id if feedback else None

        if proposal.target_type == "PREFERENCE":
            if not proposal.target_field:
                raise FeedbackConflictError("Preference proposal has no target field")
            canonical_field = PREFERENCE_FIELD_ALIASES.get(
                proposal.target_field, proposal.target_field
            )
            preferences = self.session.scalar(
                select(CareerPreferences).where(CareerPreferences.profile_id == profile.id)
            )
            if preferences is None:
                preferences = CareerPreferences(profile_id=profile.id)
                self.session.add(preferences)
            new_val = proposal.proposed_value.get("value", [])
            val_list = [str(v) for v in new_val] if isinstance(new_val, list) else []
            setattr(preferences, canonical_field, val_list)
            self.session.add(preferences)

        elif proposal.target_type == "SKILL":
            skill_name = str(proposal.proposed_value["name"]).strip()
            category_val = proposal.proposed_value.get("category")
            category = str(category_val).strip() if category_val else None
            proficiency = str(proposal.proposed_value["proficiency"]).upper().strip()

            skill = Skill(
                profile_id=profile.id,
                name=skill_name,
                category=category,
                proficiency=proficiency,
            )
            self.session.add(skill)
            self.session.flush()
            proposal.applied_skill_id = skill.id

        elif proposal.target_type == "JOB_CORRECTION":
            pass

        proposal.status = "CONFIRMED"
        proposal.confirmed_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(proposal)

        ActivityService(self.session).record_for_profile(
            profile.id,
            event_type="FEEDBACK_CONFIRMED",
            state="COMPLETED",
            message="Confirmed feedback proposal was applied.",
            job_id=job_id,
            details={
                "proposal_id": str(proposal.id),
                "target_type": proposal.target_type,
                "target_field": proposal.target_field,
                "previous_value": proposal.previous_value,
                "proposed_value": proposal.proposed_value,
                "feedback_id": str(proposal.feedback_id),
                "next_action": "Ranking uses confirmed preference or skill changes.",
            },
        )
        return proposal

    def reject_proposal(self, user_id: UUID, proposal_id: UUID) -> FeedbackProposal:
        proposal = self.get_proposal(user_id, proposal_id)
        if proposal.status == "REJECTED":
            return proposal
        if proposal.status != "PENDING":
            raise FeedbackConflictError(
                f"Only pending proposals can be rejected (status: {proposal.status})"
            )

        proposal.status = "REJECTED"
        proposal.rejected_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(proposal)
        return proposal

    def revoke_proposal(self, user_id: UUID, proposal_id: UUID) -> FeedbackProposal:
        proposal = self.get_proposal(user_id, proposal_id)
        if proposal.status == "REVOKED":
            return proposal
        if proposal.status != "CONFIRMED":
            raise FeedbackConflictError(
                f"Only confirmed proposals can be revoked (status: {proposal.status})"
            )

        profile = self._profile(user_id)
        feedback = self.session.get(JobFeedback, proposal.feedback_id)
        job_id = feedback.job_id if feedback else None

        if proposal.target_type == "PREFERENCE":
            if not proposal.target_field:
                raise FeedbackConflictError("Preference proposal has no target field")
            canonical_field = PREFERENCE_FIELD_ALIASES.get(
                proposal.target_field, proposal.target_field
            )
            preferences = self.session.scalar(
                select(CareerPreferences).where(CareerPreferences.profile_id == profile.id)
            )
            if preferences is not None:
                restored_val = proposal.previous_value.get("value", [])
                restored_list = (
                    [str(v) for v in restored_val] if isinstance(restored_val, list) else []
                )
                setattr(preferences, canonical_field, restored_list)
                self.session.add(preferences)

        elif proposal.target_type == "SKILL":
            if proposal.applied_skill_id:
                skill = self.session.get(Skill, proposal.applied_skill_id)
                if skill is not None and skill.profile_id == profile.id:
                    self.session.delete(skill)

        elif proposal.target_type == "JOB_CORRECTION":
            pass

        proposal.status = "REVOKED"
        proposal.revoked_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(proposal)

        ActivityService(self.session).record_for_profile(
            profile.id,
            event_type="FEEDBACK_REVOKED",
            state="COMPLETED",
            message="Confirmed feedback proposal was revoked and prior value restored.",
            job_id=job_id,
            details={
                "proposal_id": str(proposal.id),
                "target_type": proposal.target_type,
                "target_field": proposal.target_field,
                "restored_value": proposal.previous_value,
                "feedback_id": str(proposal.feedback_id),
                "next_action": "Ranking now uses the restored profile or preference value.",
            },
        )
        return proposal

    def _profile(self, user_id: UUID) -> Profile:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise FeedbackNotFoundError("Profile not found")
        return profile
