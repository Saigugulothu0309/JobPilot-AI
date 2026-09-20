# CHANGE-0016

## CHANGE ID
CHANGE-0016

## STATUS
COMPLETED

## DATE
2026-09-06

## SUMMARY
Implemented the Job Ranking Foundation as an authenticated, deterministic, explainable ranking layer over normalized jobs, approved candidate matching, and user-owned career preferences.

## SCOPE
This change covers the first advisory ranking slice of FR-09. It ranks a bounded set of normalized jobs using the existing deterministic match score and explicit saved preferences. It keeps hard conflicts separate from soft preference fit and exposes reasons and unknowns.

This change does not add persistence, recommendation history, preference learning, AI ranking, application preparation, application tracking, notifications, or CHANGE-0017.

## ARCHITECTURE
Authenticated request -> `JobService.search()` -> `ProfileService.get_preferences()` -> `JobMatchingService` plus `JobAnalysisService` -> `JobRankingService` -> structured ranked response.

The ranking service reads shared normalized jobs and the authenticated user’s approved candidate/profile boundary. It does not modify jobs, profiles, preferences, or match results.

## FILES CHANGED
- backend/app/modules/job/ranking.py
- backend/app/modules/job/api.py
- backend/app/modules/job/schemas.py
- backend/tests/test_job.py
- docs/changes/CHANGE-0016.md
- docs/changes/CHANGELOG.md

## API
Added:

- `GET /api/v1/jobs/rank`

Supported query parameters:

- `keyword`: optional title/description search filter
- `company`: optional company filter
- `location`: optional location filter
- `source`: optional source filter
- `limit`: 1 through 100, default 20
- `offset`: non-negative pagination offset

The response includes ranked jobs, total count, pagination values, and `preference_state` (`CONFIGURED` or `NOT_CONFIGURED`). Each ranked item includes rank, ranking score, eligibility state, reasons, unknowns, and the existing explainable match payload.

## RANKING POLICY
The deterministic ranking score is:

- match score: 70%
- preference fit: 30%

Preference fit considers only explicitly provided values:

- target role overlap
- employment type
- work mode
- location overlap
- technology mentions

Eligibility states are separate from the score:

- `ELIGIBLE`: no hard conflict and no unresolved ranking unknowns
- `REVIEW`: no hard conflict, but relevant job or preference information is unknown or mismatched
- `NOT_RECOMMENDED`: an explicit exclusion, deal-breaker, or supported hard work-mode conflict is detected

`NOT_RECOMMENDED` items are placed after eligible/review items and receive a zero ranking score. Missing information is surfaced as unknown rather than silently converted into a hard rejection.

## SECURITY
- Ranking requires bearer authentication.
- Candidate data is loaded only for the authenticated user.
- Jobs remain shared records and are never modified.
- Preferences are read through the existing profile ownership boundary.
- No client-supplied user or profile identifier is accepted.
- No external content is fetched and no AI or agent execution is involved.

## DATABASE
NO DATABASE SCHEMA CHANGES

Ranking is computed in memory from existing normalized jobs, approved candidate data, analysis signals, and career preferences. No ranking result is persisted.

## TESTS
Added coverage for:

- preference-aware ranking order
- hard-conflict separation and `NOT_RECOMMENDED` behavior
- explainable reasons and unknowns
- deterministic repeated ranking
- no-write behavior
- unauthenticated access rejection

## VALIDATION
- Focused job suite: 19 passed.
- Full backend pytest suite: run as final validation.
- Focused Ruff and full MyPy: run as final validation.
- Offline Alembic validation: run as final validation; no migration is expected for this change.

## KNOWN ISSUES
- Ranking currently evaluates at most the first 100 filtered normalized jobs before applying offset and limit. This keeps the foundation bounded and responsive but is not a full-dataset ranking strategy.
- Preference interpretation is intentionally deterministic and conservative; arbitrary free-text hard constraints are not treated as universal eligibility rules.
- Freshness and source confidence are not yet available as structured ranking inputs in the normalized job model.

## ROLLBACK
1. Remove the `GET /api/v1/jobs/rank` route and ranking response schemas.
2. Remove `JobRankingService` and its regression tests.
3. Revert the CHANGE-0016 documentation and changelog entry.
4. No database rollback is required because no schema migration was introduced.

## NEXT ACTION
Stop after CHANGE-0016. Do not begin CHANGE-0017 automatically.
