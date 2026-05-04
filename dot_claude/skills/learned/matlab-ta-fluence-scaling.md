# TA Fluence Dependence with Wire Grid Polarizers

**Extracted:** 2026-05-01
**Updated:** 2026-05-03
**Context:** Pump fluence dependence using two wire grid polarizers to control THz field

## Problem
Need to determine power-law scaling of phonon sideband amplitude with pump field/intensity using WG angle-dependent scans.

## Solution
Field factor through a wire grid: `F = cos²(θ)` for the field, `I = cos⁴(θ)` for intensity.

For each WG angle scan:
1. Load TAData, compute oscillatory power at phonon frequency
2. Record peak oscillatory power and field factor
3. Fit `log(P) = n*log(F) + c` to get power-law exponent

Exponent interpretation:
- n ≈ 1: linear in E_pump (χ² process)
- n ≈ 2: quadratic in E_pump / linear in intensity (χ³ process)

## Example

The `+thz/+ta` package now provides both pieces:

```matlab
% Per-scan field/intensity factors from the wire-grid angle
[fieldFactors, intFactors] = thz.ta.wireGridFieldFactor(angles);

% Power-law fit: log(P) = n*log(F) + c
[exponent, intercept, residRMS] = thz.ta.fitPowerLaw(fieldFactors, peaks);

fprintf('Exponent in field: %.2f (RMS log-resid %.3f)\n', exponent, residRMS);
```

The exponent in *field factor F* tells you the order of the process:
`n ≈ 1` is `chi^2` (linear in E_pump), `n ≈ 2` is `chi^3` (linear in
intensity). Pass `intFactors` instead if you want the exponent in
*intensity* and expect to see those values halved.

### Open-coded equivalent (for reference)
```matlab
logF = log(fieldFactors(:));
logP = log(peaks(:));
coeffs = [logF ones(nScans, 1)] \ logP;
exponent = coeffs(1);
```

## When to Use
- Pump fluence dependence measurements with wire grid polarizers
- Determining χ² vs χ³ scaling of nonlinear optical signals
