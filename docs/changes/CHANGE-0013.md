# CHANGE-0013

## CHANGE ID
CHANGE-0013

## STATUS
COMPLETED

## DATE
2026-09-04

## SUMMARY
Implemented the Candidate–Job Matching Foundation as a read-only, deterministic, explainable matching layer over approved candidate profile data and normalized shared jobs.

## WHY
The application now needs a trusted boundary between one candidate's approved profile and the shared job catalog. Matching must be deterministic, transparent, and safe: it must rely on approved profile fields only, must never write results back to the database, and must not use raw resume review data or AI-generated hypotheses as trusted ground truth.

## ARCHITECTURE
HTTP authenticated request -> `JobMatchingService.match_user_to_job()` -> deterministic scoring over approved profile + normalized job metadata -> structured `MatchResponse`.

The service reads only from the candidate's owned `Profile`, related `Skill`, `Experience`, `Education`, and normalized `Job` records. It does not create persistence, does not modify job records, and does not read unapproved resume-review output as trusted candidate data.

## FILES CHANGED
- backend/app/modules/job/matching.py
- backend/app/modules/job/api.py
- backend/app/modules/job/schemas.py
- backend/tests/test_job_match.py
- docs/changes/CHANGE-0013.md
- docs/changes/CHANGELOG.md

## DATA BOUNDARY
Matching uses only approved candidate data already owned by the authenticated user:

- `Profile.location`, `headline`, and `summary`
- `Skill.name` records attached to the profile
- `Education` records attached to the profile
- `Experience` records attached to the profile
- `Job` title, company, location, and description from the shared normalized catalog

The feature intentionally does not trust resume-review or parsed resume states, because those are not the approved candidate representation for matching decisions.

## MATCHING POLICY
The matching engine is deterministic and explainable:

- Skill normalization resolves aliases such as `React.js` and `PostgreSQL` into canonical names.
- Job skill recognition is limited to normalized skill knowledge and explicit text matching.
- Score components are:
  - skill overlap (55%)
  - title relevance (20%)
  - experience relevance (15%)
  - education relevance (5%)
  - location compatibility (5%)
- Scores are rounded and capped between 0 and 100.
- The response includes `matched_skills`, `missing_skills`, `positive_reasons`, and `potential_concerns` so the result remains explainable.

## API
Added read-only match endpoint:

- `POST /api/v1/jobs/{job_id}/match`

Behavior:
- Requires authenticated user access via bearer auth.
- Returns `404` when the job does not exist.
- Returns `404` when the authenticated user does not have approved candidate data.
- Returns a structured `MatchResponse` containing an overall score and explainable breakdown.

## SECURITY
- The operation is read-only; it does not create, update, or delete rows.
- Candidate matching is scoped to the authenticated user's own profile.
- The job catalog remains shared and read-only from this feature.
- No external AI or third-party service is invoked.
- No unapproved resume-review data is treated as source-of-truth candidate data.

## TESTS
Added regression coverage for:

- strong skill match and explanation payload
- partial and zero-skill matches
- skill normalization alias handling
- user isolation
- authenticated access enforcement
- missing candidate-data rejection
- missing job rejection
- deterministic repeatable output
- no database writes during match evaluation

## VALIDATION
- Focused backend job matching suite: 12 passed.
- Full backend pytest suite: run as final validation for this change.
- No Alembic migration was required because this feature is read-only and reuses existing schema.

## KNOWN ISSUES
- The score is intentionally deterministic and interpretable, not semantic or probabilistic.
- Matching does not include recommendation persistence, job application workflows, or AI ranking.
- The project continues to treat approved profile data as the only trusted candidate state.

## ROLLBACK
1. Remove the `POST /api/v1/jobs/{job_id}/match` route and response model.
2. Remove the matching service and deterministic scoring helpers.
3. Revert the matching regression tests and documentation updates.
4. No database rollback is required because no schema migration was introduced.

## NEXT ACTION
Stop after CHANGE-0013. No new work should begin beyond this matching foundation.
