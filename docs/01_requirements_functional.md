# JobPilot AI

## R01 — Functional Requirements

**Document Type:** Requirements Definition  
**Phase:** R01  
**Status:** PROPOSED — REQUIRES REVIEW  
**Date:** 2026-08-24  
**Based On:** D01–D11 Decision Records

---

## 1. Purpose

This document defines the functional requirements for the JobPilot AI MVP.

JobPilot AI helps one student or fresh graduate:

1. Create and maintain a professional profile.
2. Discover relevant internships and entry-level opportunities.
3. Understand job requirements.
4. Match opportunities against approved profile information.
5. Rank and explain opportunities.
6. Prepare grounded application materials.
7. Review and approve generated materials.
8. Track application progress manually.

The MVP prioritizes **accuracy → safety → user control → usefulness → efficiency**. It does not automatically submit applications, run browser automation, perform mass applications, or support employer/team workflows.

## 2. Core MVP Workflow

```text
User
 ↓
Create Account
 ↓
Create / Import Profile
 ↓
Review Profile
 ↓
Set Job Preferences
 ↓
Discover User-Provided Opportunity
 ↓
Preserve Source and Freshness
 ↓
Normalize Job Information
 ↓
Analyze Requirements
 ↓
Match Against Approved Profile
 ↓
Rank and Explain Opportunity
 ↓
User Selects Opportunity
 ↓
Prepare Grounded Application
 ↓
Generate Draft Materials
 ↓
Validate Content
 ↓
User Reviews and Edits
 ↓
User Approves Exact Package
 ↓
Application Package Ready for Manual Submission
 ↓
Track Application
```

The workflow must remain usable when information is missing, uncertain, conflicting, or unavailable. It must never treat draft generation as approval.

## 3. Functional Requirement IDs

- FR-01 — Account & Access
- FR-02 — User Profile
- FR-03 — Resume Processing
- FR-04 — Career Preferences
- FR-05 — Job Discovery
- FR-06 — Job Normalization
- FR-07 — Job Analysis
- FR-08 — Job Matching
- FR-09 — Job Ranking
- FR-10 — Match Explanation
- FR-11 — Application Preparation
- FR-12 — Content Validation
- FR-13 — Human Review
- FR-14 — Approval
- FR-15 — Application Tracking
- FR-16 — Agent Activity
- FR-17 — Notifications
- FR-18 — User Feedback
- FR-19 — Data Control
- FR-20 — Auditability
- FR-21 — Error Recovery
- FR-22 — Security Boundaries

---

## 4. FR-01 — Account & Access

### FR-01.1
The system shall allow a user to create an account.

### FR-01.2
The system shall authenticate returning users.

### FR-01.3
The system shall maintain an authenticated user session and allow logout.

### FR-01.4
The system shall prevent one user's private profile, application, and generated-content information from being exposed to another user.

### FR-01.5
Authentication credentials and secrets shall not be exposed to the AI reasoning layer.

## 5. FR-02 — User Profile

### FR-02.1
The system shall allow the user to create, view, edit, and delete a professional profile.

### FR-02.2
The profile shall support, where provided, name, contact information, education, graduation/expected graduation, skills, technologies, projects, work experience, internships, certifications, achievements, and professional links.

### FR-02.3
The system shall distinguish user-provided information, extracted information, AI suggestions, AI inference, corrections, and user-approved information.

### FR-02.4
AI-inferred information shall not automatically become an approved user fact.

### FR-02.5
The system shall identify missing information as not provided or unknown rather than assuming the user lacks it.

## 6. FR-03 — Resume Processing

### FR-03.1
The user shall be able to upload a resume or provide equivalent career information.

### FR-03.2
The system shall extract relevant professional information from the supplied resume.

### FR-03.3
Extracted information shall be presented for user review with its source relationship.

### FR-03.4
The user shall be able to correct, reject, or approve extraction results.

### FR-03.5
The system shall not silently overwrite approved profile information with newly extracted information.

### FR-03.6
The system shall preserve the relationship between extracted information and its source/version.

## 7. FR-04 — Career Preferences

### FR-04.1
The system shall allow the user to specify target roles, internship/full-time preference, locations, remote/hybrid/on-site preferences, industries, technologies, salary preferences where applicable, relocation preferences, career interests, exclusions, and deal-breakers.

### FR-04.2
The system shall distinguish hard constraints from ranking preferences and optional preferences.

### FR-04.3
The system shall not treat a normal preference as an eligibility restriction unless the user explicitly defines it as such.

## 8. FR-05 — Job Discovery

### FR-05.1
The system shall allow opportunities to enter the workflow through D05-approved methods: user-provided job URLs, manual job entry, or supplied job descriptions.

### FR-05.2
The system shall preserve the original opportunity source, reference, and application URL where available.

### FR-05.3
The system shall record retrieval, receipt, or last-checked context where available.

### FR-05.4
The system shall identify freshness as new, fresh, possibly outdated, expired, closed, or unknown when evidence permits.

### FR-05.5
The system shall detect or warn about potential duplicate opportunities without silently losing source information.

### FR-05.6
The system shall not silently create a confident opportunity record when critical source information cannot be verified.

### FR-05.7
The system shall respect source permissions, terms, and access restrictions and shall not bypass authentication, CAPTCHA, bot protection, or access controls.

## 9. FR-06 — Job Normalization

### FR-06.1
The system shall transform source-specific information into a consistent product-level representation containing, where available, job title, company, location, work mode, employment type, experience requirements, education requirements, required/preferred skills, compensation, deadline, description, application URL, source, and freshness context.

### FR-06.2
The system shall preserve original source information alongside normalized information.

### FR-06.3
The system shall distinguish not provided, not applicable, unknown, and conflicting information where meaningful.

### FR-06.4
The system shall not silently convert an interpretation into source-stated fact.

## 10. FR-07 — Job Analysis

### FR-07.1
For a selected opportunity, JobPilot shall identify role requirements, required skills, preferred skills, experience, education, location, work mode, employment type, and other important requirements.

### FR-07.2
The system shall identify ambiguous, conflicting, missing, or uncertain information.

### FR-07.3
Important requirements shall be distinguishable from general job-description text.

### FR-07.4
External job content shall be treated as untrusted information rather than executable instructions.

## 11. FR-08 — Job Matching

### FR-08.1
The system shall compare an opportunity against the user's approved profile and preferences using the approved hybrid matching model.

### FR-08.2
Matching shall consider role alignment, required/preferred skills, evidence type, education, professional experience, internships, projects, certifications, location, work mode, employment type, availability, graduation requirements, and career preferences as appropriate.

### FR-08.3
The system shall distinguish hard constraints from normal preferences.

### FR-08.4
The system shall not treat missing profile information as proof that a user lacks a skill or experience.

### FR-08.5
The system shall distinguish exact matches, related skills, transferable skills, project evidence, user-claimed skills, AI-inferred skills, and unknown skills.

### FR-08.6
The system shall not invent experience, qualifications, proficiency, or legal eligibility during matching.

## 12. FR-09 — Job Ranking

### FR-09.1
The system shall rank opportunities according to approved scope eligibility, match quality, user preferences, role relevance, freshness, source confidence, and other approved factors.

### FR-09.2
Hard constraints shall not be silently offset by a high soft-fit score.

### FR-09.3
The ranking system shall not imply false certainty or use arbitrary, unexplained, popularity-based, or company-name-based factors without product justification.

### FR-09.4
The user shall be able to understand when ranking priorities affect ordering.

## 13. FR-10 — Match Explanation

### FR-10.1
For each meaningful recommendation, the system shall explain strengths, relevant evidence, gaps, unknowns, constraints, and AI interpretations separately.

### FR-10.2
The system shall identify evidence supporting important claims about the user's fit.

### FR-10.3
The system shall distinguish factual evidence from AI interpretation.

### FR-10.4
The system shall not claim that a user possesses a skill without supporting evidence.

### FR-10.5
The system shall use understandable categories such as Strong potential match, Good potential match, Possible match - needs review, Weak match, Not recommended, and Insufficient information.

## 14. FR-11 — Application Preparation

### FR-11.1
For a selected opportunity, JobPilot shall prepare an application package using approved user information and opportunity context.

### FR-11.2
The MVP shall support grounded resume tailoring, a short application summary, concise common application answers, and approved project/experience descriptions.

### FR-11.3
A concise cover letter and portfolio/project selection may be supported as optional MVP materials.

### FR-11.4
The system may rephrase existing facts, reorder or highlight relevant content, tailor wording, and add only keywords supported by approved information.

### FR-11.5
The system shall not create or imply unsupported experience, job titles, projects, certifications, technologies, achievements, metrics, responsibilities, employers, dates, or proficiency.

### FR-11.6
The system shall preserve one master resume plus opportunity-specific tailored copies and the exact versions used for an application.

## 15. FR-12 — Content Validation

### FR-12.1
Before approval, the system shall validate unsupported claims, contradictions, missing required information, incorrect company/job details, incorrect technologies, excessive keyword stuffing, unprofessional wording, generic filler, and sensitive or legal unanswered questions.

### FR-12.2
The system shall flag uncertain or unsupported content.

### FR-12.3
The system shall not silently repair unsupported claims by inventing information.

### FR-12.4
The system shall allow the user to correct, reject, regenerate, or complete flagged content manually.

## 16. FR-13 — Human Review

### FR-13.1
The user shall be able to review generated application material before approval.

### FR-13.2
Review shall show what the AI generated, what information was used, what changed, what remains missing, what is uncertain, and what evidence supports important claims.

### FR-13.3
Viewing, editing, saving, or generating a draft shall not constitute approval.

## 17. FR-14 — Approval

### FR-14.1
The user shall explicitly approve the exact resume, cover letter if included, each generated answer, sensitive content if included, personal information used, and final package contents.

### FR-14.2
Draft generation shall not equal approval.

### FR-14.3
Material or context changes after approval shall invalidate the affected approval and require review again.

### FR-14.4
The system shall clearly indicate what the user is approving.

### FR-14.5
The MVP shall mark the package ready for manual submission but shall not submit it automatically.

## 18. FR-15 — Application Tracking

### FR-15.1
The MVP shall provide lightweight application tracking with statuses: Saved, Preparing, Ready for Review, Approved, Submitted, Interview, Rejected, Offer, Withdrawn, and Unknown.

### FR-15.2
The system shall retain the selected opportunity, relevant dates, known status, user notes, and exact material versions used.

### FR-15.3
The system shall not falsely mark an application as submitted.

### FR-15.4
If submission status cannot be verified, the system shall indicate: **Submission status unknown — verify manually.**

## 19. FR-16 — Agent Activity

### FR-16.1
The system shall provide visibility into meaningful agent activity, including opportunity input, analysis, matching, drafting, warnings, pauses, approvals, failures, and completion state.

### FR-16.2
The user shall be able to understand the current state and next required action.

### FR-16.3
The system shall not claim completion when an underlying action failed or remains uncertain.

## 20. FR-17 — Notifications

### FR-17.1
Notifications should be limited to meaningful events such as a draft ready, approval required, status change, action failure, or uncertain status.

### FR-17.2
Notification behavior shall not silently create automated discovery or external action. Exact notification scope remains subject to workflow requirements.

## 21. FR-18 — User Feedback

### FR-18.1
The user shall be able to mark an opportunity interested, not interested, incorrect, missing a skill, using a wrong preference, or already applied.

### FR-18.2
User corrections shall be distinguishable from AI assumptions.

### FR-18.3
Corrections affecting the profile or future ranking shall require appropriate user confirmation.

### FR-18.4
One-time feedback shall not become a durable preference unless the user confirms it.

## 22. FR-19 — Data Control

### FR-19.1
The user shall be able to view, edit, correct, export, and delete profile information.

### FR-19.2
The user shall be able to manage/remove uploaded resumes, delete application history, clear agent memory, revoke AI processing where applicable, and delete the account according to the approved privacy requirements.

### FR-19.3
Deletion and export behavior shall clearly communicate effects on active data, historical records, generated copies, and temporary data.

## 23. FR-20 — Auditability

### FR-20.1
The system shall maintain an appropriate record of profile changes, resume upload/removal, AI generation, approvals, rejections, permission changes, data exports/deletions, important agent activity, errors, and any future external action.

### FR-20.2
Audit records shall identify actor, action, time, relevant opportunity/data category, outcome, and approval context without exposing credentials or secrets.

## 24. FR-21 — Error Recovery

### FR-21.1
Job parsing failure shall be visible and shall not create invented information.

### FR-21.2
AI generation failure shall allow safe retry, manual editing, or abandonment.

### FR-21.3
Network, source, or processing failure shall preserve the user's current work where possible and provide a visible recovery state.

### FR-21.4
Conflicting profile/resume information shall pause affected claims and request user resolution.

### FR-21.5
The system shall never claim successful submission when the outcome is unknown.

### FR-21.6
The MVP shall provide manual fallback paths for incomplete or failed preparation.

## 25. FR-22 — Security Boundaries

### FR-22.1
External job content, documents, and web pages shall be treated as untrusted data, not instructions.

### FR-22.2
AI shall not access credentials, authentication tokens, cookies, browser sessions, government identifiers, financial credentials, or other secrets in the MVP.

### FR-22.3
Secrets shall not appear in generated content, logs, audit records, prompts, or source control.

### FR-22.4
Sensitive information shall not be inferred. Sensitive and legal questions require manual user involvement.

### FR-22.5
The agent shall not bypass CAPTCHA, authentication, access controls, anti-bot systems, source restrictions, or terms.

### FR-22.6
The agent shall not create fake accounts, impersonate the user, misrepresent qualifications, accept legal declarations, or submit applications automatically.

### FR-22.7
Consequential profile changes, package approval, sensitive-data use, and future external actions shall require appropriate explicit user approval.

## 26. Agent Responsibility Model

The MVP agent should perform:

```text
UNDERSTAND → DISCOVER → ANALYZE → MATCH → RECOMMEND → PREPARE → VALIDATE → WAIT FOR USER
```

It may plan and execute reversible internal preparation. It shall not independently decide to apply, accept terms, answer sensitive questions, make legal declarations, represent false information, access secrets, or submit applications.

## 27. Functional Priority

- **P0 — Core MVP:** Account/access, approved profile facts, resume review, preferences, user-provided opportunity intake, source/freshness context, normalization, job analysis, explainable matching/ranking, grounded preparation, validation, review/approval, manual tracking, activity, error recovery, and baseline security/data controls.
- **P1 — High priority:** Concise cover letters, duplicate grouping, project selection, richer quality checks, exports, reminders, and activity history improvements.
- **P2 — Later:** One separately approved external source, user-triggered source search, apprenticeships/trainee programs, and scheduled discovery.
- **P3 — Future:** Browser assistance, per-application execution, broader roles/career stages, advanced personalization, integrations, and organization workflows.

## 28. Functional Requirement Traceability

Every implementation task shall reference one or more requirements and related decisions. For example:

```text
Task: Resume extraction
Requirements: FR-03.1, FR-03.2, FR-03.3, FR-03.4
Decisions: D04, D09, D10
Validation: Approved resume extraction evaluation
```

The project must preserve this chain:

```text
Decision → Requirement → Module → Implementation → Test
```

## 29. Change Documentation Rule

Every meaningful product or engineering change shall record a change ID, date, reason, previous behavior, new behavior, affected requirements/decisions/modules/tests, and approval/status. No undocumented major behavior change may be introduced.

## 30. Requirement Acceptance Rule

A functional requirement is complete only when:

1. Its behavior is agreed.
2. Inputs and outputs are understood.
3. Failure behavior is defined.
4. Security and privacy implications are considered.
5. Acceptance criteria are defined.
6. It maps to an implementation module.
7. It can be tested.

These are requirements-definition criteria, not implementation work performed by R01.

## 31. Open Items

The following remain unresolved and must not be guessed:

- Final technology stack, backend, frontend, and database.
- AI provider/model and embedding approach.
- Authentication provider and final account mechanism.
- Job-source integrations and source permissions.
- Browser automation technology and scope.
- Hosting, deployment, and operational architecture.
- Exact matching algorithm, ranking weights, and thresholds.
- Exact notification mechanism.
- Detailed acceptance criteria and measurable thresholds, to be finalized through D11 requirements/evaluation work.

## 32. Current Status

**Document:** R01 — Functional Requirements  
**Phase:** Requirements Definition  
**Status:** PROPOSED — REQUIRES REVIEW  
**Based On:** D01–D11 Decision Records

**Next Requirement Document:** R02 — Non-Functional Requirements

## 33. Engineering Principle

JobPilot should not be built as “an AI that applies to jobs.” It should be built as:

> **A controlled system that helps a user discover, understand, prepare, review, and manage job applications, with AI doing repetitive reasoning work while the user retains control over consequential decisions.**

Implementation must not begin until R01 is reviewed and approved and the requirements set is sufficiently complete for the next planning step.
