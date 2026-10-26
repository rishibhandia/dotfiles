---
name: matlab
description: MATLAB R2025a coding patterns and the personal +thz analysis package at ~/Code/matlab-thz-analysis/. Use when writing or reviewing MATLAB code (.m files), working in the +thz package, or analyzing THz/TA data. Trigger on package names (thz.fft, thz.eos, thz.ta, thz.io), function names from +thz, or general MATLAB style/performance questions. Do NOT use for executing scripts headlessly — that's matlab-runner's job.
---

# MATLAB Skill — +thz Package and Coding Patterns

**Extracted:** 2026-03-15
**Updated:** 2026-09-10
**Context:** NbOI2 SHG/THz pump-probe scripts; general MATLAB R2025a; the personal `+thz` analysis package at `~/Code/matlab-thz-analysis/` (the `rishibhandia/matlab-thz-analysis` repo).

This SKILL.md is the entry point. It documents the package layout,
calling conventions, and the patterns that affect every script in
`~/Code/matlab-thz-analysis/` and `~/Documents/Scientific Data/`. For deeper
topic-specific guidance, see the satellite docs in this directory.

## Navigation

| Topic | File |
|---|---|
| MATLAB style: naming, formatting, function/class authoring, error handling, env-var overrides for `clearvars` scripts | [`style-guide.md`](style-guide.md) |
| Performance: vectorization, pre-allocation, memory, parallel, JIT-friendly idioms, caching parfor ODE sweeps | [`performance.md`](performance.md) |
| Plotting recipes: color, polar in tiledlayout, region highlighting, figure fonts and exportgraphics sizing, a table under a row of maps, title/label collisions | [`plotting.md`](plotting.md) |
| FFT in tables: `thz.fft.disc_ft` zero-padding, datatable row-vector conventions for stored FFTs | [`fft.md`](fft.md) |
| Transient absorption: sideband analysis, fluence scaling with wire grids, FFT frequency axis for negative-going time vectors, SHG probe-polarization normalization | [`ta.md`](ta.md) |
| Golden-baseline workspace verification for output-identical refactors (loader migrations, package moves); pixel-identity check of rebuilt figures against git | [`verification.md`](verification.md) |
| 2D THz nonlinear spectroscopy: NL = AB - A - B keeps only cross terms, peak positions by order, Mahmood delay convention, projection-slice limits of 1D traces, filtered-pump pitfalls | [`thz2d.md`](thz2d.md) |

---

## Scripts, not monolithic functions (HARD RULE, user-set 2026-07-15)

Analysis/figure-build files are **top-to-bottom SCRIPTS**, never one giant
`function build_x() ... end` wrapper. The user edits interactively and runs
`%%` sections in the editor; a function wrapper hides the workspace and blocks
section-by-section execution.

- Start with `clearvars; close all;` so each run is clean and scripts can be
  chained (`scriptA; scriptB` in one `-batch`) without workspace leakage.
- Break every logical stage with a `%% section title` line (paths/config →
  load → compute → each panel → export).
- Factor repeated logic into **local functions at the END of the script file**
  (legal since R2016b) or standalone helper files — helpers are encouraged,
  wrappers are not.
- `matlab -batch "scriptName"` invokes scripts exactly like functions, so
  headless builds are unaffected.

---

### Helpers that need the script workspace: anonymous, not local (added 2026-09-21)

A local function at the end of a script cannot see the script's variables (`function guides(ax) yline(ax, carrierWl, ...)` fails at call time with "Unrecognized function or variable 'carrierWl'"), and MATLAB refuses a `function` block in the middle of a script. When a small helper only repeats a few plotting calls with the script's own values, write it as an anonymous function, which captures the workspace at definition:

```matlab
guides = @(ax, col) [yline(ax, carrierWl, ':',  'Color', col,    'LineWidth', lwG), ...
                     yline(ax, blueWl,    '--', 'Color', S.blue, 'LineWidth', lwG), ...
                     yline(ax, redWl,     '--', 'Color', S.red,  'LineWidth', lwG)];
hold(ax, 'on'); guides(ax, gCarMap); hold(ax, 'off');
```

Graphics calls return handles, so the bracketed list is one valid expression. Define it after the variables it uses; it freezes their values at that point. Keep end-of-script local functions for helpers that take everything they need as arguments.

## The +thz Analysis Package

All shared THz/TA analysis lives in the `+thz` package at the root of
`~/Code/matlab-thz-analysis/` (a clone of the
`rishibhandia/matlab-thz-analysis` GitHub repo). MATLAB picks it up via
`~/Documents/MATLAB/startup.m` (userpath), which delegates to the repo's
own `startup.m` for path setup and figure defaults. Per-experiment
scripts live in `~/Documents/Scientific Data/` and call into the package.

### Package layout

```
+thz/
├── +eos/      % Electro-optic sampling, E-field conversion (calcEOS, calcEOSAdv, ...)
├── +fft/      % Windowed FFT, frequency utilities (disc_ft, rfftFreq, fft2DMap, ...)
├── +io/       % Importers, loaders, generators (TAData, loadTHzPumpProbeTimeTrace, ...)
├── +models/   % Drude / Lorentz / Fano fitting (drudeLorentz, twoDrude, ...)
├── +optics/   % Transmission, conductivity, index, thin-film thickness
├── +plot/     % Plotting and figure export helpers
├── +spec2d/   % 2D-spectroscopy classes (TimeTrace2D, FreqTrace2D)
├── +ta/       % Transient absorption primitives (sidebands, fluence scaling)
├── +util/     % General utilities (averages, ratios, label helpers)
└── plotDefaults.m   % Publication-style figure defaults (export-safe sizes)
```

### Calling conventions

Use fully qualified names in new code:

```matlab
ft        = thz.fft.disc_ft(signal, 1024, @hanning);
freq      = thz.fft.rfftFreq(time, 1024);
Ef        = thz.eos.calcEOS(0.01, 0.3, 'GaP', 0);
ta        = thz.io.TAData("scan.h5");
oscPower  = thz.ta.oscillatoryPower(ta, 3.0, Bandwidth=0.15);
```

Or `import` for brevity inside a script:

```matlab
import thz.fft.* thz.ta.*
ft  = disc_ft(signal, 1024, @hanning);
sb  = findSidebands(oscPower, ta.Wavelengths, 600);
```

Bare unqualified calls (`disc_ft(...)`, `calcEOS(...)`) still work via thin
root wrappers that delegate to the package — kept indefinitely so existing
analysis scripts on other computers don't need edits.

**Loading pump-probe/Kerr time traces (2026-07-22):** use
`thz.io.loadTHzPumpProbeTimeTrace` for ALL new loading code — its
`columnMap`/`columnsToExtract` schema covers every 2–6 column text format.
`loadKerrTimeTrace` is a deprecated thin delegate (2-col schema, legacy
`DataFileName`/`ScanNumber` names) pinned by `tests/testKerrEquivalence.m`;
all TiSe2 call sites were migrated. String-valued template parameters are
not supported by the universal loader — `replace()` them into the template
before the call and re-attach as a column afterward.

### Headless `-batch` runs do not load the package

**Updated:** 2026-09-10

`matlab -batch "cd('...'); myScript"` does not reliably execute the userpath
`startup.m` that delegates to the repo's `startup.m`, so the first `thz.*` call
fails with `Unable to resolve the name 'thz.io.load2DTimeTraceNew'`. Guard every
script that is meant to run headless:

```matlab
if isempty(which('thz.fft.disc_ft'))
    run(fullfile(getenv('HOME'), 'Code', 'matlab-thz-analysis', 'startup.m'));
end
```

or prepend `run('~/Code/matlab-thz-analysis/startup.m');` to the `-batch`
string. Do not use `exist('thz.io.load2DTimeTraceNew', 'class')` as the test;
package functions are not classes and it returns false even when they resolve.

### TA analysis primitives in `+thz/+ta`

Five reusable helpers for transient-absorption work — see [`ta.md`](ta.md)
for end-to-end workflows:

| Function | Purpose |
|---|---|
| `thz.ta.oscillatoryPower(ta, freq, Bandwidth=...)` | Per-pixel FFT power in a +/-bandwidth window around a phonon frequency |
| `thz.ta.findSidebands(oscPower, wl, centerWl, ExclusionRadius=...)` | Blue/red sideband peak struct (pixel, wavelength, THz shift, power) |
| `thz.ta.wavelengthToFreqShift(lambda, lambdaCenter)` | `c/lambda - c/lambdaCenter` in THz |
| `thz.ta.wireGridFieldFactor(angleDeg)` | Malus-law `cos^2` (field) and `cos^4` (intensity) factors |
| `thz.ta.fitPowerLaw(x, y)` | Log-log regression returning exponent, intercept, RMS residual |

### Figure defaults

Always call `thz.plotDefaults()` at the top of plotting scripts (after
`clc; clear; close all`). It sets export-safe sizes (axes 11pt, lines
1.5, normal weight) so `exportgraphics` output never clips and matches
the on-screen figure.

```matlab
clc; clear; close all
thz.plotDefaults()
```

### When NOT to add to the package

Per-experiment glue (filename templates, hardcoded sample names,
specific fluence sweeps) belongs in the analysis script, not the
package. The bar for promoting code into `+thz` is: *will I want to
call this from a future, unrelated experiment?*

---

## Running MATLAB from Claude on this machine

Two etiquette rules when invoking MATLAB on the user's box. Both are
project-wide and apply to every analysis script.

**1. Never blanket-kill MATLAB processes.** The user almost always has
an interactive MATLAB session open in another window — they have said
explicitly: *"i'm running matlab session in another window, don't quit
all matlab sessions."* `taskkill /im matlab.exe`, `Stop-Process
-Name matlab`, and similar will wipe their workspace. If a single
`-batch` invocation is hung, terminate only that PID; never sweep all
MATLAB processes.

**2. Run `matlab -batch` invocations serially, never in parallel.**
The user has hit failures running batch jobs concurrently: *"it failed
maybe becaus you ran to many in parallel"* → *"rerun them
sequentially. 1 at a time"*. Likely a mix of license-checkout
contention, shared figure-output paths, and the parallel interactive
session all competing. When a task implies multiple MATLAB runs
(regenerating a family of plots, sweeping a parameter), chain them
inside one `-batch` call or queue them one at a time. Reserve
parallelism for cases the user explicitly approves.

For headless execution use the `matlab-runner` skill (it bakes in the
right entry point on this machine).

---

## EOS field-conversion quick reference

`thz.eos.calcEOSAdv` (and its root-namespace wrapper `calcEOSAdv`)
converts a measured EOS lock-in ratio `ΔI/I` to a peak field in
**kV/cm**, accounting for `n` silicon filter wafers in the probe path.

```matlab
Ef = calcEOSAdv(dI_over_I, L_mm, detCrystal, siliconCount)
%   dI_over_I    column of ΔI/I (lock-in signal / DC)
%   L_mm         crystal thickness in MILLIMETERS (e.g. 0.050 for 50 µm GaP)
%   detCrystal   'GaP' or 'ZnTe'
%   siliconCount integer number of Si filter WAFERS (each contributes
%                t_Si = 4·n_Si/(n_Si+1)^2 with n_Si = 3.418); 0 if none
% Returns Ef in kV/cm.
```

Internally uses `asin(ΔI/I)`, so `|ΔI/I|` must be < 1 (always true in
practice — typical values are 1e-3 to 1e-2). For GaP it uses
`r41 = 0.88e-10 cm/V`, `n_GaP = 3.183` (probe), `n_GaP@THz = 3.24`.
ZnTe branch uses Planken's formula with `r41 = 3.9e-10 cm/V`,
`n_ZnTe = 2.8528`. Probe wavelength is hardcoded to 800 nm.

`thz.eos.calcEOS` is the older two-arg version (no silicon correction)
and `calc_E_flex` lets you override material constants.

---

## Graceful Per-File Loading for In-Progress Scans

Wrap each file load in try/catch and guard against too-short traces. Without the length guard, a 0-length trace sets `L = min(existing, 0) = 0`, zeroing all previously loaded rows and crashing downstream FFT code.

```matlab
for ii = 1:length(angles)
    try
        t = thz.io.loadTHzPumpProbeTimeTrace(fname, ...);
        t.hwpAngle = repmat(ang, height(t), 1);
        if height(t) == 0 || size(t.Time_ps, 2) < 50
            warning('Skipping %g° — trace too short (%d points).', ang, size(t.Time_ps,2));
            continue
        end
        if ~isempty(dataTable)
            L = min(size(dataTable.Time_ps, 2), size(t.Time_ps, 2));
            dataTable.Time_ps = dataTable.Time_ps(:, 1:L);
            dataTable.Delta_E = dataTable.Delta_E(:, 1:L);
            t.Time_ps = t.Time_ps(:, 1:L);
            t.Delta_E = t.Delta_E(:, 1:L);
        end
        dataTable = [dataTable; t];
    catch ME
        warning('Load failed for %g°: %s', ang, ME.message);
    end
end
```

Use `ii` (not `i`) as the loop counter — `i` shadows the imaginary unit
and breaks complex math elsewhere in the script.

For plotting recipes (color, polar in tiledlayout, region highlighting,
figure fonts), see [`plotting.md`](plotting.md). For the
`computeFFTAndIntegrate` `varargin` pattern and other TA workflow
helpers, see [`ta.md`](ta.md).

### Loaders must not resample onto a nominal axis (added 2026-09-18)

`thz.io.load2DTimeTraceNew` used to build its probe time axis from the stage parameters with 66.667 ps per 10 000 counts and `interp1` every row onto it, then set NaN to zero. The acquisition writes 0.04 ps per 6 counts, i.e. 200/3 per 10 000, so over 150 points the nominal axis overshot the file grid by 3e-5 ps, `interp1` returned NaN at the last sample and the loader wrote an exact zero into the last column of A, B, AB and NL of every row. Rules now in the loader and for any new one: when a file carries its own time column ('New' format), use it, validate it against the stage parameters and across rows, and do not interpolate; never replace NaN by zero, raise an error naming the file; write stage constants as exact fractions (`(200/3)/10000`), not rounded decimals. Diagnostic that found it: count exact zeros per column after loading (`nnz(M(:,end) == 0)`) and compare with the zeros present in the raw files.
