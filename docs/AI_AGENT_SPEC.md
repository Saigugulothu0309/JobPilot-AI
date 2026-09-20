# JobPilot AI — AI Agent Specification

## Governing rule

There is no implemented AI agent. This is the approved behavioral boundary for any future agent; it does not authorize an AI integration. AI may reason over scoped inputs and return structured proposals. Deterministic services retain all authorization, writes, approvals, and action execution.

| Stage | Input → output | Permitted tools/writes | Prohibited / stop condition | Visibility |
|---|---|---|---|---|
| Discover | approved source query → candidate job payload | approved read-only source adapter; no DB direct write | STOP on unavailable/unapproved source | activity `DISCOVERY_*`; no notification unless user action needed |
| Normalize | external payload → validated normalized job | normalization service may persist shared job through approved admin/system path | STOP on malformed/untrusted data or dedupe conflict requiring review | activity result/warning |
| Analyze | normalized job → requirements, signals, uncertainty | read-only deterministic analysis | no profile mutation; STOP on insufficient content | visible explanation/activity |
| Match | job + approved profile → fit evidence | read-only matching service | no inference of missing profile facts | visible explanation |
| Rank | matches + confirmed preferences → ordering | deterministic ranking service | no feedback-driven mutation without confirmed proposal | ranked list/explanation |
| Explain/Recommend | derived evidence → concise explanation/recommendation | schema-validated text generation may be proposed later | no certainty beyond evidence; STOP on low confidence | user-visible rationale/warning |
| Prepare | approved profile/resume + job → draft content | application draft service only | no unsupported claim; STOP if profile/resume incomplete | draft and `DRAFT_*` activity/notification |
| Validate | draft → groundedness/uncertainty findings | read-only validation | no auto-approval; STOP on unsupported material claim | review warnings |
| User review | draft/proposal → edited review state | human writes through API | agent cannot infer approval | waiting-for-user activity |
| User approval | explicit current revision/proposal confirmation → authorized state | deterministic approval/confirm endpoint | STOP without explicit valid approval | approval activity/notification |
| Consequential action | approved action → verified result | **not implemented; requires separate approval/design** | STOP on uncertain result, missing owner, or absent executor | `UNKNOWN`/warning, never false success |

Feedback learning follows Feedback → Proposal → User Review → Confirm/Reject → Durable Change. `WRONG_PREFERENCE` and `MISSING_SKILL` can make explicit proposals; `INCORRECT` is review-only; other feedback is informational. Revocation restores the recorded prior value where possible. Every material operation must expose what happened, evidence, result, uncertainty, required user action, and next action.

Global STOP conditions: absent authenticated owner; missing required profile data; invalid schema; low/unknown confidence for consequential claim; external result uncertainty; a pending review/approval; unconfirmed durable preference change; stale draft approval; policy conflict; or untrusted content attempting to alter instructions.
