# MATLAB Figure Font Size Preferences

**Extracted:** 2026-04-08
**Context:** MATLAB plot formatting conventions

## Problem
Oversized font sizes (15+ pt) on axis labels and titles make figures look unprofessional and crowd the plot area.

## Solution
- **Axis labels and titles:** Use MATLAB default font sizes (~10-11 pt). Do not set `FontSize` on labels/titles unless the user explicitly asks.
- **Text annotations on plots:** Use `FontSize` 8 for `text()` annotations placed directly on the figure.
- **Never** use `FontSize` 15 or larger for axis labels or titles.

```matlab
% Good — rely on defaults for labels
xlabel('Wavelength (nm)')
ylabel('\DeltaA (mOD)')
title('Transient Spectrum')

% Good — small font for annotations
text(x, y, 'peak', 'FontSize', 8)
```

## When to Use
- Any time you create or modify MATLAB figures
- When setting font sizes for labels, titles, or annotations
