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
| `dot_config/tmux/tmux.conf.tmpl` | `~/.config/tmux/tmux.conf` | Tmux configuration |

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
- `run_onchange_after_install-packages.sh.tmpl` - Installs Brewfile packages (when Brewfile changes)
- `darwin/run_once_after_configure-macos.sh` - Configures macOS preferences

### Package Management
- `dot_Brewfile` → `~/.Brewfile` - Homebrew packages for macOS/Linux
- Packages auto-install when Brewfile changes via `run_onchange` script

## Testing

Run tests to verify setup:
```bash
dots test                    # Via dots command
bash scripts/test.sh         # Direct execution
```

CI runs on GitHub Actions for macOS, Ubuntu, and Windows on every push.
