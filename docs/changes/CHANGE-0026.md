# CHANGE-0026

## STATUS
COMPLETED

## SUMMARY
Added the authenticated Job Discovery & Ranking Workspace.

## SCOPE
`/jobs` uses existing job search and ranking endpoints for server-validated filters, deterministic match/ranking explanations, eligibility states, unknowns, normalized job detail, user-attributed feedback, and explicit SAVED application-record creation. It never opens external links automatically, applies, submits, generates, approves, or changes profile/preferences from feedback.

## APIS REUSED
`GET /jobs`, `GET /jobs/rank`, `POST /feedback`, and `POST /applications/records`.

## FILES CHANGED
- `frontend/app/jobs/page.tsx`
- `frontend/app/page.tsx`
- `frontend/app/globals.css`
- `docs/changes/CHANGE-0026.md`
- `docs/changes/CHANGELOG.md`

## VALIDATION
No frontend test runner is configured. Frontend dependency/build validation remains blocked because dependency installation did not create `node_modules`; no backend code changed.

## LIMITATIONS
Applications navigation is a visible placeholder because application-record UI is explicitly outside this change. Feedback remains informational; CHANGE-0023 learning workflows are not exposed.

## NEXT ACTION
Stop after CHANGE-0026. Do not begin CHANGE-0027 automatically.
