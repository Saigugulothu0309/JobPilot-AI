# CHANGE-0025

## STATUS
COMPLETED

## DATE
2026-09-09

## SUMMARY
Added the authenticated Profile and Resume Readiness Workspace using existing backend APIs only.

## SCOPE
The frontend now provides a Profile & Resumes workspace for personal profile edits, skills/education/experience/projects creation and deletion, career-preference editing, resume upload/listing, parsing, structured-review editing, explicit approval, and deletion. Resume copy makes clear that parsed data is not trusted until the user saves review edits and explicitly approves it, and that approval never submits an application.

## API AND DATABASE
Uses only existing `/profile` and `/resumes` endpoints. No backend code, API changes, migrations, or database tables were added.

## SECURITY AND CONTROL
- Session token is read from the existing session storage key; no owner identifier is sent by the client.
- A 401 clears the session and returns the user to sign-in.
- Delete and approval require an explicit browser confirmation.
- The UI does not create applications, submit anything, invoke AI, or modify preferences other than through the owner-scoped existing preferences endpoint.

## FILES CHANGED
- `frontend/app/page.tsx`
- `frontend/app/profile/page.tsx`
- `frontend/app/profile-workspace.tsx`
- `frontend/app/globals.css`
- `docs/changes/CHANGE-0025.md`
- `docs/changes/CHANGELOG.md`

## VALIDATION
Frontend dependencies are not present in the workspace, so build/lint validation requires `npm install` followed by `npm run build` in `frontend/`. No backend files changed.

## KNOWN LIMITATIONS
- Parsed resume review is presented as editable structured JSON because the existing review payload is nested and no approved field-level editor contract exists.
- No frontend test runner is configured in the repository.

## NEXT ACTION
Stop after CHANGE-0025. Do not begin CHANGE-0026 automatically.
