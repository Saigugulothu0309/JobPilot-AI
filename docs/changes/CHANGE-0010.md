# CHANGE-0010

## CHANGE ID
CHANGE-0010

## STATUS
COMPLETED

## DATE
2026-08-27

## SUMMARY
Implemented the Resume Review & Approval Foundation. Parsed resume output remains untrusted until the authenticated owner reviews, edits, and explicitly approves it. Only approved data is promoted into the existing candidate profile and professional-data tables.

## WHY
Parser output must never automatically become trusted candidate data. Edits and approval must survive across requests, so the existing resume record now stores the minimal review snapshot and state needed to enforce that boundary.

## ARCHITECTURE
Stored resume -> ResumeProcessingService -> ResumeParser -> persisted review snapshot -> owner review/edit -> explicit approval -> existing Profile, Skill, Education, Experience, and Project records.

Review states are intentionally limited to `PARSED` and `APPROVED`. Approved reviews are immutable and repeated approval is idempotent.

## FILES CHANGED
- backend/app/modules/resume/api.py
- backend/app/modules/resume/models.py
- backend/app/modules/resume/schemas.py
- backend/app/modules/resume/service.py
- backend/alembic/versions/0005_add_resume_review_state.py
- backend/tests/test_resume.py
- docs/changes/CHANGE-0010.md
- docs/changes/CHANGELOG.md

## DATABASE
Added Alembic revision `0005_add_resume_review_state`.

The migration adds `review_status` and nullable JSON `review_data` columns to the existing `resumes` table. This is required because edited review data and approval state must persist between the review and approval requests. No new tables were created and no professional-data tables were duplicated.

Approval writes only to the existing profile, skills, education, experience, and projects tables.

## API
- `GET /api/v1/resumes/{resume_id}/review` retrieves the owner’s parsed or saved review data.
- `PUT /api/v1/resumes/{resume_id}/review` replaces the owner’s validated review snapshot before approval.
- `POST /api/v1/resumes/{resume_id}/approve` explicitly promotes the reviewed snapshot into trusted candidate data.
- All endpoints require authentication and enforce ownership through the existing resume/profile resolution.
- Approved reviews cannot be edited and repeated approval does not create duplicate professional records.

## DEPENDENCIES
No new runtime dependencies were added. Existing FastAPI, Pydantic, SQLAlchemy, Alembic, and parser dependencies are reused.

## SECURITY
- No request-supplied `user_id` or `profile_id` is accepted for review or approval.
- Another user receives a not-found response for a resume they do not own.
- Unapproved parsed data does not mutate trusted professional records.
- Resume contents, storage paths, and secrets are not logged or exposed.

## TESTS
Focused resume/review suite: `24 passed`.

Coverage includes authenticated retrieval, unauthenticated rejection, ownership isolation, validated edits, invalid payload rejection, approval authentication, approval ownership isolation, explicit trusted-data writes, edit preservation, unapproved-data isolation, and idempotent repeated approval.

## VALIDATION
- Focused pytest: passed, 24 tests.
- Full backend pytest, Ruff, MyPy, and offline Alembic SQL generation were run for final validation.
- Existing repository-wide Ruff issues in older Alembic files remain outside this change and are documented under KNOWN ISSUES.

## KNOWN ISSUES
- Parser entries without usable dates cannot be promoted into the existing education, experience, or project tables because those trusted models require a start date. They remain in the review snapshot for correction.
- The repository has pre-existing Ruff findings in older migration files and `alembic/env.py`; these are unrelated to CHANGE-0010 and were not modified.

## ROLLBACK
1. Remove the review endpoints and `ResumeReviewService` wiring.
2. Revert Alembic revision `0005_add_resume_review_state` to remove the two resume review columns.
3. Remove the review schemas, regression tests, and documentation updates.
4. Existing upload, extraction, parsing, authentication, and professional-data behavior remains otherwise unchanged.

## NEXT ACTION
Stop after CHANGE-0010. Do not begin CHANGE-0011 automatically.
