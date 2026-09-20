# CHANGE-0003

## Date
2026-08-24

## Module
Database Foundation

## Requirement
CHANGE-0003 database foundation, aligned with `docs/02_requirements_non_functional.md` sections 13 (Data Integrity), 15 (Maintainability), and 17 (Testability).

## Objective
Prepare PostgreSQL, SQLAlchemy, and Alembic infrastructure for future modules without creating business entities or database tables.

## Previous Behavior
The backend had optional `DATABASE_URL` configuration but no engine, session lifecycle, declarative metadata, Alembic environment, PostgreSQL driver, or database-specific tests.

## New Behavior
The backend provides a synchronous SQLAlchemy engine and request-scoped session dependency that activate only when `DATABASE_URL` is configured. Alembic is wired to the shared empty SQLAlchemy metadata and has an initialized migration directory. No connection is made for non-database application paths.

## Files Changed
- backend/pyproject.toml
- backend/app/database/__init__.py
- backend/app/database/base.py
- backend/app/database/session.py
- backend/alembic.ini
- backend/alembic/env.py
- backend/alembic/script.py.mako
- backend/alembic/versions/.gitkeep
- backend/tests/test_database.py
- docs/changes/CHANGE-0003.md
- docs/changes/CHANGELOG.md

## Database Changes
No database tables or migrations were created. `Base.metadata` is empty, and no business entities were implemented.

## API Changes
None. `GET /health` remains unchanged and does not expose database configuration.

## Dependencies
- Added `psycopg[binary]>=3.2,<4.0` as the PostgreSQL SQLAlchemy driver declaration.
- Added standard setuptools build/package-discovery configuration so the backend package can be installed without treating the Alembic directory as an application package.
- Installed declared SQLAlchemy, Alembic, Psycopg, and Ruff packages into the existing project virtual environment for validation.
- MyPy installation could not complete because Windows reported a locked MyPy package file.

## Tests
- `..\\.venv\\Scripts\\python.exe -m pytest tests -q` (run from `backend/`): passed, 6 tests.
- `..\\.venv\\Scripts\\python.exe -m ruff check app tests` (run from `backend/`): passed.
- `..\\.venv\\Scripts\\alembic.exe -c alembic.ini heads` (run from `backend/`): passed with no migrations present.
- `DATABASE_URL=<temporary fixture> ..\\.venv\\Scripts\\alembic.exe -c alembic.ini upgrade head --sql` (run from `backend/`): passed; generated only transaction boundary SQL because there are no revisions.
- MyPy was not run because its installation is incomplete after a Windows file-lock error.

## Validation
- Verified optional database configuration, empty metadata, and construction of a PostgreSQL session factory without connecting to a database.
- Verified Alembic recognizes the initialized migration environment; no revisions exist.
- Verified the Alembic environment loads the SQLAlchemy metadata in offline mode without connecting to PostgreSQL.
- Started the backend with Uvicorn on `127.0.0.1:8013` and confirmed `GET /health` returned `{"status":"healthy","service":"jobpilot-ai"}`.
- Docker is not installed in this environment, so PostgreSQL integration testing could not be performed.
- Git diff validation could not be performed because the directory is not a Git repository.

## Security Impact
Database credentials remain environment-only through `DATABASE_URL`. The URL is not returned by any API and is hidden from the configuration object's representation. No secrets were introduced.

## Known Issues
- No live PostgreSQL instance or Docker installation is available, so database connectivity and migrations were not integration-tested.
- MyPy is not runnable because its installation encountered a Windows file lock.
- The repository is not initialized as a Git repository.

## Rollback
Revert the listed files and remove the `psycopg` dependency declaration. No database rollback is needed because no tables, migrations, or database operations were performed.

## Status
COMPLETED
