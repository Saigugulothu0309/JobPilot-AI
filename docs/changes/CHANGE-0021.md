# CHANGE-0021

## STATUS
COMPLETED

## DATE
2026-09-07

## SUMMARY
Implemented a private in-app Notification Foundation for meaningful, owner-scoped workflow events.

## SCOPE
This change implements the bounded in-app portion of FR-17. Users can see and acknowledge private notifications for a draft ready for review, a manually changed application status, an uncertain manual submission status, and recoverable draft-preparation failure.

The project documentation leaves external notification mechanics unresolved and classifies scheduled discovery/notifications as future. Consequently, this change does not add email, push, SMS, webhooks, scheduling, reminders, discovery, background workers, or any external action. It does not begin CHANGE-0022.

## API
- `GET /api/v1/notifications?limit=50&offset=0`
- `POST /api/v1/notifications/{notification_id}/read`

Notifications are newest-first, bounded, private to the authenticated profile, and idempotently deduplicated per meaningful workflow event. Marking a notification read is idempotent.

## DATABASE
Added Alembic revision `0012_create_notifications`. The owner-scoped `notifications` table stores notification type, concise message, deduplication key, optional workflow references, read timestamp, and creation timestamp. Profile deletion cascades; removed referenced job, draft, or record identifiers are cleared.

## SECURITY AND HUMAN CONTROL
- Notification queries and acknowledgement use the authenticated profile boundary; other users receive `404` for notification IDs they do not own.
- Notifications do not approve drafts, alter tracking status, submit applications, or invoke any delivery service.
- A `SUBMITTED` tracking message explicitly remains a manual record; `UNKNOWN` uses the required manual-verification wording.
- No secret, credentials, external content, or sensitive inferred data is persisted in notification messages.

## FILES CHANGED
- backend/app/api/router.py
- backend/app/modules/application/api.py
- backend/app/modules/application/service.py
- backend/app/modules/notification/__init__.py
- backend/app/modules/notification/api.py
- backend/app/modules/notification/models.py
- backend/app/modules/notification/schemas.py
- backend/app/modules/notification/service.py
- backend/alembic/env.py
- backend/alembic/versions/0012_create_notifications.py
- backend/tests/test_activity.py
- backend/tests/test_database.py
- docs/changes/CHANGE-0021.md
- docs/changes/CHANGELOG.md

## VALIDATION
- Focused notification/activity/application/database tests: run as final validation.
- Full backend pytest suite, Ruff, MyPy, and offline Alembic SQL validation: run as final validation.

## KNOWN LIMITATIONS
- Notifications are in-app records only; delivery channels and notification preferences are intentionally deferred.
- Only the explicit FR-17 event set above is notified. Analysis and matching remain visible in activity but do not create notifications.
- This is not a full audit, reminder, or export system.

## ROLLBACK
1. Downgrade `0012_create_notifications` in an approved database environment.
2. Remove the notification module, router registration, workflow calls, and regression tests.
3. Revert this note and changelog row.

## NEXT ACTION
Stop after CHANGE-0021. Do not begin CHANGE-0022 automatically.
