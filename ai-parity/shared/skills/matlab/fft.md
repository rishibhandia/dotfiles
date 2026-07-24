# FFT in Tables: `thz.fft.disc_ft` Conventions

**Sources:** consolidated from learned/matlab-disc-ft-nfft-sizing (2026-03-20), learned/matlab-datatable-row-vector-convention (2026-03-13).
**Updated:** 2026-05-04

How `thz.fft.disc_ft` and `thz.fft.rfftFreq` interact with multi-trace
tables that store FFT results alongside time-domain data.

## Output length is fixed by `nfft`

`thz.fft.disc_ft(signal, nfft, @rectwin)` and
`thz.fft.rfftFreq(time, nfft)` both output exactly **`nfft/2 + 1`**
points regardless of input signal length. That fixed-output property
lets you pre-allocate result columns as matrices and index by row.

For `nfft = 1024`, the output length is `513`.

## Datatable row-vector convention

Default to storing per-trace FFT results as **rows of a pre-allocated
matrix**, not as cell entries. This keeps indexing consistent with
`Time_ps` and `Delta_E` (which are already matrix rows in the loaders)
and avoids the `{i}` vs `(i,:)` mixing that cell-array storage forces.

```matlab
nfft     = 1024;
nfft_out = nfft / 2 + 1;   % = 513

dataTable.FullFreq  = zeros(num_traces, nfft_out);
dataTable.FullFFT   = zeros(num_traces, nfft_out);  % complex ok
dataTable.TruncFreq = NaN(num_traces, nfft_out);    % NaN sentinel = failed truncation
dataTable.TruncFFT  = NaN(num_traces, nfft_out);

% Assign as rows
dataTable.FullFreq(ii, :) = thz.fft.rfftFreq(time_ps, nfft);
dataTable.FullFFT(ii, :)  = thz.fft.disc_ft(delta_e, nfft, @rectwin);

% Read back as rows
if ~isnan(dataTable.TruncFreq(ii, 1))
    plot(dataTable.TruncFreq(ii, :), abs(dataTable.TruncFFT(ii, :)));
end
```

Use `NaN` as the sentinel for "this row's FFT couldn't be computed"
(e.g. truncation failed because the signal was too short). Test with
`isnan(...(ii, 1))` — checking the first column is enough.

## Zero-padding error: signal longer than `nfft`

If a single signal is longer than `nfft`, `thz.fft.disc_ft` errors:

> Zero Padding value is smaller then length of data, please use larger zero padding value

This happens when loading files from different scan sessions with
different point counts (e.g. 295 vs 1225 rows), or when extending a
"plot N most recent files" pattern where lengths are unknown ahead of
time.

**Fix:** bump `nfft` to a power of 2 large enough for the longest
signal you actually plan to FFT, and use that one `nfft` everywhere
(so all rows share the same frequency axis):

```matlab
maxLen = max(cellfun(@length, signalCells));
nfft   = 2^nextpow2(maxLen);
```

Don't try to use a different `nfft` per signal — you'll lose the
shared frequency axis and the row-vector convention above stops
working.

## When to Use

- Any script that batches FFTs over a `dataTable` with one row per
  trace (the typical NbOI2 pump-probe / TA workflow)
- Whenever `thz.fft.disc_ft` errors with the zero-padding message
- When deciding between cell vs matrix storage for FFT results — the
  matrix-of-rows convention is the default in this codebase

## Output Orientation: disc_ft and rfftFreq Both Return Rows

**Updated:** 2026-07-24

As of 2026-07-24 (`refactor!: disc_ft returns row vectors`), `thz.fft.disc_ft`
and `thz.fft.rfftFreq` BOTH return **row** vectors, matching the
row-per-trace table convention. `appliedWindow` (disc_ft's 2nd output) is a
row too. Internally disc_ft still computes in column form (the column window
would implicit-expand a row X into an NxN matrix) and transposes once on
return.

```matlab
% Row-per-trace accumulation — NO transposes anywhere:
currentFFT  = disc_ft(y, 128, @hanning);    % row
currentFreq = rfftFreq(t, 128);             % row
FFT       = [FFT; currentFFT];
frequency = [frequency; currentFreq];
```

Historical context: before 2026-07-24 disc_ft returned a column, so call
sites compensated with `disc_ft(...).'` — and six TiSe2 scripts wrongly
copied that transpose onto `currentFreq` too, stacking the frequency axis
into one tall 65N-by-1 column and breaking `table(frequency, FFT, ...)` with
"All table variables must have the same number of rows". If old code errors
that way after a library update, delete stray `.'` on BOTH accumulators.
Do NOT re-add `.'` to disc_ft results in old scripts you revive — it now
produces a column and breaks `[FFT; ...]` stacking loudly.
