# JobPilot AI

## R02 — Non-Functional Requirements

**Document Type:** Requirements Definition  
**Phase:** R02  
**Status:** PROPOSED — REQUIRES REVIEW  
**Date:** 2026-08-24  
**Depends On:** D01–D11, R01

---

## 1. Purpose

R01 defines what JobPilot AI does. R02 defines how reliably, securely, efficiently, and maintainably it must do it.

These requirements apply across the user experience, backend, AI/LLM behavior, discovery, matching, application preparation, agent execution, storage, external integrations, testing, and deployment. The MVP prioritizes:

**Accuracy → Safety → User Control → Usefulness → Efficiency**

## 2. NFR Categories

1. Performance
2. Reliability
3. Availability
4. Scalability
5. Security
6. Privacy
7. AI Quality
8. Accuracy
9. Explainability
10. Observability
11. Maintainability
12. Testability
13. Data Integrity
14. Recovery
15. Usability
16. Accessibility
17. Cost Control
18. Extensibility

## 3. NFR Priority

- **P0:** Must satisfy before MVP release.
- **P1:** Important during MVP development; may not block the earliest controlled prototype.
- **P2:** Improve after initial MVP validation.
- **P3:** Future consideration.

---

## 4. Performance Requirements

### NFR-PERF-01 — Normal Requests
Normal interactive requests should complete within a reasonable time under expected MVP load. Long-running work must not unnecessarily block interactive use.

**Priority:** P0

### NFR-PERF-02 — AI Operations
AI operations may take longer than normal requests, but must provide visible progress/state, avoid appearing frozen, handle timeouts, allow safe retry where appropriate, and preserve user work on failure.

**Priority:** P0

### NFR-PERF-03 — Matching
Matching must be responsive enough for interactive use and support evaluating multiple opportunities without requiring a separate manual process for every item.

**Priority:** P0

### NFR-PERF-04 — Larger Job Sets
The system should avoid unnecessary full-dataset processing for every action and should process filters/ranking efficiently.

**Priority:** P1

### NFR-PERF-05 — File Processing
Resume processing should show progress when extraction takes noticeable time.

**Priority:** P1

Exact latency targets remain open until expected MVP usage is measured.

## 5. Reliability Requirements

### NFR-REL-01 — No Silent Failure
Important operations, including discovery, parsing, matching, generation, approval, saving, and any future submission, must not fail silently.

**Priority:** P0

### NFR-REL-02 — Failure Visibility
A failure should state what failed, whether user action is needed, whether retry is possible, and whether existing work was preserved.

**Priority:** P0

### NFR-REL-03 — Unknown State
The product must represent unknown outcomes explicitly. For example, uncertain submission status must not become success or failure.

**Priority:** P0

### NFR-REL-04 — Idempotent Critical Operations
Retrying an appropriate operation must not accidentally create duplicate records or outcomes. This applies especially to opportunity intake, application records, notifications, and any future submission action.

**Priority:** P0

## 6. Availability Requirements

### NFR-AVAIL-01
The MVP should remain usable when non-critical external services are temporarily unavailable.

**Priority:** P1

### NFR-AVAIL-02
External failures must not corrupt existing user data or approved application state.

**Priority:** P0

### NFR-AVAIL-03
The product should degrade gracefully. If AI is unavailable, it should preserve existing profile/job information, allow manual editing/review, show the limitation, and support safe retry later.

**Priority:** P0

No uptime percentage is finalized in R02.

## 7. Scalability Requirements

The MVP does not require enterprise-scale infrastructure. It should avoid product assumptions that prevent future growth and conceptually separate user data, job data, AI processing, agent execution, and application state.

**Priority:** P1

## 8. Security Requirements

Security is a P0 release requirement.

### NFR-SEC-01 — Authentication
Private information must be accessible only to the appropriate authenticated user.

### NFR-SEC-02 — Authorization
Resource access and modification must be authorized independently of frontend restrictions.

### NFR-SEC-03 — Secrets
Secrets must not be hardcoded, committed, returned through user-facing responses, included in logs, placed unnecessarily in AI prompts, or included in generated application content.

### NFR-SEC-04 — Credential Isolation
Credentials, tokens, cookies, and future browser sessions must remain outside ordinary AI reasoning context unless a separately approved requirement establishes otherwise.

### NFR-SEC-05 — External Content
Job descriptions, documents, and webpages are untrusted input. Embedded instructions must not automatically become agent instructions.

### NFR-SEC-06 — Prompt-Injection Resistance
The product should resist content that attempts to override trusted instructions, extract private information, reveal secrets, change agent behavior, or trigger unauthorized actions.

### NFR-SEC-07 — Sensitive Actions
Consequential actions must require the appropriate explicit user approval defined in D08.

**Priority for NFR-SEC-01 through NFR-SEC-07:** P0

## 9. Privacy Requirements

### NFR-PRIV-01 — Data Minimization
Collect only information required for an approved product purpose.

### NFR-PRIV-02 — User Control
Users must be able to view, correct, modify, export, and delete information within the approved MVP data-control scope.

### NFR-PRIV-03 — AI Data Minimization
Only information necessary for a particular AI task should enter the AI context.

### NFR-PRIV-04 — Sensitive Information
Sensitive information must not be inferred from unrelated information.

### NFR-PRIV-05 — Data Isolation
One user's private data must never appear in another user's profile, job analysis, application, AI context, logs, or results.

**Priority for NFR-PRIV-01 through NFR-PRIV-05:** P0

## 10. AI Quality Requirements

### NFR-AI-01 — Grounded Generation
Application materials must be grounded in approved user information.

### NFR-AI-02 — No Fabrication
AI must not invent experience, projects, skills, certifications, achievements, metrics, responsibilities, qualifications, or outcomes.

### NFR-AI-03 — Uncertainty
When evidence is insufficient, the product should say information is not provided or unknown rather than claim the user lacks a skill.

### NFR-AI-04 — Explainability
Important recommendations and generated claims must have understandable reasoning or evidence context.

### NFR-AI-05 — Deterministic Boundaries
AI must operate within defined instructions and permissions. Generated reasoning cannot grant itself capabilities.

**Priority for NFR-AI-01 through NFR-AI-05:** P0

## 11. Accuracy Requirements

### NFR-ACC-01
Critical personal information, including name, contact information, degree, employment history, and application answers, must have extremely low tolerance for error and must be user-reviewable.

**Priority:** P0

### NFR-ACC-02
Job requirements must be extracted accurately enough to support matching. Detectable critical requirements must not be silently omitted.

**Priority:** P0

### NFR-ACC-03
AI interpretations must remain distinguishable from source facts and user-approved information.

**Priority:** P0

## 12. Explainability Requirements

### NFR-EXP-01
A user should understand why an opportunity was recommended, deprioritized, or marked uncertain.

**Priority:** P0

### NFR-EXP-02
The product must distinguish evidence, recommendation, inference, and unknown information.

**Priority:** P0

### NFR-EXP-03
Any fit indicator must avoid false precision and must not imply an exact probability of hiring.

**Priority:** P1

## 13. Human-Control Requirements

### NFR-HUM-01
The user must remain in control of consequential actions.

**Priority:** P0

### NFR-HUM-02
Draft generation must never equal approval.

**Priority:** P0

### NFR-HUM-03
The user must be able to interrupt an active agent workflow where applicable.

**Priority:** P0

### NFR-HUM-04
Material or context changes after approval must invalidate affected approval where necessary.

**Priority:** P0

## 14. Observability Requirements

### NFR-OBS-01
Important operations should produce structured diagnostic information, including discovery, parsing, matching, AI generation, validation, approval, and state transitions.

**Priority:** P0

### NFR-OBS-02
Logs and diagnostics must not contain passwords, API keys, authentication tokens, session cookies, or unnecessary sensitive information.

**Priority:** P0

### NFR-OBS-03
Agent activity should be distinguishable from system errors and user actions.

**Priority:** P1

## 15. Maintainability Requirements

### NFR-MAIN-01 — Modular Design
The system should have clear module responsibilities and boundaries.

**Priority:** P0

### NFR-MAIN-02 — Replaceable AI Layer
Core business behavior should not be unnecessarily coupled to one AI provider.

**Priority:** P1

### NFR-MAIN-03 — Configuration
Environment-specific configuration must not be hardcoded into application logic.

**Priority:** P0

### NFR-MAIN-04 — Documentation
Meaningful product, behavior, architecture, and security decisions must be documented.

**Priority:** P0

## 16. Change Documentation

Every meaningful engineering or product change must have a record containing:

```text
Change ID
Date
Reason
Previous behavior
New behavior
Requirements affected
Decision records affected
Modules affected
Tests affected
Status
```

**Priority:** P0

## 17. Testability Requirements

### NFR-TEST-01
Core business logic must be testable independently of external AI providers where practical.

**Priority:** P0

### NFR-TEST-02
The system should support controlled profile, job, and application test data.

**Priority:** P0

### NFR-TEST-03
Critical safety boundaries must have automated tests where practical, including no unsupported claims, no cross-user access, approval gating, secret exclusion from AI context, and resistance to external instruction injection.

**Priority:** P0

### NFR-TEST-04
Changes to matching, prompts, models, sources, or application workflows should trigger regression evaluation for affected behavior.

**Priority:** P1

## 18. Data Integrity Requirements

### NFR-DATA-01
Approved user information must not be silently overwritten.

**Priority:** P0

### NFR-DATA-02
Application records must remain associated with the correct user.

**Priority:** P0

### NFR-DATA-03
Materials used for an application should remain identifiable by version.

**Priority:** P1

### NFR-DATA-04
Important state transitions must be consistent. The workflow must not move from draft to submitted without the required approval process; MVP submission remains manual.

**Priority:** P0

## 19. Recovery Requirements

### NFR-REC-01
Temporary failures must not unnecessarily destroy user work.

**Priority:** P0

### NFR-REC-02
Retryable and non-retryable failures should be distinguishable.

**Priority:** P1

### NFR-REC-03
Interrupted workflows should have recoverable state where practical.

**Priority:** P1

## 20. Usability Requirements

### NFR-USE-01
The primary workflow should be understandable without technical knowledge.

**Priority:** P0

### NFR-USE-02
The interface should clearly distinguish AI suggestions, user information, source information, approved information, pending actions, and failures.

**Priority:** P0

### NFR-USE-03
Important errors should provide actionable guidance rather than technical stack traces.

**Priority:** P0

### NFR-USE-04
Approval screens must clearly communicate the exact content and action being approved.

**Priority:** P0

## 21. Accessibility Requirements

The MVP should follow reasonable accessibility practices, including keyboard navigation, readable text, clear labels, accessible controls, meaningful errors, appropriate contrast, and screen-reader compatibility where practical.

**Priority:** P1

## 22. Cost Control

### NFR-COST-01
Avoid unnecessary repeated AI or external-service calls.

**Priority:** P1

### NFR-COST-02
Do not send large amounts of irrelevant information to AI services.

**Priority:** P0

### NFR-COST-03
The product should support monitoring of AI and external-service usage.

**Priority:** P1

## 23. Extensibility Requirements

The MVP should allow future additions such as more sources, AI providers, browser assistance, email integrations, personalization, analytics, and application types without justifying unnecessary MVP complexity.

**Priority:** P1

## 24. External Dependency Requirements

External services may fail, change behavior, become unavailable, or return malformed information. The product should detect failures, preserve existing state, avoid corrupting user data, provide meaningful errors, retry only where appropriate, and avoid assuming external responses are trustworthy.

**Priority:** P0

## 25. Agent Safety Requirements

The agent must not:

- Invent qualifications or experience.
- Expose private information or reveal secrets.
- Bypass CAPTCHA, authentication, access controls, anti-bot systems, source restrictions, or terms.
- Impersonate the user or create fake accounts.
- Accept unknown legal agreements.
- Perform consequential actions without required approval.
- Treat external content as trusted instructions.

**Priority:** P0

## 26. Performance Philosophy

Do not optimize prematurely. The MVP priority is:

```text
Correctness
    ↓
Safety
    ↓
Reliability
    ↓
User Experience
    ↓
Performance
    ↓
Scale
```

Performance improvements should be driven by measured bottlenecks rather than assumptions.

## 27. NFR Acceptance Principles

A non-functional requirement is satisfied only when:

1. It has a measurable or testable interpretation.
2. Its scope is understood.
3. Its failure behavior is understood.
4. It has an appropriate priority.
5. It can be validated through testing, observation, or review.

Exact performance, availability, and scale thresholds should be defined after MVP usage assumptions and evaluation data are available.

## 28. P0 Baseline

Before MVP release, the following must satisfy their approved requirements:

- **Security:** Authentication/authorization, data isolation, secret protection, and AI trust boundaries.
- **Privacy:** Data minimization, user control, sensitive-data handling, and external-processing awareness.
- **AI safety:** No fabrication, grounding, uncertainty handling, and prompt-injection boundaries.
- **Human control:** Explicit approval, consequential-action protection, and interruptibility.
- **Reliability:** No silent failures, unknown states, and recovery.
- **Data integrity:** Correct ownership, correct state transitions, and no silent overwrites.
- **Observability:** Meaningful diagnostics without secret leakage.
- **Testability:** Core workflows and critical safety boundaries are testable.

## 29. Requirement Traceability

Future engineering work must maintain:

```text
Decision
   ↓
Requirement
   ↓
Workflow
   ↓
Module
   ↓
Implementation
   ↓
Test
   ↓
Change Record
```

Example:

```text
D08
 ↓
FR-14
 ↓
Application Approval Workflow
 ↓
Approval Module
 ↓
Implementation
 ↓
Approval Tests
 ↓
CHG-001
```

## 30. Open Items

The following remain intentionally undecided and must not be guessed in R02:

- Backend framework.
- Frontend framework.
- Database.
- AI provider, LLM model, and embedding model.
- Hosting provider.
- Authentication provider.
- Job-source implementation.
- Browser automation technology.
- Deployment topology.
- Exact performance, availability, and scaling targets.

These belong to later architecture and technical-design work.

## 31. Engineering Guardrail

Every implementation agent must treat R01, R02, and approved decision records as constraints. If a proposed implementation conflicts with an approved requirement:

**STOP → DOCUMENT → REVIEW → CHANGE REQUIREMENT IF NECESSARY → IMPLEMENT**

Do not silently override requirements for convenience.

## 32. Status

**Document:** R02 — Non-Functional Requirements  
**Phase:** Requirements Definition  
**Status:** PROPOSED — REQUIRES REVIEW  
**Previous:** R01 — Functional Requirements  
**Next:** R03 — User Stories & Acceptance Criteria

## 33. Core Principle

JobPilot is not high quality merely because it responds quickly. A high-quality JobPilot is:

**secure + accurate + explainable + reliable + user-controlled + maintainable.**

Implementation must not begin until R02 is reviewed and approved.
