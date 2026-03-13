---
name: session-wrap
description: End-of-session workflow to extract learnings, create or update skills, and commit everything to the chezmoi-managed dotfiles repo. Use when the user says "wrap up", "end session", "save learnings", or asks to commit skills/patterns to their dotfiles. Also use proactively at natural session endings after significant work has been done.
---

# Session Wrap

Guided end-of-session workflow. Work through each step in order, pausing for user decisions where noted.

## Step 1: Extract Learnings (`/learn`)

Run `/learn` to review the session and identify reusable patterns.

- Patterns worth saving: debugging techniques, project conventions, tool quirks, workarounds
- Save to `~/.claude/skills/learned/<pattern-name>.md`
- Skip if the session had no non-trivial technical work

## Step 2: Create or Update Skills (`/skill-creator`)

After `/learn`, decide:

- **New skill warranted?** → Run `/skill-creator` to build it
- **Existing skill needs updating?** → Edit its `SKILL.md` directly with the Edit tool
- **No skill needed?** → Skip to Step 3

A skill is warranted when the pattern involves a multi-step workflow, tool integration, or domain knowledge that Claude won't reliably reconstruct from scratch.

## Step 3: Sync to Chezmoi

Track any new or modified files under `~/.claude/` with chezmoi, then commit.

```bash
# Add new/changed files (repeat for each)
chezmoi add ~/.claude/skills/<skill-name>/SKILL.md
chezmoi add ~/.claude/skills/<skill-name>/scripts/<file>
chezmoi add ~/.claude/skills/learned/<pattern-name>.md

# Verify what's staged
chezmoi git -- status

# Commit
chezmoi git -- commit -m "feat: <short description of what was added/updated>"
```

Commit message conventions:
- `feat:` new skill or learned pattern
- `fix:` correction to existing skill
- `chore:` housekeeping (deleting stale patterns, renaming)

## Step 4: Confirm

Report back to the user:
- What was learned/saved
- What skills were created or updated
- The commit hash and message

---

**Note on `dots` vs `chezmoi`:** The `dots` alias may not be available in all shell contexts. Use `chezmoi` directly if `dots` is not found.
