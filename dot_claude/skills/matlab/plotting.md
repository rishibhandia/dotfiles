# Plotting Recipes

**Sources:** consolidated from learned/matlab-color-lightening (2026-03-15), learned/matlab-polar-in-tiledlayout (2026-03-15), learned/matlab-plot-region-highlighting (2026-03-15), learned/matlab-figure-export-sizing (2026-05-01), learned/matlab-figure-font-sizes (2026-04-08).
**Updated:** 2026-05-04

Patterns for color, polar axes inside grid layouts, region highlighting,
and figure-export font sizing in MATLAB R2025a. Most of these were
extracted from NbOI2 SHG/THz pump-probe scripts.

> **Figure defaults note:** call `thz.plotDefaults()` at the top of any
> plotting script. It already sets export-safe sizes (axes 11pt, lines
> 1.5, normal weight) so you only need the font overrides below for
> non-default annotations.

## Color lightening

`lighten()` does NOT exist in MATLAB R2025a. Calling it errors:

```
Unrecognized function or variable 'lighten'
```

`fliplightness()` exists but FLIPS lightness — it darkens light colors
AND lightens dark colors, which is inconsistent across a color set.

Use `brighten` instead:

```matlab
% RECOMMENDED — uniform lightening regardless of base color
light_color = brighten(c, 0.5);   % c is 1×3 RGB; positive beta (0–1) lightens

% Manual fallback (~equivalent to brighten at beta=0.5)
light_color = c + (1 - c) * 0.5;  % blend toward white
```

Use `brighten` for error bounds, dashed secondary lines, and
confidence bands.

## Polar axes inside `tiledlayout`

`tiledlayout` + `nexttile` creates Cartesian axes. `polarplot` inside a
tile does NOT produce a proper polar axes — there's no direct
`polaraxes` support as a `nexttile` target.

Workaround:

1. Call `nexttile` → capture `.Position`
2. `delete` that axes
3. Create `polaraxes('Parent', fig, 'Position', pos)` at the same position
4. Call `polarplot(pax, ...)` on the returned handle

```matlab
fig = figure(1);
tl = tiledlayout(fig, 3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

for k = 1:3
    ax_tmp = nexttile(tl, 2*k-1);
    pos = ax_tmp.Position;       % capture BEFORE delete
    delete(ax_tmp);
    pax = polaraxes('Parent', fig, 'Position', pos);
    polarplot(pax, angles_rad, r, '-o', 'LineWidth', 2, 'Color', c);
    title(pax, 'Title Here', 'FontSize', 9);
    set(pax, 'FontSize', 9);
end
```

Caveats:

- **Never call `ylabel` on polar axes** — it errors. Use `title` only.
- The `TileSpacing`/`Padding` in `tiledlayout` affects the position you
  capture, so set those before the loop.
- `exportgraphics` on the parent figure exports all tiles correctly.

## Error bounds on polar plots

Use dashed `polarplot` lines, NOT filled patches. A patch drawn with
Cartesian `r*cos(theta)` / `r*sin(theta)` on polar axes produces
X-shaped artifacts when `r - err < 0`.

```matlab
lc = brighten(c, 0.5);
hold(pax, 'on');
polarplot(pax, theta, r + err, '--', ...
          'LineWidth', 0.8, 'Color', lc, 'HandleVisibility', 'off');
polarplot(pax, theta, max(r - err, 0), '--', ...
          'LineWidth', 0.8, 'Color', lc, 'HandleVisibility', 'off');
hold(pax, 'off');
```

## Region highlighting with `patch`

Always capture `ylim` AFTER plotting all data lines, then restore after
adding patches (patches can expand limits). Use `'HandleVisibility',
'off'` to keep patches out of the legend.

### Time trace — shade the FFT'd region (after cutoff)

```matlab
hold on;
for ii = 1:num_traces
    plot(time, signal + offset*(ii-1), ...);
end
yl = ylim;
t_end = time(end);
patch([time_cutoff t_end t_end time_cutoff], [yl(1) yl(1) yl(2) yl(2)], ...
    [0.5 0.5 0.5], 'FaceAlpha', 0.12, 'EdgeColor', 'none', 'HandleVisibility', 'off');
ylim(yl);
hold off;
```

### FFT plot — shade each integration window with per-range color

```matlab
integration_ranges = {[2.9 3.3], [4.1 4.5], [1.6 2.0]};
region_colors      = {[0.8 0.1 0.1], [0.1 0.3 0.9], [0.1 0.7 0.3]};

yl = ylim;
for k = 1:length(integration_ranges)
    rng = integration_ranges{k};
    patch([rng(1) rng(2) rng(2) rng(1)], [yl(1) yl(1) yl(2) yl(2)], ...
        region_colors{k}, 'FaceAlpha', 0.15, 'EdgeColor', 'none', 'HandleVisibility', 'off');
end
ylim(yl);
```

Recommended `FaceAlpha`: 0.10–0.15 for FFT windows (more transparent),
0.12 for time-cutoff regions. Apply highlighting in both standalone
figures AND matching tiles in summary `tiledlayout` panels so the same
region reads the same way everywhere.

## Figure fonts and `exportgraphics` sizing

Default MATLAB axis font size (~12pt) plus a `tiledlayout` with compact
padding plus a long ylabel = clipped labels in `exportgraphics` PNG/PDF
output.

`thz.plotDefaults()` already sets axes/text to 11pt and normal weight,
which is the export-safe baseline. The remaining rules:

- **Axis labels and titles:** never override; let the 11pt default win.
  Never use `FontSize 15+` on labels — that's the size that started
  clipping in the first place.
- **Text annotations on plots:** `FontSize 8` for `text()` calls placed
  directly on the figure. Anything else competes with the data.
- **Legends:** the default 10pt is fine. Crank up only when projecting.
- **ylabel content:** keep it short. `"FFT power @ 3 THz"` not
  `"Integrated FFT power (2.5–3.5 THz, normalized)"`. The former always
  fits; the latter sometimes needs manual margin tweaking.

```matlab
% Good — rely on defaults for labels
xlabel('Wavelength (nm)')
ylabel('\DeltaA (mOD)')
title('Transient Spectrum')

% Good — small font for annotations
text(x, y, 'peak', 'FontSize', 8)
```

If a particular figure needs heavier styling (e.g. for a slide), set the
relevant `set(groot, ...)` after `thz.plotDefaults()` runs, or set
properties on the specific axes/legend handle to keep the default
unchanged for the rest of the script.

## When to Use

Any plotting script in `~/Documents/Scientific Data/` or anywhere
`thz.plotDefaults()` is in effect. Particularly:

- Multi-panel tiled comparisons that include polar plots
- Time-trace and FFT plots with marked-region overlays
- Figures bound for `exportgraphics` (paper/poster output)
- Error-bound visualization on polar data
