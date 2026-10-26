# Golden-Baseline Verification for Refactors That Must Not Change Outputs

**Extracted:** 2026-07-22
**Updated:** 2026-10-24
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

## Pixel-identity check of a rebuilt figure against git (added 2026-10-24)

For figure builders the outputs are images, and "a rework must leave the output pixel-identical" is checked on the committed PNG, not the workspace:

```bash
git show HEAD:AdvMat_Figures/rough/Fig4.png > "$TMP/Fig4_HEAD.png"     # before or after the rebuild, any time
matlab -batch "a = imread('$TMP/Fig4_HEAD.png'); b = imread('AdvMat_Figures/rough/Fig4.png'); \
  d = any(a ~= b, 3); [r, c] = find(d); \
  fprintf('size %s vs %s, %d px differ, rows %d..%d cols %d..%d\n', mat2str(size(a)), mat2str(size(b)), \
  nnz(d), min(r), max(r), min(c), max(c));"
```

- `0 px` proves a refactor or an opt-in switch changed nothing by default.
- When a change is meant to touch one panel, the **bounding box** of the differing pixels proves that nothing else moved: a colour-scale change confined to rows 791–1185 (the FFT row) showed the time maps above were untouched; a model swap confined to columns 1023–1814 showed only the Theory panel changed.
- PDFs: render the first page with macOS `sips -s format png -Z 1600 in.pdf --out out.png` and compare renders of old and new the same way (the PDF bytes differ on every build because of timestamps). Crop the differing bounding box from both renders, stack them vertically and look: it shows at once whether a difference is a relabel or new data.
- Rebuilding an unchanged figure rewrites its PDF/PNG/FIG with new timestamps. When the PNG compares identical to HEAD, `git checkout --` those outputs (and any collected copies) so the working tree carries only real changes, then rerun the collector so downstream copies are byte-identical to the committed sources (check with `md5 -q`).
