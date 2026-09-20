# CHANGE-0007

## Date
2026-08-25

## Module
Resume Management

## Objective
Implement the authenticated candidate resume management foundation, including secure upload validation, local storage abstraction, ownership-bound database metadata, and safe file lifecycle management without adding parsing or AI processing.

## Previous Behavior
The backend did not include a resume entity, authenticated resume API routes, file storage abstraction, upload validation, resume ownership enforcement, or migration for resume persistence.

## New Behavior
- Added a `Resume` SQLAlchemy model linked to `profiles.id` with ownership enforced through the authenticated profile.
- Added authenticated resume endpoints:
  - `POST /api/v1/resumes`
  - `GET /api/v1/resumes`
  - `GET /api/v1/resumes/{resume_id}`
  - `DELETE /api/v1/resumes/{resume_id}`
- Added a small storage abstraction with a local filesystem implementation for the development environment.
- Enforced upload validation for PDF and DOCX files based on MIME type, actual file signature, extension, and maximum size.
- Enforced ownership checks using the authenticated user and their resolved profile, never trusting a client-supplied `profile_id` or `user_id`.
- Added the storage location configuration via `RESUME_STORAGE_PATH` and excluded the local storage directory from Git.
- Kept the scope limited to resume storage metadata and file handling; no parsing, AI extraction, or vectorization was added.

## Files Changed
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\.gitignore
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\alembic\env.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\alembic\versions\0004_create_resumes.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\api\router.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\core\config.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\profile\models.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\resume\__init__.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\resume\api.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\resume\models.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\resume\schemas.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\resume\service.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\app\modules\resume\storage.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\pyproject.toml
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\tests\test_database.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\backend\tests\test_resume.py
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\docs\changes\CHANGE-0007.md
- c:\Users\SYS\OneDrive\Desktop\JobPilot AI\docs\changes\CHANGELOG.md

## Database Changes
Added Alembic revision `0004_create_resumes`.

The `resumes` table includes:
- `id` as the primary key
- `profile_id` as a foreign key to `profiles.id` with cascade delete
- `original_filename` and `stored_filename`
- `storage_key` unique and indexed for safe file lookup
- `mime_type`
- `file_size`
- `created_at` and `updated_at` timezone-aware timestamps

## API Changes
- `POST /api/v1/resumes`: accepts a validated uploaded file, stores it through the storage abstraction, and persists safe metadata to the authenticated user profile.
- `GET /api/v1/resumes`: returns only the authenticated user’s resume metadata.
- `GET /api/v1/resumes/{resume_id}`: returns metadata for the authenticated user’s own resume and rejects access to any other user’s record.
- `DELETE /api/v1/resumes/{resume_id}`: deletes the stored file and the database row only for the authenticated user’s own resume.

## Storage
- Storage abstraction: `StorageService` protocol with `save()`, `get()`, and `delete()` methods.
- Local implementation: `LocalStorageService` writes uploaded resumes into a configured project-local directory.
- Storage location configuration: `RESUME_STORAGE_PATH` with a default of `storage/resumes` under the project.
- Uploaded files are never stored under the original user filename; they use a unique generated identifier and a safe sanitized storage key.

## Security Impact
- Uploaded resumes are treated as untrusted content.
- Only PDF and DOCX are accepted.
- MIME type, file signature, extension, and size are validated before persistence.
- Files are stored under safe generated names with path traversal protection.
- Ownership is resolved from the authenticated user and the user’s profile, preventing cross-user access.
- The code does not execute uploaded files and does not log file contents.

## Dependencies
Actual dependency changes:
- Added `python-multipart` to support FastAPI multipart form upload handling in the backend environment.

## Tests
Added and executed:
- `backend/tests/test_resume.py`
  - upload valid PDF
  - upload valid DOCX
  - reject unsupported file type
  - reject oversized file
  - handle unsafe filename safely
  - ensure stored filename differs from original filename
  - list only own resumes
  - prevent access to another user’s resumes
  - access own resume successfully
  - prevent access to another user’s resume
  - delete own resume and remove file
  - reject delete for another user’s resume
  - reject unauthenticated routes
  - ensure resume is linked to authenticated profile

## Validation
- `pytest`: passed, 34 tests passed
- `Ruff`: passed
- `Mypy`: passed
- Alembic validation: offline SQL generation succeeded and included the new `resumes` table without modifying unrelated tables

## Known Issues
- No live PostgreSQL instance was available in this environment, so live migration execution against PostgreSQL was not performed; offline Alembic SQL validation was used instead.
- The Starlette form parser emits a pending deprecation warning when importing `python_multipart`, but the runtime behavior remains valid and the resume upload flow passes in the project’s test environment.

## Rollback
1. Revert the Alembic migration `0004_create_resumes` in an approved database environment.
2. Remove the resume routes and router registration from the application.
3. Remove the resume module files and the `RESUME_STORAGE_PATH` configuration.
4. Remove the storage directory from Git tracking and delete any local test uploads if a full rollback is required.

## Status
COMPLETED
