---
name: build-fix
description: Incrementally fix TypeScript and build errors with minimal changes. Focuses on getting the build green quickly without architectural changes.
---

# Build Fix

Incrementally fix TypeScript and build errors.

## What This Command Does

1. Run build: `npm run build` or `pnpm build`
2. Parse error output and group by file
3. For each error:
   - Show error context (5 lines before/after)
   - Explain the issue
   - Propose minimal fix
   - Apply fix
   - Re-run build
   - Verify error resolved
4. Stop if:
   - Fix introduces new errors
   - Same error persists after 3 attempts
   - User requests pause
5. Show summary of errors fixed

## Key Principles

- **Minimal diffs** - Make smallest possible changes
- **No architecture changes** - Only fix the error, don't refactor
- **One at a time** - Fix one error, verify, then move to next
- **Safety first** - Stop if fixes introduce new errors

## Common Error Types

- Type inference failures
- Null/undefined errors
- Missing properties
- Import errors
- Type mismatches
- Generic constraints

## Quick Commands

```bash
# TypeScript check
npx tsc --noEmit

# Build project
npm run build

# Clear cache and rebuild
rm -rf .next node_modules/.cache && npm run build
```

## Related Agents

This command invokes the `build-error-resolver` agent located at:
`~/.claude/agents/build-error-resolver.md`
