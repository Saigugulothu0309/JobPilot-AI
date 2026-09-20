# JobPilot AI — Security Model

Authentication is local email/password plus JWT. Authorization is service/API owner scoping from the token; client profile IDs are not trusted. Admin local job ingestion is restricted to `JOB_INGESTION_ADMIN_EMAILS`. Shared jobs are readable to authenticated users; private candidate data, resumes, drafts, records, activity, notifications, feedback, and proposals are never returned across owners.

Input uses Pydantic validation plus module-specific file/URL handling. External job descriptions, URLs, uploads, and future tool results are untrusted content; they must never become system instructions or expand tool permission. Future LLM prompts must delimit and label external content, schema-validate output, expose uncertainty, prohibit direct database access, and route all mutations through deterministic services.

Secrets are environment-backed (`DATABASE_URL`, `AUTH_SECRET`, `AI_API_KEY`) and must not be committed, returned, or logged. PII belongs to the profile/resume domain; logs/activity should contain the minimum useful structured context, not raw credentials or resume contents. Activity/proposals supply auditability but are not a substitute for a formal immutable audit policy.

Least privilege applies to users, admin ingestion, storage, database roles, and future tools. The system must reject or pause uncertain external results; only reliable evidence may yield Submitted. **UNDEFINED — REQUIRES PRODUCT DECISION:** production secret manager/rotation, encryption-at-rest posture, upload malware scanning, rate limiting, session revocation, CORS/CSRF deployment policy, log retention/redaction, export/deletion fulfillment, incident response, and admin governance.
