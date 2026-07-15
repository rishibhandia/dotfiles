---
name: matlab-style-guide
description: MATLAB R2019b+ coding style rules — naming conventions, formatting, function/class authoring, error handling, functions to avoid. Use when writing or reviewing any new function or class.
type: reference
---

# MATLAB Style Guide

**Extracted:** 2026-03-15
**Sources:** MathWorks MATLAB Coding Guidelines, matlab/rules repo, Johnson MatlabStyle1p5

## When to Use
Writing or reviewing any MATLAB function or class; naming variables; formatting code for shared use.

---

## Naming Conventions

| Element | Convention | Examples |
|---|---|---|
| Variables | lowerCamelCase | `totalPowerLoss`, `initialTemp` |
| Functions/methods | lowerCamelCase or lowercase | `calculatePower`, `initpressure` |
| Classes (in namespace) | UpperCamelCase | `PrintQueue`, `SignalProcessor` |
| Properties | UpperCamelCase | `StartTime`, `RelativeTolerance` |
| Events | UpperCamelCase | `RowSelected`, `DeviceAdded` |
| Name-Value args | UpperCamelCase | `LineWidth`, `FaceColor` |
| Namespaces | short, lowercase | `multivariate`, `clustering` |

**Key rules:**
- Max **32 characters** per identifier
- **No abbreviations** unless domain-standard (`idx` ok, `nxIdx` not)
- **Acronyms** uniformly cased: `htmlwrite`, `createURL`, `DNAMatch`
- **Never shadow** MATLAB builtins (`rand`, `sin`, `sqrt`, `i`, `j`)
- Boolean-output functions use **`is`/`has`** prefix: `isConfigured`, `hasValue`
- Conversion functions use **"2"**: `joule2Calorie`, `struct2table`
- Loop counters: use `ii`, `jj`, `kk` — **not `i`, `j`** (shadows imaginary unit)
- Symmetric pairs: `readData`/`writeData`, `start`/`stop`

---

## Formatting

- **4 spaces** per indent level — never tabs
- Max **120 characters** per line
- **One statement per line** — never `a=1; b=2;` on one line
- Space after `%` in comments: `% comment text`
- Spaces around `=` in assignments: `x = 3.2`
- **No spaces** around `=` in Name=Value calls: `plot(x, y, LineWidth=3)`
- Spaces around relational and logical operators: `a <= b`, `x && y`
- **No spaces** around `:`: `2:2:10`, `A(2:end-1)`
- **No spaces** around `*`, `.*`, `/`, `./`, `^`, `.^`
- Spaces around `+` and `-` at top level; no spaces within grouped subexpressions: `(a+b) + exp(c+d)`
- No spaces after unary operators: `-x`, `~flag`
- No spaces inside grouping operators: `sin(exp(1))` not `sin( exp(1) )`
- One blank line between logical code sections and between local function declarations
- No trailing whitespace

---

## Comments and Documentation

- Place comments **before the code they explain**
- Use `%%` to define named code sections
- **H1 line** immediately after `function` declaration (before `arguments` block): one-line description
- Help block after H1: syntax, inputs, outputs, side effects
- Indent H1/help at function level; indent internal comments at code level

---

## Statements and Expressions

- Write floating-point literals with leading digit: `0.1` not `.1`
- Use `"double quotes"` for string literals; `'single quotes'` only for char arrays
- Never use `==` or `~=` to compare floats — use `abs(a-b) < tol`
- Use `&&` / `||` (short-circuit) for scalar conditions; reserve `&` / `|` for array operations
- Use `(parentheses)` to clarify operator precedence: `w = (c*d)/(e^f)`
- Use **functional form**, not command syntax, inside functions: `load('file.mat')` not `load file.mat`
- Use `fileparts`, `fullfile`, `filesep` for platform-independent paths
- Use empty parentheses to distinguish function calls from variables: `datetime()` not `datetime`
- Suppress unused outputs with `~`: `[~, ~, V] = svd(A)`
- Limit **nesting depth to 5 levels**
- In `if-else`, put normal case in `if`, exceptional case in `else`
- Every `switch` must have an **`otherwise` block** (comment if empty)
- `break`, `continue`, `return` only when they clearly improve readability

---

## Variables and Data

- **Avoid global variables** — pass as function arguments
- **Minimize persistent variables** — only for caching large recomputable data; document why
- Define all struct fields in one block; never add/remove fields outside their creating function
- Use **cell arrays only for heterogeneous data**; use **string arrays** for text collections
- Assign named constants instead of literal values in expressions: `gasConstant = 8.314`

---

## Functions to Avoid

| Function/Pattern | Problem | Alternative |
|---|---|---|
| `eval`, `evalin`, `evalc` | Unexpected execution, security risk, disables JIT | Function handles, direct indexing |
| `feval(fname_string, ...)` | Dynamic dispatch by string | Function handles |
| `cd` / `addpath` / `rmpath` inside functions | Path side effects, triggers recompilation | `onCleanup(@()path(oldPath))` to restore |
| `clear all` | Clears everything, kills JIT | Clear specific variables |
| `exist`, `whos`, `inputname`, `dbstack` | Expensive runtime introspection | Avoid in performance-critical paths |
| `varargin` for name-value pairs | Unvalidated, no autocomplete | Use `arguments` block |
| Command syntax in functions | Silent path issues | Functional form |

---

## Function Authoring

- **File name must match function name** exactly
- Always **terminate functions with `end`**
- Max **6 input arguments**, max **4 output arguments**
- Do not change the meaning of an output based on `nargout`
- Use **`arguments` block** (R2019b+) for validation instead of `narginchk`/`validateattributes`:
  ```matlab
  arguments
      x     (1,1) double {mustBeReal, mustBeFinite}
      label (1,:) char
      opts.Tolerance (1,1) double {mustBePositive} = 1e-6
  end
  ```
- Prefer **local functions** over nested functions — nested functions share parent workspace (subtle bugs) and are JIT-unfriendly
- Keep **anonymous functions** simple; convert to local function if complex or reused
- Refactor duplicate code blocks into local functions (DRY)
- Restore MATLAB global state on exit using `onCleanup`:
  ```matlab
  oldPath = path();
  c = onCleanup(@() path(oldPath));
  ```

---

## Class Authoring

- **classdef filename must match class name**
- Prefer **value classes** over handle classes; use handle only for: hardware/unique objects, graphics, relational data structures
- Mark classes `Sealed` if not designed for subclassing
- Use **property validation syntax** instead of `set` methods for pure validation:
  ```matlab
  Width (1,1) double {mustBeReal, mustBeNonnegative}
  ```
- Make property access as restrictive as needed (`private`, `SetAccess = private`)
- Use `Dependent` properties only when value derives from other properties
- Avoid `subsref`/`subsasgn` overloads — use modular indexing mixins

---

## Error Handling

- Fix **all Code Analyzer warnings** before committing
- Use `try-catch` for error handling only — **not for normal control flow**
- Use `MException` to identify specific error types
- Reset global state in `catch` or via `onCleanup` before rethrowing
- Use `rethrow(exception)` or `throw(exception)` — **never `throwAsCaller`** (obscures stack trace)
- Error messages should state problem + solution: `"Sparse matrices not supported. Use eigs instead."`
