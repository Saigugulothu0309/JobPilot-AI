# CHANGE-0009

## Date
2026-08-25

## Module
Structured Resume Parsing Foundation

## Objective
Implement the structured resume parsing foundation without adding LLM parsing, embeddings, job matching, agent behavior, or database schema changes. The scope is limited to deterministic extraction of resume metadata and sectioned data from already-normalized text for authenticated resumes.

## Previous Behavior
The backend had resume upload, secure storage, and text extraction foundations, but it did not include a structured parsing layer or an endpoint that returned parsed candidate data from extracted text.

## New Behavior
The resume parser foundation now includes:
- a deterministic parser for basic contact metadata, skills, education, experience, and projects using normalized resume text
- a read-only `ResumeParser` result model that returns structured dictionaries without writing into profile or professional tables
- an authenticated endpoint at `POST /api/v1/resumes/{resume_id}/parse`
- ownership enforcement through the existing resume lookup path before parsing
- graceful handling for empty or incomplete resumes with explicit warnings instead of database writes
- no LLM usage, no embeddings, no vector database work, and no database migration work

## Files Changed
- backend/app/modules/resume/api.py
- backend/app/modules/resume/parser.py
- backend/tests/test_resume.py
- docs/changes/CHANGE-0009.md
- docs/changes/CHANGELOG.md

## Architecture

Stored Resume
↓
ResumeProcessingService
↓
Normalized text
↓
ResumeParser
↓
StructuredResumeResult

## API Changes
- Added `POST /api/v1/resumes/{resume_id}/parse`
- Requires authenticated access through the existing JWT user boundary
- Verifies resume ownership before parsing
- Returns structured candidate fields including contact details, skills, education, experience, and projects
- Does not mutate the profile or professional tables

## Database Changes
NO DATABASE SCHEMA CHANGES

No new tables or migrations were added. Structured parsing output is returned as an API payload and is not persisted.

## Security Impact
- resume parsing is restricted to resumes already owned by the authenticated user
- no new database writes are introduced during parsing
- no LLM or external inference service is invoked
- no profile or professional records are mutated from parsed output

## Tests
Executed tests and results:
- `backend/tests/test_resume.py` — 20 passed
- full backend suite — 43 passed

## Validation
- pytest: passed
- relevant parser endpoint verification: passed

## Known Issues
- the parser is deterministic and heuristic-based; it does not perform LLM reasoning or advanced semantic extraction
- future work may extend section parsing precision or add machine-based parsing, but this foundation intentionally does not do so

## Rollback
1. Remove the parse endpoint and parser imports from the resume API.
2. Remove the parser module and parser tests introduced for this change.
3. Revert the change-note and changelog updates if the change is rolled back.
4. No database rollback is required because there were no schema changes.

## Status
COMPLETED
