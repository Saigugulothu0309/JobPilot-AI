# JobPilot AI — UI/UX Specification

## Current state and navigation plan

The implemented frontend is a placeholder only. This plan does not authorize UI implementation or new APIs. Proposed navigation, constrained by existing backend capability: Dashboard; Jobs (list, details, match, analysis, ranking, feedback); Applications (drafts, review/approval, records); Profile (personal, skills, education, experience, projects, preferences, resumes); Activity; Notifications; Settings. Agent live task/status and privacy controls are **UNDEFINED — REQUIRES PRODUCT DECISION** because no agent state/settings APIs exist.

| Screen | Purpose and primary action | States and safeguards |
|---|---|---|
| Dashboard | Private overview of existing records/activity/notifications; navigate to work | Empty onboarding, load/error/retry; do not imply backend aggregate exists. |
| Jobs list/detail | Search shared jobs; view source, description, match/rank/analysis; record feedback | Loading skeleton, no-results/filter reset, unavailable analysis warning. Source link is external/untrusted and opens with warning. |
| Feedback proposal | Review current vs proposed value, source feedback and effect | Explicit `[Reject] [Confirm change]`; no preselected confirmation. Terminal states visible; revoke asks confirmation and restores stated prior value. |
| Profile/resume | Maintain user facts and professional data; upload and review parsed resume | Required/invalid-field messages, unsaved-change warning, extraction failure recovery, clear distinction between parsed and approved data. |
| Draft/review | View grounded job/profile snapshot, edit, validate, approve current revision | Unsupported/uncertain claims block or warn; edit invalidates approval; approval dialog names revision and states “does not submit.” |
| Application record | Create/update manual status, dates, notes and follow-up | Status control only permits canonical transitions; unknown external outcome uses `Unknown`, not Submitted. Destructive deletion is not currently supported. |
| Activity/notifications | Explain meaningful work and required next action; mark notification read | Chronological loading/error/empty state; no success statement for uncertain external action. |

Every screen must have keyboard operation, visible focus, semantic labels, screen-reader status/error announcements, color-independent status indicators, responsive single-column mobile layouts, touch targets, and readable contrast. Owner absence/expired session routes to sign-in; cross-owner references show not-found, never private data.

## Confirmation UX

Preference-learning: show feedback type, target field, prior value, proposed value, reason, ranking implication, and irreversible/restore limitation. Draft approval: show current revision, grounding summary, warnings, and that approval is not submission. Consequential action: no design is approved because no executor exists. Any future destructive operation requires target, effect, recoverability, and explicit confirm/cancel.
