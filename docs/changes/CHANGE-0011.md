# CHANGE-0011

## CHANGE ID
CHANGE-0011

## STATUS
COMPLETED

## DATE
2026-09-04

## SUMMARY
Implemented the Job Source Integration Foundation for importing normalized shared job listings through a source adapter boundary and an admin-controlled local test ingestion path.

## WHY
Future job sources should provide normalized jobs without forcing the core job model or application workflow to understand provider-specific formats. This change establishes the shared persistence and deduplication boundary without integrating or scraping any production job website.

## ARCHITECTURE
`JobSource` defines the source adapter contract with `source_name`, `fetch_jobs()`, and `normalize_job()`. `LocalJobSource` is the safe in-memory adapter for tests and local development.

The flow is:

Local source records -> JobSource -> NormalizedJob -> JobService -> JobRepository -> shared Job table

Jobs are shared system data and are not associated with users, profiles, resumes, or professional records.

## FILES CHANGED
- backend/app/api/router.py
- backend/app/core/config.py
- backend/app/modules/job/__init__.py
- backend/app/modules/job/api.py
- backend/app/modules/job/models.py
- backend/app/modules/job/repository.py
- backend/app/modules/job/schemas.py
- backend/app/modules/job/service.py
- backend/app/modules/job/sources.py
- backend/alembic/env.py
- backend/alembic/versions/0006_create_jobs.py
- backend/tests/test_database.py
- backend/tests/test_job.py
- docs/changes/CHANGE-0011.md
- docs/changes/CHANGELOG.md

## DATABASE
Added Alembic revision `0006_create_jobs` with one shared `jobs` table.

The table contains only normalized foundation fields: title, company, location, description, employment type, source, external identifier, external URL, posted timestamp, deduplication key, and timestamps. It has no candidate ownership foreign key.

The unique `dedupe_key` constraint prevents duplicate normalized jobs during repeated ingestion.

## API
Added the minimum protected ingestion endpoint:

- `POST /api/v1/jobs/ingest/local`

The endpoint requires a valid bearer token and the authenticated email must be listed in `JOB_INGESTION_ADMIN_EMAILS`. It accepts validated local source records and returns normalized persisted jobs plus created/updated counts.

No public job search or candidate-facing job workflow was added.

## DEPENDENCIES
No new runtime dependencies were added. Existing FastAPI, Pydantic, SQLAlchemy, and Alembic dependencies are reused.

## SECURITY
- Ingestion is authenticated and admin-controlled through an environment-backed email allowlist.
- Jobs are not attached to candidate profiles or users.
- External URLs are validated as HTTP URLs and are stored as data only; they are never treated as filesystem paths or fetched.
- Source descriptions are not executed or logged.
- No credentials, API keys, scraping, browser automation, or external provider integration was introduced.

## TESTS
Added `backend/tests/test_job.py` coverage for:

- normalized job creation
- source attribution
- external identifier storage
- repeated ingestion deduplication
- distinct external jobs
- fallback deduplication when no external identifier exists
- missing optional source fields
- malformed source data rejection
- local source normalization
- unauthenticated and non-admin ingestion rejection
- successful admin-controlled ingestion

The database metadata regression test was updated to include the jobs table.

## VALIDATION
- Focused pytest: 10 passed.
- Full backend pytest: run as part of final validation.
- Focused Ruff for new job code and migration: passed.
- Focused MyPy for the new job module and wiring: passed.
- Offline Alembic SQL generation: run as part of final validation and verified revision `0006_create_jobs`.

## KNOWN ISSUES
- The existing `alembic/env.py` has repository-wide Ruff import-order and unused-import findings inherited from its metadata-loading convention; it was not refactored because that is unrelated to CHANGE-0011.
- No live PostgreSQL service is available in this environment, so the migration is validated through offline SQL generation and SQLite test metadata creation.
- The local adapter is intentionally not a production external provider and does not fetch remote jobs.

## ROLLBACK
1. Downgrade Alembic revision `0006_create_jobs` in an approved database environment.
2. Remove the job router registration and job module files.
3. Remove the `JOB_INGESTION_ADMIN_EMAILS` setting.
4. Revert the job metadata test and documentation updates.
5. Existing authentication, profile, resume, parsing, and approval flows remain unchanged.

## NEXT ACTION
Stop after CHANGE-0011. Do not begin CHANGE-0012 automatically.
