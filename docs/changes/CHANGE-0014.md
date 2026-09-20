# CHANGE-0014

## CHANGE ID
CHANGE-0014

## STATUS
COMPLETED

## DATE
2026-09-06

## SUMMARY
Implemented the Job Analysis Foundation as a read-only, deterministic analysis layer for normalized shared jobs.

## SCOPE
This change covers FR-07 only. It identifies reviewable role and requirement signals from an existing normalized `Job` record without persisting an interpretation, changing matching behavior, ranking opportunities, preparing applications, or tracking applications.

CHANGE-0015 was not started.

## WHY
CHANGE-0013 compares approved candidate data with normalized jobs, but the job side still relied on raw title and description text. Job analysis establishes a structured boundary for required and preferred skills, experience, education, location, work mode, employment type, important requirements, and uncertainty before later product capabilities consume those signals.

## ARCHITECTURE
Authenticated request -> `JobService.get_by_id()` -> `JobAnalysisService.analyze()` -> structured `JobAnalysisResponse`.

The service reads normalized job fields only. Description text is treated as untrusted data: it is parsed as text, never executed, fetched, or allowed to change application instructions.

## FILES CHANGED
- backend/app/modules/job/analysis.py
- backend/app/modules/job/api.py
- backend/app/modules/job/schemas.py
- backend/tests/test_job.py
- docs/changes/CHANGE-0014.md
- docs/changes/CHANGELOG.md

## API
Added:

- `POST /api/v1/jobs/{job_id}/analyze`

The endpoint requires authentication because job analysis is part of the authenticated product workflow, while the normalized job itself remains shared data. It returns `404` when the job does not exist.

The response contains:

- normalized job identity and source attribution
- role/title
- required skills
- preferred skills
- experience requirement when explicitly stated
- education requirement when explicitly stated
- normalized job location
- detected work mode or `unknown`
- employment type
- important requirement sentences
- explicit unknowns for missing or unclear information
- ambiguity warnings for equivalent paths and conflicting requirement language

## ANALYSIS POLICY
- Known skill aliases are detected deterministically using the existing job-matching skill vocabulary.
- Required and preferred classifications use explicit requirement markers such as `required`, `must have`, `preferred`, `nice to have`, and `bonus`.
- Experience and education values are returned only when the posting contains recognizable text; missing information remains unknown.
- Work mode is limited to `remote`, `hybrid`, `on-site`, or `unknown`.
- No semantic similarity, LLM inference, legal eligibility decision, or unsupported qualification claim is introduced.
- Results are generated in memory and are not written to the database.

## DATABASE
NO DATABASE SCHEMA CHANGES

The existing `jobs` table contains all source fields needed by this deterministic foundation. No Alembic migration was added.

## SECURITY
- Authentication is enforced by the existing bearer-token boundary.
- Job ownership is not invented; jobs remain shared normalized records.
- The route accepts no user or profile identifier.
- External job content is parsed as inert input and is never executed or fetched.
- No credentials, secrets, or raw internal storage details are returned.

## TESTS
Added coverage for:

- required and preferred skill extraction
- experience, education, work-mode, location, and employment-type signals
- important requirement extraction
- equivalent qualification and mixed requirement ambiguity warnings
- explicit unknown states for missing job information
- authentication and missing-job behavior
- deterministic repeated output
- no-write behavior through before/after normalized job responses

## VALIDATION
- Focused job suite: 16 passed.
- Full backend pytest suite: run as final validation.
- Ruff and MyPy: run as final validation.
- Offline Alembic SQL generation: run as final validation; no migration is expected for this change.

## KNOWN ISSUES
- The analyzer is intentionally deterministic and marker-based. It does not claim semantic understanding of arbitrary job language.
- The current normalized job model does not yet store separate structured work mode, compensation, deadline, or freshness fields; absent signals are reported as unknown rather than inferred.
- No ranking, application preparation, application tracking, or CHANGE-0015 work is included.

## ROLLBACK
1. Remove the `POST /api/v1/jobs/{job_id}/analyze` route.
2. Remove `JobAnalysisService`, analysis schemas, and regression tests.
3. Revert the CHANGE-0014 documentation and changelog entry.
4. No database rollback is required because no schema migration was introduced.

## NEXT ACTION
Stop after CHANGE-0014. Do not begin CHANGE-0015 automatically.
