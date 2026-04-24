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
- **Machine detection**: Identifies specific machines (MacBook Pro 2019, Mac Mini 2020, Ubuntu) by hostname
- **Feature flags**: `ephemeral`, `work`, `headless`, `personal` for conditional configuration
- **1Password integration**: API keys and secrets retrieved via `onepassword` template function
- **CPU detection**: Cross-platform CPU info via `.chezmoitemplates/cpu`

### Key Configuration Files
| Source Path | Target | Purpose |
|-------------|--------|---------|
| `dot_zshenv.tmpl` | `~/.zshenv` | Environment variables, XDG paths, API keys |
| `dot_config/zsh/dot_zshrc` | `~/.config/zsh/.zshrc` | Main shell config, history, completions |
| `dot_config/zsh/scripts.zsh` | `~/.config/zsh/scripts.zsh` | Custom shell functions |
| `dot_config/zsh/aliases/aliases` | `~/.config/zsh/aliases/aliases` | Shell aliases |
| `dot_config/git/config.tmpl` | `~/.config/git/config` | Git user config (templated email) |
| `dot_config/nvim/init.vim` | `~/.config/nvim/init.vim` | Neovim configuration |
| `dot_config/tmux/tmux.conf.tmpl` | `~/.config/tmux/tmux.conf` | Tmux configuration (macOS/Linux) |
| `dot_config/psmux/psmux.conf.tmpl` | `~/.config/psmux/psmux.conf` | psmux configuration (Windows) |

### XDG Directory Structure
This repo follows XDG Base Directory spec:
- `XDG_CONFIG_HOME` = `~/.config`
- `ZDOTDIR` = `~/.config/zsh` (zsh files in config, not home)

### Notable Shell Functions (in `scripts.zsh`)
- `dots()` - Dotfiles management command (see Common Commands above)
- `extract()` / `x` - Universal archive extractor (20+ formats)
- `gcm()` - AI-powered git commit message generator using LLM
- `q()` / `qv()` - Ask questions about web pages or YouTube videos via LLM
- `sheet2csv()` - Extract spreadsheet data from images using Gemini AI
- `pdf2text()` - Extract text from PDFs using Gemini AI

### Neovim Configuration (`dot_config/nvim/init.vim`)
- **Plugin manager**: vim-plug — auto-installs on first launch if missing
- **Plugins**: catppuccin theme, telescope.nvim (fuzzy finder), cheatsheet.nvim
- **Key bindings**:
  - `<leader>?` — open cheatsheet browser (via cheatsheet.nvim + telescope)
  - `<leader>ff` — fuzzy file finder (telescope)
  - `<leader>fg` — live grep (telescope)
- **New machine setup**: `run_once_after_01` scripts run `nvim --headless +PlugInstall` on both macOS/Linux and Windows
- **Windows paths**: Uses `$LOCALAPPDATA/nvim` instead of `$XDG_CONFIG_HOME/nvim`
- Add custom cheatsheets at `~/.config/nvim/cheatsheet.txt` (format: `## Section` + `command | description`)

### Terminal Multiplexer (tmux / psmux)
- **tmux** (macOS/Linux) and **psmux** (Windows) share configuration via `.chezmoitemplates/tmux-shared`
- Shared settings (mouse, vi keys, status bar, keybindings) live in the template; platform-specific settings live in each config file
- Edit `.chezmoitemplates/tmux-shared` to change settings for both platforms at once
- tmux config adds Unix-specific terminal settings (`default-terminal`, `terminal-overrides`, `allow-passthrough`)
- psmux auto-launches on PowerShell terminal open (attaches to `main` session or creates one); skipped inside existing sessions, VS Code, and non-interactive contexts
- **psmux installation**: Via Scoop when available, otherwise portable binary from GitHub releases to `~/.local/bin/psmux/` (installed by `run_once_after_01-install-cli-tools.ps1.tmpl`)

### Security Tools
- **tirith** - Terminal security tool that guards against URL/ANSI injection attacks
  - macOS: Installed via Homebrew tap (`brew install sheeki03/tap/tirith`) — use fully qualified name in Brewfile
  - Windows: Installed via Scoop (`scoop bucket add tirith https://github.com/sheeki03/scoop-tirith && scoop install tirith`)
  - Initialized in shell via `eval "$(tirith init)"` (zsh) or `Invoke-Expression (& tirith init powershell)` (PowerShell)
  - **Claude Code MCP**: Registered as MCP server on personal machines (`settings.json.tmpl`) — provides `tirith_check_command`, `tirith_check_url`, `tirith_scan_file`, etc.

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
- `run_onchange_after_install-packages.sh.tmpl` - Installs Brewfile/Scoopfile packages (when package files change)
- `run_once_after_01-install-cli-tools.sh.tmpl` - Installs Claude Code, Shell Sage, nvim plugins (macOS/Linux)
- `windows/run_once_after_01-install-cli-tools.ps1.tmpl` - Installs Claude Code, Tirith, psmux, nvim plugins (Windows)
- `darwin/run_once_after_configure-macos.sh` - Configures macOS preferences

### Windows Portable Mode (`.chezmoiexternal.toml.tmpl`)
Fallback for Windows machines where Scoop is unavailable (`.portable = true`). Downloads pre-built binaries directly from GitHub releases to `~/.local/bin`, which is added to PATH in the PowerShell profile. Covers: rg, fd, bat, fzf, zoxide, starship, lsd, jq, yq, gh, duf, fastfetch, uv, uvx, ruff. Note: nvim, navi, and tirith are NOT included in portable mode.

### Package Management
- `dot_Brewfile` → `~/.Brewfile` - Homebrew packages for macOS/Linux
- `dot_Scoopfile` → `~/.Scoopfile` - Scoop packages for Windows
- Packages auto-install when package files change via `run_onchange` scripts

**Windows package manager policy:** Use Scoop exclusively. Do not use npm, cargo, winget, or other package managers as alternatives for CLI tools.

### Claude Code Skills
Skills are synced via chezmoi to `~/.claude/skills/`. Included skills:
- **pdf** - PDF manipulation and form extraction
- **pdf-chunk** - Handle large PDFs without filling context (selective page extraction)
- **xlsx** - Excel spreadsheet creation
- **pptx** - PowerPoint presentations
- **docx** - Word document creation
- **skill-creator** - Create new custom skills
- **theme-factory** - Generate color themes
- **doc-coauthoring** - Document collaboration

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
- **matlab.md** — MATLAB R2025a best practices (polar plots, color lightening, region highlighting, error bounds, varargin)
- **matlab-style-guide.md** — MATLAB coding style conventions
- **matlab-performance.md** — MATLAB performance patterns
- **matlab-color-lightening.md** — `brighten()` usage, avoiding nonexistent `lighten()`
- **matlab-datatable-row-vector-convention.md** — Row vector conventions in data tables
- **matlab-disc-ft-nfft-sizing.md** — Discrete FT NFFT sizing
- **matlab-plot-region-highlighting.md** — Region highlighting with `patch()`
- **matlab-polar-in-tiledlayout.md** — Polar axes workaround inside `tiledlayout`
- **matlab-shg-normalization.md** — SHG normalization patterns
- **mockobject-attribute-getattr-trap.md** — Python mock `__getattr__` trap
- **qt-test-window-close-blocking-shutdown.md** — Qt test window close blocking shutdown

## Testing

Run tests to verify setup:
```bash
dots test                    # Via dots command
bash scripts/test.sh         # Direct execution
```

CI runs on GitHub Actions for macOS, Ubuntu, and Windows on every push.
