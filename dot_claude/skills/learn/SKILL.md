---
name: learn
description: Extract reusable patterns from the current session. Identifies debugging techniques, workarounds, and project-specific knowledge.
---

# Learn Command

Analyze the current session and extract any patterns worth saving as skills.

## When to Use

Run `/learn` at any point during a session when you've solved a non-trivial problem.

## What to Extract

Look for:

1. **Error Resolution Patterns**
   - What error occurred?
   - What was the root cause?
   - What fixed it?
   - Is this reusable for similar errors?

2. **Debugging Techniques**
   - Non-obvious debugging steps
   - Tool combinations that worked
   - Diagnostic patterns

3. **Workarounds**
   - Library quirks
   - API limitations
   - Version-specific fixes

4. **Project-Specific Patterns**
   - Codebase conventions discovered
   - Architecture decisions made
   - Integration patterns

## Output Format

Create a skill file at `~/.claude/skills/learned/[pattern-name].md`:

```markdown
# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [Brief description of when this applies]

## Problem
[What problem this solves - be specific]

## Solution
[The pattern/technique/workaround]

## Example
[Code example if applicable]

## When to Use
[Trigger conditions - what should activate this skill]
```

## Process

1. Review the session for extractable patterns
2. Identify the most valuable/reusable insight
3. Draft the skill file
4. Ask user to confirm before saving
5. Write to **both** locations (see Saving below)

## Saving — Chezmoi-Managed Dotfiles

Skills are managed by chezmoi so they sync across machines. **Always write to both locations:**

1. **Chezmoi source** (canonical, synced to other machines):
   `~/.local/share/chezmoi/dot_claude/skills/learned/[pattern-name].md`

2. **Live location** (used by Claude Code immediately):
   Applied automatically via `dots apply` after writing to chezmoi source.

After writing to the chezmoi source, run:
```bash
dots apply   # sync chezmoi source → ~/.claude/
```

Then remind the user to commit:
```bash
dots git add -A && dots git commit -m "learn: [description]"
```

**Important:** The chezmoi source uses `dot_claude/` (not `.claude/`) because chezmoi encodes dot-prefixed directories with the `dot_` prefix.

## Notes

- Don't extract trivial fixes (typos, simple syntax errors)
- Don't extract one-time issues (specific API outages, etc.)
- Focus on patterns that will save time in future sessions
- Keep skills focused - one pattern per skill
