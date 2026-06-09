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
- **`include` paths use the actual source filename**, not the target name. For example, `.chezmoiexternal.toml.tmpl` is included as `{{ include ".chezmoiexternal.toml.tmpl" }}`, not `dot_chezmoiexternal.toml.tmpl`. The `dot_` prefix is only for files that chezmoi renames when applying to the home directory; chezmoi-native config files (`.chezmoi*.toml.tmpl`, `.chezmoiignore`, etc.) already start with a dot and don't use `dot_`.

### Template System
The main configuration template `.chezmoi.toml.tmpl` defines:
- **Machine detection**: Identifies specific machines by a stable signal — MacBook Pro 14" M5 Max (`Mac17,7`) → `rishi-mbp-2025` via hardware model; MacBook Pro 2019 and Mac Mini 2020 via ComputerName; Ubuntu via hostname
- **Feature flags**: `ephemeral`, `work`, `headless`, `personal` for conditional configuration
- **1Password integration**: API keys and secrets retrieved via `onepassword` template function

### Key Configuration Files
| Source Path | Target | Purpose |
|-------------|--------|---------|
| `private_dot_zshenv.tmpl` | `~/.zshenv` | Environment variables, XDG paths, API keys |
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

### Security Tools
- **tirith** - Terminal security tool that guards against URL/ANSI injection attacks
  - macOS: Installed via Homebrew tap as `sheeki03/tap/tirith` (see "Tap-based formulae" rule above)
  - Windows: Installed via Scoop (`scoop bucket add tirith https://github.com/sheeki03/scoop-tirith && scoop install tirith`)
  - Initialized in shell via `eval "$(tirith init)"` (zsh) or `Invoke-Expression (& tirith init powershell)` (PowerShell)
  - **Claude Code MCP**: Registered user-scope on personal machines by the `run_once_after_01-install-cli-tools` scripts via `claude mcp add --scope user tirith -- tirith mcp-server` (a `mcpServers` key in settings.json is NOT honored by Claude Code) — provides `tirith_check_command`, `tirith_check_url`, `tirith_scan_file`, etc.

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
- `run_after_06-tailscale-serve-jellyfin.sh.tmpl` - Exposes Jellyfin over Tailscale Serve at `https://<mini>.<tailnet>.ts.net:8443` — gated to `rishi-macmini-2020`. Uses a dedicated HTTPS port instead of a path mount: Jellyfin double-prefixes its `BaseUrl` on redirects (e.g. `/jellyfin/System/Info/Public` → `/jellyfin/jellyfin/web/`), which browsers tolerate but native mobile apps don't. Requires the mini to already be logged into a tailnet; otherwise the script logs a notice and retries on the next apply.
- `run_after_07-install-shoko.sh.tmpl` - Runs **Shoko Server** as a Docker container (`ghcr.io/shokoanime/server`) on Colima — gated to `rishi-macmini-2020`. Shoko is the anime metadata/organization backend for Jellyfin's Shokofin plugin. Writes `~/.config/shoko/docker-compose.yml` then `docker compose up -d`. The anime drive is bind-mounted at its identical host path (`/Volumes/Easystore/Movies & Shows`, read-only) so Shokofin's host-side symlinks resolve without remapping; Shoko's own data lives in the `shoko-config` Docker named volume. API/UI on `127.0.0.1:8111` (localhost-only). Runs on every apply with a converged fast-path (compose unchanged + Shoko answering); also wires `~/.docker/config.json`'s `cliPluginsExtraDirs` so the brew docker CLI finds the Compose v2 plugin. See `docs/shoko-jellyfin.md` for the manual UI/API steps.
- `run_after_08-jellyfin-keepalive.sh.tmpl` - Loads a LaunchAgent (`~/Library/LaunchAgents/com.rishi.jellyfin.plist`) that watchdogs Jellyfin and relaunches it if it goes down — crash, reboot, or the macOS app's in-app "Restart" (which otherwise stops the server without relaunching) — gated to `rishi-macmini-2020`. Drives the real `.app` via `open` to keep its macOS file-access (TCC) permission to the external media drive.

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

### Claude Code Skills
Skills are synced via chezmoi to `~/.claude/skills/`. Included skills, by category:

**Documents & files:** `pdf`, `pdf-chunk` (large PDFs without filling context), `xlsx`, `pptx`, `docx`, `doc-coauthoring`, `theme-factory`

**Development workflow:** `plan`, `tdd`, `code-review`, `build-fix`, `verify`, `checkpoint`, `e2e`, `eval`, `test-coverage`, `refactor-clean`, `orchestrate`, `update-codemaps`, `update-docs`, `learn`, `session-wrap`, `skill-creator`

**Research & science:** `academic-review` (papers/proposals review), `matlab` (R2025a patterns + the personal `+thz` package), `matlab-runner` (headless script execution), `zotero` (local-library citation lookup; **personal machines only**)

**macOS app integrations (darwin-only via `.chezmoiignore`):** `things` (Things 3), `fantastical` (calendar), `keynote` (presentations; **also personal-only**)

**Adding more skills from the marketplace:**
```
/plugin marketplace add anthropics/skills              # Register marketplace (one-time)
/plugin install example-skills@anthropic-agent-skills  # Install a bundle
```

**Custom skills:** Create a folder with a `SKILL.md` file containing YAML frontmatter (`name`, `description`) and markdown instructions. Add to `dot_claude/skills/` in this repo.

### Learned Skills
Extracted patterns and project-specific knowledge live in `dot_claude/skills/learned/` and sync via chezmoi to `~/.claude/skills/learned/`. These are reference files (not invocable commands) created by the `/learn` skill during sessions.

**Important:** After `/learn` creates a new file in `~/.claude/skills/learned/`, it must be explicitly added to chezmoi and committed to sync across machines:
```bash
dots add ~/.claude/skills/learned/<new-file>.md
dots git add -A && dots git commit -m "feat: add learned skill <name>"
dots git push
```

Current learned files:
- **andor-sdk-dll-lifecycle.md** — Never force-kill Python holding Andor SDK handles (`atmcd64d.dll` / `ShamrockCIF.dll`); avoids `DRV_NOT_AVAILABLE` DLL lockups
- **windows-phantom-usb-devices.md** — Recovering Andor USB instruments that show as phantom (`CM_PROB_PHANTOM`) devices in Windows Device Manager
- **mockobject-attribute-getattr-trap.md** — Python mock `__getattr__` trap
- **qt-test-window-close-blocking-shutdown.md** — Qt test window close blocking shutdown
- **powershell-utf8-bom-em-dash.md** — ASCII-only in `*.ps1.tmpl`: PowerShell 5.1 mis-decodes UTF-8 without BOM and em-dashes break parsing

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
- [ ] DHCP Reservation pinning the mini's MAC → `192.168.1.185` — Connectivity → Local Network → DHCP Reservations
- [ ] Static DNS 1 = `192.168.1.185`, DNS 2 + 3 empty — same screen, DHCP Server section. Use the *web UI* at `http://192.168.1.1`; the Linksys app hides this field on Hydra firmware

**Per-Apple-ID** — apply to the iCloud account, not to chezmoi
- [ ] iCloud Private Relay off — Settings → [your name] → iCloud → Private Relay → Off. (Otherwise Safari bypasses local DNS for HTTPS.)

**Per-browser** — app-internal preference, gets clobbered if chezmoi'd
- [ ] Chrome: Settings → Privacy & Security → "Use secure DNS" → Off (or "With current service provider"). DoH inside Chrome bypasses the system resolver.
- [ ] Firefox: Settings → Privacy & Security → "DNS over HTTPS" → "Off"
- [ ] Edge: similar to Chrome — Settings → Privacy → "Use secure DNS" → Off

**Per-device on the LAN** — usually nothing required (DHCP hands DNS out to clients), but force a lease renewal after the router DHCP change so devices pick up the new DNS server right away.

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
