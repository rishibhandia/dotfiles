# Transient Absorption Workflow

**Sources:** consolidated from learned/ta-fft-frequency-axis (2026-04-08, fixed in package 2026-05-03), learned/ta-sideband-analysis (2026-05-01), learned/matlab-ta-fluence-scaling (2026-05-01), learned/matlab-shg-normalization (2026-03-15).
**Updated:** 2026-05-04

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

## When to Use

- Broadband TA data with coherent phonon oscillations
- SHG vs transmission sideband structure comparisons
- Fluence-dependent phonon scaling (χ² vs χ³ identification)
- SHG pump-probe scans where the probe efficiency varies with angle
- Any FFT on TA traces where the time vector may include negative delays
- Any analysis script that calls into `thz.io.TAData`, `thz.ta.*`, or
  `thz.fft.*` for transient-absorption work
