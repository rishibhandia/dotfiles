# Transient Absorption Workflow

**Sources:** consolidated from learned/ta-fft-frequency-axis (2026-04-08, fixed in package 2026-05-03), learned/ta-sideband-analysis (2026-05-01), learned/matlab-ta-fluence-scaling (2026-05-01), learned/matlab-shg-normalization (2026-03-15).
**Updated:** 2026-05-10

End-to-end TA pump-probe analysis built on the `+thz/+ta` package. All
five primitives — `oscillatoryPower`, `findSidebands`,
`wavelengthToFreqShift`, `wireGridFieldFactor`, `fitPowerLaw` — are
documented in [`SKILL.md`](SKILL.md). This file shows how they fit
together for full workflows.

---

## FFT frequency axis on negative-going time vectors

**Status: fixed in the package.** `thz.fft.rfftFreq` wraps the time
step in `abs()` internally, so a negative-going `TimeDelays` vector
(e.g. pump-probe delays running from -5 ps to +20 ps) produces a
positive sampling rate and a monotonically increasing frequency axis
automatically.

```matlab
freq = thz.fft.rfftFreq(TimeDelays, nfft);
```

**Original problem (kept for context when reading old code):** with the
prior `dt = time(2) - time(1)` formula a negative time step gave an
inverted frequency axis. Old scripts may use the manual workaround
`dt = abs(TimeDelays(2) - TimeDelays(1))` — those can now be replaced
with a plain `thz.fft.rfftFreq` call.

If you ever build a frequency axis from scratch outside the package
(e.g. when calling MATLAB's bare `fft`), keep using the manual form:

```matlab
dt   = abs(TimeDelays(2) - TimeDelays(1));
freq = (0:nfftOut-1) / (nfft * dt);
```

---

## Canonical kinetic-trace FFT pipeline (physical units)

For "give me the FFT of this kinetic trace at one wavelength" tasks
— the spectroscopist's default ask — use this exact pipeline. It mirrors
the user's reference Python recipe (`np.fft.rfft` + `np.hanning`) and adds
the physical-units calibration (1/N normalization × 2 for one-sided
spectrum) that the Python code intentionally omits.

```matlab
% Inputs: t (delays in ps, uniform), y (kinetic at one wavelength)
N      = numel(t);
dt_ps  = abs(mean(diff(t)));                          % matches Python's abs(mean(diff(...)))
yDC    = y - mean(y);                                  % step 1: mean (DC) subtract
freq   = thz.fft.rfftFreq(t, N);                       % NFFT = N (no zero-padding)
F      = abs(thz.fft.disc_ft(yDC, N, @hann)) * (2 / N); % steps 2-5: Hann window, |rfft|, 2/N
% step 6: drop the DC bin from BOTH arrays before plotting
F      = F(2:end);
freq   = freq(2:end);
```

**Rules (DO):**
1. Mean (DC) subtract — and *only* mean subtraction. No detrending.
2. Hann window via `@hann` passed to `thz.fft.disc_ft`.
3. **NFFT = N** — do NOT zero-pad. (Zero-padding only interpolates the
   plotted spectrum; it does not improve resolution. The user's spectra
   are compared *quantitatively*, so the bin count must equal N.)
4. **`abs(...) * (2/N)`** — one-sided amplitude spectrum in physical
   units. The `2/N` is `(2 one-sided factor) / (N normalization)`. NOT
   power, NOT corrected for window coherent gain.
5. **Drop the DC (0-Hz) bin** from both `freq` and the magnitude array
   before plotting.

**Rules (DON'T):**
- Don't zero-pad (changes the implicit normalization and the bin
  density makes ratios across scans inconsistent).
- Don't apply per-trace baseline-detrending (movmean / polyfit
  subtraction) unless the user explicitly asks. The Hann window
  already suppresses the impulse-decay's spectral leakage well enough
  for typical pump-probe traces.
- Don't truncate the trace to a "post-peak window" or "oscillating
  region" unless the user explicitly asks. FFT the whole DC-subtracted
  trace.
- Don't return a power spectrum; the user wants amplitude.
- Don't normalize per-wavelength (e.g. by peak amplitude). Keep
  absolute physical units so amplitudes across wavelengths AND across
  scans are directly comparable.

**Why 2/N (not 4/N):** Hann window's coherent gain is 0.5, so a
strictly "physical" calibration that recovers the original signal
amplitude would use `4/N`. The user has explicitly chosen `2/N`
(matches `numpy.fft.rfft` with no normalization, divided by N and
doubled). This is the documented convention — apply it without
"correcting" upward to 4/N.

**Default visualization band:** trim to `freq <= 5 THz` after dropping
the DC bin, for THz/coherent-phonon work on NbOI2-class samples.

**Why no truncation / no detrend:** combined with the proper window
(Hann) and the full-trace FFT, the impulse-response decay contributes
mostly to the lowest 1–2 bins after the DC bin. Those few bins get
dropped or are visually distinct from the THz-range phonon peaks. The
result is honest — what's actually in the data — and ratios between
scans are meaningful.

For broadband per-wavelength loops (TA scans on the spectrograph), wrap
the above in a `for` loop over wavelength pixels. See
`+thz/+ta/oscillatoryPower.m` for an efficient implementation that
reuses the FFT plan.

---

## Coherent-phonon sideband analysis

When broadband pump-probe TA shows oscillatory features at specific
wavelengths, you usually want to: identify the probe center, find
sideband peaks, compute frequency shifts, and verify anti-phase
behavior between blue and red sidebands.

### Workflow

1. **Find the probe center** from the average of `_ref.txt` files in
   the spectra folder.
2. **Compute oscillatory power per pixel**: FFT each wavelength's time
   trace, integrate power in a narrow band (±0.2 THz) around the
   phonon frequency.
3. **Find sideband peaks**: max power on the blue side
   (`λ < center - 1 nm`) and red side (`λ > center + 1 nm`).
4. **Compute shifts in THz**: `c/λ_sideband - c/λ_center` with
   `c = 2.998e5 nm·THz`.
5. **Phase comparison**: overlay normalized time traces at symmetric
   offsets (±2, ±4, ±6, ±8, ±10 nm) — anti-phase confirms derivative
   spectral modulation.

### Use the package primitives

```matlab
ta = thz.io.TAData("scan.h5");

% Per-pixel oscillatory power in a band around the phonon frequency
oscPower = thz.ta.oscillatoryPower(ta, phononFreq, ...
                                   Bandwidth = 0.2, ...
                                   PixelMask = roiMask, ...
                                   Window    = @rectwin);

% Blue/red sideband peaks (excludes +/-1 nm around the probe center)
sb = thz.ta.findSidebands(oscPower, ta.Wavelengths, centerWl, ...
                          ExclusionRadius = 1);

fprintf('Blue: %.2f nm  (+%.2f THz)\n', sb.BlueWavelength, sb.BlueShiftTHz);
fprintf('Red:  %.2f nm  (%.2f THz)\n',  sb.RedWavelength,  sb.RedShiftTHz);
```

`thz.ta.wavelengthToFreqShift(lambda, lambdaCenter)` is also available
on its own (e.g. for tick labels).

### Open-coded equivalent (reference only — do not copy into new code)

```matlab
phononBand = freq > (phononFreq - 0.2) & freq < (phononFreq + 0.2);
oscPower   = zeros(numel(roiIdx), 1);
for ii = 1:numel(roiIdx)
    fftPix = abs(thz.fft.disc_ft(ta.DeltaSignal(:, roiIdx(ii)), nfft, @rectwin));
    oscPower(ii) = sum(fftPix(phononBand));
end
```

---

## Fluence dependence with wire-grid polarizers

Field factor through a wire grid:

- `F = cos²(θ)` for the field
- `I = cos⁴(θ)` for intensity

Per scan: load TAData, compute peak oscillatory power at the phonon
frequency, record the field factor, then fit
`log(P) = n*log(F) + c` for the power-law exponent.

Exponent in **field factor F**:

- `n ≈ 1` → linear in E_pump (χ² process)
- `n ≈ 2` → linear in intensity / quadratic in E_pump (χ³ process)

```matlab
% Per-scan field/intensity factors from wire-grid angle
[fieldFactors, intFactors] = thz.ta.wireGridFieldFactor(angles);

% log(P) = n*log(F) + c
[exponent, intercept, residRMS] = thz.ta.fitPowerLaw(fieldFactors, peaks);

fprintf('Exponent in field: %.2f (RMS log-resid %.3f)\n', exponent, residRMS);
```

Pass `intFactors` instead of `fieldFactors` if you want the exponent in
intensity (expect values to halve).

### Open-coded fit (reference only)

```matlab
logF     = log(fieldFactors(:));
logP     = log(peaks(:));
coeffs   = [logF ones(nScans, 1)] \ logP;
exponent = coeffs(1);
```

---

## SHG probe-polarization normalization

SHG pump-probe signal depends on **both** the THz-driven phonon
response AND the static SHG probe efficiency at each probe-polarization
angle. To isolate the phonon anisotropy, divide out the static SHG.

### Angle mapping

Static SHG covers HWP 0–172.5° (24 points, 7.5° steps); pump-probe
covers HWP -90° to +90° (25 points). Map with `mod(hwpAngle, 180)` —
−90° and +90° both map to 90° (same waveplate orientation).

```matlab
staticData     = readmatrix('StaticSHG');         % col1=HWP, col2=intensity, col3=std
staticAngles   = staticData(:, 1);
staticSHG_vals = staticData(:, 2);

dataTable.staticSHG = zeros(height(dataTable), 1);
for ii = 1:height(dataTable)
    ang_mapped = mod(dataTable.hwpAngle(ii), 180);
    [~, idx]   = min(abs(staticAngles - ang_mapped));
    dataTable.staticSHG(ii) = staticSHG_vals(idx);
end
```

### Normalize before FFT, restore after

This is mathematically exact: `FFT(signal/k) = FFT(signal)/k` for any
positive scalar `k`. Integrated intensity recovers exactly as
`unnorm = norm .* staticSHG`.

```matlab
Delta_E_raw       = dataTable.Delta_E;
dataTable.Delta_E = dataTable.Delta_E ./ dataTable.staticSHG;

dataTable = computeFFTAndIntegrate(dataTable, time_cutoff_ps, ranges{:});

dataTable.Delta_E = Delta_E_raw;   % restore for time-domain display
```

### Recover unnormalized integrated intensities (no recomputation)

```matlab
unnorm_I1 = dataTable.IntegratedIntensity  .* dataTable.staticSHG;
unnorm_I2 = dataTable.IntegratedIntensity2 .* dataTable.staticSHG;
```

### Static SHG file format

3 columns: HWP angle (°), SHG intensity, std dev. Filenames:
`StaticSHG`, `StaticSHG_Analyzer_V`, `StaticSHG_Analyzer_H`, etc.

---

## `varargin` for arbitrary integration ranges

Helpers that accept N frequency bands should use `varargin` so callers
can pass any number of `[f_lo, f_hi]` pairs. The column-naming below
is backward-compatible with existing call sites that read
`IntegratedIntensity` / `IntegratedIntensity2`.

```matlab
function dataTable = computeFFTAndIntegrate(dataTable, time_cutoff_ps, varargin)
    integration_ranges = varargin;
    n_ranges = length(integration_ranges);

    for k = 1:n_ranges
        dataTable.(intColName(k)) = zeros(height(dataTable), 1);
    end
    % ... FFT loop per trace ...
    for k = 1:n_ranges
        rng = integration_ranges{k};
        dataTable.(intColName(k))(ii) = trapz(freq(idx_s:idx_e), abs(fft_mag(idx_s:idx_e)));
    end
end

function name = intColName(k)
    if k == 1,     name = 'IntegratedIntensity';
    elseif k == 2, name = 'IntegratedIntensity2';
    else,          name = sprintf('IntegratedIntensity%d', k);
    end
end
```

Existing call sites `computeFFTAndIntegrate(tbl, cutoff, r1, r2)` work
unchanged.

---

## Auto-detect dominant FFT peak by averaging across configurations

When you don't know the exact coherent-mode frequency ahead of time
(e.g. it shifts slightly with BPF, sample alignment, or temperature),
auto-detect it from the data: average **peak-normalized** FFTs across
every (plate × probe × fluence) configuration, then `findpeaks` in a
configurable search band. Cluster nearby peaks so a single mode split
by FFT resolution doesn't appear twice.

```matlab
% Collect all FFTs, normalize each to its own peak so amplitudes
% don't bias which mode dominates the average.
allMag = [];
for r = 1:nRows
    for c = 1:nCols
        m = fftStore(r,c).mag;
        allMag(end+1, :) = m / max(m);          %#ok<AGROW>
    end
end
meanMag = mean(allMag, 1);

fmask = (allF >= fLo) & (allF <= fHi);
[~, pkIdx] = findpeaks(meanMag(fmask), 'MinPeakProminence', 0.04);
cand = sort(allF(pkIdx + find(fmask, 1) - 1));

% Merge peaks within mergeTol THz — same physical mode split by resolution
mergeTol = 0.4;
modes = []; i = 1;
while i <= numel(cand)
    cluster = cand(i); j = i + 1;
    while j <= numel(cand) && (cand(j) - cluster(end)) < mergeTol
        cluster(end+1) = cand(j); j = j + 1;       %#ok<AGROW>
    end
    modes(end+1) = mean(cluster);                  %#ok<AGROW>
    i = j;
end
```

Use the returned `modes` as centers for ±0.3 THz integration windows
in `computeFFTAndIntegrate`.

---

## Origin-forced linear vs quadratic fluence fit (1- vs 2-photon diagnostic)

`thz.ta.fitPowerLaw` (above) extracts a continuous exponent `n` in
`log(P) = n·log(F)`. When you instead want a clean "is this χ² or χ³?"
test against only two specific powers (n = 1 vs n = 2), forcing both
fits through the origin and comparing R² is more diagnostic — the
intercept-free models can't trade off slope vs offset.

```matlab
% Origin-forced y = m * x  (n = 1)  and  y = a * x²  (n = 2)
xv = fluence(:); yv = peakWeight(:);
mLin  = sum(xv    .* yv) / sum(xv.^2);
mQuad = sum(xv.^2 .* yv) / sum(xv.^4);
r2Lin  = 1 - sum((yv - mLin  * xv   ).^2) / sum((yv - mean(yv)).^2);
r2Quad = 1 - sum((yv - mQuad * xv.^2).^2) / sum((yv - mean(yv)).^2);

fprintf('Linear    y = %.3e · F   R² = %.3f\n', mLin,  r2Lin);
fprintf('Quadratic y = %.3e · F²  R² = %.3f\n', mQuad, r2Quad);
```

Plot both fit curves over the data (dotted = linear, solid = quadratic)
so the model with better visual fit is obvious. With <4 fluence points
the test is underconstrained — collect 5+ before drawing conclusions.

---

## Mislabel detection via Pearson correlation

When a scan filename is ambiguous (probe angle? pump axis?
detection-side filter?), cross-correlate the candidate against known
"good" reference scans at each possible configuration. The strongest
positive correlation reveals the true label — and a negative
correlation against the wrong reference is a strong confirmation.

```matlab
% Truncate to common time window, post-rising-edge
tStart = max([sCand.t(1), sRef.t(1), 0.5]);
tEnd   = min(sCand.t(end), sRef.t(end));
mC = sCand.t >= tStart & sCand.t <= tEnd;
mR = sRef.t  >= tStart & sRef.t  <= tEnd;
n = min(sum(mC), sum(mR));
a = sCand.y(mC); a = a(1:n);
b = sRef.y(mR);  b = b(1:n);
r = corrcoef(a, b); r = r(1, 2);
```

A correlation matrix `candidate × {reference_A, reference_B}` makes
the assignment unambiguous: each candidate should land at r > 0.8
against its true label and r ≈ 0 or negative against the wrong one.
Used in this project to flag mislabeled HWP-as-QWP scans and verify
noDetBPF redo files weren't probe-angle swapped.

---

## When to Use

- Broadband TA data with coherent phonon oscillations
- SHG vs transmission sideband structure comparisons
- Fluence-dependent phonon scaling (χ² vs χ³ identification)
- SHG pump-probe scans where the probe efficiency varies with angle
- Any FFT on TA traces where the time vector may include negative delays
- Defining integration windows without prior knowledge of the mode
  frequency (auto-peak-detection across averaged FFTs)
- Diagnosing 1-photon vs 2-photon excitation channels with limited
  fluence points (origin-forced linear/quadratic R² comparison)
- Verifying scan labels after suspected mistakes (Pearson correlation
  against known-good references)
- Any analysis script that calls into `thz.io.TAData`, `thz.ta.*`, or
  `thz.fft.*` for transient-absorption work
