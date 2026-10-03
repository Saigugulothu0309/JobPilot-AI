# CHANGE-0027

## STATUS
COMPLETED

## SUMMARY
Added the authenticated Applications workspace for manual tracking, grounded draft review, and revision-bound approval.

## SCOPE
`/applications` uses existing application record and draft endpoints to list owner-scoped tracking records, update canonical statuses, dates, and notes, prepare a grounded draft for a saved job, edit unapproved draft content, and explicitly approve the current revision. Saving a job still only creates a `SAVED` record. Approval never submits an application. Status `UNKNOWN` keeps the existing manual-verification wording.

## APIS REUSED
`GET /applications/records`, `PUT /applications/records/{id}`, `POST /applications/drafts`, `GET /applications/drafts/{id}`, `PUT /applications/drafts/{id}`, and `POST /applications/drafts/{id}/approve`.

## FILES CHANGED
- `frontend/app/applications/page.tsx`
- `frontend/app/page.tsx`
- `frontend/app/jobs/page.tsx`
- `frontend/app/globals.css`
- `docs/changes/CHANGE-0027.md`
- `docs/changes/CHANGELOG.md`

## VALIDATION
No frontend test runner is configured. Frontend dependency/build validation remains blocked unless `npm install` and `npm run build` are run in `frontend/`. No backend code changed.

## LIMITATIONS
Draft content is edited as structured JSON because the existing draft payload is nested and no approved field-level editor contract exists. CHANGE-0023 feedback-learning confirmation is still not exposed. Settings and agent controls remain undefined.

## NEXT ACTION
Stop after CHANGE-0027. Do not begin CHANGE-0028 automatically.
