# MATLAB Figure Export Label Sizing

**Extracted:** 2026-05-01
**Context:** Exported MATLAB figures have clipped axis labels

## Problem
MATLAB's default axis font size (~12pt) causes labels to get cut off in `exportgraphics` output, especially for tiledlayout figures with compact padding and long ylabel strings.

## Solution
Add at the top of every plotting script (after `clc; clear; close all;`):
```matlab
set(groot, 'defaultAxesFontSize', 11);
```

Also:
- Keep ylabels short: `"FFT power @ 3 THz"` not `"Integrated FFT power (2.5–3.5 THz)"`
- Use FontSize 8 for text annotations on plots
- Never use FontSize 15+ for labels

## When to Use
- Any MATLAB script that exports figures via `exportgraphics`
- When labels appear clipped or overlapping in exported PNGs
