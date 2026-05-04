---
name: learn
description: Extract reusable patterns from the current session. Identifies debugging techniques, workarounds, and project-specific knowledge.
---

# Learn Command

Analyze the current session and extract any patterns worth saving as skills.

## When to Use

Run `/learn` at any point during a session when you've solved a non-trivial problem.

## Routing — Where Does This Pattern Belong?

Before writing anything, classify the new pattern by topic:

- **MATLAB / `+thz` package / THz / TA pump-probe / spectroscopy** →
  append to the relevant section of an **existing** topic file in the
  `matlab` skill at
  `~/.local/share/chezmoi/dot_claude/skills/matlab/`. The current
  topic files are:
  - `SKILL.md` — `+thz` package overview, calling conventions, the
    in-progress per-file loader pattern
  - `style-guide.md` — naming, formatting, function/class authoring
  - `performance.md` — vectorization, pre-allocation, JIT-friendly idioms
  - `plotting.md` — color, polar in tiledlayout, region highlighting,
    figure font and `exportgraphics` sizing
  - `fft.md` — `thz.fft.disc_ft` / `rfftFreq` table conventions and
    nfft sizing
  - `ta.md` — TA pump-probe workflow: sideband analysis, fluence
    scaling, frequency axis, SHG normalization, `varargin` integration
    helpers

  Only create a new topic file in `skills/matlab/` if the pattern
  genuinely doesn't fit any of the existing ones (and update
  `SKILL.md`'s navigation table when you do).

- **Anything else** (Python, Qt, Windows quirks, vendor SDKs,
  mock-object traps, etc.) → flat dump to
  `~/.local/share/chezmoi/dot_claude/skills/learned/<pattern-name>.md`,
  one pattern per file. Each topic earns promotion to its own real
  skill (`skills/<topic>/`) once it accumulates ~3+ related notes.

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

For an **existing topic file** (the MATLAB case), append a new section
to the file rather than rewriting it. Match the file's existing heading
depth and add a `**Updated:** [date]` line near the top if it's not
already there.

For a **new file in `learned/`** (the catch-all case), create at
`~/.local/share/chezmoi/dot_claude/skills/learned/[pattern-name].md`
with this template:

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

Skills are managed by chezmoi so they sync across machines. **Always
write to the chezmoi source, then `dots apply` to mirror into
`~/.claude/`.**

Chezmoi source paths (pick one based on the routing decision above):

- MATLAB pattern → existing topic file under
  `~/.local/share/chezmoi/dot_claude/skills/matlab/<topic>.md`
- Anything else → new file at
  `~/.local/share/chezmoi/dot_claude/skills/learned/[pattern-name].md`

After writing the chezmoi source:
```bash
dots apply   # sync chezmoi source → ~/.claude/
```

Then remind the user to commit:
```bash
dots git add -A && dots git commit -m "learn: [description]"
```

**Important:** The chezmoi source uses `dot_claude/` (not `.claude/`)
because chezmoi encodes dot-prefixed directories with the `dot_`
prefix.

## Notes

- Don't extract trivial fixes (typos, simple syntax errors)
- Don't extract one-time issues (specific API outages, etc.)
- Focus on patterns that will save time in future sessions
- Keep skills focused - one pattern per skill
