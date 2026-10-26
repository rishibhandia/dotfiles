# Tirith blocks multi-file rm: hand the user one `!` command

**Extracted:** 2026-10-24
**Context:** Claude Code with the tirith PreToolUse hook on Bash, cleaning up files Claude itself generated (stale trial builds, renamed outputs) in a project

## Problem
`rm a b c` (three or more files, or several rm calls in quick succession) is refused whole: "Tirith: [CRITICAL] Mass file deletion in a short window". It happens even when every file is an untracked output Claude made minutes earlier. Retrying, or splitting the deletion into one rm per call, is exactly the evasion the hook exists to stop.

## Solution
Do not retry and do not split. Finish the rest of the work, then give the user one command to run with the `!` prefix, listing every file explicitly with paths relative to the project root:

```
! rm AdvMat_Figures/final/FigS5.pdf AdvMat_Figures/final/FigS6.pdf AdvMat_Figures/final/FigS7.pdf
```

- Before listing, check what each output family actually wrote: MATLAB builders here write `.pdf`, `.svg`, `.png` AND `.fig`. Listing only pdf/svg/png left a 35 MB `.fig` behind and needed a second command. `ls <dir> | grep <tag>` first.
- Say plainly which files are stale until the user runs it (e.g. leftovers in an upload folder are not part of the set), and confirm afterwards with `ls`.
- Prefer designs that do not need deletion at all: name trial outputs with a suffix so they never replace deliverables, and when renaming deliverables, have the collector write the new names and list the old ones for the user to remove.
- This differs from dotfile writes (see `tirith-dotfile-write-routing.md`), where the right move is to route the write through the Write/Edit tool, not to hand the user a shell command.

## When to Use
A Bash `rm` of several files fails with a tirith "Mass file deletion" message, or a cleanup step is about to delete three or more files.
