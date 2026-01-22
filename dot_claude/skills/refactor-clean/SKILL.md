---
name: refactor-clean
description: Safely identify and remove dead code with test verification. Uses knip, depcheck, and ts-prune to find unused code.
---

# Refactor Clean

Safely identify and remove dead code with test verification.

## What This Command Does

1. Run dead code analysis tools:
   - **knip**: Find unused exports and files
   - **depcheck**: Find unused dependencies
   - **ts-prune**: Find unused TypeScript exports

2. Generate comprehensive report

3. Categorize findings by severity:
   - **SAFE**: Test files, unused utilities
   - **CAUTION**: API routes, components
   - **DANGER**: Config files, main entry points

4. Propose safe deletions only

5. Before each deletion:
   - Run full test suite
   - Verify tests pass
   - Apply change
   - Re-run tests
   - Rollback if tests fail

6. Show summary of cleaned items

## Analysis Commands

```bash
# Find unused exports/files/dependencies
npx knip

# Check unused dependencies
npx depcheck

# Find unused TypeScript exports
npx ts-prune
```

## Safety Rules

- Never delete code without running tests first
- Start with SAFE items only
- One batch at a time
- Commit after each successful batch
- When in doubt, don't remove

## Related Agents

This command invokes the `refactor-cleaner` agent located at:
`~/.claude/agents/refactor-cleaner.md`
