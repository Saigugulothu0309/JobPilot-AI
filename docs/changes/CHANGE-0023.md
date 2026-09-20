# CHANGE-0023

## STATUS
COMPLETED

## DATE
2026-09-08

## SUMMARY
Implemented explicit, owner-scoped feedback proposals for confirmed preference learning.

## SCOPE
Implements the approved `Feedback → Proposal → Confirmation → Durable Change` workflow:
- `WRONG_PREFERENCE`: Proposes an explicit replacement for an existing list-valued career-preference field (`target_roles`, `preferred_locations`, `preferred_work_modes`, `preferred_industries`, `preferred_technologies`, `exclusions`, and canonical list fields). Does not modify the preference when feedback is created.
- `MISSING_SKILL`: Proposes an explicitly supplied profile skill containing name, category, and proficiency. Does not add the skill until explicitly confirmed.
- `INCORRECT`: Generates a reviewed job-correction proposal; never modifies shared Job data or profile data.
- `INTERESTED`, `NOT_INTERESTED`, `ALREADY_APPLIED`: Informational feedback only; durable-learning proposals are rejected.

Only explicit confirmation applies a proposal. Rejection changes nothing and preserves original feedback. Revocation restores the saved prior preference value or removes the skill created by that proposal. Confirmed and revoked changes record private activity events (`FEEDBACK_CONFIRMED`, `FEEDBACK_REVOKED`). Actions on proposals are idempotent. No ranking algorithm changed; existing ranking naturally reads confirmed preferences and profile skills.

## API
- `POST /api/v1/feedback/proposals`
- `POST /api/v1/feedback/proposals/{proposal_id}/confirm`
- `POST /api/v1/feedback/proposals/{proposal_id}/reject`
- `POST /api/v1/feedback/proposals/{proposal_id}/revoke`
- `POST /api/v1/feedback/proposals/{proposal_id}/{action}` (alias support)

## DATABASE
Added Alembic revision `0014_create_feedback_proposals` for the `feedback_proposals` table:
- `id`: UUID primary key
- `profile_id`: UUID foreign key to `profiles.id` with cascade delete
- `feedback_id`: UUID foreign key to `job_feedback.id` with cascade delete
- `target_type`: VARCHAR(30) (`PREFERENCE`, `SKILL`, `JOB_CORRECTION`)
- `target_field`: VARCHAR(50) (nullable)
- `previous_value`: JSON snapshot of prior value
- `proposed_value`: JSON snapshot of proposed value
- `status`: VARCHAR(20) (`PENDING`, `CONFIRMED`, `REJECTED`, `REVOKED`)
- `applied_skill_id`: UUID foreign key to `skills.id` with set null
- `confirmed_at`: TIMESTAMP WITH TIME ZONE
- `rejected_at`: TIMESTAMP WITH TIME ZONE
- `revoked_at`: TIMESTAMP WITH TIME ZONE
- `created_at`: TIMESTAMP WITH TIME ZONE

## FILES CHANGED
- `backend/app/modules/feedback/models.py`
- `backend/app/modules/feedback/schemas.py`
- `backend/app/modules/feedback/service.py`
- `backend/app/modules/feedback/api.py`
- `backend/alembic/versions/0014_create_feedback_proposals.py`
- `backend/tests/test_activity.py`
- `docs/changes/CHANGE-0023.md`
- `docs/changes/CHANGELOG.md`

## SECURITY
All proposals are profile-owned and resolved through the authenticated user. Client-supplied profile IDs are never trusted. Feedback never silently changes durable data. Confirming an `INCORRECT` proposal preserves its review state without modifying shared Job records or profiles; no submission or external action occurs.

## TESTS
Added comprehensive regression tests in `backend/tests/test_activity.py` covering:
- proposal creation for `WRONG_PREFERENCE`
- proposal creation for `MISSING_SKILL`
- proposal creation for `INCORRECT`
- rejection of proposal creation for informational feedback types (`INTERESTED`, `NOT_INTERESTED`, `ALREADY_APPLIED`)
- proposal confirmation and activity recording
- proposal rejection with data preservation
- proposal revocation restoring prior preferences
- safe skill revocation removing created skill (and handling independent skill deletion)
- strictly enforced owner isolation (cross-user returns 404)
- repeated/idempotent actions for confirmation, rejection, and revocation
- ensuring no mutation occurs before explicit confirmation
- invalid proposal and action handling

Suite status: 17 passed in `test_activity.py`, 107 passed across the entire backend suite.

## VALIDATION
- Full pytest test suite: passed (107 passed).
- Ruff: passed with zero issues on all changed files. Pre-existing repository-wide findings in older files preserved.
- MyPy: passed (`Success: no issues found in 68 source files`).
- Alembic offline SQL: verified through revision `0014_create_feedback_proposals`.

## LIMITATIONS
Only safe list-valued preference fields and new skills are supported. Proposal history is retained, but a revoked skill cannot be restored if it was independently deleted. No CHANGE-0024 work is included.

## ROLLBACK
1. Downgrade Alembic revision `0014_create_feedback_proposals` in an approved database environment.
2. Remove proposal endpoints from `feedback/api.py`.
3. Revert proposal service methods in `feedback/service.py`, schemas, and models.
4. Remove proposal regression tests in `tests/test_activity.py`.
5. Revert `CHANGE-0023.md` and `CHANGELOG.md`.

## NEXT ACTION
Stop after CHANGE-0023. Do not begin CHANGE-0024 automatically.
