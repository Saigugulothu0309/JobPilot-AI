# CHANGE-0024

## STATUS
COMPLETED

## DATE
2026-09-09

## SUMMARY
Implemented a bounded, accessible frontend workspace for safe existing JobPilot workflows.

## SCOPE
Added a responsive Next.js client UI which uses the existing API contract only. It supports JWT sign-in stored for the browser session, shared job search, opportunity details, explicit creation of a private `SAVED` application record, recent activity, and in-app notification visibility. The UI repeatedly states that saving does not apply or submit anything.

No backend API, database schema, migration, agent, external source, submission action, notification delivery, profile editing form, or preference-learning confirmation UI was added. Registration and the broader profile/resume/draft/approval forms remain intentionally deferred to a later approved UI increment.

## FILES CHANGED
- `frontend/app/page.tsx`
- `frontend/app/layout.tsx`
- `frontend/app/globals.css`
- `docs/changes/CHANGE-0024.md`
- `docs/changes/CHANGELOG.md`

## SECURITY AND HUMAN CONTROL
- The browser session holds the JWT; no token is placed in source code.
- API requests use the existing bearer-token owner boundary.
- Saving a job creates only a private application record with status `SAVED`.
- No UI control claims or performs submission, external communication, durable preference learning, or agent activity.

## VALIDATION
- Frontend dependency directory was not present in the workspace, so `next build` could not be run without downloading dependencies.
- Type-level implementation follows the existing Next.js 14/React 18 configuration. Run `npm install` and `npm run build` from `frontend/` in an approved dependency-enabled environment before release.

## KNOWN LIMITATIONS
- The current UI is a deliberately bounded dashboard rather than a full frontend implementation of every backend route.
- The backend must be reachable at `NEXT_PUBLIC_API_BASE_URL` or its documented local default.
- Cross-origin production configuration remains an operational decision outside this change.

## ROLLBACK
Revert the three frontend files and this change record/changelog entry. No database rollback is required.

## NEXT ACTION
Stop after CHANGE-0024. Do not begin CHANGE-0025 automatically.
