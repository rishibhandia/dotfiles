# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **chezmoi** dotfiles repository for cross-platform configuration management (macOS, Linux, Windows). Chezmoi manages dotfiles by storing source files in this repository and applying them to the home directory.

## Bootstrap a New Machine

**macOS / Linux:**
```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.sh)"
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex
```

The install script will:
1. Install Xcode CLI tools (macOS) or build dependencies (Linux)
2. Install Homebrew
3. Install chezmoi
4. Apply dotfiles
5. Set zsh as default shell

## Common Commands

Use the `dots` command (defined in `scripts.zsh` / `dots.ps1`):

```bash
dots apply      # Apply dotfiles to home directory
dots apply -v   # Apply with verbose output
dots diff       # Preview changes before applying
dots status     # Show status of managed files
dots update     # Pull latest changes and apply
dots edit FILE  # Edit a dotfile source
dots add FILE   # Add a new file to chezmoi
dots cd         # Go to dotfiles source directory
dots git ...    # Run git commands in dotfiles repo
dots test       # Run setup verification tests
dots doctor     # Check chezmoi health
```

Or use raw chezmoi commands:
```bash
chezmoi apply
chezmoi diff
chezmoi init    # Re-run templates after config changes
```

## Architecture

### Chezmoi File Naming Conventions
- `dot_` prefix → dotfile (e.g., `dot_zshrc` → `~/.zshrc`)
- `_config/` → `~/.config/`
- `.tmpl` suffix → Go template processed with chezmoi data
- Files in `.chezmoitemplates/` are reusable template snippets
- `symlink_` prefix → the target is a **symlink**, and the source file's *contents* are the link target path (e.g. `dot_local/bin/symlink_terminal-widget` → `~/.local/bin/terminal-widget` pointing at the path inside the file)
- **`include` paths use the actual source filename**, not the target name. For example, `.chezmoiexternal.toml.tmpl` is included as `{{ include ".chezmoiexternal.toml.tmpl" }}`, not `dot_chezmoiexternal.toml.tmpl`. The `dot_` prefix is only for files that chezmoi renames when applying to the home directory; chezmoi-native config files (`.chezmoi*.toml.tmpl`, `.chezmoiignore`, etc.) already start with a dot and don't use `dot_`.

### Template System
The main configuration template `.chezmoi.toml.tmpl` defines:
- **Machine detection**: Identifies specific machines by a stable signal — MacBook Pro 14" M5 Max (`Mac17,7`) → `rishi-mbp-2025` via hardware model; MacBook Pro 2019 and Mac Mini 2020 via ComputerName; Ubuntu via hostname
- **Feature flags**: `ephemeral`, `work`, `headless`, `personal` for conditional configuration
- **1Password integration**: long-lived secrets use guarded chezmoi templates;
  LLM API keys use command-scoped `op run` injection from reference-only config

### Key Configuration Files
| Source Path | Target | Purpose |
|-------------|--------|---------|
| `private_dot_zshenv.tmpl` | `~/.zshenv` | Non-secret environment variables and XDG paths |
| `dot_config/llm/private_secrets.env.op` | `~/.config/llm/secrets.env.op` | Personal-only 1Password references for LLM API keys |
| `dot_config/zsh/dot_zshrc` | `~/.config/zsh/.zshrc` | Main shell config, history, completions |
| `dot_config/zsh/scripts.zsh.tmpl` | `~/.config/zsh/scripts.zsh` | Custom shell functions |
| `dot_config/zsh/aliases/aliases` | `~/.config/zsh/aliases/aliases` | Shell aliases |
| `dot_config/git/config.tmpl` | `~/.config/git/config` | Git user config (templated email) |
| `dot_config/nvim/init.vim` | `~/.config/nvim/init.vim` | Neovim configuration |
| `dot_config/tmux/tmux.conf.tmpl` | `~/.config/tmux/tmux.conf` | Tmux configuration (macOS/Linux) |
| `dot_config/psmux/psmux.conf.tmpl` | `~/.config/psmux/psmux.conf` | psmux configuration (Windows) |

### XDG Directory Structure
This repo follows XDG Base Directory spec:
- `XDG_CONFIG_HOME` = `~/.config`
- `ZDOTDIR` = `~/.config/zsh` (zsh files in config, not home)

### Notable Shell Functions (in `scripts.zsh.tmpl`)
- `dots()` - Dotfiles management command (see Common Commands above)
- `extract()` / `x` - Universal archive extractor (20+ formats)
- `gcm()` - AI-powered git commit message generator using LLM
- `q()` / `qv()` - Ask questions about web pages or YouTube videos via LLM
- `sheet2csv()` - Extract spreadsheet data from images using Gemini AI
- `pdf2text()` - Extract text from PDFs using Gemini AI
- `bbstatus()` - Backblaze Personal Backup status (activity, remaining files/GB, last completed). Reads the app's state files under `/Library/Backblaze.bzpkg/bzdata` since the product ships no CLI. Gated to **darwin + personal** (zsh-only; Windows uses PowerShell + a different path)

### Neovim Configuration (`dot_config/nvim/init.vim`)
- **Plugin manager**: vim-plug — auto-installs on first launch if missing
- **Plugins**: catppuccin theme, telescope.nvim (fuzzy finder), cheatsheet.nvim
- **Key bindings**:
  - `<leader>?` — open cheatsheet browser (via cheatsheet.nvim + telescope)
  - `<leader>ff` — fuzzy file finder (telescope)
  - `<leader>fg` — live grep (telescope)
- **New machine setup**: `run_once_after_01` scripts run `nvim --headless +PlugInstall` on both macOS/Linux and Windows
- **Windows target**: Windows nvim reads `$LOCALAPPDATA/nvim`, not `~/.config/nvim`, so `AppData/Local/nvim/init.vim.tmpl` emits the same config there (via `include` of the Unix source, which stays the single source of truth). Paths inside init.vim use `stdpath('config')` so one file works on every OS. `.chezmoiignore` skips `AppData` on Unix and `.config/nvim` on Windows.
- Add custom cheatsheets at `~/.config/nvim/cheatsheet.txt` (format: `## Section` + `command | description`)

### Terminal Multiplexer (tmux / psmux)
- **tmux** (macOS/Linux) and **psmux** (Windows) share configuration via `.chezmoitemplates/tmux-shared`
- Shared settings (mouse, vi keys, status bar, keybindings) live in the template; platform-specific settings live in each config file
- Edit `.chezmoitemplates/tmux-shared` to change settings for both platforms at once
- tmux config adds Unix-specific terminal settings (`default-terminal`, `terminal-overrides`, `allow-passthrough`)
- psmux auto-launches on PowerShell terminal open (attaches to `main` session or creates one); skipped inside existing sessions, VS Code, and non-interactive contexts
- **psmux installation**: Via Scoop when available, otherwise portable binary from GitHub releases to `~/.local/bin/psmux/` (installed by `run_once_after_01-install-cli-tools.ps1.tmpl`)

### Navi Cheatsheets
Cheats live in `dot_local/share/navi/cheats/` and sync to `~/.local/share/navi/cheats` on every OS. navi's *built-in* default cheat path varies by platform (`directories` crate: `%APPDATA%`-based on Windows, Application Support on some macOS builds), so both shells export `NAVI_PATH` pointing at the managed dir — navi's highest-precedence setting. The zsh widget loads in `.zshrc`, the PowerShell widget in `profile.ps1` (both guarded on navi existing; navi is not installed in Windows portable mode).

### macOS App CLI Shims
Some macOS apps ship a CLI inside their `.app` bundle. Expose those as a symlink in
`~/.local/bin` (already on `PATH` via `private_dot_zshenv.tmpl`) rather than a shell
function — a symlink works in scripts, cron, launchd, and non-zsh shells, while a
function only exists in interactive zsh.

| Shim | Target | Gating |
|------|--------|--------|
| `~/.local/bin/terminal-widget` | `/Applications/TerminalWidget.app/Contents/MacOS/TerminalWidget` (Brett Terpstra's Terminal Widget, Mac App Store) | darwin **and** `.personal` — a Mac App Store purchase tied to the personal Apple ID; gated so other machines don't get a dangling symlink |

Verified that invoking through the symlink behaves identically to invoking the bundle
binary directly (some `.app` binaries resolve their bundle from the executable path and
break behind a symlink — this one does not).

**Completions:** `dot_config/zsh/completions/` → `~/.config/zsh/completions/` is a
chezmoi-managed `fpath` entry for tools that generate their own completion scripts. The
`.zshrc` prepends it to `FPATH` **before** `compinit` (fpath is only scanned at compinit
time, so order matters). Do **not** use a tool's own `--install` flag — Terminal Widget's
writes to `~/.zsh/completions/`, which is neither on this setup's fpath nor managed by
chezmoi. Generate to stdout into the source tree instead:

```bash
terminal-widget completions --shell zsh --name terminal-widget --stdout \
  > "$(chezmoi source-path)/dot_config/zsh/completions/_terminal-widget"
```

The checked-in script is a **generated snapshot** — regenerate it with the command above
after an app update adds or renames flags.

### Security Tools
- **tirith** - Terminal security tool that guards against URL/ANSI injection attacks
  - macOS: Installed via Homebrew tap as `sheeki03/tap/tirith` (see "Tap-based formulae" rule above)
  - Windows: Installed via Scoop (`scoop bucket add tirith https://github.com/sheeki03/scoop-tirith && scoop install tirith`)
  - Initialized in shell via `eval "$(tirith init)"` (zsh) or `Invoke-Expression (& tirith init powershell)` (PowerShell)
  - **Claude Code MCP**: Registered user-scope on personal machines by the `run_once_after_01-install-cli-tools` scripts via `claude mcp add --scope user tirith -- tirith mcp-server` (a `mcpServers` key in settings.json is NOT honored by Claude Code) — provides `tirith_check_command`, `tirith_check_url`, `tirith_scan_file`, etc.
  - **Claude Code PreToolUse hook**: `tirith setup claude-code --scope user` (run by the same cli-tools scripts on any machine with tirith) installs `~/.claude/hooks/tirith-check.py` and merges a `PreToolUse` Bash hook into `~/.claude/settings.json`, so every command Claude runs is vetted by `tirith check` before execution (fail-closed; set `TIRITH_FAIL_OPEN=1` to fail open). The `~/.zshrc` append it also makes is inert under ZDOTDIR.

### AI/LLM Tools
- **rtk** - Claude Code output compressor (intercepts common dev commands and filters their output before it reaches Claude's context, ~60-90% token reduction)
  - macOS/Linux: Installed via official Homebrew formula (`brew "rtk"` in Brewfile, no tap needed)
  - Windows: Not in Scoop. Always installed from GitHub releases via `.chezmoiexternal.toml.tmpl` (outside the `.portable` gate, since the Scoop path can't supply it). Lands at `~/.local/bin/rtk.exe`
  - **Claude Code hook**: `run_once_after_01` runs `rtk init -g --auto-patch --hook-only` to register the `Bash` PreToolUse hook in `~/.claude/settings.json`. Flags chosen so the install is non-interactive and doesn't add `RTK.md` / `@RTK.md` to the global CLAUDE.md (the hook works transparently — Claude doesn't need to know rtk exists)
  - **Bypass for one command**: rtk's matchers are pattern-based; off-pattern variants pass through. Run `git -P status` or pipe through `cat` to skip rewriting. Full removal: `rtk init -g --uninstall`. There is no `RTK_HOOK_DISABLE` env var

### Template Variables
When editing `.tmpl` files, these variables are available:
- `.chezmoi.hostname` - Machine hostname
- `.chezmoi.os` - Operating system (darwin, linux, windows)
- `.chezmoi.arch` - Architecture (amd64, arm64)
- `.personal` - Boolean for personal machines (enables secrets)
- `.work` - Boolean for work machines
- `.ephemeral` - Boolean for temporary/cloud environments
- `.headless` - Boolean for machines without display
- `.name`, `.email` - User identity (varies by machine type)

### Chezmoi Scripts (`.chezmoiscripts/`)
Scripts that run automatically during `chezmoi apply`:
- `run_once_before_install-homebrew.sh.tmpl` - Installs Homebrew (first run only)
- `run_onchange_after_00-install-packages.sh.tmpl` - Installs Brewfile/Scoopfile packages (when package files change)
- `run_once_after_01-install-cli-tools.sh.tmpl` - Installs Claude Code, Shell Sage, nvim plugins, wires rtk hook (macOS/Linux)
- `windows/run_once_after_01-install-cli-tools.ps1.tmpl` - Installs Claude Code, Tirith, psmux, nvim plugins, wires rtk hook (Windows)
- `darwin/run_once_after_configure-macos.sh` - Configures macOS preferences
- `run_once_after_02-install-adguardhome.sh.tmpl` - Installs AdGuard Home on the Mac mini (LAN DNS host) — gated to `rishi-macmini-2020`
- `run_once_after_03-configure-mini-always-on.sh.tmpl` - `pmset` 24/7 settings for the Mac mini — gated to `rishi-macmini-2020`
- `run_after_04-set-mini-dns-loopback.sh.tmpl` - Points the Mac mini's resolver at `127.0.0.1` once AGH is answering — gated to `rishi-macmini-2020`. Runs on every apply and converges: after the AGH first-run wizard, just `chezmoi apply`. When already converged it changes nothing and never prompts for sudo.
- `run_after_05-start-colima.sh.tmpl` - Runs Colima from its XDG location (`~/.config/colima`) with 4 CPU / 6 GiB and `/Volumes/Easystore` mounted **read-only** (so the Shoko container can read the anime library) — gated to `rishi-macmini-2020`. Replaces the old `brew services` approach with a chezmoi-managed LaunchAgent (`~/Library/LaunchAgents/com.rishi.colima.plist`, gated via `.chezmoiignore`) that pins `COLIMA_HOME` because Colima 0.10.x has flaky XDG auto-detection (`COLIMA_HOME` is also exported in `private_dot_zshenv.tmpl` for interactive shells). Runs on every apply (converges once colima is installed and the drive is mounted); creates the VM only if missing, **never deletes** an existing VM (that would wipe Docker named volumes such as Shoko's DB). Recreating the VM (e.g. to change mounts/resources) is a deliberate manual step: `colima delete && rm -rf ~/.colima` then re-run.
- `run_after_06-tailscale-serve.sh.tmpl` - Exposes the mini's services over Tailscale Serve (tailnet-only HTTPS), all under `https://<mini>.<tailnet>.ts.net`: Jellyfin on `:8443` (`localhost:8096`), Shoko on `:8111`, and the Showtime Finder at `/showtime` (`localhost:5151`) — gated to `rishi-macmini-2020`. Uses a dedicated HTTPS port instead of a path mount: Jellyfin double-prefixes its `BaseUrl` on redirects (e.g. `/jellyfin/System/Info/Public` → `/jellyfin/jellyfin/web/`), which browsers tolerate but native mobile apps don't. Requires the mini to already be logged into a tailnet; otherwise the script logs a notice and retries on the next apply.
- `run_after_07-install-shoko.sh.tmpl` - Runs **Shoko Server** as a Docker container (`ghcr.io/shokoanime/server`) on Colima — gated to `rishi-macmini-2020`. Shoko is the anime metadata/organization backend for Jellyfin's Shokofin plugin. Writes `~/.config/shoko/docker-compose.yml` then `docker compose up -d`. The anime drive is bind-mounted at its identical host path (`/Volumes/Easystore/Movies & Shows`, read-only) so Shokofin's host-side symlinks resolve without remapping; Shoko's own data lives in the `shoko-config` Docker named volume. API/UI on `127.0.0.1:8111` (localhost-only). Runs on every apply with a converged fast-path (compose unchanged + Shoko answering); also wires `~/.docker/config.json`'s `cliPluginsExtraDirs` so the brew docker CLI finds the Compose v2 plugin. See `docs/shoko-jellyfin.md` for the manual UI/API steps.
- `run_after_08-jellyfin-keepalive.sh.tmpl` - Loads a LaunchAgent (`~/Library/LaunchAgents/com.rishi.jellyfin.plist`) that watchdogs Jellyfin and relaunches it if it goes down — crash, reboot, or the macOS app's in-app "Restart" (which otherwise stops the server without relaunching) — gated to `rishi-macmini-2020`. Drives the real `.app` via `open` to keep its macOS file-access (TCC) permission to the external media drive.
- `run_after_10-install-rustdesk-server.sh.tmpl` - Runs the **RustDesk OSS server** (`hbbs` rendezvous + `hbbr` relay) as Docker containers on Colima — gated to `rishi-macmini-2020`. Self-hosted replacement for AnyDesk, whose free tier nags about commercial use when reaching a work machine. Writes `~/.config/rustdesk/docker-compose.yml` then `docker compose up -d`; converging fast-path like script 07. **Port binding is split by trust level:** the native ports (21115/tcp, 21116/tcp+udp, 21117/tcp) bind `0.0.0.0` so a router forward can reach them, while the WebSocket listeners (21118, 21119) bind **loopback only** — hbbs/hbbr trust `X-Real-IP`/`X-Forwarded-For` on those ports *without validating them*, so anything that reaches them directly can spoof a client IP. Only ever front them with a reverse proxy that sets those headers itself. Clients authenticate with the server's ed25519 public key (printed at the end of the script), so the native ports being reachable does not make this an open relay. `ALWAYS_USE_RELAY=N` keeps sessions on direct P2P where possible, keeping the mini's upstream out of the hot path.

**Note on the `docker` CLI:** scripts 07 and 10 both gate on `command -v docker`. Homebrew's `docker` formula was found *installed but unlinked* (2026-07-26), so `/opt/homebrew/bin/docker` was missing and **script 07 had been silently no-op'ing on every apply** — Shoko only stayed up because `restart: unless-stopped` kept the existing container alive. Fix is `brew link --overwrite docker`. If either script starts logging "docker not installed yet", check linkage before anything else.

### Windows Portable Mode (`.chezmoiexternal.toml.tmpl`)
Fallback for Windows machines where Scoop is unavailable (`.portable = true`). Downloads pre-built binaries directly from GitHub releases to `~/.local/bin`, which is added to PATH in the PowerShell profile. Covers: rg, fd, bat, fzf, zoxide, starship, lsd, jq, yq, gh, duf, fastfetch, ruff — plus the Hack Nerd Font (portable mode only; Scoop's `nerd-fonts/Hack-NF` owns fonts otherwise, and installing both ways made them fight over the same HKCU registry names). Note: nvim, navi, and tirith are NOT included in portable mode.

**uv / uvx exception:** Used to be in the list above, but `uv.exe` gets file-locked on Windows during `chezmoi apply` (commit `0a8b52c`). `.chezmoiignore` now blocks `.local/bin/uv.exe` and `.local/bin/uvx.exe` on all Windows targets. Install paths now: Scoop (`main/uv`) on non-portable Windows; the official Astral installer (`irm https://astral.sh/uv/install.ps1 | iex`) run from `windows/run_once_after_01-install-cli-tools.ps1.tmpl` on portable Windows. The Astral installer manages its own replacement logic, so it doesn't trigger the file-lock that prompted the chezmoi-external removal.

**Always-on Windows externals (regardless of `.portable`):** rtk is installed from GitHub releases on every Windows machine because rtk-ai publishes no Scoop manifest. Listed outside the `.portable` block in `.chezmoiexternal.toml.tmpl`.

### Package Management
- `dot_Brewfile.tmpl` → `~/.Brewfile` - Homebrew packages for macOS/Linux (templated; supports per-machine gating via `{{ if .personal }}` etc.)
- `dot_Scoopfile.tmpl` → `~/.Scoopfile` - Scoop packages for Windows
- Packages auto-install when package files change via `run_onchange` scripts. The Brewfile install script reads the rendered `~/.Brewfile`, not the template source.

**Tap-based formulae:** Always use the fully qualified `tap/formula` name in the Brewfile when adding entries from a third-party tap. `brew bundle` resolves unqualified `brew "name"` lines against the formula index loaded at startup, which doesn't include taps added later in the same Brewfile, so a fresh-machine apply will fail with `No available formula`. Examples in this repo: `sheeki03/tap/tirith`, `run-llama/liteparse/llamaindex-liteparse`.

**Windows package manager policy:** Use Scoop exclusively. Do not use npm, cargo, winget, or other package managers as alternatives for CLI tools.

**Cask upgrades that need `sudo` (bites hardest on the mini):** some casks — `tailscale-app`, `macfuse`, anything installing a pkg or system extension — shell out to `sudo` during uninstall-then-reinstall. In a non-interactive shell that fails with `sudo: a terminal is required`, but **only after brew has already quit the running app**. On the mini that means the service stays down and the upgrade never completes. Symptom seen 2026-08-02: `brew upgrade --cask tailscale-app` quit Tailscale, failed at the sudo step, and left the mini off the tailnet (AGH/LAN DNS was unaffected — it's a LaunchDaemon and doesn't route through Tailscale). Run these yourself with a `! sudo -v && brew upgrade --cask <name>` rather than delegating them, and prefer doing them when you're physically at the machine.

**`--greedy` mis-reports self-updating casks — do not chase `tailscale-app`.** Tailscale auto-updates itself, so the app on disk drifts ahead of Homebrew's install record. As of 2026-08-02 brew's receipt said `1.62.1` while the running app and system extension were `1.98.8`; the cask only offered `1.98.10`. `brew outdated --cask --greedy` will keep listing it forever, and "upgrading" it buys ~nothing while risking the sudo-abort above. Verify the *real* version with `tailscale version` or `systemextensionsctl list | grep -i tailscale` before believing brew. Same caution applies to any cask marked `auto_updates`.

**`libtiff` ⇄ `webp` circular dependency warning is cosmetic — do NOT run the suggested fix.** `brew bundle check` prints "Formulae dependency graph sorting found a circular dependency: libtiff, webp" and suggests `brew uninstall --ignore-dependencies --force libtiff webp`. **Ignore it.** The cycle is real and intentional upstream, not stale keg-tab data: `libtiff.dylib` links `libwebp` (WebP codec) and webp's `cwebp`/`dwebp`/`img2webp` link `libtiff` (TIFF I/O). Installed receipts already match the current formula definitions, so a reinstall pours identical bottles and the warning returns — while `--ignore-dependencies --force` temporarily breaks ~19 dependents (`qt`, `mpv`, `poppler`, `deno`, `yt-dlp`, `librsvg`, `gtk4`, `libheif`…). `brew doctor` reports no linkage problems and `brew bundle check` still returns "satisfied". It only affects Homebrew's topological sorter.

**Version-locked casks:** `onyx` ships a separate build per macOS major version (the cask URL carries the version, e.g. `/download/26/OnyX.dmg`) and declares `depends_on macos`. Homebrew picks the right build from the running OS automatically, but after a macOS major upgrade you need `brew reinstall --cask onyx` — `brew upgrade` won't switch builds on its own if the cask version string hasn't changed.

### AI Parity (Claude ↔ Codex Skill Sync)

**Read [`ai-parity/SPEC.md`](ai-parity/SPEC.md) before modifying Claude or Codex skills.** The `ai-parity/` directory is a manifest-driven layer that keeps selected Claude Code and Codex configuration semantically aligned. Canonical content is human-authored under `ai-parity/`; the parity engine renders it into checked-in chezmoi source trees. [`ai-parity/README.md`](ai-parity/README.md) is the shorter workflow guide.

**Ownership — where to edit:**

| Path | Role |
|---|---|
| `ai-parity/shared/**` | Canonical content for both tools — the default place for cross-tool changes |
| `ai-parity/adapters/**` | Tool-specific variants of shared content (e.g. Codex `SKILL.md` overrides) |
| `ai-parity/contracts/**` | Codex-native config (`AGENTS.md`, agent TOML, rules, profiles) |
| `ai-parity/manifest.toml` | Ownership, mappings, render policy, review acknowledgements |
| Non-migrated `dot_claude/**` | Legacy Claude-owned source (still edited directly) |

**Generated — never hand-edit:** `dot_codex/**`, `dot_agents/**`, `ai-parity/generated-state.json`, and these migrated `dot_claude/skills/` roots: `matlab`, `matlab-runner`, `zotero`, `pdf-chunk`, `llm-pdf-processing`, `scientific-figures`. Two Claude-owned sources are additionally *rendered* to Codex (edit the Claude side, then sync): `dot_claude/skills/gemini-billing-blocks` and `dot_claude/skills/learned` (→ `dot_agents/skills/learned-patterns/references`). If a useful edit already landed in a rendered target, import it with `dots ai propose` — do not treat the rendered file as source.

**Quick decision guide:** shared behavior → `shared/`; tool-specific expression → `adapters/`; Codex-native config → `contracts/`; legacy Claude skill → its `dot_claude/` path; edit found in rendered output → proposal; runtime memory worth keeping → `dots ai memories scan` then curate.

**Commands** (run via `dots ai …`; requires `uv`):

| Command | Purpose |
|---|---|
| `dots ai status` / `diff` | Inspect parity state / pending render changes (read-only) |
| `dots ai sync` | Dry run (default). `--write` renders into chezmoi source — **never** applies to `$HOME` |
| `dots ai verify` | Check manifest, digests, inventory, and generated outputs |
| `dots ai propose --from claude\|codex NAME` | Turn a rendered-target edit into a review proposal |
| `dots ai proposals list\|show\|accept\|resolve\|reject ID` | Review intake (accept = direct-shared only, atomic transaction) |
| `dots ai doctor` → `repair TXN --finish\|--rollback` | Diagnose / recover an interrupted write |
| `dots ai reconcile --after-merge` | Regenerate derived files after resolving canonical Git conflicts |
| `dots ai hooks install` | Opt-in Git hooks (pre-commit blocks stale parity commits and turns staged rendered-target edits into proposals) |
| `dots ai memories scan --from claude\|codex` | Create local review proposals from runtime memories |

**Gotchas:**
- Every top-level `dot_claude/skills/` directory and every `dot_claude/agents/*.md` **must** have a `[[skills]]`/`[[agents]]` entry in `manifest.toml` — the inventory check fails closed on unlisted (or stale) names.
- Editing a `[[reviews]]` source (`dot_claude/CLAUDE.md`, `dot_claude/skills/verify/`, `dot_claude/agents/code-reviewer.md`, `dot_claude/agents/debugger.md`) stales its `acknowledged_digest`. Review the Codex counterpart still matches in spirit, then update the digest that the `verify` failure prints.
- Adapted skills (`matlab-runner`, `zotero`, `pdf-chunk`) have full Codex `SKILL.md` overrides — a general change to the canonical `SKILL.md` must be reviewed against the adapter too. Bundled scripts stay shared byte-for-byte.
- Never touch parity runtime state: `ai-parity/.proposals/`, `.transactions/`, `.sync-journal.json`, `.sync-lock` (git- and chezmoi-ignored; schemas enforced by the normal commands).
- `dot_claude/skills/pdf` is protected licensed content — never a parity input, adapter, or destination (the Codex `pdf` skill under `adapters/skills/pdf` is independently authored).
- Shared scripts use manifest-declared `literal_*` source names (e.g. `literal_run_matlab.sh` → `run_matlab.sh`), deploy as `0644` non-executables, and are invoked with `uv run`.
- Parity sync and home deployment are separate review boundaries: after `dots ai sync --write`, deployment is still an explicit `chezmoi diff` → `chezmoi apply`.

### Claude Code Skills
Skills are synced via chezmoi to `~/.claude/skills/`. Included skills, by category:

**Documents & files:** `pdf`, `pdf-chunk` (large PDFs without filling context), `xlsx`, `pptx`, `docx`, `doc-coauthoring`, `theme-factory`

**Development workflow:** `plan`, `tdd`, `code-review`, `build-fix`, `verify`, `checkpoint`, `e2e`, `eval`, `test-coverage`, `refactor-clean`, `orchestrate`, `update-codemaps`, `update-docs`, `learn`, `session-wrap`, `skill-creator`

**Research & science:** `academic-review` (papers/proposals review), `matlab` (R2025a patterns + the personal `+thz` package), `matlab-runner` (headless script execution), `zotero` (local-library citation lookup; **personal machines only**)

**macOS app integrations (darwin-only via `.chezmoiignore`):** `things` (Things 3), `fantastical` (calendar), `keynote` (presentations; **also personal-only**)

**Parity-generated skills:** `matlab`, `matlab-runner`, `zotero`, `pdf-chunk`, `llm-pdf-processing`, and `scientific-figures` are rendered from `ai-parity/shared/skills/` — edit the canonical source (and adapter, if any), then `dots ai sync --write`. See "AI Parity" above.

**Adding more skills from the marketplace:**
```
/plugin marketplace add anthropics/skills              # Register marketplace (one-time)
/plugin install example-skills@anthropic-agent-skills  # Install a bundle
```

**Custom skills:** Create a folder with a `SKILL.md` file containing YAML frontmatter (`name`, `description`) and markdown instructions. Decide placement first: a skill shared with Codex goes in `ai-parity/shared/skills/` with a `[[shared_artifacts]]` manifest entry; a Claude-only skill goes in `dot_claude/skills/` **and requires** a `[[skills]]` entry (`mode = "planned"`) in `ai-parity/manifest.toml` — the parity inventory check fails without one. Then `dots ai sync --write` and `dots ai verify`.

### Claude Code Plugins
Third-party plugins are registered in `dot_claude/create_settings.json.tmpl` via the
`extraKnownMarketplaces` + `enabledPlugins` keys. Because of the `create_` prefix this
only reaches **fresh** machines — an existing machine needs the two commands by hand:

```bash
claude plugin marketplace add "$(chezmoi source-path)/i-have-adhd"
claude plugin install i-have-adhd@i-have-adhd
```

| Plugin | Source | Notes |
|--------|--------|-------|
| `i-have-adhd` | `i-have-adhd/` submodule (`github.com/ayghri/i-have-adhd`) | ADHD-friendly output shaping. Opt-in via `/i-have-adhd` (`disable-model-invocation: true`); "stop adhd mode" ends it. Optional always-on flag: `~/.claude/.i-have-adhd-always` |

**The marketplace points at the source tree, not GitHub.** The template renders
`{{ .chezmoi.sourceDir }}/i-have-adhd` (backslash-escaped for Windows, same treatment as
`statusLine`) so the path resolves per-machine and the **pinned submodule SHA stays
authoritative**. Using `ayghri/i-have-adhd` as the source instead would have Claude clone
upstream separately and float on latest, defeating the pin. The directory is
`.chezmoiignore`d so it is never deployed into `$HOME`, and `chezmoi init` defaults
`--recurse-submodules` to true, so a fresh clone populates it before `apply` runs.

**Stay pinned — this is deliberate, not neglect.** The plugin registers a `SessionStart`
hook (`hooks/always-on.sh`, matcher `startup|resume|clear|compact`) that runs shell in
*every* session in *every* project. Upstream is fast-moving and multi-author (~50 commits
in 30 days; 17 of the last 50 commits were merged external PRs), so auto-following would
execute unreviewed third-party shell. The only upside would be fresher output-*formatting*
rules — not worth giving up the review boundary. Bump deliberately, reading the
executable surface first:

```bash
cd "$(chezmoi source-path)/i-have-adhd"
git fetch origin
git log --oneline HEAD..origin/main -- hooks/ scripts/   # review executable changes FIRST
git checkout origin/main
dots git add i-have-adhd && dots git commit -m "chore: bump i-have-adhd to <sha>"
```

Not routed through ai-parity: upstream ships its own `.codex-plugin/` and `.agents/`
manifests, so parity would duplicate work the author already does.

### Learned Skills
Extracted patterns and project-specific knowledge live in `dot_claude/skills/learned/` and sync via chezmoi to `~/.claude/skills/learned/`. These are reference files (not invocable commands) created by the `/learn` skill during sessions.

**Important:** After `/learn` creates a new file in `~/.claude/skills/learned/`, it must be explicitly added to chezmoi, rendered to Codex, and committed to sync across machines. The `learned/` collection is a parity source rendered to `dot_agents/skills/learned-patterns/references/`, so run `dots ai sync --write` and commit the regenerated Codex copies alongside:
```bash
dots add ~/.claude/skills/learned/<new-file>.md
dots ai sync --write   # renders the Codex copy under dot_agents/
dots git add -A && dots git commit -m "feat: add learned skill <name>"
dots git push
```

Current learned files:
- **andor-sdk-dll-lifecycle.md** — Never force-kill Python holding Andor SDK handles (`atmcd64d.dll` / `ShamrockCIF.dll`); avoids `DRV_NOT_AVAILABLE` DLL lockups
- **windows-phantom-usb-devices.md** — Recovering Andor USB instruments that show as phantom (`CM_PROB_PHANTOM`) devices in Windows Device Manager
- **mockobject-attribute-getattr-trap.md** — Python mock `__getattr__` trap
- **qt-test-window-close-blocking-shutdown.md** — Qt test window close blocking shutdown
- **powershell-utf8-bom-em-dash.md** — ASCII-only in `*.ps1.tmpl`: PowerShell 5.1 mis-decodes UTF-8 without BOM and em-dashes break parsing
- **homebrew-cask-sudo-abort.md** — `brew upgrade --cask` quits the app *before* the `sudo` step that fails non-interactively, leaving a service down; also why `--greedy` lies about self-updating casks
- **homebrew-circular-dep-false-hint.md** — Homebrew's "stale keg tab data" circular-dependency advice is often wrong (`libtiff` ⇄ `webp` is real); verify before running the destructive suggested fix

> MATLAB/TA patterns formerly listed here were consolidated into the **matlab** skill (`dot_claude/skills/matlab/`): `fft.md`, `performance.md`, `plotting.md`, `style-guide.md`, `ta.md`.

## Mac Mini AdGuard Home Setup

The Mac mini (`rishi-macmini-2020`) hosts LAN-wide DNS via AdGuard Home. Most setup is automated by chezmoi scripts 02-04 (02/03 are `run_once`; 04 is `run_` and converges on every apply); the items below are the bits that genuinely can't live in chezmoi.

### What's automated by chezmoi
- **Install** AGH binary into `/Applications/AdGuardHome` (`run_once_after_02`)
- **Always-on** `pmset` settings so the mini doesn't sleep (`run_once_after_03`)
- **DNS loopback** — point the mini's resolver at `127.0.0.1` once AGH answers (`run_after_04`, converges on every apply)
- **Seed restore** — if `~/.local/share/adguardhome-seed/AdGuardHome.yaml` is present (decrypted from the age-encrypted source), `run_once_after_02` copies it to `/Applications/AdGuardHome/` so AGH boots fully configured (no first-run wizard)

### Manual checklist (one-time per machine / per Apple ID / per device)

**Router (Linksys MR7500, lives on the device, not chezmoi-able)**
- [ ] DHCP Reservation pinning the mini's MAC → `192.168.1.185` — Connectivity → Local Network → DHCP Reservations. **Pin the interface the mini actually uses** (wired `en0` = `14:98:77:49:6b:6d`, or Wi-Fi `en1` hardware MAC = `14:98:77:60:dc:a9`). If on Wi-Fi, **Private Wi-Fi Address must be OFF** for the home network first (see next item), otherwise the mini presents a randomized MAC that won't match the reservation.
- [ ] Static DNS 1 = `192.168.1.185`, DNS 2 + 3 empty — same screen, DHCP Server section. Use the *web UI* at `http://192.168.1.1`; the Linksys app hides this field on Hydra firmware

**On the mini — if connected via Wi-Fi rather than Ethernet**
- [ ] Private Wi-Fi Address OFF for the home network — System Settings → Wi-Fi → Details… → Private Wi-Fi Address → Off. macOS defaults this ON, which randomizes the MAC per-network and breaks the `.185` DHCP reservation. Wired Ethernet (`en0`) is never randomized and is preferred for an always-on DNS host.

**Per-Apple-ID** — apply to the iCloud account, not to chezmoi
- [ ] iCloud Private Relay off — Settings → [your name] → iCloud → Private Relay → Off. (Otherwise Safari bypasses local DNS for HTTPS.)

**Per-browser** — app-internal preference, gets clobbered if chezmoi'd
- [ ] Chrome: Settings → Privacy & Security → "Use secure DNS" → Off (or "With current service provider"). DoH inside Chrome bypasses the system resolver.
- [ ] Firefox: Settings → Privacy & Security → "DNS over HTTPS" → "Off"
- [ ] Edge: similar to Chrome — Settings → Privacy → "Use secure DNS" → Off

**Per-device on the LAN** — usually nothing required (DHCP hands DNS out to clients), but force a lease renewal after the router DHCP change so devices pick up the new DNS server right away.

### Troubleshooting: "LAN devices aren't being filtered"

Almost always a **reachability/addressing** problem, not AGH itself. AGH can be perfectly healthy (filtering correctly when queried directly) while clients get no filtering — because they're pointed at `192.168.1.185` and the mini has drifted off that IP.

**Diagnose in order (stop at the first failure):**

```bash
# 1. Is AGH running and filtering AT ALL? (query the loopback directly)
dig +short @127.0.0.1 doubleclick.net          # expect 0.0.0.0 → engine is fine
ps aux | grep '[A]dGuardHome'                   # expect the -s run process

# 2. Is the mini actually AT .185? (this is the usual culprit)
ipconfig getifaddr en0                          # wired — expect 192.168.1.185
ipconfig getifaddr en1                          # Wi-Fi — expect 192.168.1.185
dig +short +time=2 +tries=1 @192.168.1.185 doubleclick.net   # 0.0.0.0 = reachable+filtering; timeout = mini not at .185

# 3. Is the active interface presenting a randomized MAC?
ifconfig en1 | grep ether                       # if it's NOT 14:98:77:60:dc:a9, Private Wi-Fi Address is ON
networksetup -listallhardwareports              # maps en0/en1 → hardware MAC
```

**Root cause seen before (2026-06):** built-in Ethernet (`en0`) was unplugged → mini fell back to **Wi-Fi (`en1`) with Private Wi-Fi Address ON** → presented a randomized MAC (`b6:b6:…`) → router didn't match the reservation → mini got a *dynamic* lease (`192.168.1.28`) → nothing at `.185` → every client's DNS queries timed out and fell back to unfiltered upstream. AGH was healthy the whole time.

**Fix:** either plug in Ethernet (reclaims `.185` via the wired reservation), or turn Private Wi-Fi Address OFF and pin the Wi-Fi hardware MAC (`14:98:77:60:dc:a9`) to `.185`. Then renew leases / toggle Wi-Fi on affected clients so they stop using the cached dead resolver. Confirm via the AGH Query Log at `http://192.168.1.185:3000` populating as a client browses.

### DNS architecture: LAN vs roaming (the decided design)

**Decision (2026-07):** do **not** route AGH over Tailscale. Keep the split below. Rationale
below; this replaced an earlier plan to add AGH as a tailnet global nameserver, which
Tailscale blocks anyway (see "Why not AGH over Tailscale").

| Scope | Resolver | Notes |
|---|---|---|
| **LAN clients** | **AdGuard Home** on the mini (`192.168.1.185`), handed out by router DHCP | Self-hosted blocklists + unified query log. Set AGH's **upstream → NextDNS** so LAN also gets NextDNS filtering layered under AGH's own rules. |
| **Roaming / tailnet** | Per-device **NextDNS profile** (preferred), *not* Tailscale's global override | Filter roaming devices at the device level so you can add per-SSID exceptions (e.g. disable on the corporate Wi-Fi). Keep Tailscale's **Override DNS servers OFF** — see the tradeoff below. |
| **The mini itself** | AGH via MagicDNS fallback to `127.0.0.1` | Tailscale MagicDNS forwards non-`.ts.net` queries to the system default, which the loopback fix points at AGH. |

Two independent "NextDNS" roles — don't conflate them: **AGH's upstream = NextDNS**
(only affects queries that reach AGH, i.e. LAN) vs **Tailscale's global nameserver =
NextDNS** (roaming devices hit NextDNS *directly*, bypassing the mini entirely). They can
point at the same provider but are different layers.

**Why not AGH over Tailscale (why this is the right call, not a limitation we settled for):**
- **A self-hosted box can't be its own backup.** Whatever stays up when the mini is down must live *off* the mini — i.e. a cloud resolver. NextDNS already is that. Making AGH the roaming resolver would make all roaming DNS depend on the mini's uptime + tailnet reachability.
- **Tailscale won't allow it alongside NextDNS anyway.** With a **DoH** global nameserver configured (NextDNS is DoH), the admin console forces any *additional* nameserver to be **restricted to a search domain** (Split DNS) — you cannot add a second *global* one. Tailscale also does no health-checked failover between resolvers. (This is the "Restrict to domain won't turn off" wall hit in the console.)

**Why Tailscale "Override DNS servers" stays OFF (corporate-DNS tradeoff):** turning it ON
forces *all* DNS on every tailnet device to the global nameserver while Tailscale is
connected, **ignoring the local network's DNS**. That breaks resolution of
local/corporate internal names — intranet hosts, printers, and shares behind a private
DNS server (e.g. a private AD domain) return NXDOMAIN, so you can't reach them by name on
a work network. (`.local`/AirPrint printers still work — macOS/iOS resolve those via mDNS,
not the configured DNS server; it's *unicast* internal DNS that breaks.) The flip side:
with Override OFF, the global nameserver is largely *not* enforced on networks that hand
out their own DNS — which is why routing roaming filtering through Tailscale is a poor fit.
Conclusion: leave Override OFF and do roaming ad-filtering with a **NextDNS device
profile** instead (supports per-SSID/on-demand exceptions Tailscale's tailnet-wide toggle
can't). To opt a single device out of Tailscale DNS entirely: `tailscale set --accept-dns=false`.

**If you ever DO want self-hosted roaming DNS** (accepting the mini-uptime dependency): AGH can *serve* DoH itself. Enable AGH → Encryption with a TLS cert; Tailscale issues free `.ts.net` certs via `tailscale cert mini.dropbear-bitterling.ts.net`. AGH then serves DoH at `https://mini.dropbear-bitterling.ts.net/dns-query`, which can *replace* NextDNS as the single global DoH nameserver. Adds cert-renewal (~90 day) upkeep and still dies if the mini is down — hence not chosen.

**Reference — mini's tailnet identity:** IP `100.117.214.99`, MagicDNS name `mini.dropbear-bitterling.ts.net`. AGH already listens on all interfaces (`bind_hosts: 0.0.0.0`; `dig @100.117.214.99 doubleclick.net` → `0.0.0.0`), so it's *reachable* over the tailnet — the design simply chooses not to point Tailscale's DNS at it.

**Note on the AGH web UI:** the DNS settings page fields (Upstream / Bootstrap / Fallback / Private reverse DNS servers, EDNS, DNSSEC) are all *outbound*/validation settings, **not** the listen interface. `bind_hosts` (what AGH listens on) lives only in the install wizard and `/Applications/AdGuardHome/AdGuardHome.yaml`.

### Age encryption setup (one-time, mini only)

Push-button rebuild requires the AGH config seed to live in git, encrypted with `age` so the public dotfiles repo doesn't expose secrets.

```bash
# 1. Generate keypair (only needed once for your identity, ever)
mkdir -p ~/.config/age && chmod 700 ~/.config/age
age-keygen -o ~/.config/age/key.txt
chmod 600 ~/.config/age/key.txt

# 2. Capture the public key
grep '^# public key:' ~/.config/age/key.txt
#   → "# public key: age1xxxx...zzzz"

# 3. Push the private key to 1Password as the source of truth
op item create --category="Secure Note" --title="Age Encryption Key" \
  --vault=Personal "credential[concealed]=$(cat ~/.config/age/key.txt)"

# 4. Verify the 1Password backup matches local exactly
diff ~/.config/age/key.txt <(op read 'op://Personal/Age Encryption Key/credential') \
  && echo "✓ 1Password backup verified"

# 5. Wire chezmoi to the recipient.
#    `chezmoi init` prompts for the public key on the first run per machine
#    and caches the answer in `[data].age_recipient` of
#    ~/.config/chezmoi/chezmoi.toml, so subsequent inits don't re-prompt.
#    (No need to touch the local key file — `dot_config/private_age/private_key.txt.tmpl`
#    has been chezmoi-managing it via 1Password since the encryption was set up.)

# 6. Round-trip test
echo hello | chezmoi encrypt | chezmoi decrypt
#   → "hello" if the round-trip works
```

### Snapshot the live AGH config to the encrypted seed

After completing the AGH first-run wizard (or after any config change you want preserved):

```bash
# Copy the live config (root:wheel mode 600) to a user-readable temp,
# then let chezmoi add+encrypt it as a managed source file.
mkdir -p ~/.local/share/adguardhome-seed
sudo cat /Applications/AdGuardHome/AdGuardHome.yaml > ~/.local/share/adguardhome-seed/AdGuardHome.yaml
chmod 600 ~/.local/share/adguardhome-seed/AdGuardHome.yaml

chezmoi add --encrypt ~/.local/share/adguardhome-seed/AdGuardHome.yaml
# → creates dot_local/share/adguardhome-seed/encrypted_private_AdGuardHome.yaml.age in source

dots git add dot_local/share/adguardhome-seed/
dots git commit -m "chore: snapshot AGH config seed"
dots git push
```

### Fresh-machine rebuild flow

```
1. Bootstrap dotfiles (curl install.sh)
2. chezmoi init  → prompts; one prompt fetches the age key from 1Password
3. chezmoi apply → installs age, decrypts seed, runs scripts 02-04:
                   - 02: installs AGH, copies seed to /Applications, restarts service
                   - 03: pmset always-on
                   - 04: AGH is already answering (because seeded), DNS flips to 127.0.0.1
4. Manual one-off:
   - Router DHCP: set Static DNS 1 → 192.168.1.185 (one click in Linksys UI)
   - iCloud Private Relay off (if reusing same Apple ID, already off)
   - Browser DoH off (per browser, per profile)
```

## Mac Mini Shoko + Jellyfin Anime

The anime stack — **Shoko Server** (Docker/Colima) → **Shokofin** plugin → **Jellyfin** —
and its full setup runbook (GUI *and* API procedures, the franchise-grouping setting, and
the gotchas that bite) live in **[`docs/shoko-jellyfin.md`](docs/shoko-jellyfin.md)**.

Chezmoi automates the infra only: `run_after_05` (Colima VM + Easystore mount),
`run_after_07` (Shoko container), `run_after_08` (Jellyfin keep-alive). The
Shoko/Shokofin/library configuration is stateful UI+DB setup and is documented in that
file rather than codified.

## Testing

Run tests to verify setup:
```bash
dots test                    # Via dots command
bash scripts/test.sh         # Direct execution
DOTFILES_CI=1 bash scripts/test.sh   # CI mode: skips checks that assume a fully bootstrapped machine
```

CI (GitHub Actions, on push/PR to `main`) runs on macOS, Ubuntu, and Windows:
each platform does an unmasked `chezmoi init → diff → apply
--exclude=scripts,externals → verify` (always with explicit `--source`; init
does not persist it) plus `test.sh` in CI mode. The lint job shellchecks all
`.sh` files at warning severity (blocking) and the rendered `.sh.tmpl`
scripts at error severity; a templates job renders every `.tmpl` with the
non-personal CI profile, so an ungated 1Password call fails the build.
`GITHUB_TOKEN` is exported workflow-wide for chezmoi's `gitHub*` template
functions.

An `ai-parity` job additionally runs `ai_parity.py verify` plus the engine's
unit tests (`unittest discover -s ai-parity/tests`), and each OS job runs
`test_chezmoi_deploy.py`, which applies only the generated parity source paths
into an isolated temporary home and checks the full deployed inventory, bytes,
modes, and a second idempotent apply.
