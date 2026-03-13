# MATLAB Data Table: Row-Vector Convention

**Extracted:** 2026-03-13
**Context:** NbOI2 THz pump-probe analysis scripts (Transmission_800nm, QWP_HWP_Temperature_Dependence)

## Problem
MATLAB tables storing per-trace FFT results default to cell arrays when outputs vary in length. This makes indexing awkward (`{i}` vs `(i,:)`) and breaks consistency with how `Time_ps` and `Delta_E` are already stored (as matrix rows).

## Solution
Since `disc_ft(signal, 1024, @rectwin)` and `rfftFreq(time, 1024)` always output exactly `nfft/2 + 1 = 513` points regardless of input length, pre-allocate matrices and store results as rows:

```matlab
nfft     = 1024;
nfft_out = nfft / 2 + 1;   % = 513

dataTable.FullFreq  = zeros(num_traces, nfft_out);
dataTable.FullFFT   = zeros(num_traces, nfft_out);  % complex ok
dataTable.TruncFreq = NaN(num_traces, nfft_out);    % NaN = failed truncation
dataTable.TruncFFT  = NaN(num_traces, nfft_out);

% Assign
dataTable.FullFreq(i, :) = rfftFreq(time_ps, nfft);
dataTable.FullFFT(i, :)  = disc_ft(delta_e, nfft, @rectwin);

% Check truncation failure
if ~isnan(dataTable.TruncFreq(i, 1))
    plot(dataTable.TruncFreq(i,:), abs(dataTable.TruncFFT(i,:)));
end
```

## When to Use
Any time FFT results are being stored in a MATLAB table in this project. Applies to `computeFFTAndIntegrate.m` and any future helpers.
