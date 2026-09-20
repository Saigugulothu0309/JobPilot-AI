"""Source abstraction and the deterministic local test adapter."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Protocol

from app.modules.job.schemas import LocalJobRecord


class JobSourceError(ValueError):
    """Raised when a source record cannot be normalized safely."""


@dataclass(frozen=True, slots=True)
class NormalizedJob:
    title: str
    company: str
    location: str | None
    description: str
    employment_type: str | None
    source: str
    external_job_id: str | None
    external_url: str | None
    posted_at: object | None
    dedupe_key: str


class JobSource(Protocol):
    """Interface implemented by every future job source adapter."""

    @property
    def source_name(self) -> str:
        ...

    def fetch_jobs(self) -> Iterable[object]:
        ...

    def normalize_job(self, raw_job: object) -> NormalizedJob:
        ...


class LocalJobSource:
    """Safe in-memory adapter for tests and local development."""

    source_name = "local"

    def __init__(self, records: Iterable[object]) -> None:
        self.records = tuple(records)

    def fetch_jobs(self) -> Iterable[object]:
        return self.records

    def normalize_job(self, raw_job: object) -> NormalizedJob:
        try:
            record = LocalJobRecord.model_validate(raw_job)
        except ValueError as exc:
            raise JobSourceError("Local job record is invalid") from exc

        external_url = str(record.external_url) if record.external_url is not None else None
        dedupe_key = build_dedupe_key(
            self.source_name,
            record.external_job_id,
            record.title,
            record.company,
            record.location,
            external_url,
        )
        return NormalizedJob(
            title=record.title,
            company=record.company,
            location=record.location,
            description=record.description,
            employment_type=record.employment_type,
            source=self.source_name,
            external_job_id=record.external_job_id,
            external_url=external_url,
            posted_at=record.posted_at,
            dedupe_key=dedupe_key,
        )


def build_dedupe_key(
    source: str,
    external_job_id: str | None,
    title: str,
    company: str,
    location: str | None,
    external_url: str | None,
) -> str:
    """Use source identity first, then a stable normalized field fallback."""
    if external_job_id:
        identity = f"id:{external_job_id.strip().casefold()}"
    else:
        fields = (title, company, location or "", external_url or "")
        identity = "fields:" + "|".join(_normalize_identity(value) for value in fields)
    return sha256(f"{source.casefold()}|{identity}".encode("utf-8")).hexdigest()


def _normalize_identity(value: str) -> str:
    return " ".join(value.casefold().split())
