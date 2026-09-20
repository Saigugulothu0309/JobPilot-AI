# JobPilot AI — API Contract

All routes except `/health`, registration, and login use JWT bearer authentication; private resources resolve the current user's profile and return not-found rather than exposing another owner's resource. Requests/responses use Pydantic schemas. Validation/domain conflict failures return client errors; unhandled server faults must not disclose secrets. Base path is `/api/v1`.

| Method / path | Current contract and side effects |
|---|---|
| `GET /health` | Public health response. |
| `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | Create local account, obtain token, view authenticated user. |
| `GET/PUT /profile`, `GET/PUT /profile/preferences` | Read/update current owner profile/preferences. PUT is durable and owner-only. |
| `GET/POST /profile/{skills,education,experience,projects}` | List/create owner data. |
| `PUT/DELETE /profile/{skills,education,experience,projects}/{id}` | Update/delete owner item; delete is permanent within current storage. |
| `POST /resumes`, `GET /resumes`, `GET /resumes/{id}`, `DELETE /resumes/{id}` | Owner resume upload/list/read/delete; upload validates supported file handling. |
| `POST /resumes/{id}/process`, `/parse`, `GET/PUT /review`, `POST /approve` | Extract/parse, review/edit, and explicitly promote resume data. Approval is idempotent and side-effectful. |
| `GET /jobs` | Authenticated shared-job search with bounded pagination/filters; read-only deterministic order. |
| `POST /jobs/ingest/local` | Configured admin email only; validates/normalizes shared job payload; deduplicates by key. |
| `POST /jobs/{id}/match`, `/analyze`; `GET /jobs/rank` | Owner-context derived match, analysis, and ranking; no persistent match/rank write. |
| `POST /applications/drafts`; `GET/PUT /applications/drafts/{id}`; `POST /approve` | Create/read/edit private grounded draft and explicitly approve its current revision. Edit invalidates stale approval. |
| `POST /applications/records`; `GET /applications/records`, `/{id}`; `PUT /{id}` | Create/list/read/update private manual tracking record, including truthful `UNKNOWN` handling. |
| `GET /activity`, `GET /notifications`, `POST /notifications/{id}/read` | Read owner activity/notifications and mark only owner notification read. |
| `POST/GET /feedback` | Upsert/list private job feedback. Recording is informational until a proposal is confirmed. |
| `POST /feedback/proposals` | Create owner proposal from matching feedback type. No durable profile mutation. |
| `POST /feedback/proposals/{id}/confirm|reject|revoke` | Explicit state action. Confirm applies valid preference/skill proposal; reject preserves feedback; revoke restores/deletes the proposal-applied value where safe. Repeated terminal same action is idempotent. Alias `/{id}/{action}` exists. |

The current schemas are the authoritative field-level contract; this document deliberately does not reproduce them loosely. All create/update operations have side effects as stated. Activity is recorded for material workflows (including feedback confirmation/revocation); notifications are issued by existing workflow services where supported. No endpoint submits an application, sends an external notification, or invokes an LLM.

## Planned APIs

None are approved. **UNDEFINED — REQUIRES PRODUCT DECISION:** dashboard aggregation, agent-state, preference-proposal listing, UI-session, external source, submission, notification-delivery, and deletion/export endpoints. Do not infer them from the UI plan.
