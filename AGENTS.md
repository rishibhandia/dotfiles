# Repository Agent Instructions (`chezmoi` Dotfiles)

This file is the entry point for **Codex**, **Antigravity (`agy`)**, and other
`AGENTS.md`-aware harnesses working in `~/.local/share/chezmoi`. The full
machine/infra runbook lives in [`CLAUDE.md`](CLAUDE.md), with architectural
walkthroughs in [`docs/dotfiles-walkthrough.md`](docs/dotfiles-walkthrough.md)
and [`docs/ai-parity-walkthrough.md`](docs/ai-parity-walkthrough.md).

## Core Commands

```bash
dots diff / dots apply            # Preview / deploy dotfiles to $HOME (human step)
dots test                         # Run setup verification tests (DOTFILES_CI=1 in CI)
dots ai status / diff / verify    # Inspect or verify AI parity state
dots ai sync --write              # Render canonical AI sources into chezmoi source only
```

## Multi-Harness AI Setup (Claude Code ↔ Codex ↔ Antigravity)

| Path | Role | Edit directly? |
|---|---|---|
| `ai-parity/shared/**` | Canonical cross-tool skills (`git-commit`, `keynote`, `llm-pdf-processing`, `matlab`, `matlab-runner`, `pdf-chunk`, `scientific-figures`, `smolvm-sandbox`, `zotero`) | **Yes** (then `dots ai sync --write`) |
| `ai-parity/adapters/**` | Codex/shared `SKILL.md` overrides, `agents/openai.yaml`, Codex-only skills (`pdf`, `verify`, `learned-patterns`) | **Yes** (then `dots ai sync --write`) |
| `ai-parity/contracts/**` | Shared `AGENTS.md`, Codex profiles, rules, and agents (`reviewer`, `debugger`, `git-commit`) | **Yes** (then `dots ai sync --write`) |
| `dot_codex/**`, `dot_agents/**`, migrated `dot_claude/skills/*` | Compiled parity outputs | **Never** (use `dots ai propose` for reverse intake) |
| `dot_gemini/config/**` | Antigravity (`agy`) global config: `skills.json` → `~/.agents/skills`, `rules/AGENTS.md.tmpl` → `contracts/AGENTS.md`, personal `mcp_config.json.tmpl`, pinned `plugins.json.tmpl` (`i-have-adhd`), `hooks.json.tmpl` + Python `PreToolUse` hooks | **Yes** |
| `dot_gemini/antigravity-cli/create_settings.json.tmpl` | Fresh-machine `agy` CLI settings seed (`create_` never overwrites existing machines) | **Yes** |
| `dot_claude/**` (non-migrated) | Legacy Claude-only config, agents, and `planned` skills | Only on explicit Claude request |

## Key Repository Rules

- **Strict `.personal` gating:** Personal-only MCPs (`tirith`, `smogon-vgc`, `superlogical`), skills (`zotero`, `keynote`), LiteParse, and 1Password calls must stay gated on `{{ if .personal }}` so work machines and non-personal CI templates never invoke them.
- **Runtime state stays unmanaged:** Never track or propose managing `~/.codex` runtime files (`config.toml`, sqlite, sessions, auth) or `~/.gemini` runtime files (`antigravity-cli/brain/`, `builtin/`, `antigravity/`, `antigravity-ide/`, OAuth/caches), or Rex's `$HOME`-local `rex skill setup` output.
- **Rex multiplexer (`dot_config/rex/init.lua`):** macOS-only (`.chezmoiignore`). `init.lua` only holds server-side keybindings, modes, custom actions, event hooks, and remote hosts (`rex.host`); themes/fonts live in Rex GUI Settings.
- **Windows compatibility:** `*.ps1.tmpl` must remain strictly ASCII (PowerShell 5.1 mis-decodes BOM-less UTF-8 em-dashes); JSON templates embedding Windows paths must backslash-escape (`replace "\\" "\\\\"`).
- **Parity commits & verification:** Stage canonical edits, regenerated outputs, and `ai-parity/generated-state.json` together (`.githooks/pre-commit` enforces `dots ai verify --staged`). Run `dots ai verify` and `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ai-parity/tests/test_ai_parity.py ai-parity/tests/test_chezmoi_deploy.py` before reporting parity work complete.
