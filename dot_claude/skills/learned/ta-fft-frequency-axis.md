# TA FFT Frequency Axis Construction

**Extracted:** 2026-04-08
**Context:** Building frequency axes for FFT of transient absorption kinetics

## Problem
When TA TimeDelays run negative-to-zero (e.g., pump-probe delays before time-zero), `rfftFreq` computes a negative `dt` from the time vector, producing an inverted or incorrect frequency axis.

## Solution
Always use `dt = abs(TimeDelays(2) - TimeDelays(1))` to guarantee a positive sampling interval. Then build the frequency axis manually instead of relying on helper functions:

```matlab
dt = abs(TimeDelays(2) - TimeDelays(1));
freq = (0:nfftOut-1) / (nfft * dt);
```

This ensures the frequency axis is always monotonically increasing regardless of the sign convention of the time-delay vector.

## When to Use
- Any FFT on TA kinetic traces where the time vector may include negative delays
- Whenever `rfftFreq` or similar helpers produce unexpected negative frequencies
