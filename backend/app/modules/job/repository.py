"""Persistence boundary for normalized jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.job.models import Job
from app.modules.job.sources import NormalizedJob


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, job_id: UUID) -> Job | None:
        return self.session.get(Job, job_id)

    def get_by_dedupe_key(self, dedupe_key: str) -> Job | None:
        return self.session.scalar(select(Job).where(Job.dedupe_key == dedupe_key))

    def search(
        self,
        *,
        keyword: str | None,
        company: str | None,
        location: str | None,
        source: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Job], int]:
        filters = []
        if keyword:
            pattern = f"%{keyword}%"
            filters.append(or_(Job.title.ilike(pattern), Job.description.ilike(pattern)))
        if company:
            filters.append(Job.company.ilike(f"%{company}%"))
        if location:
            filters.append(Job.location.ilike(f"%{location}%"))
        if source:
            filters.append(func.lower(Job.source) == source.casefold())

        base_query = select(Job).where(*filters)
        total = self.session.scalar(
            select(func.count()).select_from(base_query.order_by(None).subquery())
        )
        jobs = list(
            self.session.scalars(
                base_query.order_by(Job.created_at.desc(), Job.id.asc())
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return jobs, int(total or 0)

    def create(self, normalized_job: NormalizedJob) -> Job:
        job = Job(
            title=normalized_job.title,
            company=normalized_job.company,
            location=normalized_job.location,
            description=normalized_job.description,
            employment_type=normalized_job.employment_type,
            source=normalized_job.source,
            external_job_id=normalized_job.external_job_id,
            external_url=normalized_job.external_url,
            posted_at=normalized_job.posted_at,
            dedupe_key=normalized_job.dedupe_key,
        )
        self.session.add(job)
        return job

    def update(self, job: Job, normalized_job: NormalizedJob) -> Job:
        for field in (
            "title",
            "company",
            "location",
            "description",
            "employment_type",
            "source",
            "external_job_id",
            "external_url",
            "posted_at",
        ):
            setattr(job, field, getattr(normalized_job, field))
        return job

    def save_all(self, jobs: list[Job]) -> list[Job]:
        self.session.commit()
        for job in jobs:
            self.session.refresh(job)
        return jobs
