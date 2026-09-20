# CHANGE-0020

## CHANGE ID
CHANGE-0020

## STATUS
COMPLETED

## DATE
2026-09-07

## SUMMARY
Implemented the Agent Activity Foundation: an authenticated, owner-scoped timeline of meaningful internal workflow activity and its next required user action.

## SCOPE
This change implements FR-16.1 through FR-16.3. It records visibility events for opportunity input, job analysis, matching, drafting, warnings, paused approval, explicit approval, and recoverable failures. Each event has a state, a human-readable message, related job/draft identifiers where applicable, and a `next_action` in its non-sensitive details.

This change does not implement notifications (FR-17), reminders, activity-history enhancements, audit logging beyond the FR-16 activity timeline, agent/AI execution, browser automation, external action, or CHANGE-0021.

## ARCHITECTURE
Authenticated workflow endpoint -> existing owner/profile boundary -> activity event persistence -> authenticated owner-scoped activity retrieval.

Activity is attached to the authenticated user's profile. Shared normalized jobs remain shared; activity events are private and are never used to change jobs, profiles, drafts, approvals, or application records.

## FILES CHANGED
- backend/app/modules/activity/service.py
- backend/app/modules/application/api.py
- backend/app/modules/application/service.py
- backend/app/modules/job/api.py
- backend/tests/test_activity.py
- backend/tests/test_database.py
- docs/changes/CHANGE-0020.md
- docs/changes/CHANGELOG.md

## DATABASE
Added Alembic revision `0011_create_activity_events`.

The `activity_events` table contains the owning profile, event type, state, message, optional job/draft/application-record references, non-sensitive details, and timestamp. Profile deletion cascades activity deletion; removed referenced jobs, drafts, or records are set to null.

## API
Added:

- `GET /api/v1/activity?limit=50&offset=0`

The endpoint requires bearer authentication, returns only the caller's profile events in deterministic newest-first order, and supports bounded pagination. It exposes no client-supplied ownership controls.

## SECURITY AND HUMAN CONTROL
- Activity retrieval and recording use the authenticated profile ownership boundary.
- Another user cannot read a user's events.
- Read-only job actions available before profile creation remain usable; activity is skipped rather than creating a shared or unowned event.
- Event details contain workflow context and next actions only, never credentials or external-action authority.
- Activity does not imply draft approval, application submission, or completion of an uncertain external action.
- Failed and paused states remain visible as such; no event claims completion for an unsuccessful or uncertain operation.

## TESTS
Added coverage for:

- authenticated activity retrieval
- owner isolation
- opportunity input, analysis, warning, drafting, and approval event visibility
- explicit next-action guidance
- metadata registration of the activity table

## VALIDATION
- Focused activity/application/database tests: run as final validation.
- Full backend pytest suite: run as final validation.
- Ruff and MyPy: run as final validation.
- Offline Alembic SQL generation: run as final validation and verify revision `0011_create_activity_events`.

## KNOWN LIMITATIONS
- The timeline is an activity foundation, not a complete FR-20 audit trail.
- Failure visibility is recorded only when a caller has an owned profile to safely scope the event.
- No notification delivery, scheduled reminder, background agent, external status verification, or activity deletion/export UI is included.

## ROLLBACK
1. Downgrade Alembic revision `0011_create_activity_events` in an approved database environment.
2. Remove the activity module, router registration, workflow event calls, and regression tests.
3. Revert this change note and changelog entry.

## NEXT ACTION
Stop after CHANGE-0020. Do not begin CHANGE-0021 automatically.
