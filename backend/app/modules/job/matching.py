"""Deterministic job-to-candidate matching built from trusted profile information."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.job.models import Job
from app.modules.profile.models import Education, Experience, Profile, Project, Skill


def _normalize_skill_token(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9+#]+", " ", value.casefold())
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_skill_name(value: str) -> str:
    return SKILL_ALIAS_MAP.get(_normalize_skill_token(value), _normalize_skill_token(value))


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python", "py"),
    "JavaScript": ("javascript", "js", "ecmascript"),
    "TypeScript": ("typescript", "ts"),
    "React": ("react", "reactjs", "react.js", "react js"),
    "Node.js": ("node", "nodejs", "node.js"),
    "SQL": ("sql", "structured query language"),
    "PostgreSQL": ("postgres", "postgresql", "postgres sql"),
    "FastAPI": ("fastapi",),
    "Flask": ("flask",),
    "Django": ("django",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services"),
    "Java": ("java",),
    "Go": ("go", "golang"),
    "C#": ("c#", "c sharp", "csharp"),
    "C++": ("c++", "c plus plus", "cpp"),
    "Rust": ("rust",),
    "Spark": ("spark",),
    "Airflow": ("airflow",),
    "Redis": ("redis",),
    "GraphQL": ("graphql",),
    "Terraform": ("terraform",),
    "Linux": ("linux",),
    "Bash": ("bash", "shell"),
    "Machine Learning": ("machine learning", "ml"),
    "Data Science": ("data science", "data-science"),
    "Postgres": ("postgres", "postgresql"),
}

SKILL_ALIAS_MAP: dict[str, str] = {}
for canonical, aliases in SKILL_ALIASES.items():
    for alias in aliases:
        SKILL_ALIAS_MAP[_normalize_skill_token(alias)] = canonical
    SKILL_ALIAS_MAP[_normalize_skill_token(canonical)] = canonical


@dataclass(frozen=True, slots=True)
class CandidateMatchData:
    profile: Profile
    skills: list[Skill]
    education: list[Education]
    experience: list[Experience]
    projects: list[Project]


@dataclass(frozen=True, slots=True)
class MatchResult:
    overall_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    positive_reasons: list[str]
    potential_concerns: list[str]
    scoring_breakdown: dict[str, Any]
    candidate: dict[str, Any]
    job: dict[str, Any]


class CandidateDataNotFoundError(RuntimeError):
    """Raised when the authenticated user has no approved candidate data."""


class JobMatchingService:
    """Compute a deterministic match score between an approved candidate and a job."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def match_user_to_job(self, user_id: UUID, job: Job) -> MatchResult:
        candidate = self._load_candidate(user_id)
        job_skill_set = _job_skill_terms(job.title, job.description)
        candidate_skill_set = {
            normalize_skill_name(skill.name) for skill in candidate.skills if skill.name
        }
        matched_skills = sorted(
            {
                skill.name
                for skill in candidate.skills
                if normalize_skill_name(skill.name) in job_skill_set
            }
        )
        missing_skills = [
            skill_name
            for skill_name in sorted(job_skill_set)
            if skill_name not in candidate_skill_set and skill_name != ""
        ]

        skill_score = _calculate_skill_score(matched_skills, job_skill_set)
        title_score = _calculate_title_score(job.title, candidate)
        experience_score = _calculate_experience_score(job.title, candidate.experience)
        education_score = _calculate_education_score(job.title, job.description, candidate.education)
        location_score = _calculate_location_score(job.location, candidate.profile.location)

        overall_score = round(
            skill_score * 0.55
            + title_score * 0.2
            + experience_score * 0.15
            + education_score * 0.05
            + location_score * 0.05,
            2,
        )
        overall_score = max(0.0, min(100.0, overall_score))

        positive_reasons = _positive_reasons(
            matched_skills=matched_skills,
            title_score=title_score,
            experience_score=experience_score,
            education_score=education_score,
            location_score=location_score,
        )
        potential_concerns = _potential_concerns(
            missing_skills=missing_skills,
            title_score=title_score,
            experience_score=experience_score,
            candidate=candidate,
        )

        breakdown = {
            "skill_overlap": round(skill_score, 2),
            "title_relevance": round(title_score, 2),
            "experience_relevance": round(experience_score, 2),
            "education_relevance": round(education_score, 2),
            "location_compatibility": round(location_score, 2),
            "weights": {
                "skill_overlap": 0.55,
                "title_relevance": 0.2,
                "experience_relevance": 0.15,
                "education_relevance": 0.05,
                "location_compatibility": 0.05,
            },
        }

        return MatchResult(
            overall_score=overall_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills[:10],
            positive_reasons=positive_reasons,
            potential_concerns=potential_concerns,
            scoring_breakdown=breakdown,
            candidate={
                "profile_id": candidate.profile.id,
                "location": candidate.profile.location,
                "headline": candidate.profile.headline,
                "summary": candidate.profile.summary,
                "skills_count": len(candidate.skills),
                "experience_count": len(candidate.experience),
                "education_count": len(candidate.education),
                "project_count": len(candidate.projects),
            },
            job={
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "employment_type": job.employment_type,
                "source": job.source,
                "external_job_id": job.external_job_id,
                "external_url": job.external_url,
                "posted_at": job.posted_at,
            },
        )

    def _load_candidate(self, user_id: UUID) -> CandidateMatchData:
        profile = self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise CandidateDataNotFoundError("Approved candidate data not found for user")

        skills = list(
            self.session.scalars(
                select(Skill)
                .where(Skill.profile_id == profile.id)
                .order_by(Skill.name.asc())
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

        if not any((profile.headline, profile.summary, profile.location, skills, education, experience, projects)):
            raise CandidateDataNotFoundError("Approved candidate data not found for user")

        return CandidateMatchData(
            profile=profile,
            skills=skills,
            education=education,
            experience=experience,
            projects=projects,
        )


def _job_skill_terms(title: str, description: str | None) -> set[str]:
    combined = " ".join(part for part in (title, description or "") if part)
    seen: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9+#.]+", combined):
        canonical = normalize_skill_name(token)
        if canonical in SKILL_ALIAS_MAP.values():
            seen.add(canonical)
    return seen


def _calculate_skill_score(matched_skills: list[str], job_skill_set: set[str]) -> float:
    if not job_skill_set:
        return 0.0
    if not matched_skills:
        return 0.0
    return round((len(matched_skills) / len(job_skill_set)) * 100.0, 2)


def _calculate_title_score(job_title: str, candidate: CandidateMatchData) -> float:
    title_tokens = _tokenize(job_title)
    if not title_tokens:
        return 0.0

    candidate_tokens: set[str] = set()
    if candidate.profile.headline:
        candidate_tokens |= _tokenize(candidate.profile.headline)
    for item in candidate.experience:
        if item.job_title:
            candidate_tokens |= _tokenize(item.job_title)
    if candidate.profile.summary:
        candidate_tokens |= _tokenize(candidate.profile.summary)

    if not candidate_tokens:
        return 0.0
    overlap = len(title_tokens & candidate_tokens)
    return round((overlap / len(title_tokens)) * 100.0, 2) if overlap else 0.0


def _calculate_experience_score(job_title: str, experience: list[Experience]) -> float:
    if not experience:
        return 0.0
    job_tokens = _tokenize(job_title)
    if not job_tokens:
        return 0.0
    match_tokens: set[str] = set()
    for item in experience:
        match_tokens |= _tokenize(item.job_title)
    overlap = job_tokens & match_tokens
    return round((len(overlap) / max(1, len(job_tokens))) * 100.0, 2) if overlap else 0.0


def _calculate_education_score(
    job_title: str,
    description: str | None,
    education: list[Education],
) -> float:
    if not education:
        return 0.0
    text = " ".join(part for part in (job_title, description or "") if part)
    if not text:
        return 0.0
    token_set = _tokenize(text)
    for item in education:
        subject = " ".join(part for part in (item.degree, item.field_of_study, item.institution) if part)
        if not subject:
            continue
        if token_set & _tokenize(subject):
            return 100.0
    return 0.0


def _calculate_location_score(job_location: str | None, profile_location: str | None) -> float:
    if not job_location and not profile_location:
        return 100.0
    if not job_location or not profile_location:
        return 100.0
    normalized_job = _normalize_location(job_location)
    normalized_profile = _normalize_location(profile_location)
    if normalized_job == normalized_profile:
        return 100.0
    if normalized_job == "remote" or normalized_profile == "remote":
        return 100.0
    if _location_overlap(normalized_job, normalized_profile):
        return 80.0
    return 0.0


def _positive_reasons(
    *,
    matched_skills: list[str],
    title_score: float,
    experience_score: float,
    education_score: float,
    location_score: float,
) -> list[str]:
    reasons: list[str] = []
    if matched_skills:
        reasons.append(f"Matched key skills: {', '.join(matched_skills[:5])}.")
    if title_score >= 25:
        reasons.append("Job title aligns well with the candidate's recorded background.")
    if experience_score >= 25:
        reasons.append("Relevant experience signals are present in the candidate profile.")
    if education_score > 0:
        reasons.append("Education supports the technical domain of the job.")
    if location_score >= 80:
        reasons.append("Location is compatible with the job requirements.")
    return reasons[:5] or ["No strong positive signals were found beyond the candidate profile data."]


def _potential_concerns(
    *,
    missing_skills: list[str],
    title_score: float,
    experience_score: float,
    candidate: CandidateMatchData,
) -> list[str]:
    concerns: list[str] = []
    if missing_skills:
        concerns.append(f"Missing relevant skills: {', '.join(missing_skills[:5])}.")
    if title_score < 25 and not candidate.experience:
        concerns.append("The profile has limited title-level evidence for this role.")
    if experience_score < 25 and not candidate.experience:
        concerns.append("Experience details do not strongly reinforce the job title.")
    return concerns[:5] or ["No obvious gaps were detected in the approved candidate data."]


def _tokenize(value: str) -> set[str]:
    result: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9+#.]+", value):
        normalized = _normalize_skill_token(token)
        if normalized:
            result.add(normalized)
    return result


def _normalize_location(value: str) -> str:
    return "remote" if "remote" in value.casefold() else re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _location_overlap(left: str, right: str) -> bool:
    left_tokens = set(part for part in left.split() if part)
    right_tokens = set(part for part in right.split() if part)
    return bool(left_tokens & right_tokens)
