---
name: disc_ft dynamic nfft sizing
description: Fix "Zero Padding value is smaller than length of data" when signal lengths vary across loaded files
type: feedback
---

# disc_ft: Dynamic nfft Sizing When Signal Lengths Vary

**Extracted:** 2026-03-20
**Context:** MATLAB scripts that load multiple files of different lengths before computing FFTs

## Problem

`disc_ft(signal, nfft, @rectwin)` throws:
> "Zero Padding value is smaller than length of data, please use larger zero padding value"

when any signal is longer than `nfft`. This happens when loading files from different
scan sessions that have different point counts (e.g. 295 vs 1225 rows), or when using
a "plot N most recent files" pattern where file lengths are unknown in advance.

## Solution

Compute `nfft` dynamically after loading all signals, rounding up to the next power of 2:

```matlab
maxLen = max(cellfun(@(s) length(s.signal), scans));
nfft   = 2^nextpow2(maxLen);
```

Or if data is stored in a cell array of vectors:

```matlab
nfft = 2^nextpow2(max(cellfun(@length, signalCells)));
```

## When to Use

Any script that loads an unknown or variable number of files before calling `disc_ft` —
e.g. "plot N most recent files" scripts, graceful loaders that skip missing files, or
scripts combining data from different scan sessions. Fixed `nfft=1024` is fine only when
all files are guaranteed shorter than 1024 points.
