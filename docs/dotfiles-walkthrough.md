# Dotfiles: Annotated Walkthrough

An annotated tour of this chezmoi repo — how a fresh machine becomes a
configured one, and where everything lives. Written against commit `897e14f`
(2026-07-16); line numbers will drift as files change. Companion document:
[`ai-parity-walkthrough.md`](ai-parity-walkthrough.md) for the Claude ↔ Codex
parity system.

## The chezmoi model in 30 seconds

Source files live here (`~/.local/share/chezmoi`); `chezmoi apply` renders
them into `$HOME`. Naming drives behavior: `dot_` → leading dot, `private_` →
0600, `encrypted_` → age-decrypted, `executable_` → +x, `literal_` → strip
attribute semantics, `.tmpl` → Go template rendered with the machine's data.
Scripts under `.chezmoiscripts/` *execute* during apply: `run_once_` once per
machine, `run_onchange_` when their rendered content changes, plain `run_` on
every apply (written to converge). `.chezmoiignore` uses **target** paths and
gates whole trees per OS/machine/flag.

## Bootstrap

- **macOS/Linux** — `install.sh` (curl-pipe from GitHub): Xcode CLT or distro
  build deps → Homebrew → chezmoi → `chezmoi init --apply rishibhandia` → 
  offer `op signin` and re-apply (secrets populate on the second pass) → zsh
  as default shell.
- **Windows** — `install.ps1`: **Scoop first** (critical: `.chezmoi.toml.tmpl`
  sets `portable=true` if Scoop is missing at init time, which permanently
  changes the machine's profile) → git → chezmoi → init → dot-source the
  PowerShell profile. `DOTFILES_PORTABLE=1` forces portable mode.

## The data layer: `.chezmoi.toml.tmpl`

Runs at `chezmoi init` and produces `~/.config/chezmoi/chezmoi.toml`. This is
the single decision point for the whole repo.

**Five flags** (defaults false): `personal`, `work`, `ephemeral`, `headless`,
`portable`.

**Machine detection** (lines 27–43): darwin machines are identified by
hardware where possible — `hw.model == "Mac17,7"` → `rishi-mbp-2025` (rename-
immune); the 2019 MBP and 2020 mini match on `scutil` ComputerName
substrings; `ubuntu` by hostname. Known hostnames → `personal=true`.
Containers/Codespaces/root users auto-set `ephemeral+headless` (22–26).
Unknown interactive machines get prompted; unknown non-interactive machines
(CI) default to `ephemeral+headless+work` so no 1Password/age call ever fires.

**What each flag gates:**

| Flag | Gates |
|---|---|
| `personal` | command-scoped 1Password API keys for `llm`, age encryption + key file, zotero/keynote skills, LiteParse, tirith MCP registration, lab-sync function |
| `work` | NYU email in git config; personal apps (1Password, tailscale, …) excluded from Brewfile/Scoopfile |
| `portable` (Windows) | GitHub-release externals instead of Scoop, psmux shell path, Astral uv installer, font install path |
| `ephemeral`/`headless` | skips prompts/secrets; CI profile |
| `hostname == rishi-macmini-2020` | the entire server stack (below) |

Also set here: `[interpreters.py]` → `uvx python` (chezmoi `.py` scripts run
under uv), `[onepassword] prompt=false`, `[age]` identity/recipient
(personal only), `[git] autoAdd=true, autoCommit=false`.

## Ignore rules, externals, shared templates

- **`.chezmoiignore`** — target-path gating: OS-foreign scripts and configs,
  mac-only/personal-only skills, mini-only files (LaunchAgents, AGH seed),
  the age key on non-personal/portable machines, repo-only files (`CLAUDE.md`,
  `docs/**`, `ai-parity/**`, `scripts`, `.githooks/**`), `**/__pycache__`,
  and a long `.codex/**` runtime-state blocklist (auth, sessions, sqlite,
  caches — never sourced from this repo).
- **`.chezmoiexternal.toml.tmpl`** — Windows-portable-only: ~15 CLI tools
  (rg, fd, bat, fzf, zoxide, starship, …) from GitHub releases into
  `~/.local/bin`, plus Hack Nerd Font (portable only — Scoop's font otherwise
  fights over the same HKCU registry names). `rtk.exe` is outside the
  portable gate (no Scoop manifest exists). Unix gets no externals — Brew
  covers everything. `uv.exe`/`uvx.exe` are deliberately excluded
  (file-locking during apply; installed via Scoop or Astral's installer).
- **`.chezmoitemplates/tmux-shared`** — one source of truth for tmux (Unix)
  and psmux (Windows) shared settings; included by both config templates.

## Packages

- **`dot_Brewfile.tmpl`** → `~/.Brewfile`. Categories: essentials, modern CLI
  replacements, utilities, archive tools, languages (uv, node, go, rustup),
  dev tools, AI/LLM (tirith via `sheeki03/tap`, rtk, llm). Gating: casks are
  darwin-only; `{{ if not .work }}` hides personal apps; `{{ if .personal }}`
  adds LiteParse; the mini hostname block adds jellyfin/colima/docker/fswatch.
  **Rule:** tap formulae must use fully-qualified `tap/formula` names —
  `brew bundle` resolves unqualified names against the startup index and
  fresh machines fail otherwise.
- **`dot_Scoopfile.tmpl`** → `~/.Scoopfile`, same categories/gating for
  Windows. Policy: Scoop exclusively — no npm/cargo/winget for CLI tools.
- Both install via `run_onchange` scripts keyed on the **rendered** file
  hash, so flag flips retrigger installs even without template edits.

## The apply pipeline (`.chezmoiscripts/`)

Subdirectory names are organizational only; order = phase, then alphabetical
target name (hence the `00`–`09` numbering). Platform gating lives *inside*
each template (non-matching hosts render empty scripts, which chezmoi skips).

macOS sequence:

1. `run_once_before_install-homebrew` — install brew; skips on ephemeral/root
   (a failing *before* script aborts the whole apply).
2. *(dotfiles land)*
3. `00-install-packages` (onchange) — `brew bundle`, then cleanup.
4. `01-install-cli-tools` (once) — Claude Code (with Rosetta-aware arch check
   that force-reinstalls a wrong-arch binary), Shell Sage, the rtk PreToolUse
   hook (`rtk init -g --auto-patch --hook-only`), vim-plug + headless
   PlugInstall; personal machines also register the tirith MCP (deliberately
   without `claude mcp list`, which can hang).
5. `02`–`09` — the Mac mini stack (all no-ops elsewhere; see below).
6. `darwin/` — macOS `defaults` (once), Ghostty as shell-script handler via
   duti (once), Backblaze exclusion-rules patcher (onchange; validates with
   xmllint, writes only on diff).

Windows sequence mirrors it: Scoop (before) → Scoopfile (onchange, hash
includes `.work`) → cli-tools (Claude Code via install.ps1→winget→npm
fallback; uv via Astral in portable mode; rtk run with stdin closed + 30 s
kill timeout because it has hung) → Windows Terminal theming (strips JSONC
comments for PS 5.1; its rewrite drops hand comments) → portable font
registration. WSL adds tmux/shell-sage/wslu, gated on `/proc/version`
actually containing "microsoft".

Two known quirks: the three `darwin/*.sh` scripts have no template gate (they
self-gate by content and run harmlessly elsewhere), and the Backblaze patcher
writes to `/Library/Backblaze.bzpkg/...` without sudo, relying on that dir
being world-writable.

## Shell environment

### zsh (macOS/Linux) — the primary shell

Load order: `~/.zshenv` (every zsh: XDG, `EDITOR=nvim`, history, brew
shellenv, `~/.local/bin`, **`ZDOTDIR=~/.config/zsh`** — the load-bearing
line) → macOS `path_helper` reorders PATH → `.zshrc` (interactive: re-runs
`brew shellenv` to undo path_helper, then navi → setopts → aliases →
`compinit` → `completion.zsh` → `scripts.zsh` → starship → autosuggestions →
syntax-highlighting → zoxide → fzf → **tirith last**).

Ordering constraints: the brew re-fix must precede anything using
`$HOMEBREW_PREFIX`; `compinit` must precede `scripts.zsh` (whose `dots`
completion calls `compdef`). Set `ZSH_DEBUG=1` to trace sourcing.

Secrets: personal machines deploy `~/.config/llm/secrets.env.op`, a mode-0600
file containing only 1Password references. The `llm` shell wrapper resolves
those references with `op run` for the lifetime of each command; API-key values
are not rendered into `.zshenv`. Non-personal machines do not deploy the
reference file, so the wrapper delegates to `llm`'s normal key resolution.

Key functions in `scripts.zsh.tmpl`: `dots` (the chezmoi wrapper —
`apply/diff/status/update/edit/add/cd/git/doctor/test/brew/ai`; `dots ai` →
`uv run ai_parity.py`; `dots brew add` auto-detects cask vs formula),
`extract`/`x` (20+ formats), `gcm` (AI commit messages from the staged diff),
`q`/`qv` (LLM Q&A over web pages / YouTube), `sheet2csv`, `pdf2text`
(LiteParse → Gemini fallback), `update`, `cb`, `mkcd`/`take`; gated: `agh`
(mini), `bbstatus` (darwin+personal), `sync_tise2` (personal, config from
1Password).

Aliases: interactive-only overrides (`cat→bat`, `top→btop`, `cp/mv/rm→-iv`,
`vim→nvim`) are guarded by `[[ -o interactive ]]` so scripts/agents are
unaffected; numbered dir-stack jumps `1`–`9`; `claude='caffeinate -s claude'`
(keeps the Mac awake during sessions); `mwin` (Ghostty + mosh + tmux).

### PowerShell (Windows)

`profile.ps1.tmpl`: PSReadLine prediction options version-gated (PS 5.1 ships
2.0 and would error), `~/.local/bin` added to the *persisted* User PATH with
exact-segment matching, starship/zoxide/navi/tirith init, `dots.ps1`
(PowerShell mirror of the zsh `dots`, alias `cz`), cross-shell helper
functions, and psmux auto-launch (skipped in existing sessions, VS Code, and
non-interactive shells). `dot_bashrc.tmpl`/`dot_bash_profile.tmpl` give Git
Bash the same basics; both are Windows-only.

## Tool configs

- **Neovim** — `dot_config/nvim/init.vim` (plain): vim-plug self-bootstraps
  via `stdpath('config')`; catppuccin, telescope (`<leader>ff`/`fg`),
  cheatsheet (`<leader>?`). Windows gets the identical file at
  `$LOCALAPPDATA/nvim` via `AppData/Local/nvim/init.vim.tmpl`, a one-line
  `include` of the Unix source.
- **tmux/psmux** — thin platform wrappers around `tmux-shared`. psmux picks
  its default shell by `.portable` (PowerShell 5.1 path vs Scoop pwsh shim).
- **Ghostty** — Hack Nerd Font, catppuccin-macchiato, launches
  `/bin/zsh -lc 'tmux new-session -A -s main'` (login shell so brew PATH
  works), `shift+enter` mapped for multi-line Claude Code input.
- **Starship** — near-default; the 2025 MBP ("Lambda") gets a `λ ❯` prompt
  character via a hostname-gated block.
- **Navi** — seven cheat files under `dot_local/share/navi/cheats/`; both
  shells export `NAVI_PATH` because navi's built-in default path varies by
  platform.
- Catppuccin Macchiato is repeated per-app (nvim, ghostty, Windows Terminal,
  PSReadLine) — each keeps its own palette copy.

## The Mac mini server stack (`rishi-macmini-2020`)

LAN DNS + anime media server; everything gated by hostname.

- **AdGuard Home** — installed by script `02` (vendor installer, sudo),
  seeded from an **age-encrypted** config
  (`dot_local/share/adguardhome-seed/encrypted_private_AdGuardHome.yaml.age`)
  so a rebuild boots configured; `03` sets `pmset` always-on; `04` (every
  apply) converges the mini's own resolver to `127.0.0.1` only after AGH
  answers. LAN vs roaming DNS design and troubleshooting: repo `CLAUDE.md`.
- **Colima/Docker** — `05` starts the VM (4 CPU / 6 GiB, Easystore mounted
  read-only); never deletes an existing VM (named volumes!). LaunchAgent
  `com.rishi.colima.plist` pins `COLIMA_HOME` (flaky XDG detection in 0.10.x).
- **Shoko** — `07` writes a docker-compose and brings up the container
  (media bind-mounted at the *identical host path* so Shokofin symlinks
  resolve; data in the `shoko-config` named volume; fast-path exit when
  converged). Runbook: [`shoko-jellyfin.md`](shoko-jellyfin.md).
- **Tailscale Serve** — `06`: Jellyfin `:8443` (dedicated port because
  Jellyfin double-prefixes BaseUrl on redirects), Shoko `:8111`, Showtime
  `/showtime`.
- **LaunchAgents** — jellyfin keep-alive (drives the real `.app` via `open`
  to preserve TCC media access; covers the in-app "Restart"), shoko-import
  (`fswatch` on the host because virtiofs doesn't forward FS events into the
  VM; API key read at runtime from `~/.config/shoko/apikey`, kept off the
  repo), tagorganizer (weekly; calls `bash` not `uv run` — uv's pre-flight
  stalls under launchd).

## Secrets

1Password is the source of truth; nothing secret is committed. Four
mechanisms: command-scoped `op run` injection for LLM API keys; template-time
`onepassword*` calls (git identity, lab sync config, and the age private key via
`dot_config/private_age/private_key.txt.tmpl`), **age encryption** for whole
files (the AGH seed; `chezmoi add --encrypt`), and runtime reads (the Shoko
API key file). Non-personal/ephemeral profiles never invoke `op` — the age
key and secret-bearing templates are ignore-gated.

## AI tooling

- **`dot_claude/`** — `create_settings.json.tmpl` (the `create_` prefix means
  it only lands if missing — template changes need a delete + re-apply):
  plan-by-default, permission allow/deny/ask lists per OS (git push is an
  *ask* rule since hooks can't prompt), and two inline hooks — block
  arbitrary `.md`/`.txt` writes (PreToolUse on Write) and console.log
  warnings (PostToolUse). Plus 11 agents, ~36 skills (six of them
  parity-generated), the `learned/` note collection, and dual statusline
  scripts (context % / rate-limit % / git status).
- **`dot_codex/`** + **`dot_agents/`** — entirely generated: Codex global
  AGENTS.md, `careful-review` profile, reviewer/debugger subagents,
  `ai-parity.rules` (blocks `git reset --hard` / `push --force`), and the
  Codex skills tree with `agents/openai.yaml` interface files.
- Ownership rules, commands, and recovery: see
  [`ai-parity-walkthrough.md`](ai-parity-walkthrough.md).

## Testing & CI

`dots test` → `scripts/test.sh` (or `test.ps1`): commands, structure, env,
git identity, brew/scoop health, chezmoi state; `DOTFILES_CI=1` softens
machine-specific checks. GitHub Actions (`.github/workflows/test.yml`): three
OS jobs (init → parity deploy test → diff → apply/verify excluding
scripts+externals → test.sh), a lint job (shellcheck on sources at warning
severity, on *rendered* templates at error severity), a templates job
(renders every `.tmpl` with the non-personal CI profile — an ungated
1Password call fails the build), and an `ai-parity` job per OS
(`verify` + the 55-test suite). `GITHUB_TOKEN` is exported workflow-wide for
chezmoi's `gitHub*` template functions.

## Gotchas index

1. `include` paths in templates use the actual **source** filename, and
   chezmoi-native files (`.chezmoi*.toml.tmpl`) never take a `dot_` prefix.
2. `create_` files don't propagate template updates to existing machines.
3. Scoop must exist before `chezmoi init` on Windows, or the machine is
   permanently profiled portable (re-run `chezmoi init` to fix).
4. Never `colima delete` casually — Docker named volumes (Shoko's DB) die.
5. Tap formulae need fully-qualified names in the Brewfile.
6. `*.ps1.tmpl` must stay ASCII (PS 5.1 misdecodes BOM-less UTF-8; em-dashes
   break parsing).
7. `.chezmoiignore` matches **target** paths, not source names.
8. rtk rewrites common commands for Claude Code; bypass one command with
   `git -P …` or piping through `cat` (there is no disable env var).
