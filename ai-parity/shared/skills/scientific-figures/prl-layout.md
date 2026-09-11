# PRL Figure Layout and Annotation Guide

**Updated:** 2026-09-10
**Context:** single-column PRL figures built by one MATLAB entry point per
figure (`buildPRLFig<N>.m`) that regenerates pieces and a rough; learned on the
NbOI2 Fig 1 and Fig 4 rebuilds. Complements the faithfulness rules in
`SKILL.md`; those always win.

## Layout mechanics

- One LAYOUT block at the top of the script holds every size in cm. Heights
  cascade bottom-up (each panel's y = previous y + height + gap) and the page
  height is the sum, so adding, removing or cropping a panel never needs manual
  re-spacing. Print the resulting positions at the end of the build.
- Single column W = 8.6 cm. Map panels 6.05 cm wide with the colorbar at one
  fixed x (7.35 cm) so bars align down the page; xlabel clearance 0.92 cm.
- 2D maps at 1:1 data aspect (1 ps = 1 ps, 1 THz = 1 THz). Shorten the page by
  cropping the displayed WINDOW, never the color range; clim = full range of the
  displayed window, symmetric for signed data. Any saturation is a named constant
  in the script and a sentence in the caption.
- A quantity label inside the panel (e.g. `E_NL`, top-left, white box) when the
  plotted quantity is not obvious from the axis labels.

## Raster panels from renders

- Trim whitespace in the renderer (frame size, camera shift), not by cropping
  the file, so the pipeline stays reproducible. Stage as 635 dpi TIFF (`sips`).
- The build reads the staged image's pixel size (`imfinfo`) to set the panel
  height; never hard-code the render resolution in two places.

## Stacked panels sharing an axis

- A 1D cut above its map: identical x-limits, x tick labels only on the lower
  panel, gap >= 0.3 cm so the upper panel's "0" and the lower panel's top tick
  do not touch, two or three y ticks on the small panel, keep "(arb. units)" in
  the y-label. It is a reading aid for the map, not independent evidence; say
  so in the caption.

## Annotations

- Text over maps sits on white background boxes (`BackgroundColor`, `Margin`).
- Markers MarkerSize 8; filled arrowheads via `prl_solidArrow`, which draws the
  head in data units and therefore needs a 1:1 aspect panel.
- Nominal coordinates in labels (3.2, not 3.27) when the marker is nominal;
  physical names (rectification, SHG, non-rephasing) go on the 1D cut where
  there is room, coordinates on the map.
- Pulse markers in time maps: arrows NORMAL to the wavefront (propagation
  direction), offset beside the streak so the data stay visible; a fixed pulse
  gets a horizontal arrow, a delayed pulse a 45-degree one.
- Frequency-vector labels (nu_B, +nu_A, -nu_A) beside the vectors, away from
  the circles.
- After EVERY rebuild view the rough PNG at 300 dpi and hunt collisions: panel
  letter vs annotation, adjacent tick labels across a shared axis, label vs
  circle, label vs peak. Fix by moving text into quiet regions of the data
  (between peaks, below a word label), never by shrinking fonts.

## Notation

- Transmission as DeltaT/T_0 (not DeltaI/I_0); never "carrier" (use omega_0,
  lambda_0, "center frequency"); frequency axes as nu; y-labels "|FFT| (arb.
  units)"; no exclamation marks; panel letters only on the rough.

## Process

- Each style step is one atomic commit carrying the script, the pieces and the
  rough files together; try a variant, view it, keep or revert.
- The figure's `ASSEMBLY.md` keeps the layout tree with y-ranges, piece sizes,
  disclosed exceptions, the conventions carried over, and the open caveats
  that constrain what the caption may claim.
