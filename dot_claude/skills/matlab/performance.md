---
name: matlab-performance
description: MATLAB R2016b+ performance patterns — vectorization, pre-allocation, memory types, I/O, parallel computing, modern idioms. Use when optimizing loops, handling large data, or choosing data structures.
type: reference
---

# MATLAB Performance and Modern Idioms

**Extracted:** 2026-03-15
**Sources:** MathWorks Performance Docs, MathWorks Coding Guidelines, Schoepfloeffel expert tips

## When to Use
Optimizing slow loops; choosing data types; large dataset I/O; writing idiomatic modern MATLAB (R2016b+).

---

## Profile Before Optimizing

```matlab
timeit(@myFunc)           % measure function time (handles JIT warm-up automatically)
tic; myCode; toc          % measure code sections
profile on; myFunc; profile viewer   % line-level profiling
```

- Do 3–5 warm-up runs before measuring (JIT compilation effect)
- Focus on functions consuming >10% of total time
- Minimum 0.1 s execution for reliable measurement

---

## Pre-Allocation (Critical)

**Never grow arrays inside loops** — each resize copies the entire array.

```matlab
% BAD
result = [];
for i = 1:N
    result = [result, compute(i)];   % O(N²) copies
end

% GOOD
result = zeros(1, N);               % pre-allocate with correct type
for i = 1:N
    result(i) = compute(i);
end
```

- Pre-allocate with the **correct type**: `zeros(100, 'int8')` not `int8(zeros(100))`
- Never grow tables row-by-row in loops either

---

## Vectorization

Replace explicit loops with array operations wherever possible:

```matlab
% Loop version
for i = 1:N
    y(i) = x(i)^2 + 2*x(i);
end

% Vectorized
y = x.^2 + 2.*x;
```

- Use **logical indexing** instead of `find()` for retrieving values:
  ```matlab
  vals = x(x > 0);          % faster than: vals = x(find(x > 0))
  ```
- Use **implicit expansion** (R2016b+) instead of `repmat`/`bsxfun`:
  ```matlab
  A - mean(A, 2)             % subtracts column means without repmat
  ```
- `arrayfun`/`cellfun`/`structfun` are **not faster than explicit loops** — they're for readability only
- Move loop-invariant code outside the loop
- Page-wise functions (`pagemtimes`, `pageinv`, R2020b+) can be 30–40x faster than loop-over-slices

---

## Data Types and Memory

| Type | Use case | Memory vs double |
|---|---|---|
| `double` | Default; general numeric | 1× |
| `single` | When 7 decimal digits suffice | 0.5× |
| `logical` | Boolean arrays | 0.125× |
| `uint8`/`int16`/`uint32` | Integer image/signal data | 0.125–0.5× |

- **Struct of arrays** is faster than array of structs for column-wise access:
  ```matlab
  % Prefer: data.x(i), data.y(i)
  % Over:   data(i).x, data(i).y
  ```
- Use **in-place operations** where semantics allow (same variable as input and output avoids copy)
- Keep **variable types consistent** — type changes inside loops trigger reallocation

---

## String Arrays vs Char / Cell Arrays

Prefer `string` over `char` arrays and `cell` arrays of char:

```matlab
% Use
labels = ["alpha", "beta", "gamma"];   % string array — vectorized ops, 2–40× faster
msg    = "hello world";                % string scalar

% Avoid for collections
labels = {'alpha', 'beta', 'gamma'};  % cell array of char — slower, more memory
```

- String arrays support vectorized comparison, `contains`, `startsWith`, `regexp`, etc.
- Use `'single quotes'` **only** when you specifically need a `char` array (e.g. legacy functions)

---

## Modern Language Idioms

### `arguments` block (R2019b+)
Replaces `narginchk`, `validateattributes`, manual `if` checks, and `varargin` for name-value:
```matlab
function result = myFunc(x, opts)
    arguments
        x    (1,:) double {mustBeReal, mustBeFinite}
        opts.Tolerance (1,1) double {mustBePositive} = 1e-6
        opts.Method    (1,1) string = "linear"
    end
end
```
Call with: `myFunc(data, Tolerance=1e-8, Method="cubic")`

### sprintf for filename/string formatting
```matlab
fname = sprintf("scan_%03d_%.2f.mat", idx, value);
% %d=integer, %f=float, %.2f=2 decimals, %03d=zero-padded, %s=string
```

### Tables and Dictionaries
```matlab
% Table for heterogeneous named-column data
T = table(angles, intensities, 'VariableNames', {'HWP_deg', 'Signal'});
T = sortrows(T, 'HWP_deg');

% Dictionary (R2022b+) for key-value lookups
d = dictionary(["a","b","c"], [1, 2, 3]);
d("b")   % → 2
```

### Missing Values
```matlab
% Unified missing across types:
% double → NaN,  datetime → NaT,  string → <missing>,  categorical → <undefined>

ismissing(x)               % works on any type
mean(x, "omitmissing")     % always pass omit flag explicitly
% Note: NaN ~= NaN — unique() treats each NaN as distinct
```

### Approximate float comparisons
```matlab
abs(a - b) < tol                    % manual tolerance check
ismembertol(a, b, 1e-9)             % approximate membership
```

### Iterate over struct fields
```matlab
for field = string(fieldnames(myStruct))'
    val = myStruct.(field);
end
```

---

## Parallel Computing

- Use `parfor` for **independent iterations** each taking >100 ms:
  ```matlab
  parfor i = 1:N
      result(i) = expensiveCompute(i);
  end
  ```
- Parallelize **outer loops** to minimize overhead; nested `parfor` is not allowed
- `parfeval` for async background work; `backgroundPool` for UI responsiveness
- Allocate ≥4 GB RAM per parallel worker
- Keep GPU data on GPU; minimize CPU↔GPU transfers; use `single` for GPU

---

## File I/O

| Format | When to use | Notes |
|---|---|---|
| MAT v7 | Default for all saves | Max 2 GB per variable |
| MAT v7.3 | Variables >2 GB | HDF5-based, slower read/write |
| Parquet | Large tabular data replacing CSV | 10–12× smaller, 10–150× faster reads |
| CSV/TXT | Interchange only | Import with `detectImportOptions` first |

```matlab
% Read only needed columns (much faster on large files)
opts = detectImportOptions('data.csv');
opts.SelectedVariableNames = {'Time_ps', 'Signal'};
T = readtable('data.csv', opts);

% Cache expensive results
memoizedFn = memoize(@expensiveFunction);
result = memoizedFn(arg);   % cached after first call
```

- Process network files by copying locally first (10–30× speedup)
- Use `matfile` for partial loading of large v7.3 MAT files without loading everything
- For large data initialization (500+ lines of code), save as MAT-file instead

---

## JIT-Friendly Coding

- **Functions outperform scripts** — use functions
- Prefer **local functions** over nested functions (JIT-friendly)
- Avoid: `eval`, `evalin`, `clear all`, `exist`/`whos`/`dbstack`, `cd`/`addpath` inside functions — all prevent JIT optimization
- Keep variable types consistent throughout a function — type changes trigger reallocation
