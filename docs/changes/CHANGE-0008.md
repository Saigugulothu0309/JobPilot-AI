# CHANGE-0008

## Date
2026-08-25

## Module
Resume Text Extraction

## Objective
Implement the resume document text-extraction foundation for PDF and DOCX files without adding LLM parsing, embeddings, job matching, or agent behavior. The scope is limited to reading stored resume files, extracting plain text, normalizing it, and returning a safe processing result for the authenticated owner.

## Previous Behavior
The backend supported secure resume upload, metadata storage, and ownership enforcement but did not include a processing pipeline, document extraction, text normalization, or a user-facing processing endpoint.

## New Behavior
The resume processing foundation now includes:
- a reusable document extraction layer for PDF and DOCX files
- plain-text normalization that removes excessive whitespace while preserving readable paragraph boundaries
- a `ResumeProcessingService` that resolves the authenticated user’s resume, opens the stored file, selects the appropriate extractor, normalizes text, and returns a processing result
- an authenticated endpoint at `POST /api/v1/resumes/{resume_id}/process`
- graceful error handling for unsupported formats, missing storage files, empty documents, image-only PDFs requiring OCR, corrupted PDFs, and corrupted DOCX files
- no database schema changes and no extracted-text persistence

## Files Changed
- backend/app/modules/resume/api.py
- backend/app/modules/resume/processing.py
- backend/app/modules/resume/service.py
- backend/app/modules/resume/schemas.py
- backend/pyproject.toml
- backend/tests/test_resume.py
- docs/changes/CHANGE-0008.md
- docs/changes/CHANGELOG.md

## Architecture

Stored Resume
↓
StorageService
↓
ResumeProcessingService
↓
DocumentExtractor
↓
Text Normalizer
↓
ProcessingResult

## Supported Formats
- PDF using PyMuPDF for page-by-page textual extraction
- DOCX using python-docx for paragraphs and simple table content
- unsupported formats are rejected cleanly

## API Changes
- Added `POST /api/v1/resumes/{resume_id}/process`
- Requires authenticated access through the existing JWT user boundary
- Verifies resume ownership before processing
- Returns a safe processing payload containing status, text, character count, page count when available, extractor, and error metadata when needed
- Does not expose absolute file paths, raw storage keys, or internal stack traces

## Database Changes
NO DATABASE SCHEMA CHANGES

No new tables or migrations were added. Existing resume metadata remains unchanged; extracted text is not persisted.

## Dependencies
Actual additions:
- PyMuPDF
- python-docx

No OCR, vector database, embedding, or LLM dependencies were added.

## Tests
Executed tests and results:
- `backend/tests/test_resume.py` — 16 passed
- full backend suite — 39 passed

## Validation
- pytest: passed
- Ruff: passed
- Mypy: passed
- relevant resume-processing verification: passed

## Security Impact
- resume processing is restricted to files already owned by the authenticated user
- no arbitrary filesystem paths are accepted from the API
- no document content is logged
- no uploaded content is executed
- no storage internals are exposed to the caller

## Known Issues
- image-only or scanned PDFs still require OCR in a future change; this implementation returns a clear `OCR_REQUIRED` error instead of attempting unsupported OCR logic
- the project continues to use the development local storage abstraction; this is intentionally not a production file-store implementation

## Rollback
1. Remove the processing endpoint and service wiring from the resume API.
2. Remove the extraction modules and dependencies introduced for this change.
3. Revert the documentation updates in the changelog and change notes if the change is rolled back.
4. No database rollback is required because there were no schema changes.

## Status
COMPLETED
