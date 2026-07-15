---
name: scientific-figures
description: >-
  Rules for producing publication-quality scientific figures (line plots, 2D
  intensity maps, polar/RA plots, schematics) that faithfully represent
  measured data. Use whenever creating, editing, or reviewing a figure or plot
  for a paper, presentation, or report in MATLAB, Python/matplotlib, or Blender.
  Always represent data faithfully unless the user explicitly asks otherwise:
  never silently clip or saturate color ranges, interpolate data images, mirror
  or symmetrize measurements, or fill gaps. Also apply Hoffman/Tufte figure
  craft, accessible palettes, final-size typography, labeled units and
  colorbars, and vector export.
---

# Scientific figures

Treat a scientific figure as a representation of evidence, not an illustration.
Use the `matlab` skill for MATLAB-specific implementation and `matlab-runner`
for headless execution and output inspection.

## Cardinal rule

Always represent the data faithfully unless the user explicitly requests a
different presentation. If a choice changes what a reader would infer the data
to be, do not apply it silently.

- **Do not clip or saturate color ranges.** Span the full data range, or use
  symmetric `±max(abs(data))` limits for diverging-at-zero data. Do not use
  percentile limits to make a weak signal look stronger. If the user requests
  clipping, disclose it.
- **Keep measured pixels honest.** Use MATLAB `imagesc` or matplotlib
  `imshow(interpolation='none', rasterized=True)` for data images. Do not smooth
  or interpolate them for appearance.
- **Do not manufacture symmetry or samples.** Do not mirror rotational data,
  duplicate angles, fill gaps, or fabricate points. Close loops only using real
  measured endpoints.
- **Disclose processing.** State detrending, normalization, background
  subtraction, smoothing, filtering, and binning. Ask first if a transformation
  could add, remove, or hide features.
- **Zoom rather than silently decimating.** Use a narrower axis window to expose
  fine structure; retain the complete record for calculations such as FFTs.
- **Use real statistics for uncertainty.** State offsets in waterfall plots or
  draw a faint zero line for each trace.

## Figure craft

- Choose the final physical size first: for example, PRL single-column 8.6 cm
  or double-column 17.2 cm. Avoid rescaling after layout.
- Use Arial or another explicitly approved sans-serif font, at least 6 pt at
  final size and preferably 7–8 pt. Keep typography consistent across a set.
- Export vector PDF and, when assembling in Illustrator, SVG. Rasterize only
  the measured image layer while retaining vector axes and annotations.
- Label every axis with units, for example `Delay (ps)`, `ΔI/I₀`, or
  `Frequency (THz)`.
- Give every 2D image a numerically labeled colorbar with units. Use an accurate
  numbered length scale bar where spatial scale matters.
- Prefer direct horizontal labels or concise legends. Avoid decorative boxes,
  hatching, and chart junk.
- Avoid red–green encodings. Use a colorblind-safe palette; use a white-centered
  diverging palette such as reversed RdBu for signed data.

## Assembly-piece workflow

When building a figure for Illustrator, export each panel separately as PDF and
SVG at its final placed dimensions. Do not bake panel letters or titles into the
pieces. Add those during assembly. Keep a per-figure `ASSEMBLY.md` describing
layout and a draft caption for every sub-part in order.

## MATLAB helper pattern

Use the configured MATLAB version for this setup (currently R2026a) and verify
the toolchain before falling back to an older release. Reuse project helpers
where available:

- `prl_style()` for typography, line weights, and a consistent accessible palette.
- `prl_exportPiece(fig, outBase, wCm, hCm)` for exact-size PDF and SVG output.
- `prl_honestImage(ax, x, y, C)` for an uninterpolated, correctly oriented image.
- Set signed image limits from the full range, for example
  `cl = max(abs(C(:))); clim(ax, [-cl cl]);`.

## Pre-ship checklist

- [ ] Color limits span the full data unless explicitly disclosed otherwise.
- [ ] No interpolation, mirroring, symmetrizing, gap filling, or fabricated points.
- [ ] All processing is disclosed.
- [ ] Every axis has units and every 2D map has a labeled colorbar.
- [ ] Typography is legible at final size and output uses appropriate vector layers.
- [ ] Colors remain distinguishable without red–green discrimination.
