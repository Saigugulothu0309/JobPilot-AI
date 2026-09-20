# CHANGE-0018

## CHANGE ID
CHANGE-0018

## STATUS
COMPLETED

## DATE
2026-09-06

## SUMMARY
Implemented the Human Review and Approval Foundation for grounded application drafts.

## SCOPE
This change covers the review and approval boundary from FR-12, FR-13, FR-14, and D08. Users can edit an unapproved draft, explicitly approve the exact current revision, retrieve approval state, and receive a conflict when attempting to edit an approved draft.

This change does not submit applications, track application status, answer sensitive or legal questions, perform browser automation, or begin CHANGE-0019.

## ARCHITECTURE
Authenticated request -> owner-scoped `ApplicationDraftService` -> revisioned draft content -> explicit review edit or confirmation -> approval state bound to the current revision.

Approval is stored on the same owner-scoped application draft. `approved_revision` identifies the exact content revision approved by the user. Edits are rejected after approval in this foundation rather than silently invalidating and mutating an approved package.

## FILES CHANGED
- backend/app/modules/application/models.py
- backend/app/modules/application/schemas.py
- backend/app/modules/application/service.py
- backend/app/modules/application/api.py
- backend/alembic/versions/0009_add_application_draft_approval.py
- backend/tests/test_application.py
- docs/changes/CHANGE-0018.md
- docs/changes/CHANGELOG.md

## API
Added:

- `PUT /api/v1/applications/drafts/{draft_id}`
- `POST /api/v1/applications/drafts/{draft_id}/approve`

Review updates replace the draft content and increment its revision while the draft remains `DRAFT`. Approval requires `{ "confirm": true }` and stores:

- `status: APPROVED`
- `approved_revision`
- `approval_confirmed: true`

`confirm: false` is rejected. Repeated approval of the same revision is idempotent. Approved drafts cannot be edited and return a conflict response.

## APPROVAL POLICY
- Viewing, saving, preparing, or editing a draft does not approve it.
- Approval is explicit and attributable to the authenticated owner.
- Approval is tied to the exact current revision.
- Draft content remains grounded in approved profile data and selected job context.
- The system never marks an application as submitted and performs no external action.

## DATABASE
Added Alembic revision `0009_add_application_draft_approval`.

The migration adds `approved_revision` and `approval_confirmed` to `application_drafts`. No new application tracking table was added.

## SECURITY
- Review and approval enforce the existing profile ownership join.
- No client-supplied owner identifier is accepted.
- Another user receives `404` for an owned draft.
- Approval does not grant permission to submit or share any material externally.
- Sensitive, legal, sponsorship, salary, and identity answers are not generated or approved by these endpoints.

## TESTS
Added coverage for:

- explicit approval confirmation requirement
- approval state and revision binding
- review edits before approval
- approved draft immutability
- repeated approval idempotency
- existing owner isolation and authentication behavior

## VALIDATION
- Focused application/database suite: 9 passed.
- Full backend pytest suite: run as final validation.
- Focused Ruff and full MyPy: run as final validation.
- Offline Alembic SQL generation: run as final validation and verified revision `0009_add_application_draft_approval`.

## KNOWN ISSUES
- Approved drafts cannot be edited in place; a later change may add explicit material replacement that invalidates approval and creates a new revision.
- This foundation does not yet provide a separate package containing multiple individually approved materials or a full audit trail.
- Application tracking and external submission remain out of scope.

## ROLLBACK
1. Downgrade Alembic revision `0009_add_application_draft_approval` in an approved database environment.
2. Remove the review and approval routes and service methods.
3. Remove approval fields from the application draft model and response schema.
4. Revert the approval regression tests and documentation updates.

## NEXT ACTION
Stop after CHANGE-0018. Do not begin CHANGE-0019 automatically.
