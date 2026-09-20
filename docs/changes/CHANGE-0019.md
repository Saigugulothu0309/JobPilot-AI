# CHANGE-0019

## CHANGE ID
CHANGE-0019

## STATUS
COMPLETED

## DATE
2026-09-06

## SUMMARY
Implemented the Manual Application Tracking Foundation for owner-scoped application records.

## SCOPE
This change covers FR-15. It allows an authenticated user to create, view, list, and update a lightweight application record for a normalized job. The record stores manual status, notes, relevant dates, selected draft/material revision reference, and a preserved job snapshot.

This change does not submit applications, infer status from external systems, send notifications, perform browser automation, or begin CHANGE-0020.

## REQUIREMENTS
- FR-15.1: controlled application statuses are supported.
- FR-15.2: selected opportunity, dates, notes, and exact draft revision references are retained.
- FR-15.3: the system never marks a record submitted automatically.
- FR-15.4: unknown status uses the exact manual-verification message.

## ARCHITECTURE
Authenticated request -> profile ownership boundary -> `ApplicationRecordService` -> `ApplicationRecord` linked to normalized `Job` and optional `ApplicationDraft`.

Application records are private user workflow data. Jobs remain shared normalized records. The tracking layer never changes draft approval state and never performs an external application action.

## FILES CHANGED
- backend/app/modules/application/models.py
- backend/app/modules/application/schemas.py
- backend/app/modules/application/service.py
- backend/app/modules/application/api.py
- backend/alembic/env.py
- backend/alembic/versions/0010_create_application_records.py
- backend/tests/test_application.py
- backend/tests/test_database.py
- docs/changes/CHANGE-0019.md
- docs/changes/CHANGELOG.md

## DATABASE
Added Alembic revision `0010_create_application_records`.

The `application_records` table stores:

- authenticated profile ownership
- normalized job reference
- optional application draft reference
- controlled status
- user notes
- saved, applied, interview, and follow-up timestamps
- exact draft revision used when linked
- normalized job snapshot
- lifecycle timestamps

A unique profile/job constraint prevents duplicate tracking records for the same user and normalized job. Profile/job deletion cascades remove the record; deleting a linked draft clears the draft reference.

## API
Added:

- `POST /api/v1/applications/records`
- `GET /api/v1/applications/records`
- `GET /api/v1/applications/records/{record_id}`
- `PUT /api/v1/applications/records/{record_id}`

Supported statuses:

- `SAVED`
- `PREPARING`
- `READY_FOR_REVIEW`
- `APPROVED`
- `SUBMITTED`
- `INTERVIEW`
- `REJECTED`
- `OFFER`
- `WITHDRAWN`
- `UNKNOWN`

Status changes are user-supplied manual tracking updates. When `UNKNOWN` is selected, notes are normalized to:

`Submission status unknown — verify manually.`

## SECURITY AND HUMAN CONTROL
- All endpoints require bearer authentication.
- Records are scoped through the authenticated user’s profile.
- Cross-user access returns `404`.
- No client-supplied owner identifier is accepted.
- Creating or updating a tracking record does not approve a draft.
- `SUBMITTED` is never inferred or produced by an external integration; it can only be recorded through the user’s manual tracking request.
- No credentials, tokens, external URLs, or job content are executed or sent externally.

## TESTS
Added coverage for:

- creating and listing a tracking record
- preserving job and draft revision snapshots
- all manual status boundary behavior through representative statuses
- exact unknown submission wording
- duplicate record rejection
- manual status and note updates
- authentication enforcement
- cross-user ownership isolation
- missing profile ownership behavior
- metadata registration for the new table

## VALIDATION
- Focused application/database suite: 13 passed.
- Full backend pytest suite: run as final validation.
- Focused Ruff and full MyPy: run as final validation.
- Offline Alembic SQL generation: run as final validation and verified revision `0010_create_application_records`.

## KNOWN ISSUES
- Tracking is manual and does not verify external submission or interview events.
- Application records currently keep the latest linked draft revision reference rather than a separate immutable material-history table.
- Notifications, reminders, exports, audit history, and external integrations remain outside this change.

## ROLLBACK
1. Downgrade Alembic revision `0010_create_application_records` in an approved database environment.
2. Remove the application tracking routes, service, schemas, and model.
3. Remove the metadata expectation and tracking regression tests.
4. Revert the CHANGE-0019 documentation and changelog entry.

## NEXT ACTION
Stop after CHANGE-0019. Do not begin CHANGE-0020 automatically.
