# Global Claude Code Rules

This file provides global guidance to Claude Code across all projects. It is loaded from `~/.claude/CLAUDE.md`.

Project-specific CLAUDE.md files in individual repositories will be loaded in addition to this global configuration.

## Development Rules

These rules are enforced by the agents and skills configured in this dotfiles setup.

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
