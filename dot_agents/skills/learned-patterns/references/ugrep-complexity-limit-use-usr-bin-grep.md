# `grep` here is ugrep: bounded repeats on UTF-8 text fail, use /usr/bin/grep

**Extracted:** 2026-10-24
**Context:** Bash tool on this Mac; `grep` resolves to ugrep through the `rtk` wrapper, not BSD grep

## Problem
Context searches such as

```bash
grep -n -o -E ".{0,90}Fig 4\(g\).{0,90}" README.md
```

fail with `ugrep: error: error at position 86 ... exceeds complexity limits`. ugrep expands `.` into a multi-byte UTF-8 automaton, so a bounded repeat like `.{0,90}` blows past its state limit, especially with two of them or with files containing Greek letters, arrows or en dashes. In some invocations the wrapper instead prints `rtk grep` usage text and no matches, which looks like "nothing found".

## Solution
- Call the system binary explicitly for regex-heavy context searches: `/usr/bin/grep -n -o -E ".{0,90}pattern.{0,60}" file`.
- Or keep the context short (`.{0,40}`), or drop `-o` and print whole lines with `cut -c1-200`.
- For anything that needs real context windows across Unicode text, a few lines of Python (`re.finditer` and slicing the line) are clearer and never hit a complexity limit.
- Simple fixed-string or short-pattern greps work fine through the wrapper; only the bounded-repeat context pattern needs the workaround.

## When to Use
A grep with `.{0,N}` context, or any long `-E` pattern, returns "exceeds complexity limits", or returns rtk usage text instead of matches.
