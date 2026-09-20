"""Deterministic ranking of normalized jobs for an authenticated candidate."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.modules.job.analysis import JobAnalysisService
from app.modules.job.matching import JobMatchingService, MatchResult
from app.modules.job.models import Job
from app.modules.profile.models import CareerPreferences


@dataclass(frozen=True, slots=True)
class RankedJobResult:
    rank: int
    ranking_score: float
    eligibility: str
    reasons: list[str]
    unknowns: list[str]
    match: MatchResult


class JobRankingService:
    """Rank jobs using explicit preferences and the existing deterministic match."""

    def __init__(self, matching_service: JobMatchingService) -> None:
        self.matching_service = matching_service
        self.analysis_service = JobAnalysisService()

    def rank_jobs(
        self,
        user_id: UUID,
        jobs: list[Job],
        preferences: CareerPreferences | None,
    ) -> list[RankedJobResult]:
        ranked: list[tuple[Job, RankedJobResult]] = []
        for job in jobs:
            match = self.matching_service.match_user_to_job(user_id, job)
            analysis = self.analysis_service.analyze(job)
            preference_score, reasons, unknowns, hard_conflict = _preference_signals(
                job, analysis, preferences
            )
            score = round(match.overall_score * 0.7 + preference_score * 0.3, 2)
            if hard_conflict:
                eligibility = "NOT_RECOMMENDED"
                score = 0.0
            elif unknowns:
                eligibility = "REVIEW"
            else:
                eligibility = "ELIGIBLE"
            ranked.append(
                (
                    job,
                    RankedJobResult(
                        rank=0,
                        ranking_score=score,
                        eligibility=eligibility,
                        reasons=reasons,
                        unknowns=unknowns,
                        match=match,
                    ),
                )
            )

        ranked.sort(key=lambda item: _sort_key(item[0], item[1]))
        return [
            RankedJobResult(
                rank=index,
                ranking_score=result.ranking_score,
                eligibility=result.eligibility,
                reasons=result.reasons,
                unknowns=result.unknowns,
                match=result.match,
            )
            for index, (_, result) in enumerate(ranked, start=1)
        ]


def _preference_signals(
    job: Job,
    analysis: Any,
    preferences: CareerPreferences | None,
) -> tuple[float, list[str], list[str], bool]:
    if preferences is None:
        return 0.0, [], ["Career preferences are not configured."], False

    text = " ".join((job.title, job.company, job.description)).casefold()
    reasons: list[str] = []
    unknowns = list(analysis.unknowns)
    hard_conflict = _has_explicit_conflict(text, analysis.work_mode, preferences)
    if hard_conflict:
        reasons.append("An explicit user exclusion or hard constraint conflicts with this job.")

    components: list[float] = []
    role_score = _list_overlap_score(job.title, preferences.target_roles)
    if preferences.target_roles:
        components.append(role_score)
        if role_score > 0:
            reasons.append("The role aligns with a saved target role.")
        else:
            unknowns.append("The role does not match a saved target role exactly.")

    employment_score = _value_score(job.employment_type, preferences.employment_types)
    if preferences.employment_types:
        components.append(employment_score)
        if employment_score > 0:
            reasons.append("Employment type matches a saved preference.")
        else:
            unknowns.append("Employment type does not match a saved preference.")

    work_mode_score = _value_score(analysis.work_mode, preferences.work_modes)
    if preferences.work_modes:
        components.append(work_mode_score)
        if work_mode_score > 0:
            reasons.append("Work mode matches a saved preference.")
        elif analysis.work_mode == "unknown":
            unknowns.append("Work mode preference cannot be evaluated from the job.")

    location_score = _list_overlap_score(job.location or "", preferences.locations)
    if preferences.locations:
        components.append(location_score)
        if location_score > 0:
            reasons.append("Location overlaps a saved preference.")
        elif not job.location:
            unknowns.append("Location preference cannot be evaluated because location is missing.")

    technology_score = _list_overlap_score(text, preferences.technologies)
    if preferences.technologies:
        components.append(technology_score)
        if technology_score > 0:
            reasons.append("The job mentions saved technology interests.")

    score = sum(components) / len(components) if components else 0.0
    return min(100.0, round(score, 2)), reasons, _unique(unknowns), hard_conflict


def _has_explicit_conflict(
    text: str,
    work_mode: str,
    preferences: CareerPreferences,
) -> bool:
    negative_terms = [*preferences.exclusions, *preferences.deal_breakers]
    if any(_normalize_term(term) in text for term in negative_terms):
        return True
    hard_text = " ".join(preferences.hard_constraints).casefold()
    if "remote only" in hard_text and work_mode not in {"remote", "unknown"}:
        return True
    if "hybrid only" in hard_text and work_mode not in {"hybrid", "unknown"}:
        return True
    if "on-site only" in hard_text and work_mode not in {"on-site", "unknown"}:
        return True
    return False


def _list_overlap_score(value: str, preferences: list[str]) -> float:
    if not value or not preferences:
        return 0.0
    normalized_value = _normalize_term(value)
    return 100.0 if any(_normalize_term(item) in normalized_value for item in preferences) else 0.0


def _value_score(value: str | None, preferences: list[str]) -> float:
    if value is None or not preferences:
        return 0.0
    normalized = value.casefold().replace("-", "_")
    normalized_preferences = {
        item.casefold().replace("-", "_") for item in preferences
    }
    return 100.0 if normalized in normalized_preferences else 0.0


def _sort_key(job: Job, result: RankedJobResult) -> tuple[int, float, UUID]:
    eligibility_order = {"ELIGIBLE": 0, "REVIEW": 1, "NOT_RECOMMENDED": 2}
    return eligibility_order[result.eligibility], -result.ranking_score, job.id


def _normalize_term(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#.]+", " ", value.casefold())).strip()


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value.casefold() not in seen:
            seen.add(value.casefold())
            result.append(value)
    return result