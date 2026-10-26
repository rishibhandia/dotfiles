# Plotting Recipes

**Sources:** consolidated from learned/matlab-color-lightening (2026-03-15), learned/matlab-polar-in-tiledlayout (2026-03-15), learned/matlab-plot-region-highlighting (2026-03-15), learned/matlab-figure-export-sizing (2026-05-01), learned/matlab-figure-font-sizes (2026-04-08).
**Updated:** 2026-10-24

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

## `exportgraphics` Resolution — keep PNGs under 2000 px

Claude's image inspection rejects any PNG over 2000 px per dimension
once a session contains many images — and a single oversized image in
the conversation blocks ALL later image reads until compaction.
Slide-figure exports at 220 dpi silently cross this (13.5 in × 220 dpi
= 2970 px) and stalled the NbOI2 deck session (2026-06).

Rule: **`Resolution` × figure width (inches) < 2000**.

```matlab
% 13.5-in-wide slide figure -> 144 dpi (1944 px); 11-in -> up to 180 dpi
exportgraphics(fig, path, 'Resolution', 144);
```

144 dpi is still ~1.5× oversampled for a figure shown 1260 pt wide on a
1920×1080 Keynote slide — no visible quality loss.

## `\hbar` needs the latex interpreter

The default `tex` interpreter has no `\hbar` — it emits SceneNode
warnings and a missing glyph. Switch just that string to latex and wrap
in `$...$`:

```matlab
text(x, y, '$\hbar\Omega$', 'Interpreter', 'latex', 'FontSize', 14);
```

Mixing interpreters within a figure is fine: keep ordinary labels on
`tex`; only strings using latex-only macros (`\hbar`, `\mathcal`, ...)
need `'Interpreter', 'latex'`.

`\parallel` and `\perp` are also latex-only — the `tex` interpreter
warns "not valid interpreter syntax" and drops them. Same fix: that
string gets `'Interpreter', 'latex'` with e.g. `$\delta P \parallel P$`.

Derivative primes in a single-quoted latex string need FOUR quotes per
double-prime: MATLAB collapses `''` → `'`, so `F''''(P_s)` is what
renders as `F''(P_s)`. e.g. `'$\omega_0^2 = F''''(P_s)\,/\,m_p$'`.
## THz / TA plotting conventions

User has standardized on the following defaults across NbOI2 campaigns.
Apply them automatically; only deviate when asked.

### 2D TA maps: symmetric `clim`, white = 0

User: *"in the future for 2D maps, always set clim to be symmetric
such that white is the zero color. can you update all the scans for
that?"* Use a diverging colormap and force the limits to ±max(|data|).

```matlab
M = max(abs(deltaSignal(:)));
imagesc(time_ps, wavelength_nm, deltaSignal)
clim([-M M])
colormap(redbluecmap)   % or any diverging map
colorbar
```

### Wavelength-coded line plots: blue = short λ, red = long λ, no yellow

User: *"a color map that doesn't use yellow in the center... when we
going from red to blue it should flow short wavelengths should be blue
not longer"*. The pattern that satisfies this is `plasma` sliced to
drop the bright-yellow end:

```matlab
fullCmap = plasma(512);
cmap     = fullCmap(52:410, :);     % trims yellow upper end
idx      = round(linspace(1, size(cmap,1), numel(wavelengths)));
lineColors = cmap(idx, :);
```

Add a horizontal `yline(0, ':k', 'HandleVisibility', 'off')` baseline
per offset trace and label the wavelength **next to the trace**
(`text(...)`), rather than relying on a colorbar — the colorbar adds
visual noise to multi-trace plots.

### Stacked / offset waterfalls for time-trace families

When plotting a family of related traces (fluence series, multiple
wavelengths), offset them vertically. User has said both *"can you
make them offset, its hard to read"* and *"they aren't stacked in the
bottom plot"* — meaning the FFT panel in a paired time/FFT figure
should be stacked the same way as the time panel.

```matlab
offset = 1.2 * max(abs(traces(:)));
for ii = 1:nTraces
    plot(t, traces(:,ii) + offset*(ii-1), 'Color', lineColors(ii,:))
    yline(offset*(ii-1), ':k', 'HandleVisibility', 'off')
    text(t(end), offset*(ii-1), sprintf(' %g nm', wavelengths(ii)), ...
         'FontSize', 8, 'VerticalAlignment', 'middle')
end
```

### "De-emphasized" FFT overlay

When a reference trace (typically a pump-only scan, filename pattern
`test_m*_DR_*` in the NbOI2 campaigns) is plotted as background under
a data FFT, use **reduced alpha** so it reads as a guide rather than
competing for attention:

```matlab
plot(freq, abs(ref_fft), 'Color', [0.5 0.5 0.5 0.35], 'LineWidth', 1.0)
hold on
plot(freq, abs(data_fft), 'k', 'LineWidth', 1.5)
```

(MATLAB accepts a 1×4 RGBA color in modern releases. If using an older
version, fall back to a light gray `[0.7 0.7 0.7]` with a thinner
line.)

### Don't crop the rising edge

On pump-probe time traces, keep enough pre-zero data to show the
rising edge cleanly. Don't trim the plot window to "just the
oscillations" — the rising edge is part of the diagnostic.

### Save to `Figures/`, repeatable filenames

Every plotting script writes PNGs to a sibling `Figures/` directory.
**Use repeatable filenames** — each rerun overwrites the file.
User explicitly reversed the earlier "don't overwrite" rule on
2026-05-20: *"I prefer each figure has a repeatable name so it gets
updated every time you run the script."*

```matlab
figDir = fullfile(scriptDir, 'Figures');
if ~exist(figDir, 'dir'); mkdir(figDir); end
exportgraphics(fig, fullfile(figDir, 'TA_summary.png'), ...
               'Resolution', 200)
```

For loops over multiple input files, build the filename from the
input stem so each input gets its own (still-repeatable) output:

```matlab
[~, h5stem] = fileparts(h5name);
exportgraphics(fig, fullfile(figDir, sprintf('%s_TA.png', h5stem)), ...
               'Resolution', 200)
```

**Exception:** keep timestamps on **notebook-entry text files**
(`Notebook_Entries/*.txt`) — those are an audit trail of what was
in the lab notebook at each point in time and must not be overwritten.

### Hardcoded numeric ranges → variables

Any wavelength window or time range that appears more than once must
be pulled into a named variable at the top of the script. User:
*"change the [520 655] to [500 700]... store it as a variable so I can
only change it once."*

```matlab
% Top of script
WL_RANGE_NM   = [500 700];
TIME_RANGE_PS = [-1 10];

% Then reference WL_RANGE_NM and TIME_RANGE_PS everywhere downstream
```

---

## When to Use

Any plotting script in `~/Documents/Scientific Data/` or anywhere
`thz.plotDefaults()` is in effect. Particularly:

- Multi-panel tiled comparisons that include polar plots
- Time-trace and FFT plots with marked-region overlays
- Figures bound for `exportgraphics` (paper/poster output)
- Error-bound visualization on polar data
- THz/TA time-trace + FFT pairs (stacked offsets, de-emphasized
  reference overlay)
- 2D TA maps (symmetric `clim`, diverging colormap)

## Splitting a saved figure into panel pieces (added 2026-09-18)

`copyobj(fig, groot)` duplicates a whole figure with the `allchild` order preserved, so a panel can be exported by deleting every top-level object outside its group on the copy and calling `exportgraphics(copy, 'x.pdf', 'ContentType', 'vector', 'BackgroundColor', 'none')`, which crops tightly to what is left. Grouping rule that worked for eight manuscript figures: the axes that owns each "(x)" panel-letter text anchors a panel; every unlabelled object (colorbars, side spectra, polar axes under a label overlay) joins the labelled axes with the smallest rectangle gap in centimetres (zero when overlapping). Stacked panels sharing an x axis get an extra merged piece.

Two traps that produced absurd pages:

- The tight bounding box of a vector export includes text objects parked far outside their axes limits. They are invisible in the full figure but inflate the crop (two dead labels at y = 212 in an axes with ylim [-0.2 4] gave a 228 x 4211 pt PDF). Before exporting, delete text in data units whose position lies more than half a range beyond the axes limits, and fix the builder that drew them.
- An invisible full-page axes used as a label carrier (e.g. a colorbar label placed in page centimetres) overlaps every panel, so nearest-neighbour grouping attaches it to the first one. Treat axes covering more than 80 % of the page as overlays: keep them in every group but delete their text objects outside the group's bounding box (+0.6 cm), and drop the overlay when nothing is left.

## Sectioned maps with their own colour bars, and edges that line up (added 2026-09-21)

Splitting one delay map into adjacent sections with separate colour scales (e.g. the incoherent transient and the ringing, each on the full range of its own window): give each section its own axes with widths proportional to its delay span so the picoseconds per centimetre match; set the gap between them to zero so the shared border marks the split; put each colour bar against its own map so ownership is unambiguous (bar I on the left edge of map I, bar II on the right edge of map II) and tag the bars underneath, where nothing else lives, rather than above where they collide with the row above. A trace panel above the maps is drawn as two axes with identical y limits placed exactly over the two maps, `linkaxes` per pair, so every delay registers with the map below; one continuous trace, split for display only.

Two MATLAB facts found on the way:

- A manually positioned `colorbar` draws its tick labels on its right whatever `AxisLocation` says. For a bar whose values must sit on its left, set `cb.Ticks = []` and write the values as right-aligned `annotation('textbox', ...)` entries at the bar's top, middle and bottom.
- Plot boxes in different pieces line up only if their margins are absolute centimetres divided by each piece's own width (`[m(1)/W, ..., (W - sum(m))/W, ...]`), not shared normalized fractions; a 0.185 fraction is 0.78 cm in a 4.2 cm piece and 1.59 cm in an 8.6 cm one.

## A table under a row of maps, and title collisions (added 2026-10-24)

Numbers that compare several maps (e.g. each map's peak heights relative to its own reference peak) read better as a table under the maps than as a second title line per map ("0.87 : 1 : 0.72 : 0.62" means nothing without a legend). Use a nested `tiledlayout` so the colour bar stays beside the maps only, and draw the table as text in an axis-off axes, which exports as vectors (a `uitable` does not reliably appear in `exportgraphics` output):

```matlab
layoutOuter = tiledlayout(fig, 2, 1, TileSpacing="compact", Padding="compact");
layoutMaps = tiledlayout(layoutOuter, 1, numMaps, TileSpacing="compact", Padding="compact");
layoutMaps.Layout.Tile = 1;
for k = 1:numMaps
    ax = nexttile(layoutMaps);  ...                      % maps, one short title line each
end
bar = colorbar(ax);  bar.Layout.Tile = "east";            % east of the INNER layout: spans the maps only
title(layoutOuter, ["what the maps are", "what the table is"], FontSize=9);

axTable = nexttile(layoutOuter, 2);
axis(axTable, "off");  set(axTable, XLim=[0 1], YLim=[0 1]);
columnX = 0.30 + (0:numMaps-1) * 0.17;                    % value columns; row names at x = 0.02
rowY = 0.55 - (0:numRows-1) * 0.12;
text(axTable, 0.02, 0.97, "caption of the table", VerticalAlignment="top");
for k = 1:numMaps
    text(axTable, columnX(k), 0.81, header(k), FontWeight="bold", HorizontalAlignment="center");
    text(axTable, columnX(k), 0.71, subheader(k), HorizontalAlignment="center", Color=[0.35 0.35 0.35]);
end
line(axTable, [0.02 columnX(end) + 0.08], [0.645 0.645], Color=[0.5 0.5 0.5]);
% ... one text() per cell, sprintf("%.2f", value), HorizontalAlignment="center"
```

The outer rows are equal in height, so size the figure for the taller of the two (here 27 x 11.6 cm for four 1:1 maps and a five-row table) and place the table rows in normalized units with room between header, rule and rows; shrinking the figure to remove white space above the table made the header overlap its caption.

Collisions to check on every exported PNG, not in the live window:

- A centred multi-line `title` wider than its axes spills into the neighbouring panel and loses its first characters at the figure edge ("ι) a x² model" for "(a) a x² model"); shorten the longest line rather than shrinking the font.
- Two side-by-side panels with long `xlabel`s run into each other in the gap ("...drive)Drive scale factor"); give each a two-line label (`xlabel(ax, ["Drive scale factor s", "(definition)"])`) and put the long definition in the layout title.
- Log axes spanning about one decade label only one tick (10^3); set `XTick` to the simulated values with `XTickLabel=compose("%.0f", values)` so every point is readable.
