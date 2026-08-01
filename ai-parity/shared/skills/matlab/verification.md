# Golden-Baseline Verification for Refactors That Must Not Change Outputs

**Extracted:** 2026-07-22
**Context:** Proving a library/loader refactor is output-identical across a
fleet of analysis scripts (used for the loadKerrTimeTrace →
loadTHzPumpProbeTimeTrace migration: 17 TiSe2 scripts, 17/17 identical).

## Problem

Analysis scripts are `%%`-section scripts run interactively; there are no
tests over them. A refactor (loader swap, package move) needs proof that
every script's numerical results are unchanged.

## Solution

1. **Baseline before ANY edit.** For each script generate a wrapper that runs
   it headlessly and snapshots the full end-state workspace:

   ```matlab
   run('/Users/rishi/Documents/MATLAB/startup.m');   % see matlab-runner skill
   cd('<scriptDir>');
   <scriptName>;
   close all;                                        % never save figures
   wsVars = whos; wsKeep = {};
   for wsIdx = 1:numel(wsVars)
       if ~startsWith(wsVars(wsIdx).class, 'matlab.ui.') && ...
          ~startsWith(wsVars(wsIdx).class, 'matlab.graphics.')
           wsKeep{end+1} = wsVars(wsIdx).name;
       end
   end
   save('baseline/<scriptName>.mat', wsKeep{:});
   ```

2. **Scripts that error at baseline** are pre-existing breakage: record the
   error, still migrate them, and verify **error parity** (same line, same
   message) instead of workspace equality — or fix them first and re-baseline.

3. **After the refactor**, rerun identical wrappers into `after/`, then diff
   variable-by-variable requiring `isequaln`, after normalizing types that
   can NEVER compare equal across MATLAB sessions:
   - `function_handle` → compare `func2str(x)`
   - `cfit`/`sfit` → compare `{formula(x), coeffvalues(x)}`
   - `MException` → skip (stacks embed run-specific paths)
   - recurse into cells/structs/table columns — loader tables often hide
     inside `scans{i}` cells
   - map enumerated allowed renames (e.g. `DataFileName` → `dataFileName`)
     before diffing, and compare tables with sorted column names

4. Report per-variable max-abs-diff for anything that still differs.

## When to Use

- Any refactor of `+thz` loaders or shared helpers with live analysis
  scripts in `~/Documents/Scientific Data/`
- Migrating call sites to a new API that claims to be behavior-identical
- Before deleting a "duplicate" function that scripts may depend on
