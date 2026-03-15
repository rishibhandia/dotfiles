# Plot Region Highlighting with Patch

**Extracted:** 2026-03-15
**Context:** MATLAB — visually marking regions of interest in time-trace and FFT waterfall plots

## Pattern

### Time trace — highlight the FFT'd region (after cutoff)
Plot all traces first, then add a grey semi-transparent patch over the analyzed region:
```matlab
hold on;
for i = 1:num_traces
    plot(time, signal + offset*(i-1), ...);
end
yl = ylim;
t_end = time(end);
patch([time_cutoff t_end t_end time_cutoff], [yl(1) yl(1) yl(2) yl(2)], ...
    [0.5 0.5 0.5], 'FaceAlpha', 0.12, 'EdgeColor', 'none', 'HandleVisibility', 'off');
ylim(yl);   % restore — patch can expand limits
hold off;
```

### FFT plot — highlight integration windows
Use per-range colored patches matching the polar plot colors:
```matlab
integration_ranges = {[2.9, 3.3], [4.1, 4.5], [1.6, 2.0]};
region_colors      = {[0.8 0.1 0.1], [0.1 0.3 0.9], [0.1 0.7 0.3]};

yl = ylim;
for k = 1:length(integration_ranges)
    rng = integration_ranges{k};
    patch([rng(1) rng(2) rng(2) rng(1)], [yl(1) yl(1) yl(2) yl(2)], ...
        region_colors{k}, 'FaceAlpha', 0.15, 'EdgeColor', 'none', 'HandleVisibility', 'off');
end
ylim(yl);
```

## Key Details
- Always capture `ylim` AFTER plotting all data lines, then restore it after adding patches
- `HandleVisibility', 'off'` prevents patches from appearing in the legend
- Apply the same highlighting in both standalone figures AND summary tiled layout tiles
- Use `FaceAlpha` 0.10–0.15 for FFT windows (more transparent), 0.12 for time cutoff

## When to Use
Any spectroscopy script with a time cutoff and/or frequency integration windows that you want to visually communicate to the reader.
