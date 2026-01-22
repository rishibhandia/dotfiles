---
name: test-coverage
description: Analyze test coverage and generate missing tests. Identifies under-covered files and creates unit, integration, and E2E tests.
---

# Test Coverage

Analyze test coverage and generate missing tests.

## What This Command Does

1. Run tests with coverage: `npm test --coverage`

2. Analyze coverage report (`coverage/coverage-summary.json`)

3. Identify files below 80% coverage threshold

4. For each under-covered file:
   - Analyze untested code paths
   - Generate unit tests for functions
   - Generate integration tests for APIs
   - Generate E2E tests for critical flows

5. Verify new tests pass

6. Show before/after coverage metrics

7. Ensure project reaches 80%+ overall coverage

## Focus Areas

- Happy path scenarios
- Error handling
- Edge cases (null, undefined, empty)
- Boundary conditions

## Coverage Thresholds

Required thresholds:
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

## Commands

```bash
# Run tests with coverage
npm test -- --coverage

# View HTML report
open coverage/lcov-report/index.html

# Check coverage thresholds
npm test -- --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80}}'
```

## Output Format

```
COVERAGE REPORT
===============
Before: X% overall
After:  Y% overall

Files improved:
- src/utils.ts: 45% -> 85%
- src/api/users.ts: 60% -> 92%

New tests created:
- src/__tests__/utils.test.ts (12 tests)
- src/__tests__/api/users.test.ts (8 tests)

Remaining under threshold:
- src/legacy.ts: 55% (needs manual review)
```
