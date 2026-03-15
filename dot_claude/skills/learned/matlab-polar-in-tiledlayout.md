# Polar Axes Inside tiledlayout

**Extracted:** 2026-03-15
**Context:** MATLAB R2025a — placing `polarplot` inside a `tiledlayout` grid

## Problem
`tiledlayout` + `nexttile` creates Cartesian axes. `polarplot` called inside a tile still creates a Cartesian axes context, not a proper polar axes. There is no direct `polaraxes` support as a `nexttile` target.

## Solution
1. Call `nexttile` to get a temporary Cartesian axes and capture its `.Position`
2. `delete` that axes
3. Create `polaraxes('Parent', fig, 'Position', pos)` manually at the same position
4. Call `polarplot(pax, ...)` on the returned polar axes handle

```matlab
compFig = figure(1);
tl = tiledlayout(compFig, 3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

for k = 1:3
    ax_tmp = nexttile(tl, 2*k-1);
    pos = ax_tmp.Position;
    delete(ax_tmp);
    pax = polaraxes('Parent', compFig, 'Position', pos);
    polarplot(pax, angles_rad, r, '-o', 'LineWidth', 2, 'Color', color);
    title(pax, 'My Title', 'FontSize', 9);
    set(pax, 'FontSize', 9);
end
```

## Caveats
- Do NOT call `ylabel(pax, ...)` on polar axes — it errors. Use `title` instead.
- The tile spacing/padding in `tiledlayout` affects the position captured, so set those before looping.
- `exportgraphics` on the parent figure exports all tiles correctly.

## When to Use
Any time you need multiple polar plots in a grid comparison figure (e.g. normalized vs unnormalized polar plots side by side for multiple frequency ranges).
