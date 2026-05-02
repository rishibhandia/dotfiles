# TA Coherent Phonon Sideband Analysis

**Extracted:** 2026-05-01
**Context:** Analyzing coherent phonon sidebands in spectrally-resolved transient absorption

## Problem
When broadband pump-probe TA data shows oscillatory features at specific wavelengths, need a systematic way to identify the probe center, find sideband peaks, compute frequency shifts, and verify anti-phase behavior.

## Solution

### Workflow
1. **Find probe center** from reference spectrum peak (average `_ref.txt` files from spectra folder)
2. **Compute oscillatory power per pixel**: FFT each wavelength's time trace, integrate power in a narrow band (±0.2 THz) around the phonon frequency
3. **Find sideband peaks**: max oscillatory power on blue side (λ < center - 1nm) and red side (λ > center + 1nm)
4. **Compute shifts in THz**: `shift = c/λ_sideband - c/λ_center` where c = 2.998e5 nm·THz
5. **Phase comparison**: overlay normalized time traces at symmetric offsets (±2, ±4, ±6, ±8, ±10 nm) — anti-phase sidebands confirm derivative spectral modulation

## Example
```matlab
% Oscillatory power at each pixel
phononBand = freq > (phononFreq - 0.2) & freq < (phononFreq + 0.2);
oscPower = zeros(numel(roiIdx), 1);
for ii = 1:numel(roiIdx)
    fftPix = abs(disc_ft(ta.DeltaSignal(:, roiIdx(ii)), nfft, @rectwin));
    oscPower(ii) = sum(fftPix(phononBand));
end

% Sideband peaks
[~, bIdx] = max(oscPower(wlRoi < centerWl - 1));
[~, rIdx] = max(oscPower(wlRoi > centerWl + 1));

% Shift in THz
blueShift = 2.998e5/blueSbWl - 2.998e5/centerWl;
```

## When to Use
- Broadband TA data with coherent phonon oscillations
- Comparing SHG vs transmission sideband structure
- Fluence-dependent phonon scaling analysis
- When the user asks about vibrational sidebands, phonon coupling, or oscillatory TA features
