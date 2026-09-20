# JobPilot AI — Implementation Roadmap

## Completed map

| Changes | Requirement/design | Status |
|---|---|---|
| 0001–0003 | project/backend/database foundation | DONE |
| 0004–0010 | identity, profile/professional data, resume review, draft approval | DONE |
| 0011–0016 | shared jobs, search, matching, analysis, preferences, ranking | DONE |
| 0017–0019 | drafts, human approval, manual application tracking | DONE |
| 0020–0022 | activity, in-app notifications, user feedback | DONE |
| 0023 | confirmation-gated feedback learning (present despite supplied brief's no-0023 baseline) | DONE |

## Remaining work

| Category | Objective / likely impact / acceptance criteria |
|---|---|
| PLANNED | End-user frontend: `frontend/app`, API client and tests. Acceptance: all currently implemented safe workflows are usable, responsive, accessible, and owner/error states are explicit. Database/API impact: none unless separately approved. |
| BLOCKED | Production job-source integration. Needs approved source list, terms, credentials, polling/refresh ownership, safety, and tests before adapter/API/schema work. |
| BLOCKED | LLM/agent implementation. Needs provider, model, prompt/versioning, tool contracts, evaluation, privacy, fallback, and approval design. |
| UNDEFINED | External application submission, messaging, scheduling, email/push, data export/deletion, deployment/observability requirements. |

The next exact change number is **CHANGE-0024**, but its objective is **UNDEFINED — REQUIRES PRODUCT DECISION**. Recommended first candidate is frontend workflow implementation because the API foundation exists, but that is a recommendation—not approval—and must define scope, screens, API gaps, tests, and acceptance criteria before a change document is created.
