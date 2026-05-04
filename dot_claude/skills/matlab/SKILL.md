---
name: matlab
description: MATLAB R2025a coding patterns and the personal +thz analysis package at ~/Documents/MATLAB/. Use when writing or reviewing MATLAB code (.m files), working in the +thz package, or analyzing THz/TA data. Trigger on package names (thz.fft, thz.eos, thz.ta, thz.io), function names from +thz, or general MATLAB style/performance questions. Do NOT use for executing scripts headlessly — that's matlab-runner's job.
---

# MATLAB Skill — +thz Package and Coding Patterns

**Extracted:** 2026-03-15
**Updated:** 2026-05-04
**Context:** NbOI2 SHG/THz pump-probe scripts; general MATLAB R2025a; the personal `+thz` analysis package at `~/Documents/MATLAB/` (synced via `rishibhandia/matlab-thz-analysis`).

This SKILL.md is the entry point. It documents the package layout,
calling conventions, and the patterns that affect every script in
`~/Documents/MATLAB/` and `~/Documents/Scientific Data/`. For deeper
topic-specific guidance, see the satellite docs in this directory.

## Navigation

| Topic | File |
|---|---|
| MATLAB style: naming, formatting, function/class authoring, error handling | [`style-guide.md`](style-guide.md) |
| Performance: vectorization, pre-allocation, memory, parallel, JIT-friendly idioms | [`performance.md`](performance.md) |
| Plotting recipes: color, polar in tiledlayout, region highlighting, figure fonts and exportgraphics sizing | [`plotting.md`](plotting.md) |
| FFT in tables: `thz.fft.disc_ft` zero-padding, datatable row-vector conventions for stored FFTs | [`fft.md`](fft.md) |
| Transient absorption: sideband analysis, fluence scaling with wire grids, FFT frequency axis for negative-going time vectors, SHG probe-polarization normalization | [`ta.md`](ta.md) |

---

## The +thz Analysis Package

All shared THz/TA analysis lives in the `+thz` package at the root of
`~/Documents/MATLAB/` (synced across machines via the
`rishibhandia/matlab-thz-analysis` GitHub repo). Per-experiment scripts
live in `~/Documents/Scientific Data/` and call into the package.

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
