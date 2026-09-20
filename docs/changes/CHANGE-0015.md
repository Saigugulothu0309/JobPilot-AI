# CHANGE-0015

## CHANGE ID
CHANGE-0015

## STATUS
COMPLETED

## DATE
2026-09-06

## SUMMARY
Implemented the Career Preferences Foundation as an authenticated, user-owned, validated preference layer for future matching and ranking workflows.

## SCOPE
This change covers the persisted foundation for FR-04. It allows a user to record target roles, employment preferences, locations, work modes, industries, technologies, career interests, exclusions, relocation preference, salary range, availability date, and explicitly separated hard constraints, ranking preferences, optional preferences, and deal-breakers.

This change does not implement ranking, automatic eligibility decisions, preference learning, recommendations, applications, notifications, or CHANGE-0016.

## ARCHITECTURE
Authenticated request -> profile ownership boundary -> `ProfileService` -> `CareerPreferencesRepository` -> one-to-one `career_preferences` record.

Preferences are owned through `profiles.user_id`. No request accepts a client-supplied `user_id` or `profile_id`. `PUT` replaces the preference snapshot for the authenticated user; `GET` returns only that user’s snapshot.

## FILES CHANGED
- backend/app/modules/profile/models.py
- backend/app/modules/profile/schemas.py
- backend/app/modules/profile/repository.py
- backend/app/modules/profile/service.py
- backend/app/modules/profile/api.py
- backend/alembic/env.py
- backend/alembic/versions/0007_create_career_preferences.py
- backend/tests/test_database.py
- backend/tests/test_profile.py
- docs/changes/CHANGE-0015.md
- docs/changes/CHANGELOG.md

## DATABASE
Added Alembic revision `0007_create_career_preferences`.

The `career_preferences` table is one-to-one with `profiles` through a unique `profile_id` foreign key with cascade deletion. It stores typed scalar values and JSON arrays for user-controlled preference categories. No preference is inferred from profile, resume, job, or behavior data.

## API
Added:

- `GET /api/v1/profile/preferences`
- `PUT /api/v1/profile/preferences`

Behavior:

- Both endpoints require bearer authentication.
- `PUT` creates the authenticated user’s profile if needed, then creates or replaces the owned preference record.
- `GET` returns `404` when the authenticated user has no preferences.
- Another user cannot read or modify the owner’s preference record.
- Employment type, work mode, and relocation values are normalized to controlled uppercase values.
- Salary ranges reject `salary_max` values below `salary_min`.
- Blank free-text preference values and unsupported enum values are rejected.

## PREFERENCE BOUNDARY
The response keeps these concepts separate:

- `hard_constraints`: conditions that may later affect eligibility when job evidence is clear.
- `ranking_preferences`: factors that may affect ordering but should not silently exclude an opportunity.
- `optional_preferences`: low-confidence or exploratory signals.
- `exclusions` and `deal_breakers`: user-declared negative signals, preserved without applying them automatically.

This change stores user intent but does not consume it in matching or ranking.

## SECURITY
- Preferences are private profile data and are scoped through the authenticated user.
- No client-supplied ownership identifier is accepted.
- Profile deletion cascades to the preference record through the database foreign key.
- Salary, availability, relocation, and deal-breaker values remain user-provided and editable.
- No AI inference, external integration, or secrets are involved.

## TESTS
Added coverage for:

- authenticated preference creation and retrieval
- list and scalar enum normalization
- hard/ranking/optional category preservation
- salary range validation
- unsupported work-mode validation
- unauthenticated access rejection
- missing preference behavior
- cross-user isolation
- metadata inclusion for the new table

## VALIDATION
- Focused profile/database suite: 18 passed.
- Full backend pytest suite: run as final validation.
- Focused Ruff and full MyPy: run as final validation.
- Offline Alembic SQL generation: run as final validation and verified revision `0007_create_career_preferences`.

## KNOWN ISSUES
- Preferences are stored as controlled JSON arrays rather than normalized child rows; this keeps the foundation compact but does not yet provide per-preference provenance or history.
- Ranking and eligibility behavior intentionally do not consume these fields yet.
- The repository retains pre-existing Ruff findings in older migration files and earlier matching code; those are outside CHANGE-0015.

## ROLLBACK
1. Downgrade Alembic revision `0007_create_career_preferences` in an approved database environment.
2. Remove the preferences routes, service, repository, schemas, and model relationship.
3. Remove the preference regression tests and metadata expectation.
4. Revert the CHANGE-0015 documentation and changelog entry.

## NEXT ACTION
Stop after CHANGE-0015. Do not begin CHANGE-0016 automatically.
