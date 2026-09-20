# JobPilot AI — Product Requirements Document

## Status and authority

This is a deterministic blueprint of the repository as inspected on 2026-09-09. Product requirements documents and approved change records are authoritative. The repository has progressed through CHANGE-0023, although the supplied planning brief describes a CHANGE-0022 baseline; this is documented as an implementation divergence, not silently discarded.

## Vision, problem, and users

JobPilot AI is a controlled assistant for an individual early-career job seeker or student. It helps them discover, understand, match, rank, explain, prepare, validate, review, approve, and manage applications. Job searching is fragmented and repetitive; the product reduces that work while preserving truthful, reviewable, user-controlled decisions. Employers, recruiters, advisors, teams, and autonomous mass-application workflows are outside the initial target.

## Goals and non-goals

Goals: normalize shared opportunities; preserve an owner-scoped candidate profile and resume; give deterministic fit/ranking explanations; prepare grounded drafts; make review and approval explicit; track applications manually and truthfully; record activity, feedback, and notifications.

Non-goals: autonomous application submission; claiming a submission or status without evidence; inventing profile facts; silent preference learning; email/push/calendar integrations; broad browser automation; externally sourced status automation. **UNDEFINED — REQUIRES PRODUCT DECISION:** initial production job sources, any consequential external-action integration, notification delivery channels, and retention/deletion policy.

## MVP scope and journeys

1. A user registers, signs in, creates a profile, adds professional data and resumes, then reviews parsed resume data before promotion to trusted profile data.
2. An authorized administrator ingests normalized shared jobs. A signed-in user searches, matches, analyzes, and ranks them using approved profile data and saved preferences.
3. A user creates a grounded application draft, edits it, reviews its revision, and explicitly approves that revision. The system does not submit it.
4. A user creates and updates a private manual application record. `SUBMITTED` is only user-recorded; uncertain external submission is `UNKNOWN`.
5. A user records feedback. Only the CHANGE-0023 proposal/review/confirm workflow can alter a preference or add a skill. Rejection changes no durable data; revocation restores the saved prior value where safely possible.

## Functional requirements

| Area | Requirement | Current state |
|---|---|---|
| Identity | Email/password registration, JWT authentication, active-user enforcement | DONE |
| Profile | Owner-scoped profile, skills, education, experience, projects, preferences | DONE |
| Resume | Upload, extract, parse, review/edit, approve and promote trusted data | DONE |
| Jobs | Admin local ingestion, shared persistence/deduplication, search | DONE |
| Evaluation | Deterministic matching, analysis, ranking, explanations | DONE |
| Applications | Grounded revisioned drafts; explicit revision approval; manual records | DONE |
| Activity/notifications | Private activity feed and in-app notifications | DONE |
| Feedback | Owner-scoped feedback and confirmation-gated proposals | DONE through CHANGE-0023 |
| UI | End-user workflow UI | PARTIALLY DONE: foundation page only |
| Agent/external actions | Actual LLM tools, discovery automation, submission | NOT IMPLEMENTED / UNDEFINED |

## Control, safety, and responsibilities

AI (when introduced) may extract, interpret, summarize, explain, recommend, and draft only from permitted inputs. Deterministic services enforce identity, ownership, validation, status transitions, approval, writes, audit events, and any submission authorization. The human supplies truthful information, reviews extracted data and drafts, approves material changes, records manual application outcomes, and confirms proposed learning.

Never: apply or submit silently; treat weak signals as approval; mutate durable preferences from feedback; fabricate user facts or application status. A draft is not actionable until its current revision is explicitly approved. A failed or uncertain external action must be visible and recoverable, never reported as success.

## Application, feedback, activity, and notification behavior

Canonical record statuses are `SAVED`, `PREPARING`, `READY_FOR_REVIEW`, `APPROVED`, `SUBMITTED`, `INTERVIEW`, `REJECTED`, `OFFER`, `WITHDRAWN`, `UNKNOWN`. Transitions must be validated by the application service; the present implementation is manual tracking and has no submission executor. Activity explains meaningful workflow work with state, related entity, timestamp, details, and next action. Notifications are in-app, private, read/unread records; current approved cases include draft-ready, record status updates, unknown submission, and recoverable preparation failure.

Feedback mapping: `WRONG_PREFERENCE` may propose one approved list-valued preference replacement; `MISSING_SKILL` may propose an explicit skill; `INCORRECT` stores a reviewed correction without changing shared job/profile data; `INTERESTED`, `NOT_INTERESTED`, and `ALREADY_APPLIED` are informational. Confirmation records before/after values and source feedback; revoke restores/removes only the value created by that proposal.

## Non-functional requirements and metrics

Owner isolation, validation, deterministic ordering and state control, auditability, recoverable failures, secret handling, accessible review UI, and regression testing are required. Success is measured by critical unsupported-claim rate, critical-field accuracy, relevant top results, explanation comprehension, grounded-material pass rate, task completion, active effort, and critical incidents. No launch decision is implied by this document.
