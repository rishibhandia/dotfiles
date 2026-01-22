---
name: code-review
description: Comprehensive security and quality review of uncommitted changes. Reviews for OWASP vulnerabilities, code quality, and best practices.
---

# Code Review

Comprehensive security and quality review of uncommitted changes.

## What This Command Does

1. Get changed files: `git diff --name-only HEAD`
2. Review each changed file for issues
3. Generate prioritized report
4. Block commit if critical issues found

## Security Issues (CRITICAL)

- Hardcoded credentials, API keys, tokens
- SQL injection vulnerabilities
- XSS vulnerabilities
- Missing input validation
- Insecure dependencies
- Path traversal risks
- CSRF vulnerabilities
- Authentication bypasses

## Code Quality (HIGH)

- Functions > 50 lines
- Files > 800 lines
- Nesting depth > 4 levels
- Missing error handling
- console.log statements
- TODO/FIXME comments without tickets
- Missing JSDoc for public APIs

## Best Practices (MEDIUM)

- Mutation patterns (use immutable instead)
- Missing tests for new code
- Accessibility issues (a11y)
- Poor variable naming
- Magic numbers without explanation

## Report Format

For each issue found:
```
[SEVERITY] Issue Title
File: path/to/file.ts:42
Issue: Description of the problem
Fix: How to resolve it
```

## Approval Criteria

- **Approve**: No CRITICAL or HIGH issues
- **Warning**: MEDIUM issues only (can merge with caution)
- **Block**: CRITICAL or HIGH issues found

Never approve code with security vulnerabilities!

## Related Agents

This command invokes the `code-reviewer` agent located at:
`~/.claude/agents/code-reviewer.md`
