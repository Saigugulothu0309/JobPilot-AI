# CHANGE-0005

## Date
2026-08-25

## Module
Candidate Profile Foundation

## Requirement
CHANGE-0005 candidate profile foundation, scoped to the authenticated profile CRUD layer described in the approved backend architecture and security constraints.

## Objective
Create the first authenticated candidate profile layer connected to the existing User record. The profile is intentionally minimal and remains limited to private account data needed for future AI and job-matching workflows.

## Previous Behavior
The backend did not include a profile entity, owned profile API, service/repository abstraction, profile schema validation, or migration to link a profile to a single authenticated user.

## New Behavior
- Added a `Profile` SQLAlchemy model with a one-to-one relationship to `User`.
- Enforced `profiles.user_id` as a unique foreign key to `users.id` and kept the relationship private to the authenticated owner.
- Added authenticated endpoints:
  - `GET /api/v1/profile`
  - `PUT /api/v1/profile`
- Kept request handling within the service/repository architecture and ensured the authenticated user context determines ownership.
- Added request/response Pydantic schemas with sensible field-length validation.
- Included offline Alembic validation generating the PostgreSQL schema for the new table.

## Files Changed
- backend/app/api/router.py
- backend/app/modules/auth/models.py
- backend/app/modules/profile/__init__.py
- backend/app/modules/profile/api.py
- backend/app/modules/profile/models.py
- backend/app/modules/profile/repository.py
- backend/app/modules/profile/schemas.py
- backend/app/modules/profile/service.py
- backend/alembic/env.py
- backend/alembic/versions/0002_create_profiles.py
- backend/tests/test_profile.py
- docs/changes/CHANGE-0005.md
- docs/changes/CHANGELOG.md

## Database Migration
Added Alembic revision `0002_create_profiles`.

Database characteristics:
- Foreign key to `users.id`
- Unique constraint on `user_id` to enforce one-to-one ownership
- Nullable fields for profile content while preserving `NOT NULL` on identity and timestamps
- `created_at` and `updated_at` columns with timezone-aware defaults and `onupdate` handling

The migration was validated offline using Alembic SQL generation because no live PostgreSQL service was present in this environment.

## API Changes
- `GET /api/v1/profile` returns the current authenticated user's profile.
- `PUT /api/v1/profile` creates a profile when missing or updates the existing one for the authenticated user.
- The API rejects unauthenticated requests and never trusts a client-supplied `user_id`.

## Dependencies
No new package dependencies were required beyond the already approved FastAPI, SQLAlchemy, Alembic, Pydantic, and authentication stack.

## Tests
Added coverage for:
- authenticated profile creation
- authenticated profile retrieval
- authenticated profile update
- unauthenticated rejection
- profile ownership enforcement
- duplicate profile prevention by single-user constraint
- invalid input rejection
- authentication regression safety
- `/health` regression safety

## Validation
- `..\.venv\Scripts\python.exe -m pytest tests -q` passed with the backend suite.
- Ruff linting was run and verified clean.
- `mypy` was checked when available in the environment; if unavailable, the result was reported as such rather than assumed.
- Alembic migration generation was validated offline without a live database connection.

## Security Impact
- Profile access remains scoped to the authenticated user identity.
- Users cannot read or modify another user's profile.
- No user-supplied `user_id` is accepted or used.
- No sensitive profile payloads are logged.

## Known Issues
- No live PostgreSQL instance was available in this environment, so migration execution against PostgreSQL was not performed.
- The project is not a Git repository, so no Git diff or commit history is available to inspect here.

## Rollback
1. Revert the profile migration revision `0002_create_profiles` in an approved database environment.
2. Remove the profile module and route registrations.
3. Revert any relationship and metadata updates in the authentication model.
4. Remove the profile tests and documentation files if the change is fully rolled back.

## Status
COMPLETED
