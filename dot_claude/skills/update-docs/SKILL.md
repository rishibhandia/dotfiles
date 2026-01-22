---
name: update-docs
description: Sync documentation from source-of-truth. Updates READMEs, generates contribution guides, and identifies obsolete docs.
---

# Update Documentation

Sync documentation from source-of-truth.

## What This Command Does

1. **Read package.json scripts section**
   - Generate scripts reference table
   - Include descriptions from comments

2. **Read .env.example**
   - Extract all environment variables
   - Document purpose and format

3. **Generate docs/CONTRIB.md** with:
   - Development workflow
   - Available scripts
   - Environment setup
   - Testing procedures

4. **Generate docs/RUNBOOK.md** with:
   - Deployment procedures
   - Monitoring and alerts
   - Common issues and fixes
   - Rollback procedures

5. **Identify obsolete documentation**
   - Find docs not modified in 90+ days
   - List for manual review

6. **Show diff summary**

## Source of Truth

- `package.json` - Scripts and dependencies
- `.env.example` - Environment variables
- Actual codebase - File structure and APIs

## Documentation Files

- `README.md` - Project overview, quick start
- `docs/CONTRIB.md` - Contribution guide
- `docs/RUNBOOK.md` - Operations runbook
- `docs/CODEMAPS/` - Architecture documentation

## Quality Checklist

- [ ] All file paths verified to exist
- [ ] Code examples compile/run
- [ ] Links tested
- [ ] Freshness timestamps updated
- [ ] No obsolete references

## Related Agents

This command invokes the `doc-updater` agent located at:
`~/.claude/agents/doc-updater.md`
