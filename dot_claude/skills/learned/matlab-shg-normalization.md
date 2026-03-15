# SHG Probe Polarization Normalization

**Extracted:** 2026-03-15
**Context:** NbOI2 SHG pump-probe — normalizing pump-probe signals by static SHG probe efficiency

## Problem
In SHG pump-probe, the detected signal depends on both the THz-driven phonon response AND the static SHG probe efficiency at each probe polarization angle. To isolate the phonon anisotropy, divide out the static SHG.

## Pattern

### Angle mapping
The static SHG scan covers HWP 0–172.5° (24 points, 7.5° steps).
The pump-probe scan covers HWP -90° to +90° (25 points).
Map with `mod(hwpAngle, 180)`: -90° and +90° both → 90° (same waveplate orientation, physically correct).

```matlab
staticData     = readmatrix('StaticSHG');          % col1=HWP angle, col2=intensity, col3=std
staticAngles   = staticData(:, 1);
staticSHG_vals = staticData(:, 2);

dataTable.staticSHG = zeros(height(dataTable), 1);
for i = 1:height(dataTable)
    ang_mapped = mod(dataTable.hwpAngle(i), 180);
    [~, idx]   = min(abs(staticAngles - ang_mapped));
    dataTable.staticSHG(i) = staticSHG_vals(idx);
end
```

### Normalize before FFT, restore after
This is mathematically exact: FFT(signal/k) = FFT(signal)/k for scalar k > 0.
Integrated intensity recovers as: `unnorm = norm .* staticSHG` (exact).

```matlab
Delta_E_raw       = dataTable.Delta_E;
dataTable.Delta_E = dataTable.Delta_E ./ dataTable.staticSHG;

dataTable = computeFFTAndIntegrate(dataTable, time_cutoff_ps, ranges{:});

dataTable.Delta_E = Delta_E_raw;   % restore for time-domain display
```

### Recover unnormalized integrated intensities (no recomputation needed)
```matlab
unnorm_I1 = dataTable.IntegratedIntensity  .* dataTable.staticSHG;
unnorm_I2 = dataTable.IntegratedIntensity2 .* dataTable.staticSHG;
```

## Static SHG file format
3 columns: HWP angle (°), SHG intensity, std dev.
Named `StaticSHG`, `StaticSHG_Analyzer_V`, `StaticSHG_Analyzer_H`, etc.

## When to Use
Any SHG pump-probe probe-polarization scan in this project where the probe efficiency varies with angle and you want to see the intrinsic phonon anisotropy.
