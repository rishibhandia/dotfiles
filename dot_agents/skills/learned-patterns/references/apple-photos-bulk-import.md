# Apple Photos Bulk Import via AppleScript — Jam Avoidance & Gotchas

**Extracted:** 2026-07-02
**Context:** Importing thousands of files into Apple Photos (macOS) via
`osascript`/AppleScript — bulk library migrations, recovered-photo imports,
any headless/scripted feed into Photos.app.

## Problem
Feeding Photos thousands of files, it starts throwing "Cannot import — file
is an unrecognizable format or does not contain any valid data," or silently
imports **0** (even for perfectly valid files, and even a blank PNG). Restarting
Photos fixes it temporarily, then it re-jams. Easy to misdiagnose as corrupt
files / bad format / ExFAT / chroma subsampling — all red herrings.

## Root Cause
`mediaanalysisd` (face/scene analysis) saturates CPU (150–280%) as the library
grows and **starves Photos' importer**, which then rejects everything until
Photos is relaunched. The files are fine.

## Solution
**Suspend the analysis daemon for the duration of the import**, then resume:
```bash
killall -STOP mediaanalysisd mediaanalysisd-access   # freeze (state 'T')
# ... feed import batches at full speed, no jams (~350–400 files/min) ...
killall -CONT mediaanalysisd mediaanalysisd-access   # resume (analysis catches up later)
```
- Re-assert `-STOP` each batch (macOS may respawn it).
- Trap to always resume: `trap 'killall -CONT mediaanalysisd mediaanalysisd-access' EXIT INT TERM`.
- **Jam detector** (when you can't suspend, or as a safety net): import a known-good
  control image; if `count of media items` doesn't rise, Photos is jammed →
  quit + `open -a Photos` to clear it. Restart proactively every ~10–24 batches.
- Verify each batch by media-item count delta, not by the import call returning.

## Other Photos/AppleScript gotchas from the same job
- **AppleDouble `._*` files**: ExFAT/ non-HFS drives create a `._name` sidecar
  per file (~4 KB). A naive `find` **doubles every count**. Always
  `find … ! -name '._*'`.
- **Photos can't delete via AppleScript** (`delete` errors -1700). Workaround:
  `make new album`, `add` the items, tell the user to empty it manually.
- **System Events has no assistive access** in this context (errors -1728 /
  -25211) → cannot read or click Photos' modal dialogs programmatically. A
  blocking dialog needs a human (Screen Sharing) click.
- **Video imports (AVI/MOV) make Photos briefly unresponsive** to
  `count of media items` (query times out) *even when the import succeeds*.
  Don't over-react — restart Photos, then re-check the count; it usually landed.
- **Disk space is deferred**: with analysis suspended, each file costs ~its own
  size. Once resumed, `mediaanalysisd` writes previews/derivatives and free
  space drops substantially later. Budget for it; macOS also reclaims purgeable
  space when the disk gets tight.
- **AVI needs transcoding** (Photos is finicky): `ffmpeg -c:v libx264 -crf 23
  -c:a aac -movflags +faststart out.mp4` (~36% of source size). MOV imports as-is.

## Deduping renamed / recovered files
Recovery tools rename files (flat `00000.JPG`, `Clip #1_2.mov`), so you can't
diff by name. Fingerprint by **`filesize : md5(first 64 KB)`** — fast (doesn't
read whole files over USB), ~zero false matches for real photos/videos.
**Suffix gotcha**: recovery emits `_2`/`_3`/`_4` copies. When stripping the
copy-suffix to find a base name, only strip a trailing `_<1-2 digits>` —
otherwise `MVI_0001.AVI` mangles to `MVI` (its real number looks like a suffix)
and you get false "unique/orphan" results.

## When to Use
Any scripted/bulk import into Apple Photos; diagnosing Photos "unrecognizable
data"/silent-0 import failures; deduping a recovered photo/video dump; scripting
around Photos.app's AppleScript limitations.
