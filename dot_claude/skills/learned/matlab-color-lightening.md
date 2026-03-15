# Color Lightening in MATLAB R2025a

**Extracted:** 2026-03-15
**Context:** MATLAB R2025a — lightening an RGB color triplet for error bounds, shading, etc.

## Problem
`lighten()` does not exist in MATLAB (R2025a or earlier). Calling it gives:
```
Unrecognized function or variable 'lighten'
```

## Options

### 1. `brighten(c, beta)` — recommended for uniform lightening
Works on any N×3 color matrix. Positive `beta` (0–1) lightens, negative darkens.
```matlab
light_color = brighten(c, 0.5);   % c is a 1×3 RGB triplet
```
Consistent: always lightens regardless of the base color's starting lightness.

### 2. `fliplightness(c)` — R2025a built-in, but FLIPS, not lightens
```matlab
newcolor = fliplightness(c);
```
**Caveat:** This darkens light colors AND lightens dark colors. Not suitable when you always want a lighter version of the same hue — it produces inconsistent results across a color set.

### 3. Manual formula (fallback)
```matlab
light_color = c + (1 - c) * 0.5;   % blend toward white
```
Equivalent to `brighten` at beta≈0.5 for most colors.

## When to Use
When plotting error bounds, confidence bands, or secondary lines in the same hue as the primary line (e.g. dashed ±σ lines around a polar plot main line).
