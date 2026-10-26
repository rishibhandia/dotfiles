# LaTeX display-math pitfalls (and a pdflatex log trap)

**Extracted:** 2026-10-24
**Context:** Fixing or writing equations for a manuscript or SI (revtex / Wiley templates, amsmath), and compiling notes headlessly

## Problem
Equations that look right break the build or run off the page, and the error messages point elsewhere. Users also want pasted LaTeX that they can read and paste back.

## Solution
- `\\` inside `equation` does nothing useful (one line, runs off the page). Wrap the lines in `split` (alignment with `&`) or use `align`/`multline`.
- `\left( ... \right)` cannot span a `\\`. Close each line with an invisible delimiter and reopen on the next: `\left[ a + b \right. \\ & \left. + c \right]`.
- In `split`, the alignment `&` must come before `\left.` on the continuation line (`& \left. + c \right]`), not after it.
- `\right\ ` (backslash-space) is not a delimiter; the invisible one is `\right.`.
- A blank line inside `equation`/`split` is a hard error ("Missing $ inserted"/"Paragraph ended before ..."). Keep display math free of empty lines; a blank line before `\begin{equation}` also starts a new paragraph and adds space.
- Inside an equation the trailing punctuation belongs to the sentence: end with `.` when the next sentence starts with a capital, `,` when the sentence continues ("from Eq. 1 ...").
- Conjugate symmetry and signs: a term written for the negative-frequency half needs `A^{*}`, and symbols must match the prose (`\tilde E_p`, not `E_{\mathrm{opt}}`, if the prose defines `E_p`).
- When giving LaTeX to the user to paste, use ASCII only (no Unicode Greek, primes or dashes) so it renders in their editor; use `\propto` instead of carrying prefactors when they asked for proportionality; change only what they asked to change.
- Compiling headlessly: do NOT redirect console output to `<jobname>.out` (`pdflatex x.tex > x.out`). hyperref writes its bookmark file to `<jobname>.out`, so the redirect corrupts it and the next run reports errors that are not in the source. Redirect to `<jobname>.console` (or `/dev/null`) and read the `.log`.

## When to Use
Writing or fixing display equations, splitting long equations, compiling LaTeX notes in a script, or pasting equations for a user to drop into their manuscript.
