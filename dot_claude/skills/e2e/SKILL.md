---
name: e2e
description: Generate and run end-to-end tests with Playwright. Creates test journeys, runs tests, captures screenshots/videos/traces, and uploads artifacts.
---

# E2E Command

Generate, maintain, and execute end-to-end tests using Playwright.

## What This Command Does

1. **Generate Test Journeys** - Create Playwright tests for user flows
2. **Run E2E Tests** - Execute tests across browsers
3. **Capture Artifacts** - Screenshots, videos, traces on failures
4. **Upload Results** - HTML reports and JUnit XML
5. **Identify Flaky Tests** - Quarantine unstable tests

## When to Use

Use `/e2e` when:
- Testing critical user journeys (login, checkout, etc.)
- Verifying multi-step flows work end-to-end
- Testing UI interactions and navigation
- Validating frontend/backend integration
- Preparing for production deployment

## Playwright Commands

```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/example.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Debug test with inspector
npx playwright test --debug

# Generate test code
npx playwright codegen http://localhost:3000

# Show HTML report
npx playwright show-report
```

## Test Artifacts

**On All Tests:**
- HTML Report with timeline and results
- JUnit XML for CI integration

**On Failure Only:**
- Screenshot of the failing state
- Video recording of the test
- Trace file for debugging

## Best Practices

**DO:**
- Use Page Object Model for maintainability
- Use data-testid attributes for selectors
- Wait for API responses, not arbitrary timeouts
- Test critical user journeys end-to-end
- Review artifacts when tests fail

**DON'T:**
- Use brittle selectors (CSS classes can change)
- Test implementation details
- Run against production
- Ignore flaky tests

## Related Agents

This command invokes the `e2e-runner` agent located at:
`~/.claude/agents/e2e-runner.md`
