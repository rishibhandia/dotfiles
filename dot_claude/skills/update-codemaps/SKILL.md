---
name: update-codemaps
description: Analyze the codebase structure and update architecture documentation. Generates token-lean codemaps for key areas.
---

# Update Codemaps

Analyze the codebase structure and update architecture documentation.

## What This Command Does

1. Scan all source files for imports, exports, and dependencies

2. Generate token-lean codemaps:
   - `codemaps/architecture.md` - Overall architecture
   - `codemaps/backend.md` - Backend structure
   - `codemaps/frontend.md` - Frontend structure
   - `codemaps/data.md` - Data models and schemas

3. Calculate diff percentage from previous version

4. If changes > 30%, request user approval before updating

5. Add freshness timestamp to each codemap

6. Save reports to `.reports/codemap-diff.txt`

## Codemap Format

```markdown
# [Area] Codemap

**Last Updated:** YYYY-MM-DD
**Entry Points:** list of main files

## Architecture
[ASCII diagram of component relationships]

## Key Modules
| Module | Purpose | Exports | Dependencies |
|--------|---------|---------|--------------|

## Data Flow
[Description of how data flows through this area]

## External Dependencies
- package-name - Purpose
```

## Best Practices

- Focus on high-level structure, not implementation details
- Keep codemaps under 500 lines each
- Use consistent formatting
- Always include freshness timestamps
- Generate from actual code, don't manually write

## Related Agents

This command invokes the `doc-updater` agent located at:
`~/.claude/agents/doc-updater.md`
