# Global Claude Code Rules

This file provides global guidance to Claude Code across all projects. It is loaded from `~/.claude/CLAUDE.md`.

Project-specific CLAUDE.md files in individual repositories will be loaded in addition to this global configuration.

## Development Rules

These rules are enforced by the agents and skills configured in this dotfiles setup.

### Development Workflow

**ALWAYS break plans into atomic commits.** When planning any change, first identify the atomic commits that will be created, then execute each commit using this workflow:

**Per-Commit Workflow:**
1. **Orchestrate** - Use `/orchestrate` to coordinate the work for this commit
2. **Review** - Use `/architect` to review the source module(s) being changed
3. **Write Tests** - Use **tdd-guide** agent to write tests first (RED phase)
4. **Verify Failure** - Run tests to confirm they fail appropriately
5. **Implement** - Write minimal code to make tests pass (GREEN phase)
6. **Fix Issues** - Resolve any problems found
7. **Commit** - Use `/git-commit` to create the atomic commit
8. **Debug** - Use `/debugger` if tests fail unexpectedly

**Planning Example:**
```
Task: "Add user authentication"

Atomic Commits:
1. Add User model and migration
2. Add password hashing utility
3. Add login endpoint with tests
4. Add logout endpoint with tests
5. Add auth middleware
6. Integrate middleware with protected routes

For each commit → follow Per-Commit Workflow above
```

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

### Python Package Management

**ALWAYS use `uv` instead of `pip`** for Python package operations:

```bash
# NEVER: pip install
pip install package-name

# ALWAYS: uv
uv pip install package-name          # If in a venv
uv pip install --system package-name # System-wide (if needed)
uvx package-name                     # Run tools without installing
```

**For scripts with dependencies**, use inline script metadata:
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests", "rich"]
# ///

import requests
from rich import print
```

This allows scripts to auto-install dependencies on first run without manual setup.

### Python Project Creation

**Use Copier with cookiecutter-uv template** for new Python projects:

```bash
# Create new project
uvx copier copy gh:fpgmaas/cookiecutter-uv my-project

# Update existing project when template improves
cd my-project
uvx copier update
```

**Why Copier over Cookiecutter:**
- `copier update` pulls template improvements into existing projects
- Saves answers in `.copier-answers.yml` for reproducibility
- Supports version-aware migrations between template versions

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

### Debugging

**When implementation fails or tests don't pass**, use systematic debugging:

1. **Don't shotgun debug** - Avoid random fix attempts
2. **Gather evidence** - Read error messages, logs, and relevant code
3. **Form hypotheses** - Rank possible causes by likelihood
4. **Create fix plan** - Document root cause and solution before coding
5. **Verify fix** - Ensure the fix addresses root cause, not symptoms

**Agent Support:**
- **debugger** - Use PROACTIVELY after first implementation attempt fails

### Git Workflow

**Atomic Commits (CRITICAL)** - Each commit should be ONE logical unit of change:

The "AND" Test: If your commit message needs "and", split it into multiple commits.

```bash
# BAD: Monolithic commit
git commit -m "fix: login bug and add logout button and update styles"

# GOOD: Atomic commits
git commit -m "fix: prevent null pointer in login validation"
git commit -m "feat: add logout button to navbar"
git commit -m "style: update button hover states"
```

**What to Split Into Separate Commits:**
| Don't Combine | Split Into |
|---------------|------------|
| Fix bug A + Fix bug B | 2 commits (one per bug) |
| Remove dead code + Add feature | 2 commits (cleanup, then feature) |
| Refactor + New functionality | 2 commits (refactor first, then feature) |
| Formatting + Logic changes | 2 commits (format first, then logic) |
| Multiple unrelated file changes | Separate by concern |

**Valid Atomic Commits:**
- Fix a specific bug
- Add one user-facing feature
- Update a single dependency
- Refactor one module (no behavior change)
- Add/update tests for one feature

**Atomic Commit Checklist:**
- [ ] Commit does exactly ONE thing
- [ ] Tests pass after this commit
- [ ] Could revert this commit without side effects
- [ ] Message doesn't need "and" to describe changes
- [ ] Doesn't mix refactoring with new features

**Commit Message Format:**
```
<type>: <description>

<optional body explaining WHY, not WHAT>
```
Types: feat, fix, refactor, docs, test, chore, perf, ci, style

**Feature Implementation Workflow:**
1. **Plan First** - Break feature into atomic sub-tasks
2. **TDD Approach** - Write test, commit; implement, commit
3. **One Concern Per Commit** - Resist bundling changes
4. **Code Review** - Use `/code-review` before final push
5. **Interactive Staging** - Use `git add -p` to separate mixed changes

**Agent Support:**
- **git-commit** - Use PROACTIVELY before committing to ensure atomic commits

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
| `git-commit` | Atomic commit enforcement | Before committing to ensure atomic commits |
| `debugger` | Systematic debugging | When initial implementation fails or bugs occur |

### Available Skills (Commands)

**Development Workflow:**
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

**Document & File Creation:**
| Command | Purpose |
|---------|---------|
| `/pdf` | PDF manipulation and form extraction |
| `/pdf-chunk` | Handle large PDFs without filling context |
| `/xlsx` | Excel spreadsheet creation and editing |
| `/pptx` | PowerPoint presentation creation |
| `/docx` | Word document creation |
| `/doc-coauthoring` | Structured documentation collaboration |
| `/theme-factory` | Generate color themes for artifacts |
| `/skill-creator` | Create custom Claude Code skills |

**macOS App Integrations:**
| Command | Purpose |
|---------|---------|
| `/things` | Things 3 task management |
| `/fantastical` | Fantastical calendar integration |

### Dotfiles Management

Use `dots` command (chezmoi wrapper) to manage dotfiles from any directory:

| Command | Purpose |
|---------|---------|
| `dots apply` | Apply dotfiles to home directory |
| `dots diff` | Preview changes before applying |
| `dots status` | Show status of managed files |
| `dots update` | Pull latest changes and apply |
| `dots edit FILE` | Edit a dotfile source |
| `dots add FILE` | Add a new file to chezmoi |
| `dots cd` | Go to dotfiles source directory |
| `dots git ...` | Run git commands in dotfiles repo |

Source directory: `~/.local/share/chezmoi`

### Claude Code Settings

Configuration managed via `~/.claude/settings.json` (templated from `settings.json.tmpl`).

**Default Mode:** `plan` - Claude enters plan mode by default for new tasks.

**Hooks:**
| Hook | Trigger | Behavior |
|------|---------|----------|
| Git push confirmation | `Bash(git push*)` | Prompts for confirmation before pushing |
| Block arbitrary docs | `Write(*.md)` | Blocks creating random .md files (allows README, CLAUDE, SKILL, etc.) |
| Console.log warning | `Edit(*.ts\|*.tsx\|*.js\|*.jsx)` | Warns if console.log found after edit |

**Permissions (OS-specific):**

*Common (all platforms):*
| Type | Commands |
|------|----------|
| **Allow** | `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash(git:*)`, `Bash(tree:*)`, `Bash(find:*)` |
| **Ask** | `git reset --hard`, `git push --force` |

*macOS/Linux:*
| Type | Commands |
|------|----------|
| **Deny** | `shutdown`, `reboot`, `halt`, `poweroff`, `mkfs`, `dd`, `fdisk`, `parted`, `sudo`, `doas`, `su` |
| **Ask** | `rm`, `chmod`, `chown`, `kill` |

*Windows:*
| Type | Commands |
|------|----------|
| **Deny** | `Stop-Computer`, `Restart-Computer`, `shutdown`, `Format-Volume`, `Clear-Disk`, `diskpart`, `bcdedit` |
| **Ask** | `Remove-Item`, `del`, `rd`, `rmdir`, `icacls`, `Set-Acl`, `Stop-Process`, `taskkill` |
