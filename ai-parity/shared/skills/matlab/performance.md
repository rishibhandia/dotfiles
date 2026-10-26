---
name: matlab-performance
description: MATLAB R2016b+ performance patterns — vectorization, pre-allocation, memory types, I/O, parallel computing, modern idioms. Use when optimizing loops, handling large data, or choosing data structures.
type: reference
---

# MATLAB Performance and Modern Idioms

**Extracted:** 2026-03-15
**Sources:** MathWorks Performance Docs, MathWorks Coding Guidelines, Schoepfloeffel expert tips
**Updated:** 2026-10-24

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

---

## Caching expensive parfor ODE sweeps (added 2026-10-24)

A 2D sweep that solves an ODE per (parameter, delay) pair (e.g. an a·x² oscillator driven by two delayed pulses, `ode45` at RelTol 1e-10 in a `parfor` over 71 delays, repeated for 9 parameter values) took 95–133 s per run, almost all of it ODE solves plus pool start-up, and every label or layout fix reran all of it. A cache cut reruns to ~20 s with identical printed results.

Pattern (inline in the script, no new helper):

```matlab
% SETTINGS
useSimulationCache  = true;      % false: always solve
simulationCacheFile = fullfile(scriptDir, "fooSimulationCache.mat");   % git-ignore *SimulationCache.mat

% after every simulation input is known
simulationKey = struct(timeGrid=timeGrid, tauRows=tauRows, odeTolerance=odeTolerance, ...
    odeAbsTolerance=odeAbsTolerance, readoutMode=readoutMode, f0THz=f0THz, gammaPerPs=gammaPerPs, ...
    driveTimePs=driveTimePs, drive=drive, linearPeak=linearPeak);      % EVERY input that changes the result
cachedParams = zeros(1, 0);
cachedMaps = {};
if useSimulationCache && isfile(simulationCacheFile)
    cache = load(simulationCacheFile, "simulationKey", "cachedParams", "cachedMaps");
    if isequal(cache.simulationKey, simulationKey)          % any input change invalidates the whole cache
        cachedParams = cache.cachedParams;
        cachedMaps = cache.cachedMaps;
    end
end
cacheChanged = false;
for k = 1:numel(params)
    hit = find(abs(cachedParams - params(k)) < 1e-12, 1);  % one entry per parameter value
    if ~isempty(hit)
        maps{k} = cachedMaps{hit};
        continue
    end
    if isempty(gcp("nocreate"))                              % start the pool ONLY on a miss
        parpool("Processes", numWorkers);
    end
    parfor jj = 1:numTau, ... end
    cachedParams(end + 1) = params(k);
    cachedMaps{end + 1} = maps{k};
    cacheChanged = true;
end
if useSimulationCache && cacheChanged
    save(simulationCacheFile, "simulationKey", "cachedParams", "cachedMaps", "-v7");
end
```

- Key on the **inputs**, not the script text: plotting edits should hit, a changed drive or tolerance must miss. Include derived inputs that are cheap to recompute (e.g. the linear response peak used to set the parameter) so a change upstream invalidates the cache.
- Store per parameter value so a later run that adds values (e.g. reruns at fitted values) reuses the grid and only solves the new ones.
- Cache the arrays the solver returned, never something derived from them; disclose the cache in the script's PROCESSING header.
- Verify once: run twice (fill, then hit) and diff the printed tables, ignoring the cache/pool lines; they must be identical.
- A reproduction check against a map saved by another script must allow for the **numerical floor**: an `a = 0` run of the same NL extraction measures it (here ~2e-6 of the signal), and a parameter typed to 10 significant digits reproduces the other script's map only to that floor, not exactly. Use a threshold a few times the floor (1e-5), not 1e-6.

Removing redundant solves (not yet applied, but worth doing before reaching for more workers):

- For a time-invariant system starting from rest, the single-pulse response at delay τ is the fixed-pulse response shifted by τ. If τ steps by a whole number of time-grid steps, it is an index shift of one solve on an extended grid, which removes one ODE per delay.
- The a = 0 "floor" run is linear, so it only measures solver error: one delay row suffices, not every row.
- For x'' + ... + a x² = s F(t), x = s y gives the exact identity NL(s, a) = s·NL(1, a·s): a drive-amplitude scan at fixed a is the a-scan at unit drive times s, so do not solve both.
