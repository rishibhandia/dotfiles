# zsh does not word-split unquoted variables

**Extracted:** 2026-10-24
**Context:** Bash tool commands that actually run in zsh (the user's login shell on macOS)

## Problem
A bash-style loop over "pairs" silently does the wrong thing:

```bash
for p in "FigS1 FigS3_UnfilteredProbe" "FigS2 FigS6_PeakWidths"; do
    set -- $p                       # bash: $1=FigS1 $2=FigS3_...   zsh: $1="FigS1 FigS3_..." $2=""
    md5 -q "final/$1.pdf" ...
done
```

In zsh an unquoted `$p` is NOT split on spaces (no SH_WORD_SPLIT), so `$1` is the whole string, `$2` is empty, and every command reports "No such file". The same bites `for spec in "836 1.2"; ... $spec` style parameter lists.

## Solution
- Pass the pieces as separate arguments to a function instead of packing them into one string:

  ```bash
  check() { [ "$(md5 -q "final/$1.pdf")" = "$(md5 -q "src/$2.pdf")" ] && echo "$1 = $2" || echo "$1 MISMATCH"; }
  check FigS1 FigS3_UnfilteredProbe
  check FigS2 FigS6_PeakWidths
  ```

- Or split explicitly with zsh syntax `${=p}` (zsh only), or write one explicit command per case.
- Parallel arrays and explicit lists are easier to read in a tool call than packed strings anyway.

## When to Use
A shell loop that relies on unquoted variables splitting into words, or a "No such file" error whose path contains a space-joined pair of names.
