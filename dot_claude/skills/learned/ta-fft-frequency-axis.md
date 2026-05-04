# TA FFT Frequency Axis Construction

**Extracted:** 2026-04-08
**Updated:** 2026-05-03
**Context:** Building frequency axes for FFT of transient absorption kinetics

## Status: fixed in the package

`thz.fft.rfftFreq` now wraps the time step in `abs()` internally, so a
negative-going `TimeDelays` vector produces a positive sampling rate
and a monotonically increasing frequency axis automatically. Just call:

```matlab
freq = thz.fft.rfftFreq(TimeDelays, nfft);
```

You no longer need the `dt = abs(...)` workaround in new code.

## Original problem
When TA `TimeDelays` ran negative-to-zero (e.g., pump-probe delays
before time-zero), `rfftFreq` used `dt = time(2) - time(1)` and
produced a negative sampling interval, giving an inverted or incorrect
frequency axis.

## Manual workaround (only needed if calling MATLAB's bare `fft`)
If you build a frequency axis from scratch outside the package, use:

```matlab
dt = abs(TimeDelays(2) - TimeDelays(1));
freq = (0:nfftOut-1) / (nfft * dt);
```

## When to Use
- Reading old scripts that used the manual `dt = abs(...)` workaround —
  you can replace them with a plain `thz.fft.rfftFreq` call now
- Any FFT on TA kinetic traces where the time vector may include
  negative delays (the package handles this correctly)
