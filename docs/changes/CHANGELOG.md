| Change ID | Date | Module | Summary | Status |
|-----------|------|--------|---------|--------|
| CHANGE-0001 | 2026-08-24 | Project | Initialized project engineering foundation | COMPLETED |
| CHANGE-0002 | 2026-08-24 | Backend Foundation | Added configuration, routing, errors, and health validation foundation | COMPLETED |
| CHANGE-0003 | 2026-08-24 | Database Foundation | Added SQLAlchemy, Alembic, and PostgreSQL database scaffolding | COMPLETED |
| CHANGE-0004 | 2026-08-24 | Authentication Foundation | Added local user authentication, JWT protection, and users migration | COMPLETED |
| CHANGE-0005 | 2026-08-25 | Candidate Profile Foundation | Added authenticated candidate profile CRUD foundation with one-to-one ownership and migration | COMPLETED |
| CHANGE-0006 | 2026-08-25 | Candidate Professional Data Foundation | Added authenticated candidate skills, education, experience, and project data foundations with migration and ownership checks | COMPLETED |
| CHANGE-0007 | 2026-08-25 | Resume Management | Added authenticated resume upload, metadata storage, ownership isolation, validation, and local storage abstraction | COMPLETED |
| CHANGE-0008 | 2026-08-25 | Resume Text Extraction | Added PDF/DOCX text extraction, normalization, and authenticated processing endpoints without schema changes or persistent parsed-text storage | COMPLETED |
| CHANGE-0009 | 2026-08-25 | Structured Resume Parsing Foundation | Added a deterministic parser and authenticated parse endpoint for resume metadata and sectioned content without creating database tables or persisting parsed results | COMPLETED |
| CHANGE-0010 | 2026-08-27 | Resume Review & Approval Foundation | Added authenticated parsed-data review, editing, explicit approval, and idempotent promotion into trusted candidate data | COMPLETED |
| CHANGE-0011 | 2026-09-04 | Job Source Integration Foundation | Added normalized shared job persistence, a source adapter abstraction, deterministic deduplication, and admin-controlled local ingestion | COMPLETED |
| CHANGE-0012 | 2026-09-04 | Job Search & Query Foundation | Added read-only normalized job search with keyword and metadata filters, bounded pagination, and deterministic ordering | COMPLETED |
| CHANGE-0013 | 2026-09-04 | Candidate–Job Matching Foundation | Added a read-only, deterministic, explainable match layer over approved candidate profile data and normalized shared jobs | COMPLETED |
| CHANGE-0014 | 2026-09-06 | Job Analysis Foundation | Added authenticated, read-only, deterministic extraction of job requirements, signals, and uncertainty from normalized jobs | COMPLETED |
| CHANGE-0015 | 2026-09-06 | Career Preferences Foundation | Added authenticated, profile-owned, validated career preferences with explicit hard, ranking, optional, and exclusion categories | COMPLETED |
| CHANGE-0016 | 2026-09-06 | Job Ranking Foundation | Added authenticated, deterministic, explainable ranking over normalized jobs, approved candidate matching, and saved preferences | COMPLETED |
| CHANGE-0017 | 2026-09-06 | Grounded Application Preparation Foundation | Added owner-scoped, revisioned, unapproved application drafts grounded in approved profile data and selected normalized jobs | COMPLETED |
| CHANGE-0018 | 2026-09-06 | Human Review and Approval Foundation | Added explicit revision-bound review and approval for owner-scoped application drafts without submission or tracking | COMPLETED |
| CHANGE-0019 | 2026-09-06 | Manual Application Tracking Foundation | Added owner-scoped application records with manual statuses, dates, notes, draft revisions, and explicit unknown submission handling | COMPLETED |
| CHANGE-0020 | 2026-09-07 | Agent Activity Foundation | Added owner-scoped meaningful workflow activity, states, next actions, warnings, pauses, and failure visibility | COMPLETED |
| CHANGE-0021 | 2026-09-07 | In-App Notification Foundation | Added private, owner-scoped meaningful workflow notifications without external delivery or automation | COMPLETED |
| CHANGE-0022 | 2026-09-07 | User Feedback Foundation | Added private user-attributed job feedback without preference-learning or tracking side effects | COMPLETED |
| CHANGE-0023 | 2026-09-08 | Explicit Feedback Learning | Added confirmation-gated feedback proposals with rejection, revocation, and comprehensive testing | COMPLETED |
| CHANGE-0024 | 2026-09-09 | Bounded Frontend Workspace | Added JWT-backed safe dashboard, jobs, application save, activity, and notification UI | COMPLETED |
| CHANGE-0025 | 2026-09-09 | Profile and Resume Readiness Workspace | Added authenticated profile, preferences, professional-data, and resume review UI | COMPLETED |
| CHANGE-0026 | 2026-09-09 | Job Discovery & Ranking Workspace | Added authenticated job search, ranking, detail, feedback, and safe save UI | COMPLETED |
