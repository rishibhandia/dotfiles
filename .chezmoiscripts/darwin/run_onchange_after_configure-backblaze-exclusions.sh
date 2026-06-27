#!/bin/bash
# =============================================================================
# Backblaze Personal Backup — custom exclusion rules (macOS)
# =============================================================================
# WHY THIS EXISTS
#
# Backblaze kept queuing ~3 GB of "new" files every day even with no real new
# data. The transmit logs (bzlogs/bzreports_lastfilestransmitted/<day>.log)
# showed the cause: a handful of large, monolithic databases / caches that get
# rewritten many times a day. Each rewrite changes the whole file (SQLite
# reshuffles internal pages, so block-level dedup barely helps), so Backblaze
# re-uploads the ENTIRE file every pass — several of them 2-4x per day.
#
# This script appends exclusion rules for the ones that are pure rebuildable
# cache or redundant copies (none are irreplaceable data) to Backblaze's
# user-editable rules file, and drops a README next to it explaining the same.
# It is idempotent and safe to run on every `chezmoi apply`; it no-ops if
# Backblaze is not installed.
#
# WHAT IS EXCLUDED (all regenerate locally):
#   - Apple Photos analysis & search caches (mediaanalysisd/photoanalysisd/search)
#   - zotero.sqlite.bak  (Zotero's redundant copy; the live DB is still backed up)
#   - ~/.cache/uv        (uv package cache, reproducible from lockfiles)
#   - CrossOver Bottles  (Windows game prefixes; reinstallable)
#   - Discord caches     (Cache / Code Cache / GPUCache; re-downloaded)
#   - GOG Galaxy WebCache (re-downloaded)
#
# DELIBERATELY KEPT (real data, churn accepted): live Photos DB, Messages
# chat.db, Safari History.db, live Zotero DB, Fantastical, Keynote.
#
# After this runs, Backblaze re-reads exclusions on its next file scan. To apply
# immediately:  sudo launchctl kickstart -k system/com.backblaze.bzserv  (or reboot)
# =============================================================================

set -uo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
success() { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
warn()    { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
err()     { printf "${RED}[ERR]${NC} %s\n" "$1"; }

BZDATA="/Library/Backblaze.bzpkg/bzdata"
EXCL="$BZDATA/bzexcluderules_editable.xml"
README="$BZDATA/README.md"

if [ ! -f "$EXCL" ]; then
  info "Backblaze not installed (no $EXCL); skipping exclusion setup."
  exit 0
fi

# --- the managed exclusion block ----------------------------------------------
BLOCK_TMP="$(mktemp)"
cat > "$BLOCK_TMP" <<'BLOCK'
<!-- BEGIN chezmoi backblaze-exclusions -->
<!-- Managed by chezmoi: .chezmoiscripts/darwin/run_onchange_after_configure-backblaze-exclusions.sh -->
<!-- Rebuildable caches / redundant DB copies that otherwise re-upload daily.    -->
<!-- See README.md in this directory for the full rationale.                      -->

<!-- Apple Photos analysis & search caches (continuously rebuilt by macOS) -->
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/pictures/photos library.photoslibrary/private/com.apple.mediaanalysisd/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/pictures/photos library.photoslibrary/private/com.apple.photoanalysisd/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/pictures/photos library.photoslibrary/database/search/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />

<!-- Zotero's redundant backup rotations (.bak, .1.bak, ...); live zotero.sqlite (+ -wal/-shm/-journal) still backed up -->
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/zotero/zotero.sqlite." contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />

<!-- uv Python package cache (fully reproducible from lockfiles) -->
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/.cache/uv/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />

<!-- CrossOver Windows game bottles (executable software, large daily churn) -->
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/library/application support/crossover/bottles/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />

<!-- Discord caches (re-downloaded automatically) -->
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/library/application support/discord/cache/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/library/application support/discord/code cache/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/library/application support/discord/gpucache/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />

<!-- GOG Galaxy web cache -->
<excludefname_rule bzmergeblock="003" plat="mac" osVers="*"  ruleIsOptional="t" skipFirstCharThenStartsWith="users/" contains_1="/gog.com/galaxy/webcache/" contains_2="*" doesNotContain="*" endsWith="*" hasFileExtension="*" />
<!-- END chezmoi backblaze-exclusions -->
BLOCK

# --- backup the pristine file once --------------------------------------------
if [ ! -f "$EXCL.prechezmoi.bak" ]; then
  cp -p "$EXCL" "$EXCL.prechezmoi.bak" && info "Backed up original to $EXCL.prechezmoi.bak"
fi

# --- rewrite: drop any prior managed block, reinsert fresh before closing tag --
NEW_TMP="$(mktemp)"
awk -v blockfile="$BLOCK_TMP" '
  /<!-- BEGIN chezmoi backblaze-exclusions -->/ { inblk=1 }
  inblk {
    if ($0 ~ /<!-- END chezmoi backblaze-exclusions -->/) inblk=0
    next
  }
  /<\/bzexclusions>/ && !done {
    while ((getline line < blockfile) > 0) print line
    close(blockfile)
    done=1
  }
  { print }
' "$EXCL" > "$NEW_TMP"

# --- validate, then install in place (preserves perms/owner) ------------------
if command -v xmllint >/dev/null 2>&1; then
  if ! xmllint --noout "$NEW_TMP" 2>/dev/null; then
    err "Generated exclusion file is not valid XML; leaving original untouched."
    rm -f "$NEW_TMP" "$BLOCK_TMP"
    exit 1
  fi
fi

if cmp -s "$NEW_TMP" "$EXCL"; then
  success "Backblaze exclusions already up to date."
else
  cat "$NEW_TMP" > "$EXCL"
  success "Applied Backblaze custom exclusions to $EXCL"
  warn  "To apply now: sudo launchctl kickstart -k system/com.backblaze.bzserv  (or reboot)"
fi
rm -f "$NEW_TMP" "$BLOCK_TMP"

# --- in-place README (regenerated every run) ----------------------------------
cat > "$README" <<'DOC'
# Backblaze custom exclusions — rationale

> Managed by chezmoi:
> `.chezmoiscripts/darwin/run_onchange_after_configure-backblaze-exclusions.sh`
> Edit the rules there (not this file) — this README and the rules in
> `bzexcluderules_editable.xml` are regenerated on every `chezmoi apply`.

## Why these exist

Backblaze kept queuing **~3 GB of "new" files every day** with no real new data.
The transmit logs (`bzlogs/bzreports_lastfilestransmitted/<day>.log`) showed the
cause: a small set of **large, monolithic databases / caches rewritten many times
a day**. Each rewrite changes the whole file (SQLite reshuffles internal pages, so
block-level dedup barely helps), so Backblaze re-uploads the entire file every
pass — several of them 2–4× per day.

## What is excluded (all regenerate locally)

- **Photos analysis & search caches** (`com.apple.mediaanalysisd`,
  `com.apple.photoanalysisd`, `database/search`) — macOS rebuilds them.
- **`zotero.sqlite.*.bak`** — Zotero's redundant backup rotations; live
  `zotero.sqlite` (+ `-wal`/`-shm`) is still backed up.
- **`~/.cache/uv`** — reproducible from lockfiles.
- **CrossOver `Bottles`** — Windows game prefixes (executable software).
- **Discord `Cache`/`Code Cache`/`GPUCache`** — re-downloaded automatically.
- **GOG Galaxy `WebCache`** — re-downloaded automatically.

Deliberately **kept** (real data): live Photos DB, Messages `chat.db`, Safari
`History.db`, live Zotero DB, Fantastical, Keynote.

## Apply / revert

- **Apply now:** `sudo launchctl kickstart -k system/com.backblaze.bzserv` (or reboot).
  Otherwise Backblaze picks up changes on its next scan.
- **Stop excluding something:** remove that rule line from the script's block and
  re-run `chezmoi apply`.
- **Full revert:** restore `bzexcluderules_editable.xml.prechezmoi.bak` (this dir).

## Caveat

Excluding a path stops *future* uploads; copies already in the backup age out per
your retention setting (default 30 days) — not a retroactive delete.
DOC
success "Wrote $README"
