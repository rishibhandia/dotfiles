---
name: verify
description: Run repository-native build, type, lint, test, and status checks and report exact evidence. Use when asked to verify, validate, check readiness, or before reporting a code change complete.
---

# Verify a repository change

Read the nearest `AGENTS.md` and the repository's task configuration to discover
the real verification commands. Do not assume a JavaScript toolchain or invent
commands that the repository does not define.

Run the narrowest relevant checks first, then broader checks in this order when
they exist:

1. Build or compile
2. Type checking
3. Lint and formatting checks
4. Focused tests for changed behavior
5. Broader test suite and coverage threshold
6. Repository-specific security or artifact validation
7. `git status --short` and a final diff review

Stop dependent checks after a prerequisite failure, but continue independent
read-only diagnostics when they can clarify the failure.

Report:

```text
VERIFICATION: PASS | FAIL | PARTIAL
Build:     command — result
Types:     command — result
Lint:      command — result
Tests:     command — result
Artifacts: command — result
Git:       concise status
Remaining risk: none | explanation
```

Never claim a check passed when it was skipped or unavailable.
