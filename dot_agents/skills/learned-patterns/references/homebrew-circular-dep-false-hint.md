---
name: brew's "stale keg tab data" circular-dependency hint is often wrong
description: Homebrew's circular-dependency warning suggests `brew uninstall --ignore-dependencies --force`, but the cycle is frequently real and intentional upstream (libtiff <-> webp). Verify with otool + INSTALL_RECEIPT before running a fix that breaks dozens of dependents.
type: feedback
---

When `brew bundle check` / `brew upgrade` prints:

```
Warning: Formulae dependency graph sorting found a circular dependency:
  libtiff, webp
This is usually caused by stale dependency data in installed keg tabs.
If it persists, run: brew uninstall --ignore-dependencies --force libtiff webp
```

**Do not run the suggested command before verifying the cycle is actually stale.** The word
"usually" is doing a lot of work — for `libtiff` ⇄ `webp` the cycle is real and intentional.

**Why:** the suggested fix is only correct if the installed receipts disagree with the current
formula definitions. Verify both sides:

```bash
# 1. What do the CURRENT formulae declare?
brew deps --formula libtiff; brew deps --formula webp

# 2. What do the INSTALLED receipts say?
python3 -c "import json;print([x['full_name'] for x in json.load(open('/opt/homebrew/opt/libtiff/INSTALL_RECEIPT.json'))['runtime_dependencies']])"

# 3. Is the linkage physically real?
otool -L /opt/homebrew/opt/libtiff/lib/libtiff.dylib | grep -i webp   # -> libwebp.7.dylib
otool -L /opt/homebrew/opt/webp/bin/cwebp | grep -i tiff              # -> libtiff
```

If (1) and (2) match, reinstalling pours identical bottles and writes identical receipts —
the warning returns and nothing improved. For libtiff/webp the cycle is genuine: libtiff
ships a WebP codec, and webp's `cwebp`/`dwebp`/`img2webp` tools do TIFF I/O.

Meanwhile `--ignore-dependencies --force` is exactly the flag pair that lets brew rip out
libraries **without** stopping you. On one machine those two had 19 installed dependents
(`qt`, `mpv`, `poppler`, `deno`, `yt-dlp`, `librsvg`, `gtk4`, `libheif`…), all with broken
linkage until the reinstall completed — and unrecoverable-ish if the reinstall failed partway.

The warning is **cosmetic**: it comes from Homebrew's topological sorter, which can't order a
true cycle. `brew doctor` reports no linkage problems and `brew bundle check` still returns
"dependencies are satisfied". Bottles sidestep the cycle entirely because nothing builds from
source.

**How to apply:**
- Treat a tool's own remediation advice as a hypothesis, not an instruction — especially when
  it is destructive and hedged ("usually", "if it persists").
- Check `brew uses --installed --recursive <formula>` to size the blast radius before any
  `--force` / `--ignore-dependencies` operation.
- Confirm the problem is real (`brew doctor`, an actual failing command) before "fixing" a warning.
