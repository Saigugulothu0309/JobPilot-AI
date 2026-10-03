# CHANGE-0028

## STATUS
COMPLETED

## DATE
2026-10-03

## SUMMARY
Added authenticated, owner-scoped listing for feedback-learning proposals.

## SCOPE
`GET /api/v1/feedback/proposals` returns the current user's feedback proposals in deterministic newest-first order. Bounded `limit` and `offset` parameters match the existing feedback and notification list conventions. Users without a profile receive the existing profile-not-found response.

## SECURITY
Proposal ownership is resolved from the authenticated user's profile. No client-supplied profile identifier is accepted. The endpoint is read-only and does not confirm or otherwise mutate proposals.

## VALIDATION
Added API coverage for authentication, pagination, and owner isolation. No database schema changes or migrations are required.