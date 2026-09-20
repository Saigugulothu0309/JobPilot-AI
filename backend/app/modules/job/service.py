"""Job source ingestion and normalized persistence service."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.job.models import Job
from app.modules.job.repository import JobRepository
from app.modules.job.sources import JobSource


@dataclass(frozen=True, slots=True)
class JobIngestionResult:
    source: str
    jobs: list[Job]
    created_count: int
    updated_count: int


@dataclass(frozen=True, slots=True)
class JobSearchResult:
    jobs: list[Job]
    total: int
    limit: int
    offset: int


class JobService:
    def __init__(self, session: Session) -> None:
        self.repository = JobRepository(session)

    def get_by_id(self, job_id: UUID) -> Job | None:
        return self.repository.get_by_id(job_id)

    def ingest(self, source: JobSource) -> JobIngestionResult:
        normalized_jobs = [source.normalize_job(raw_job) for raw_job in source.fetch_jobs()]
        jobs: list[Job] = []
        created_count = 0
        updated_count = 0
        seen_keys: set[str] = set()

        for normalized_job in normalized_jobs:
            if normalized_job.dedupe_key in seen_keys:
                continue
            seen_keys.add(normalized_job.dedupe_key)
            existing = self.repository.get_by_dedupe_key(normalized_job.dedupe_key)
            if existing is None:
                jobs.append(self.repository.create(normalized_job))
                created_count += 1
            else:
                jobs.append(self.repository.update(existing, normalized_job))
                updated_count += 1

        return JobIngestionResult(
            source=source.source_name,
            jobs=self.repository.save_all(jobs),
            created_count=created_count,
            updated_count=updated_count,
        )

    def search(
        self,
        *,
        keyword: str | None,
        company: str | None,
        location: str | None,
        source: str | None,
        limit: int,
        offset: int,
    ) -> JobSearchResult:
        jobs, total = self.repository.search(
            keyword=keyword,
            company=company,
            location=location,
            source=source,
            limit=limit,
            offset=offset,
        )
        return JobSearchResult(jobs=jobs, total=total, limit=limit, offset=offset)
