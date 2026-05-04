---
name: matlab
description: MATLAB R2025a coding patterns for THz/TA analysis — the +thz package layout and call patterns, polar plots in tiledlayout, color lightening, region highlighting, error bounds, varargin helpers, graceful per-file loading for in-progress scans
type: reference
---

# MATLAB Best Practices (R2025a)

**Extracted:** 2026-03-15
**Updated:** 2026-05-03
**Context:** NbOI2 SHG/THz pump-probe scripts; general MATLAB R2025a; the personal `+thz` analysis package at `~/Documents/MATLAB/`

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

Five reusable helpers for transient-absorption work — see the relevant
sub-skills (`ta-sideband-analysis`, `matlab-ta-fluence-scaling`) for
end-to-end workflows:

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

## Polar Axes Inside tiledlayout

`tiledlayout` + `nexttile` creates Cartesian axes. `polarplot` inside a tile does NOT produce a proper polar axes. Workaround:

1. Call `nexttile` → capture `.Position`
2. `delete` that axes
3. Create `polaraxes('Parent', fig, 'Position', pos)` at the same position
4. Call `polarplot(pax, ...)` on the returned handle

```matlab
fig = figure(1);
tl = tiledlayout(fig, 3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

for k = 1:3
    ax_tmp = nexttile(tl, 2*k-1);
    pos = ax_tmp.Position;   % capture BEFORE delete
    delete(ax_tmp);
    pax = polaraxes('Parent', fig, 'Position', pos);
    polarplot(pax, angles_rad, r, '-o', 'LineWidth', 2, 'Color', c);
    title(pax, 'Title Here', 'FontSize', 9);
    set(pax, 'FontSize', 9);
end
```

**Never call `ylabel` on polar axes** — it errors. Use `title` only.

## Color Lightening

`lighten()` does NOT exist in MATLAB R2025a. `fliplightness()` exists but FLIPS lightness (darkens light colors, lightens dark colors) — inconsistent across a color set.

```matlab
% RECOMMENDED — uniform lightening regardless of base color
light_color = brighten(c, 0.5);   % c is 1×3 RGB; positive beta (0–1) lightens

% Manual fallback
light_color = c + (1 - c) * 0.5;  % blend toward white, ~equivalent
```

Use `brighten` for error bounds, dashed secondary lines, confidence bands.

## Region Highlighting with patch

Always capture `ylim` AFTER plotting all data lines, then restore after adding patches. Use `'HandleVisibility','off'` to keep patches out of the legend.

**Time trace — shade the FFT'd region (after cutoff):**
```matlab
yl = ylim;
t_end = time(end);
patch([time_cutoff t_end t_end time_cutoff], [yl(1) yl(1) yl(2) yl(2)], ...
    [0.5 0.5 0.5], 'FaceAlpha', 0.12, 'EdgeColor', 'none', 'HandleVisibility', 'off');
ylim(yl);
```

**FFT — shade each integration window with per-range color:**
```matlab
region_colors = {[0.8 0.1 0.1], [0.1 0.3 0.9], [0.1 0.7 0.3]};
yl = ylim;
for k = 1:length(integration_ranges)
    rng = integration_ranges{k};
    patch([rng(1) rng(2) rng(2) rng(1)], [yl(1) yl(1) yl(2) yl(2)], ...
        region_colors{k}, 'FaceAlpha', 0.15, 'EdgeColor', 'none', 'HandleVisibility', 'off');
end
ylim(yl);
```

Apply highlighting in both standalone figures AND matching tiles in summary `tiledlayout`.

## Error Bounds on Polar Plots

Use dashed `polarplot` lines, NOT filled patches. Patch drawn with Cartesian `r*cos(θ)` / `r*sin(θ)` on polar axes produces X-shaped artifacts when `r - err < 0`.

```matlab
lc = brighten(c, 0.5);
hold(pax, 'on');
polarplot(pax, theta, r + err, '--', 'LineWidth', 0.8, 'Color', lc, 'HandleVisibility', 'off');
polarplot(pax, theta, max(r - err, 0), '--', 'LineWidth', 0.8, 'Color', lc, 'HandleVisibility', 'off');
hold(pax, 'off');
```

## varargin for Arbitrary Integration Ranges

Use `varargin` so callers can pass any number of `[f_lo, f_hi]` ranges. Column naming is backward-compatible with existing callers that read `IntegratedIntensity` / `IntegratedIntensity2`.

```matlab
function dataTable = computeFFTAndIntegrate(dataTable, time_cutoff_ps, varargin)
    integration_ranges = varargin;
    n_ranges = length(integration_ranges);

    for k = 1:n_ranges
        dataTable.(intColName(k)) = zeros(height(dataTable), 1);
    end
    % ... FFT loop per trace ...
    for k = 1:n_ranges
        rng = integration_ranges{k};
        dataTable.(intColName(k))(i) = trapz(freq(idx_s:idx_e), abs(fft_mag(idx_s:idx_e)));
    end
end

function name = intColName(k)
    if k == 1,     name = 'IntegratedIntensity';
    elseif k == 2, name = 'IntegratedIntensity2';
    else,          name = sprintf('IntegratedIntensity%d', k);
    end
end
```

Existing call sites `computeFFTAndIntegrate(tbl, cutoff, r1, r2)` work unchanged.

## When to Use

Any MATLAB R2025a script involving:
- Multi-file scans loaded incrementally (in-progress data)
- Polar plots inside grid layouts
- Color-coded region highlighting in time/frequency plots
- Error bound visualization on polar data
- Helper functions that need to accept N frequency bands

Also load this skill at the start of any work in `~/Documents/MATLAB/`
(the `+thz` package) or any analysis script in
`~/Documents/Scientific Data/` that calls into it — the package layout
section above is the canonical reference for which subpackage owns
which function.
