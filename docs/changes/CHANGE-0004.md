# CHANGE-0004

## Date
2026-08-24

## Module
Authentication Foundation

## Requirement
CHANGE-0004 authentication foundation, aligned with `docs/02_requirements_non_functional.md` sections 8 (Security), 13 (Data Integrity), and 17 (Testability).

## Objective
Provide minimal secure local account registration, login, token authentication, and protected account access.

## Previous Behavior
The backend had no user entity, authentication routes, credentials, authorization dependency, or migrations.

## New Behavior
Users can register, receive a safe account response, log in for a time-limited signed bearer token, and retrieve their own safe account data at a protected endpoint. Passwords use Argon2 through `pwdlib`; tokens contain only a user identifier and expiry.

## Files Changed
- .env.example
- backend/pyproject.toml
- backend/app/core/config.py
- backend/app/api/router.py
- backend/app/security/auth.py
- backend/app/modules/auth/__init__.py
- backend/app/modules/auth/models.py
- backend/app/modules/auth/schemas.py
- backend/app/modules/auth/repository.py
- backend/app/modules/auth/service.py
- backend/app/modules/auth/api.py
- backend/alembic/env.py
- backend/alembic/versions/0001_create_users.py
- backend/tests/test_auth.py
- backend/tests/test_database.py
- docs/changes/CHANGE-0004.md
- docs/changes/CHANGELOG.md

## Database Changes
Added the `users` table migration with UUID primary key, unique indexed email, password hash, active state, and timestamps. It was validated offline only; no live database was modified.

## API Changes
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (bearer-token protected)

## Dependencies
- Added `PyJWT`, `pwdlib[argon2]`, and `email-validator`.
- Installed those dependencies in the existing virtual environment.

## Tests
- `..\\.venv\\Scripts\\python.exe -m pytest tests -q`: passed, 10 tests.
- `..\\.venv\\Scripts\\python.exe -m ruff check app tests`: passed.
- MyPy was unavailable because its prior installation remains blocked by a Windows file lock.

## Validation
- `alembic heads` reported `0001_create_users` as the head.
- Offline `alembic upgrade head --sql` generated PostgreSQL SQL for only `alembic_version` and `users`, including the unique email index; no database connection or migration application occurred.
- FastAPI started with Uvicorn and `/health` returned `{"status":"healthy","service":"jobpilot-ai"}`.
- Git diff could not be inspected because this directory is not a Git repository.

## Security Impact
Passwords are Argon2-hashed and never returned. Authentication failures use generic credential errors. JWT secrets are read only from `AUTH_SECRET`, tokens expire by configuration, and no secrets or tokens are logged or exposed by the health endpoint.

## Known Issues
- No Docker or live PostgreSQL instance is available, so the migration was not applied against PostgreSQL.
- MyPy remains unavailable because of a Windows file lock.
- Git is not initialized.

## Rollback
Downgrade Alembic revision `0001_create_users` in an approved database environment, then revert the listed authentication files and dependency declarations.

## Status
COMPLETED
