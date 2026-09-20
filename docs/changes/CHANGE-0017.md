# CHANGE-0017

## CHANGE ID
CHANGE-0017

## STATUS
COMPLETED

## DATE
2026-09-06

## SUMMARY
Implemented the Grounded Application Preparation Foundation as a persisted, revisioned, unapproved draft workflow for one selected normalized job.

## SCOPE
This change covers the preparation slice of FR-11. An authenticated user can prepare a draft for a selected job using approved profile facts and an optional approved resume reference. The draft records source snapshots, grounded evidence, unresolved items, and explicit approval-required state.

This change does not approve materials, submit applications, track application status, answer sensitive or legal questions, invoke AI, perform browser automation, or begin CHANGE-0018.

## ARCHITECTURE
Authenticated request -> `ApplicationDraftService` -> authenticated profile ownership -> normalized `Job` + approved profile data + optional approved `Resume` -> revisioned `ApplicationDraft`.

The draft is intentionally an application-preparation record, not an application-tracking record. A repeated preparation request for the same authenticated profile and job updates the existing draft and increments its revision rather than creating a duplicate.

## FILES CHANGED
- backend/app/api/router.py
- backend/app/modules/application/__init__.py
- backend/app/modules/application/models.py
- backend/app/modules/application/schemas.py
- backend/app/modules/application/service.py
- backend/app/modules/application/api.py
- backend/alembic/env.py
- backend/alembic/versions/0008_create_application_drafts.py
- backend/tests/test_application.py
- backend/tests/test_database.py
- docs/changes/CHANGE-0017.md
- docs/changes/CHANGELOG.md

## DATABASE
Added Alembic revision `0008_create_application_drafts`.

The `application_drafts` table stores:

- authenticated profile ownership
- selected normalized job reference
- optional approved resume reference
- `DRAFT` status
- revision number
- grounded content JSON
- approved profile snapshot JSON
- normalized job snapshot JSON
- creation and update timestamps

A unique profile/job constraint makes preparation idempotent for the current draft foundation. Profile and job deletion cascades remove the draft; deleting the referenced resume sets `resume_id` to null.

## API
Added:

- `POST /api/v1/applications/drafts`
- `GET /api/v1/applications/drafts/{draft_id}`

The create request accepts `job_id` and an optional `resume_id`. The response includes the draft status, revision, source snapshots, and grounded content:

- application summary
- resume focus skills supported by the approved profile
- approved experience evidence
- approved project evidence
- approved education evidence
- unresolved items
- `approval_required: true`

An explicitly supplied resume must belong to the authenticated user and have `APPROVED` review status.

## GROUNDING POLICY
- Draft content is built from approved profile fields and approved professional records.
- Job title, company, description, location, and URL are copied into a source snapshot.
- Resume selection is a source reference only; unapproved resume review data is rejected.
- Missing evidence remains an unresolved item.
- The system does not invent metrics, responsibilities, technologies, achievements, dates, employers, or proficiency.
- Draft generation never implies approval.

## SECURITY
- Both endpoints require bearer authentication.
- Draft retrieval joins through `profiles.user_id` and cannot cross user boundaries.
- No request accepts a client-supplied profile or user owner.
- Jobs remain shared normalized records and are not modified.
- No external content is fetched, and no generated content is submitted externally.

## TESTS
Added coverage for:

- grounded draft creation and retrieval
- approved profile evidence inclusion
- unresolved item visibility
- idempotent revision updates
- cross-user ownership isolation
- missing-job handling
- unauthenticated access rejection
- application draft metadata registration

## VALIDATION
- Focused application/database suite: 7 passed.
- Full backend pytest suite: run as final validation.
- Focused Ruff and full MyPy: run as final validation.
- Offline Alembic SQL generation: run as final validation and verified revision `0008_create_application_drafts`.

## KNOWN ISSUES
- Draft content is deterministic and template-based; no LLM generation or semantic tailoring is included.
- Only the first preparation draft per profile/job is retained as the current revision; complete historical material versions are deferred.
- Approval, package-level review, application tracking, and manual submission readiness remain later workflow slices.

## ROLLBACK
1. Downgrade Alembic revision `0008_create_application_drafts` in an approved database environment.
2. Remove the application module and router registration.
3. Remove the draft regression tests and metadata expectation.
4. Revert the CHANGE-0017 documentation and changelog entry.

## NEXT ACTION
Stop after CHANGE-0017. Do not begin CHANGE-0018 automatically.
