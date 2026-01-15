# Dotfiles

Cross-platform dotfiles managed with [chezmoi](https://chezmoi.io/). Supports macOS, Linux, and Windows.

## Quick Start

### macOS / Linux

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.sh)"
```

### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex
```

The install script will:
1. Install Xcode CLI tools (macOS) or build dependencies (Linux)
2. Install Homebrew
3. Install chezmoi
4. Clone and apply dotfiles
5. Install all packages from Brewfile
6. Set zsh as default shell

## Repository Structure

```
.
├── .chezmoi.toml.tmpl          # Machine detection & feature flags
├── .chezmoiscripts/            # Auto-run scripts during apply
│   ├── run_once_before_install-homebrew.sh.tmpl
│   ├── run_onchange_after_install-packages.sh.tmpl
│   └── darwin/run_once_after_configure-macos.sh
├── .chezmoitemplates/          # Reusable template snippets
├── dot_Brewfile                # Homebrew packages → ~/.Brewfile
├── dot_zshenv.tmpl             # Environment variables → ~/.zshenv
├── dot_config/
│   ├── ghostty/                # Terminal emulator config
│   ├── git/                    # Git config & ignore
│   ├── nvim/                   # Neovim configuration
│   ├── starship/               # Cross-shell prompt
│   ├── tmux/                   # Terminal multiplexer
│   └── zsh/                    # Shell config, aliases, functions
├── dot_local/share/navi/       # Interactive cheatsheets
├── dot_claude/                 # Claude Code settings
├── install.sh                  # Bootstrap script (macOS/Linux)
├── install.ps1                 # Bootstrap script (Windows)
└── scripts/test.sh             # Setup verification tests
```

### Chezmoi Naming Conventions

| Prefix/Suffix | Meaning |
|---------------|---------|
| `dot_` | Creates dotfile (e.g., `dot_zshrc` → `~/.zshrc`) |
| `private_` | Sets 600 permissions |
| `executable_` | Sets executable bit |
| `.tmpl` | Processed as Go template |
| `run_once_` | Script runs once per machine |
| `run_onchange_` | Script runs when content changes |

## Tools Installed

### CLI Essentials
| Tool | Description |
|------|-------------|
| [chezmoi](https://chezmoi.io/) | Dotfiles manager |
| [zsh](https://www.zsh.org/) | Shell |
| [starship](https://starship.rs/) | Cross-shell prompt |
| [neovim](https://neovim.io/) | Text editor |
| [tmux](https://github.com/tmux/tmux) | Terminal multiplexer |

### Modern CLI Replacements
| Tool | Replaces | Description |
|------|----------|-------------|
| [bat](https://github.com/sharkdp/bat) | cat | Syntax highlighting |
| [lsd](https://github.com/lsd-rs/lsd) | ls | Icons and colors |
| [fd](https://github.com/sharkdp/fd) | find | Simpler syntax |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | grep | Faster search |
| [broot](https://dystroy.org/broot/) | tree | Interactive navigator |
| [btop](https://github.com/aristocratos/btop) | top/htop | Resource monitor |
| [zoxide](https://github.com/ajeetdsouza/zoxide) | cd | Smart directory jumping |
| [duf](https://github.com/muesli/duf) | df | Disk usage |
| [tldr](https://tldr.sh/) | man | Simplified help |

### Utilities
| Tool | Description |
|------|-------------|
| [fzf](https://github.com/junegunn/fzf) | Fuzzy finder |
| [jq](https://jqlang.github.io/jq/) | JSON processor |
| [yq](https://github.com/mikefarah/yq) | YAML processor |
| [navi](https://github.com/denisidoro/navi) | Interactive cheatsheet |
| [rclone](https://rclone.org/) | Cloud storage sync |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Video downloader |

### Development
| Tool | Description |
|------|-------------|
| [uv](https://github.com/astral-sh/uv) | Fast Python package manager |
| [node](https://nodejs.org/) | Node.js runtime |
| [go](https://go.dev/) | Go language |
| [rustup](https://rustup.rs/) | Rust toolchain |
| [gh](https://cli.github.com/) | GitHub CLI |
| [ruff](https://github.com/astral-sh/ruff) | Python linter |
| [shellcheck](https://www.shellcheck.net/) | Shell linter |

### AI/LLM
| Tool | Description |
|------|-------------|
| [llm](https://llm.datasette.io/) | CLI for LLMs |
| [Ollama](https://ollama.ai/) | Local LLM runtime |

### macOS Apps (Casks)
| App | Description |
|-----|-------------|
| [Ghostty](https://ghostty.org/) | GPU-accelerated terminal |
| [Zed](https://zed.dev/) | Code editor |
| [1Password](https://1password.com/) | Password manager |
| [Logseq](https://logseq.com/) | Note taking / PKM |
| [Tailscale](https://tailscale.com/) | VPN/mesh network |
| [MPV](https://mpv.io/) | Video player |
| [Skim](https://skim-app.sourceforge.io/) | PDF reader |

### Fonts
- Hack Nerd Font
- Meslo LG Nerd Font

## Common Commands

The `dots` command provides shortcuts for common operations:

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

## Custom Shell Functions

Defined in `dot_config/zsh/scripts.zsh`:

| Function | Description |
|----------|-------------|
| `extract` / `x` | Universal archive extractor (20+ formats) |
| `gcm` | AI-powered git commit message generator |
| `q` / `qv` | Ask questions about web pages or YouTube videos |
| `sheet2csv` | Extract spreadsheet data from images using AI |
| `pdf2text` | Extract text from PDFs using AI |

## Machine Configuration

The `.chezmoi.toml.tmpl` template detects machines by hostname and sets feature flags:

| Flag | Purpose |
|------|---------|
| `personal` | Personal machines (enables secrets via 1Password) |
| `work` | Work machines |
| `ephemeral` | Temporary/cloud environments |
| `headless` | Machines without display |

## Testing

Verify setup with:

```bash
dots test              # Via dots command
bash scripts/test.sh   # Direct execution
```

CI runs on GitHub Actions for macOS, Ubuntu, and Windows.

## License

MIT
