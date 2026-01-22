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
- `dot_Scoopfile` → `~/.Scoopfile` - Scoop packages for Windows
- Packages auto-install when package files change via `run_onchange` scripts

### Claude Code Skills
Skills are synced via chezmoi to `~/.claude/skills/`. Included skills:
- **pdf** - PDF manipulation and form extraction
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

## Testing

Run tests to verify setup:
```bash
dots test                    # Via dots command
bash scripts/test.sh         # Direct execution
```

CI runs on GitHub Actions for macOS, Ubuntu, and Windows on every push.

## Development Rules

These rules are enforced by the agents and skills configured in this dotfiles repo.

### Security

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data

**Secret Management:**
```typescript
// NEVER: Hardcoded secrets
const apiKey = "sk-proj-xxxxx"

// ALWAYS: Environment variables
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

**Security Response Protocol:** If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues

### Coding Style

**Immutability (CRITICAL)** - ALWAYS create new objects, NEVER mutate:
```javascript
// WRONG: Mutation
function updateUser(user, name) {
  user.name = name  // MUTATION!
  return user
}

// CORRECT: Immutability
function updateUser(user, name) {
  return { ...user, name }
}
```

**File Organization:**
- MANY SMALL FILES > FEW LARGE FILES
- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Functions < 50 lines
- Nesting depth < 4 levels
- Extract utilities from large components

**Error Handling** - ALWAYS handle errors comprehensively:
```typescript
try {
  const result = await riskyOperation()
  return result
} catch (error) {
  console.error('Operation failed:', error)
  throw new Error('Detailed user-friendly message')
}
```

**Input Validation** - ALWAYS validate user input:
```typescript
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})

const validated = schema.parse(input)
```

### Testing Requirements

**Minimum Test Coverage: 80%**

Test Types (ALL required):
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows (Playwright)

**Test-Driven Development (MANDATORY workflow):**
1. Write test first (RED)
2. Run test - it should FAIL
3. Write minimal implementation (GREEN)
4. Run test - it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (80%+)

**Agent Support:**
- **tdd-guide** - Use PROACTIVELY for new features
- **e2e-runner** - Playwright E2E testing specialist

### Git Workflow

**Commit Message Format:**
```
<type>: <description>

<optional body>
```
Types: feat, fix, refactor, docs, test, chore, perf, ci

**Feature Implementation Workflow:**
1. **Plan First** - Use `/plan` to create implementation plan
2. **TDD Approach** - Use `/tdd` for test-driven development
3. **Code Review** - Use `/code-review` immediately after writing code
4. **Commit & Push** - Detailed messages, conventional commits format

### Performance (Model Selection)

**Haiku** (90% of Sonnet capability, 3x cost savings):
- Lightweight agents with frequent invocation
- Pair programming and code generation
- Worker agents in multi-agent systems

**Sonnet** (Best coding model):
- Main development work
- Orchestrating multi-agent workflows
- Complex coding tasks

**Opus** (Deepest reasoning):
- Complex architectural decisions
- Maximum reasoning requirements
- Research and analysis tasks

**Build Troubleshooting:** If build fails, use `/build-fix`

### Common Patterns

**API Response Format:**
```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: { total: number; page: number; limit: number }
}
```

**Custom Hooks Pattern:**
```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
}
```

**Repository Pattern:**
```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
}
```

### Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `planner` | Implementation planning | Starting new features, architectural changes |
| `architect` | System design | Planning features, making architectural decisions |
| `tdd-guide` | Test-driven development | Writing new features, fixing bugs |
| `code-reviewer` | Quality & security review | After writing/modifying code |
| `security-reviewer` | Vulnerability detection | Code handling auth, user input, sensitive data |
| `build-error-resolver` | Fix build errors | When build fails or type errors occur |
| `e2e-runner` | Playwright testing | Testing critical user flows |
| `refactor-cleaner` | Dead code removal | Cleaning up unused code |
| `doc-updater` | Documentation sync | Updating codemaps and docs |

### Available Skills (Commands)

| Command | Purpose |
|---------|---------|
| `/plan` | Create implementation plan before coding |
| `/tdd` | TDD workflow (red-green-refactor) |
| `/code-review` | Quality assessment on git diff |
| `/build-fix` | Fix compilation/type errors |
| `/e2e` | Generate Playwright tests |
| `/refactor-clean` | Remove dead code |
| `/verify` | Run verification checks |
| `/checkpoint` | Save/verify workflow state |
| `/learn` | Extract patterns mid-session |
| `/eval` | Evaluation harness |
| `/orchestrate` | Workflow orchestration |
| `/test-coverage` | Coverage analysis |
| `/update-codemaps` | Codebase mapping |
| `/update-docs` | Documentation sync |
