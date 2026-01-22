---
name: eval
description: Manage eval-driven development workflow. Define, check, and report on capability and regression evals.
---

# Eval Command

Manage eval-driven development workflow.

## Usage

`/eval [define|check|report|list] [feature-name]`

## Define Evals

`/eval define feature-name`

Create a new eval definition at `.claude/evals/feature-name.md`:

```markdown
## EVAL: feature-name
Created: $(date)

### Capability Evals
- [ ] [Description of capability 1]
- [ ] [Description of capability 2]

### Regression Evals
- [ ] [Existing behavior 1 still works]
- [ ] [Existing behavior 2 still works]

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
```

## Check Evals

`/eval check feature-name`

Run evals for a feature:

1. Read eval definition
2. For each capability eval:
   - Attempt to verify criterion
   - Record PASS/FAIL
3. For each regression eval:
   - Run relevant tests
   - Compare against baseline
4. Report status

## Report Evals

`/eval report feature-name`

Generate comprehensive eval report:

```
EVAL REPORT: feature-name
=========================

CAPABILITY EVALS
----------------
[eval-1]: PASS (pass@1)
[eval-2]: PASS (pass@2) - required retry
[eval-3]: FAIL - see notes

REGRESSION EVALS
----------------
[test-1]: PASS
[test-2]: PASS

METRICS
-------
Capability pass@1: 67%
Capability pass@3: 100%
Regression pass^3: 100%

RECOMMENDATION
--------------
[SHIP / NEEDS WORK / BLOCKED]
```

## Arguments

- `define <name>` - Create new eval definition
- `check <name>` - Run and check evals
- `report <name>` - Generate full report
- `list` - Show all evals
- `clean` - Remove old eval logs
