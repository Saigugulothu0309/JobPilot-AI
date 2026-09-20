# CHANGE-0012

## CHANGE ID
CHANGE-0012

## STATUS
COMPLETED

## DATE
2026-09-04

## SUMMARY
Implemented the read-only Job Search & Query Foundation over the normalized shared jobs created by CHANGE-0011.

## WHY
The application needs a deterministic discovery boundary for normalized jobs before later matching or recommendation work. Search belongs in the job repository and service layers so the API remains thin and future sources continue to use the same core job model.

## ARCHITECTURE
HTTP query parameters -> `JobService.search()` -> `JobRepository.search()` -> normalized `Job` records.

The repository applies filters, counts matches, paginates, and orders results by `created_at DESC` followed by `id ASC` as a stable tie-breaker. Existing ingestion, source adapters, and deduplication are unchanged.

## FILES CHANGED
- backend/app/modules/job/api.py
- backend/app/modules/job/repository.py
- backend/app/modules/job/schemas.py
- backend/app/modules/job/service.py
- backend/tests/test_job.py
- docs/changes/CHANGE-0012.md
- docs/changes/CHANGELOG.md

## DATABASE
No migration was required. The existing CHANGE-0011 `jobs` schema already contains all fields needed for keyword and metadata filtering. Search is read-only and adds no indexes or tables.

## API
Added:

- `GET /api/v1/jobs`

Supported query parameters:

- `keyword` or `q`: case-insensitive search across title and description
- `company`: case-insensitive partial company filter
- `location`: case-insensitive partial location filter
- `source`: case-insensitive source filter
- `limit`: 1 through 100, default 20
- `offset`: non-negative pagination offset, default 0

The response contains `jobs`, `total`, `limit`, and `offset`. Job results include normalized identity, description, source attribution, source job identifier, URL, posted timestamp, and lifecycle timestamps. The existing `external_job_id` and `external_url` names remain available for ingestion compatibility.

## DEPENDENCIES
No new dependencies were added.

## SECURITY
- Search is read-only and does not alter ingestion or shared job records.
- No candidate ownership or profile access behavior was changed.
- Query values are validated and bounded by FastAPI/Pydantic constraints.
- No external websites, URLs, credentials, or job content are fetched or executed.

## TESTS
Expanded `backend/tests/test_job.py` coverage for:

- empty job database
- keyword search across title and description
- company, location, and source filters
- pagination and safe limits
- deterministic ordering
- multiple matching jobs
- no-match behavior
- malformed query parameters
- existing ingestion and deduplication behavior
- required `source_job_id` and `url` response fields

## VALIDATION
- Focused job pytest: 12 passed.
- Full backend pytest: run as final validation.
- Focused Ruff and MyPy: run as final validation.
- No Alembic SQL generation was required because the existing schema is sufficient.

## KNOWN ISSUES
- Repository-wide Ruff may report pre-existing findings in older Alembic files and `alembic/env.py`; these are unrelated to the search implementation and were not changed.
- Search uses database `ILIKE` semantics and simple partial matching; relevance ranking and semantic matching are intentionally out of scope.
- No production job source or external API integration was added.

## ROLLBACK
1. Remove the `GET /api/v1/jobs` route and response schema additions.
2. Remove the search methods from `JobService` and `JobRepository`.
3. Revert the search regression tests and documentation updates.
4. No database rollback is required.

## NEXT ACTION
Stop after CHANGE-0012. Do not begin CHANGE-0013 automatically.
