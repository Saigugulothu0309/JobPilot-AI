# Architecture Reconciliation

## Baseline comparison

The requirements and CHANGE history support a backend-first, controlled workflow. Current code implements the backend through feedback proposals (CHANGE-0023), while the frontend remains a placeholder. The supplied blueprint instruction says do not create CHANGE-0023, but CHANGE-0023 and migration 0014 already exist and are marked completed. This conflict is historical/current-state divergence; the source of truth for behavior is the implemented code plus CHANGE-0023 unless product requirements later reject it.

| Severity | Finding | Evidence / required decision |
|---|---|---|
| HIGH | UI/backend mismatch | Broad authenticated backend exists; frontend only renders “foundation.” Approve a frontend scope before implementation. |
| HIGH | No actual AI-agent architecture | Config placeholders and empty AI package; no LLM, prompts, worker, tools, evaluation, or agent state. Define before AI work. |
| HIGH | No production external-job or submission integration | Local admin ingestion only; no source lifecycle or verified external action. Keep no-submission boundary. |
| MEDIUM | DB state validation is chiefly service-layer | Status/type constraints are not broadly database CHECK constraints. Decide defense-in-depth requirements before non-ORM access. |
| MEDIUM | API documentation had been absent | This blueprint now documents routes; field-level schemas remain code-authoritative and should gain generated OpenAPI/versioning policy if approved. |
| MEDIUM | Observability/data lifecycle incomplete | No approved retention, deletion, structured logs, monitoring, backups, rate limits, or scanning design. |
| LOW | Feedback proposal discoverability | APIs create/action a proposal but no proposal-list endpoint was found; UI feasibility requires either supplied IDs or an approved API change. |
| DOCUMENTATION ONLY | Original brief baseline is stale | It says implementation is through 0022/no 0023; actual code includes 0023. Future work must use current head `0014` / CHANGE-0023. |

No issue above is fixed by this documentation. Recommended order: approve CHANGE-0024 frontend scope; define operational/security baseline; approve source integration; only then approve scoped agent work. Unresolved product decisions are the exact frontend surface, job sources, AI/provider/tool design, external actions, notification delivery, and data lifecycle.
