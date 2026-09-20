"""Deterministic analysis of normalized job descriptions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.modules.job.matching import SKILL_ALIASES
from app.modules.job.models import Job

REQUIRED_MARKERS = (
    "required",
    "must have",
    "must-have",
    "must possess",
    "need to have",
    "needs to have",
    "minimum",
)
PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "plus",
    "ideally",
)
IMPORTANT_MARKERS = (
    "required",
    "must",
    "responsibil",
    "qualification",
    "experience",
    "degree",
    "skill",
    "location",
    "remote",
    "hybrid",
    "on-site",
    "onsite",
    "deadline",
)


@dataclass(frozen=True, slots=True)
class JobAnalysisResult:
    job: dict[str, Any]
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


class JobAnalysisService:
    """Extract reviewable requirement signals without persisting or inferring facts."""

    def analyze(self, job: Job) -> JobAnalysisResult:
        text = " ".join(part for part in (job.title, job.description) if part).strip()
        sentences = _sentences(job.description)
        skill_contexts = _skill_contexts(text)
        required_skills = _skills_for_context(skill_contexts, REQUIRED_MARKERS)
        preferred_skills = _skills_for_context(skill_contexts, PREFERRED_MARKERS)

        for skill_name, context in skill_contexts.items():
            if skill_name not in required_skills and skill_name not in preferred_skills:
                if _contains_marker(context, PREFERRED_MARKERS):
                    preferred_skills.append(skill_name)
                else:
                    required_skills.append(skill_name)

        experience_requirement = _extract_experience_requirement(text)
        education_requirement = _extract_education_requirement(text)
        work_mode = _extract_work_mode(text)
        important_requirements = _important_requirements(sentences)
        unknowns = _unknowns(
            job=job,
            experience_requirement=experience_requirement,
            education_requirement=education_requirement,
            work_mode=work_mode,
            required_skills=required_skills,
        )
        ambiguities = _ambiguities(text, sentences)

        return JobAnalysisResult(
            job={
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "source": job.source,
                "external_job_id": job.external_job_id,
                "external_url": job.external_url,
            },
            role=job.title,
            required_skills=sorted(set(required_skills)),
            preferred_skills=sorted(set(preferred_skills)),
            experience_requirement=experience_requirement,
            education_requirement=education_requirement,
            location=job.location,
            work_mode=work_mode,
            employment_type=job.employment_type,
            important_requirements=important_requirements,
            unknowns=unknowns,
            ambiguities=ambiguities,
        )


def _skill_contexts(text: str) -> dict[str, str]:
    normalized_text = text.casefold()
    contexts: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        positions = [normalized_text.find(alias.casefold()) for alias in aliases]
        positions = [position for position in positions if position >= 0]
        if positions:
            position = min(positions)
            contexts[canonical] = normalized_text[max(0, position - 100) : position + 140]
    return contexts


def _skills_for_context(contexts: dict[str, str], markers: tuple[str, ...]) -> list[str]:
    return [skill for skill, context in contexts.items() if _contains_marker(context, markers)]


def _contains_marker(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[\n.!?]+", text) if sentence.strip()]


def _important_requirements(sentences: list[str]) -> list[str]:
    result: list[str] = []
    for sentence in sentences:
        if _contains_marker(sentence.casefold(), IMPORTANT_MARKERS):
            result.append(sentence)
    return _unique(result)[:10]


def _extract_experience_requirement(text: str) -> str | None:
    patterns = (
        r"\b(?:at least\s+)?\d+\+?\s+years?(?: of)?(?: relevant)? experience\b",
        r"\b(?:entry[- ]level|new grad(?:uate)?|recent graduate|no experience required)\b",
        r"\b(?:internship|intern) experience\b",
    )
    return _first_match(text, patterns)


def _extract_education_requirement(text: str) -> str | None:
    patterns = (
        r"\b(?:bachelor'?s?|master'?s?|ph\.d\.?|doctorate|associate'?s?)\b"
        r"(?: degree)?(?: in [a-z][a-z &/-]+)?",
        r"\bdegree in [a-z][a-z &/-]+",
        r"\b(?:computer science|software engineering|information technology) degree\b",
    )
    return _first_match(text, patterns)


def _extract_work_mode(text: str) -> str:
    normalized = text.casefold()
    if "hybrid" in normalized:
        return "hybrid"
    if "on-site" in normalized or "onsite" in normalized or "on site" in normalized:
        return "on-site"
    if "remote" in normalized:
        return "remote"
    return "unknown"


def _unknowns(
    *,
    job: Job,
    experience_requirement: str | None,
    education_requirement: str | None,
    work_mode: str,
    required_skills: list[str],
) -> list[str]:
    unknowns: list[str] = []
    if not job.location:
        unknowns.append("Location is not provided.")
    if work_mode == "unknown":
        unknowns.append("Work mode is not specified.")
    if experience_requirement is None:
        unknowns.append("Experience requirement is not clearly specified.")
    if education_requirement is None:
        unknowns.append("Education requirement is not clearly specified.")
    if not required_skills:
        unknowns.append("Required skills are not clearly specified.")
    return unknowns


def _ambiguities(text: str, sentences: list[str]) -> list[str]:
    ambiguities: list[str] = []
    normalized = text.casefold()
    if "or equivalent" in normalized or "equivalent experience" in normalized:
        ambiguities.append("The posting allows an equivalent qualification or experience path.")
    if "preferred" in normalized and "required" in normalized:
        ambiguities.append(
            "The posting contains both required and preferred qualification language."
        )
    if any(
        "remote" in sentence.casefold() and "hybrid" in sentence.casefold()
        for sentence in sentences
    ):
        ambiguities.append("The posting mentions both remote and hybrid work modes.")
    return _unique(ambiguities)


def _first_match(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.casefold()
        if normalized not in seen:
            seen.add(normalized)
            result.append(value)
    return result