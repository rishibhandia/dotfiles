# TA Fluence Dependence with Wire Grid Polarizers

**Extracted:** 2026-05-01
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
```matlab
logF = log(fieldFactors(:));
logP = log(peaks(:));
coeffs = [logF ones(nScans, 1)] \ logP;
exponent = coeffs(1);
```

## When to Use
- Pump fluence dependence measurements with wire grid polarizers
- Determining χ² vs χ³ scaling of nonlinear optical signals
