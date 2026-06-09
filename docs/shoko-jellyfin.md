# Shoko Server + Shokofin + Jellyfin — Mac mini anime stack

The Mac mini (`rishi-macmini-2020`) runs **Shoko Server** (Docker, via Colima) as the
metadata/organization backend for the anime library, surfaced in Jellyfin through the
**Shokofin** plugin. Shoko identifies every file by hash against AniDB, giving correct
franchise grouping, seasons, OVAs, movies, and AniDB episode numbering — replacing the
old per-provider plugins (AniDB / AniList / AniSearch / Kitsu).

```
AniDB ──hash match──> Shoko Server (Docker/Colima, :8111)
                           │  groups series into franchises
                           ▼
                       Shokofin plugin (inside Jellyfin)
                           │  builds a symlink VFS, one folder per Shoko group
                           ▼
                       Jellyfin "Anime (Shoko)" library (:8096)
```

## Architecture decisions

- **Docker, not native:** Shoko doesn't officially support native Apple Silicon
  (missing-library risk) and has no brew formula; the official image runs fine on Colima.
- **Identical-path mount:** Jellyfin runs natively on the host and Shokofin builds a
  symlink VFS pointing at the paths Shoko reports. The media is bind-mounted into the
  container at its *real host path* (`/Volumes/Easystore/Movies & Shows`, **read-only**),
  and `/Volumes/Easystore` is mounted into the Colima VM by `run_after_05`.
  Shokofin's host-side symlinks then resolve with zero path remapping.
- **Persistence:** Shoko's config/DB lives in the `shoko-config` Docker named volume
  (mounting `/home/shoko/.shoko` wrong is a known data-loss footgun).
- **Read-only media:** because the drive is mounted read-only, the Jellyfin library must
  have **Save artwork/NFO into media folders = OFF** (`SaveLocalMetadata: false`),
  otherwise scans error trying to write to the mount.
- **Networking:** Shoko API/UI bound to `127.0.0.1:8111` (localhost-only). Reach it on the
  mini directly, over the tailnet (`https://mini.<tailnet>.ts.net:8111`), or
  `ssh -L 8111:127.0.0.1:8111 <mini>` from elsewhere.

## What's automated by chezmoi

| Script | Does |
|--------|------|
| `run_after_05-start-colima.sh.tmpl` | Colima VM with the Easystore mount + 4 CPU / 6 GiB + auto-start LaunchAgent |
| `run_after_07-install-shoko.sh.tmpl` | Shoko container install + start (`docker compose up -d`) |
| `run_after_08-jellyfin-keepalive.sh.tmpl` | Jellyfin keep-alive watchdog LaunchAgent |

Everything below (Shoko first-run wizard, Shokofin install/config, the Jellyfin library) is
**stateful UI/DB config that is deliberately NOT chezmoi-managed** — it lives in Jellyfin's
database and Shoko's volume. This file is the runbook for reproducing it by hand.

---

## End-to-end setup

### 1. Shoko Server (backend)

First-run wizard at `http://127.0.0.1:8111`:

1. Create the Shoko admin account (its own login, separate from Jellyfin).
2. Link AniDB (AniDB username + password). **AniDB sends credentials in cleartext and is
   heavily rate-limited** — initial hash-matching of a large library takes hours and can
   span a day. That's throttling, not a hang.
3. Add an **import folder** = `/Volumes/Easystore/Movies & Shows`.
4. Set the **AVDump / UDP API key** (Settings → AniDB) so unknown files can be hashed and
   reported. Run AVDump **one job at a time** — concurrent runs throw
   `AVDumpFilesJob already exists`.
5. **Enable franchise grouping at the Shoko level:** Settings → enable
   `AutoGroupSeries` (groups related series into one franchise group), then run
   **Actions → Recreate All Groups**. Without this, every series is its own group and
   Shokofin has nothing to collapse.
6. Exclude macOS AppleDouble sidecars: Settings → Import → add an `Exclude` regex
   `[\\/]\._` so the thousands of `._*` files on an exFAT/HFS drive don't eat AniDB
   lookups. (Better still, delete them:
   `find "/Volumes/Easystore/Movies & Shows" \( -name '._*' -o -name '.DS_Store' \) -type f -delete`.)

### 2. Install the Shokofin plugin in Jellyfin

Dashboard → Plugins → Repositories → add:

- **Name:** `Shokofin Stable`
- **URL:** `https://raw.githubusercontent.com/ShokoAnime/Shokofin/metadata/stable/manifest.json`

Then Catalog → install **Shoko** → **restart Jellyfin**.

> **macOS restart caveat:** do *not* use Dashboard → Restart. On macOS that stops the
> server without relaunching it. Quit & reopen the Jellyfin app, or let the keep-alive
> watchdog (`run_after_08`) bring it back within ~15 s.

### 3. Configure the Shokofin plugin (Dashboard → Plugins → Shoko)

GUI settings → equivalent config key (in `~/.local/share/jellyfin/plugins/configurations/Shokofin.xml`,
or via the API; see below):

| GUI setting | Value | Config key |
|-------------|-------|-----------|
| Connection → Host | `http://127.0.0.1:8111` | `Url` |
| Connection → user / password | your Shoko login | `Username` / `ApiKey` |
| **Default Library Structure Mode** | **Shoko Group Structure** | `DefaultLibraryStructure = Shoko_Groups` |
| Library Operation Mode | Virtual File System (VFS) | `DefaultLibraryOperationMode = VFS` |
| Season ordering | Default | `DefaultSeasonOrdering = Default` |

**`DefaultLibraryStructure = Shoko_Groups` is THE franchise-grouping switch.** Its values:

- `AniDB_Anime` (default) — each AniDB anime = its own Jellyfin show. No franchise grouping.
- **`Shoko_Groups`** — each Shoko group = one Jellyfin show, each member series = a season.
  This is what gives `Bakemonogatari` → 16 seasons, `Gundam` → 14 seasons, etc.
- `TMDB_SeriesAndMovies` — group by TheMovieDb structure.

Set this **before** creating the library — changing it afterward requires removing and
recreating the library (Jellyfin caches the structure).

### 4. Create the "Anime (Shoko)" Jellyfin library

Dashboard → Libraries → Add Media Library:

- **Content type:** `Shows` (movies still appear inside their franchise unless you turn on
  `SeparateMovies`).
- **Folder:** `/Volumes/Easystore/Movies & Shows` — the **real path**, the same contents
  Shoko sees as its import folder. With VFS on, Shokofin auto-attaches its VFS path and
  filters out everything unrecognized; you do *not* point at the VFS directory yourself.
- **Metadata downloaders:** enable **only Shoko**; disable TheMovieDb / OMDb / etc. for
  every type (Series / Season / Episode). Mixed providers = mixed metadata.
- **Image fetchers:** **Shoko** top-most (here: Shoko only).
- **Disable:** "Save artwork/NFO into media folders" (read-only mount), embedded titles,
  and embedded episode infos.

### 5. The three gotchas that will bite you

1. **Restart Jellyfin after creating the library.** Shokofin enumerates Jellyfin
   libraries at **plugin init**. A library created while Jellyfin is already running is
   invisible to Shokofin — a scan does nothing, the VFS stays empty, and
   `Plugins/<id>/Configuration` shows `Libraries: []`. After a restart the log shows
   `MediaFolderConfigurationService: Found a match for media folder ...` and
   `Libraries: 1`. **This is the step that's easy to miss.**
2. **Two libraries can't share the same media path.** The old TMDb-based "Anime" library
   pointed at the same `/Volumes/Easystore/Movies & Shows`. Jellyfin canonicalizes paths,
   so the old library "owned" it and the new one never got resolved. **Disable** (don't
   delete — reversible, keeps cached posters) the old library before scanning the new one.
3. **macOS Jellyfin restart** doesn't relaunch the app — see the caveat in step 2 of the
   setup. The keep-alive watchdog handles it.

### 6. Scan & verify

Trigger Dashboard → Scheduled Tasks → **Scan Media Library** (or the API call below).
Shokofin generates the VFS (symlink tree, ~7.8k entries for ~390 series) in the first
minute or two; Jellyfin then attaches metadata (the slow part — ~15 min for a large
library).

**Verify franchise grouping directly from the VFS** (ground truth, available as soon as
the symlinks are laid down, before metadata finishes):

```bash
LIBVFS=$(find ~/.local/share/jellyfin/Shokofin/VFS -maxdepth 1 -mindepth 1 -type d | head -1)
for show in "$LIBVFS"/*/; do
  printf '%s|%s\n' "$(find "$show" -mindepth 1 -maxdepth 1 -type d | wc -l)" "$(basename "$show")"
done | sort -rn -t'|' -k1 | head
# Bakemonogatari → 16 season folders, Kidou Senshi Gundam → 14, Evangelion → 8, ...
```

Or in Jellyfin once metadata catches up: a Monogatari/Gundam show should report many
seasons (`Items?ParentId=<libId>&Recursive=true&IncludeItemTypes=Series&Fields=ChildCount`).

---

## SignalR (live updates) — optional

SignalR is Shokofin's real-time WebSocket link to Shoko Server. When connected, Shoko
pushes live events (file recognized, series linked, metadata/images updated, watch-state
changed) and Jellyfin reflects them **immediately, without a full rescan**.

- Config keys: `SignalR_AutoConnectEnabled`, `SignalR_RefreshEnabled`, `SignalR_FileEvents`.
- Default is off (`SignalR_AutoConnectEnabled = false`) → status shows **Disconnected**.
- Turn it on **after** the initial library build is stable, for convenient incremental
  updates. Not required for the bulk setup.

## Driving it all via the Jellyfin REST API

Everything above can be done with `curl` against the Jellyfin API instead of the GUI (the
GUI just sends these same calls). Use an API key from Dashboard → API Keys
(`X-Emby-Token` header). Plugin GUID for Shoko is `5216ccbfd24a4eb38a7e7da4230b7052`.

```bash
KEY=<jellyfin-api-key>; H="X-Emby-Token: $KEY"; BASE=http://127.0.0.1:8096
PID=5216ccbfd24a4eb38a7e7da4230b7052

# Set franchise grouping (full GET->modify one field->POST round-trip is safe)
curl -fsS -H "$H" "$BASE/Plugins/$PID/Configuration" \
  | jq '.DefaultLibraryStructure="Shoko_Groups"' > /tmp/cfg.json
curl -fsS -X POST -H "$H" -H 'Content-Type: application/json' \
  --data @/tmp/cfg.json "$BASE/Plugins/$PID/Configuration"

# Create the library (Shoko-only providers; see the LibraryOptions body in this repo's history)
curl -fsS -X POST -H "$H" -H 'Content-Type: application/json' --data @libopts.json \
  "$BASE/Library/VirtualFolders?name=Anime%20(Shoko)&collectionType=tvshows&paths=%2FVolumes%2FEasystore%2FMovies%20%26%20Shows&refreshLibrary=false"

# >>> RESTART JELLYFIN HERE so Shokofin registers the library <<<
curl -fsS -X POST -H "$H" "$BASE/System/Restart"   # watchdog relaunches it

# Scan (builds the VFS)
curl -fsS -X POST -H "$H" "$BASE/ScheduledTasks/Running/7738148ffcd07979c7ceb148e06b3aed"
```

The config JSON property names differ from the XML element names (e.g. XML `SeasonOrdering`
↔ JSON `DefaultSeasonOrdering`, XML `UseGroupsForShows` is superseded by JSON
`DefaultLibraryStructure`). Always round-trip the *full* config object you GET, changing
only the field you mean to — don't hand-build a partial body.

## Updating Shoko

```bash
docker compose -f ~/.config/shoko/docker-compose.yml pull
docker compose -f ~/.config/shoko/docker-compose.yml up -d   # restart: unless-stopped keeps it running
docker logs shoko                                            # troubleshooting
```

## Security notes

- **Rotate the AniDB password** — it was logged in cleartext during setup. Update it in
  Shoko → Settings → AniDB afterward.
- **Revoke the Shoko API key** used for one-off scripting when done (Shoko → Settings → API Keys).
- The media drive is mounted **read-only** into the container, so nothing in the stack can
  modify the library files.

## Current state (last verified 2026-06-08)

- ✅ Shoko import ~done: ~6,617 files hashed, ~389 series matched, 290 groups / 56 franchises.
- ✅ Shokofin configured (`Shoko_Groups`, VFS); "Anime (Shoko)" library created, Shoko-only providers.
- ✅ Franchise grouping verified: Bakemonogatari→16, Gundam→14, Evangelion→8, GitS→6, Code Geass→5.
- ✅ Old TMDb "Anime" library **disabled** (not deleted — re-enable to restore its posters).
- ⏳ Metadata/image attach finishing on first scan (slow tail, self-completes).
- ☐ AniList watch-history import: upload `~/Downloads/anilist-brillouinz-mal.xml` at
  AniDB → MyList → Import (MyAnimeList.net XML), then Shoko reads watched states → Jellyfin.
- ☐ ~379 unrecognized stragglers: AVDump-first then manual-link (optional, one at a time).
- ☐ Retire the disabled old "Anime" library once happy; delete `~/.local/share/jellyfin/.plugins-removed-2026-06-06/`.
