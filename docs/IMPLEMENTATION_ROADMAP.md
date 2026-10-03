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
| 0024–0027 | bounded dashboard, profile, job discovery, and applications frontend workflows | DONE |
| 0028 | owner-scoped, paginated feedback proposal listing API | DONE |

## Remaining work

| Category | Objective / likely impact / acceptance criteria |
|---|---|
| UNDEFINED | Next product/backend objective. Requires explicit product scope and acceptance criteria before implementation. |
| BLOCKED | Production job-source integration. Needs approved source list, terms, credentials, polling/refresh ownership, safety, and tests before adapter/API/schema work. |
| BLOCKED | LLM/agent implementation. Needs provider, model, prompt/versioning, tool contracts, evaluation, privacy, fallback, and approval design. |
| UNDEFINED | External application submission, messaging, scheduling, email/push, data export/deletion, deployment/observability requirements. |

The next exact change number is **CHANGE-0029**, but its objective is **UNDEFINED — REQUIRES PRODUCT DECISION**. Production job sources and LLM/agent implementation remain blocked on their documented approvals and design decisions.
