# JobPilot AI Development Rules

1. Inspect the repository and relevant documentation before modifying anything.
2. Document every meaningful change in `docs/changes/`; keep changes small, reversible, and scoped to the approved work.
3. Do not modify unrelated files, invent requirements, or silently change the approved architecture.
4. Never hardcode, commit, log, or expose secrets and credentials.
5. Validate all AI output with structured schemas; AI/agents must not access the database directly and may use only approved tools.
6. Consequential actions require the appropriate explicit approval.
7. Make database changes only through reviewed migrations.
8. Document API changes.
9. Run relevant tests before claiming completion; never fabricate results.
10. Explicitly report breaking changes, risks, and unknown requirements. Seek clarification rather than guessing when a requirement is unknown.
