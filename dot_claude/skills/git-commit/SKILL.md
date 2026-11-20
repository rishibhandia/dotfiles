---
name: git-commit
description: >-
  Analyze staged and unstaged git changes, enforce atomic commits, split mixed
  worktrees into logical single-concern commits, and write concise conventional
  commit messages. Use whenever preparing to commit, reviewing staged diffs,
  splitting a multi-concern diff, or drafting commit messages.
---

# Atomic Git Commits

Ensure every commit represents **one logical unit of change** with a clear,
conventional commit message. Never commit or push unless the user explicitly
asks to do so.

## Workflow

1. **Inspect the worktree and repo style first:**
   - `git status --short`
   - `git diff --staged` (and `git diff` if unstaged changes exist)
   - `git log --oneline -10` to match the repository's commit conventions
2. **Check for safety blockers before committing:**
   - No hardcoded secrets, tokens, keys, or credential files staged
   - No unintended build/cache debris (`.DS_Store`, `__pycache__`, temp files)
   - Never bypass hooks (`--no-verify`) or rewrite/force-push history without explicit authorization
3. **Evaluate atomicity (the "AND" test):**
   - If the subject line needs "and" to describe what changed, split it into separate commits.
   - **Must split:** multiple unrelated bug fixes; refactoring mixed with new behavior; formatting/style mixed with logic changes; changes across unrelated subsystems or domains.
   - **Valid atomic commit:** one bug fix, one feature, one behavior-preserving refactor, one dependency update, or tests for one feature.
   - **Co-generated / hook-coupled sets:** keep canonical sources, their generated outputs, and lock/ledger files together in the same commit when repository hooks or invariants require them to stay in sync.
4. **If non-atomic, propose and execute a split plan:**
   - Group files (or hunks via `git add -p`) by concern.
   - State the ordered commit plan clearly before staging.
   - Stage and commit each concern separately, verifying tests/hooks pass per commit.
5. **Write a conventional commit message:**

```text
<type>: <imperative summary under 72 chars, no trailing period>

<optional body explaining WHY, not WHAT>
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `style` (plus repository-local conventions such as `learn` when present in `git log`).

## Output Format (when reviewing before committing)

- **Atomic:** list staged files, state the single concern, and give the suggested commit message.
- **Non-atomic:** list the detected concerns, the ordered split plan, and the exact staging/commit commands.

## Pre-Commit Checklist

- [ ] Commit does exactly ONE logical thing (passes the "AND" test)
- [ ] Relevant checks/tests and pre-commit hooks pass
- [ ] Could be reverted cleanly without unrelated side effects
- [ ] Subject line is imperative, `< 72` characters, and matches repo style
- [ ] No secrets or stray runtime artifacts staged
