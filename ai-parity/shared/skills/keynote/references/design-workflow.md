# Keynote design and verification workflow

Use this reference when creating a deck, redesigning slides, or evaluating visual quality.

## Workflow

1. Start from the user's deck or approved template whenever possible. Preserve its theme,
   slide size, fonts, colors, and recurring layout language.
2. Inventory the deck before editing. Use canvas dimensions and item geometry instead of
   guessing coordinates.
3. Run the layout audit and review every finding. Treat findings as prompts for visual
   inspection, not proof that a layout is wrong; intentional overlaps are possible.
4. Plan slide-level changes. Prefer one clear claim per slide and reuse a small set of
   layouts rather than inventing a new composition for every slide.
5. Make deterministic edits with the bridge and layout helpers.
6. Preview only changed slides, inspect the downscaled PNGs, and iterate.
7. Re-inventory and re-audit after substantial geometry or accessibility changes.
8. Export the final PDF/PPTX and verify the consumer can parse it.

## Composition

- Use the document canvas reported by the inventory. Keynote's common 4:3 canvas is
  1024x768 points; wide decks are often 1920x1080, but never assume either.
- Keep a consistent safe margin. Start near 5% of canvas width/height unless the template
  clearly establishes full-bleed content.
- Align elements to shared edges and centers. Use a simple column grid and consistent gaps.
- Preserve whitespace. Do not fill every available region merely because it is empty.
- Prefer a clear hierarchy: claim/title, primary evidence, then annotation or source.
- Avoid placing multiple unrelated charts, tables, and paragraphs on one slide.
- Use native tables for small comparison grids. For complex tables, simplify the data or
  split it across slides.

## Typography

- Match the deck's established typefaces before introducing a new font.
- As a starting point, keep titles at least 28 pt and body/custom text at least 18 pt.
  Increase these substantially for large rooms or dense scientific plots.
- Use at most two font families and a restrained set of weights.
- Use sentence case unless the template consistently uses another convention.
- Keep line lengths short enough to scan. Break prose into a claim plus compact support.
- Do not shrink type to rescue an overcrowded slide; remove or split content instead.

## Color and accessibility

- Use high text/background contrast and do not communicate meaning through color alone.
- Reuse the theme palette. Reserve one accent color for emphasis rather than coloring every
  element differently.
- Add concise accessibility descriptions to meaningful images. Mark decorative images with
  an empty description only when that is an intentional accessibility choice.
- Review audit warnings for missing descriptions, small text, edge crowding, off-canvas
  items, and strong overlaps.

## Images and scientific figures

- Crop and size images intentionally; do not distort aspect ratio unless the user requests it.
- Keep inserted raster images below 2000 px per dimension for reliable model inspection.
- Prefer vector PDF/SVG artwork when Keynote and the downstream export preserve it correctly.
- For measured-data figures, never invent, mirror, symmetrize, interpolate, smooth, or clip
  data without explicit authorization. Keep measured points distinguishable from fits and
  derived values.
- Build charts in the user's scientific plotting environment when exact axes, uncertainty,
  or publication fidelity matter; insert the verified export into Keynote afterward.

## Final review

- Inspect every changed slide at presentation size, not only as text inventory.
- Confirm titles are not clipped, images remain sharp, tables are legible, and intentional
  alignments are visibly exact.
- Check slide-to-slide consistency in title position, margins, type scale, and color.
- Confirm notes, skipped-slide state, and transitions match the user's intent.
- Verify PDF page count and PPTX archive integrity after export.
