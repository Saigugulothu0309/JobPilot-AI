# CHANGE-0022

## STATUS
COMPLETED

## DATE
2026-09-07

## SUMMARY
Implemented the User Feedback Foundation for owner-scoped, explicitly user-attributed opportunity signals and corrections.

## SCOPE
This change implements FR-18.1 through FR-18.4. An authenticated user can record and list feedback for a normalized job: interested, not interested, incorrect, missing skill, wrong preference, and already applied. Each feedback record is explicitly marked `USER` sourced.

Feedback is deliberately one-time and informational. It does not alter profile facts, career preferences, ranking, matching, draft approval, application tracking, or submission state. A later, explicitly designed confirmation workflow would be required before any feedback could affect durable preferences or future ranking. This change does not begin CHANGE-0023.

## API
- `POST /api/v1/feedback`
- `GET /api/v1/feedback?limit=50&offset=0`

Posting the same feedback category for the same user and job updates that user's note rather than creating a duplicate signal. This preserves a bounded, user-editable one-time signal without learning a preference.

## DATABASE
Added Alembic revision `0013_create_job_feedback`. The `job_feedback` table records authenticated-profile ownership, normalized job, feedback category, optional note, immutable `USER` source, and timestamps. Profile or job deletion cascades feedback deletion.

## SECURITY AND HUMAN CONTROL
- All feedback endpoints require bearer authentication and use the authenticated profile ownership boundary.
- No client-supplied profile or owner identifier is accepted.
- Feedback is distinguishable from activity, AI assumptions, preference state, and application status through its `source: USER` field.
- `ALREADY_APPLIED` is only a user feedback signal; it does not create a record or claim an external submission occurred.
- Feedback does not approve materials, modify personal facts, change rankings, or trigger an external action.

## FILES CHANGED
- backend/app/api/router.py
- backend/app/modules/feedback/__init__.py
- backend/app/modules/feedback/api.py
- backend/app/modules/feedback/models.py
- backend/app/modules/feedback/schemas.py
- backend/app/modules/feedback/service.py
- backend/alembic/env.py
- backend/alembic/versions/0013_create_job_feedback.py
- backend/tests/test_activity.py
- backend/tests/test_database.py
- docs/changes/CHANGE-0022.md
- docs/changes/CHANGELOG.md

## VALIDATION
- Focused feedback/activity/application/database tests: run as final validation.
- Full backend pytest suite, Ruff, MyPy, and offline Alembic SQL validation: run as final validation.

## KNOWN LIMITATIONS
- Feedback does not yet have a separate correction-review or explicit preference-confirmation workflow.
- Historical versions of a repeated same-category feedback note are not retained.
- Feedback does not influence matching or ranking in this foundation.

## ROLLBACK
1. Downgrade `0013_create_job_feedback` in an approved database environment.
2. Remove the feedback module, router registration, activity event, and regression tests.
3. Revert this note and changelog row.

## NEXT ACTION
Stop after CHANGE-0022. Do not begin CHANGE-0023 automatically.
