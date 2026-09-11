# 2D THz Nonlinear Spectroscopy: Analysis Patterns

**Updated:** 2026-09-10
**Context:** two collinear THz pulses A and B with delay tau, transmitted field
EO-sampled at time t, nonlinear channel NL = E_AB - E_A - E_B, 2D FFT over
(t, tau). Learned on the NbOI2 BPF two-pump dataset; the math is general.

## NL keeps only cross terms (proof sketch)

Write the detected field as a Volterra series, E_out[E] = sum_n F_n[E, ..., E]
with F_n multilinear and symmetric. For E = E_A + E_B the multinomial expansion
gives F_n[E_A + E_B] = sum_k C(n,k) F_n[E_A^k, E_B^(n-k)]; the k = n and k = 0
terms are the responses to A alone and B alone. Therefore

    NL = sum_{n>=2} sum_{k=1}^{n-1} C(n,k) F_n[E_A^k, E_B^(n-k)]

for ANY kernels (instantaneous chi(n), phonon-mediated, or detector). Two
consequences that are easy to get wrong:

- The self terms E_A^2, E_A^3, ... are **subtracted, not absent**. A quadratic
  response that gives a cross term at omega_A + omega_B must also give a 2f
  term in the A-alone trace at half the cross amplitude (Boyd degeneracy
  factor 2 vs 1). Look for it in E_A alone, where it competes with the full
  linear signal; do not conclude from NL that it does not exist.
- The order of the nonlinearity is read off which cross peaks appear:
  quadratic -> (2f, f) and (0, f); cubic -> (3f, f), (f, f), (f, 2f), (f, 0),
  never (2f, f) or (0, f). A saturating EO detector is odd (sin Gamma), so a
  (2f, f)/(0, f) pair rules it out; it does NOT rule out a residual quadratic
  term of imbalanced detection.

## Delay convention (Mahmood et al., Nat. Phys. 17, 627 (2021))

Fixed pulse defines t = 0; the moving pulse arrives EARLIER as tau increases
(t = -tau); tau > 0 = moving pulse first ("AB"). Their chi(3) catalogue:
AB pump-probe (w, 0); AB rephasing / photon echo (w, -w) 4th quadrant;
AB non-rephasing (w, +w) diagonal; BA pump-probe (w, w); BA rephasing (w, 2w);
BA non-rephasing (w, 0). Frequency vectors: w_moving = W (w_tau + w_t),
w_fixed = W w_t, one vector per interaction, conjugate = reversed.

Implementation with `thz.io.load2DTimeTraceNew(..., flip2DAxis=true)`: the
relabel alone mirrors the map; also `flip(scan.NL, 1)` (and A, B) so the
moving-pulse ridge has negative slope. Identify the fixed channel as the one
whose per-row peak column has zero spread; the row where the moving ridge
crosses it is tau = 0. A scan usually spans BOTH orderings; FFT the two row
blocks separately before assigning AB/BA pathways.

## Single traces cannot show narrow 2D peaks (projection-slice)

The 1D FFT of one tau row equals the integral of the 2D FFT along nu_tau. A
peak narrow in nu_tau contributes only its integrated width to any single
row, while the instantaneous spike at coincidence (broad in nu_tau) dominates
per row. In the NbOI2 data the 3.2 THz NL content per row is 2.5 % of the
linear signal and the 6.5 THz sum peak is at the row noise floor; the 2D map
recovers them by coherently summing ~150 rows. The honest 1D display is a cut
through the 2D map at the peak's nu_tau, labelled as such, placed above the
map sharing its nu_t axis. A tau = 0 scan shows the instantaneous spike only.

## Filtered pumps ring: check the frequencies

A bandpass-filtered (BPF ~3 THz) pump keeps >10 % of its envelope for ~4 ps.
Consequences: (i) a "persists after the pulse" test needs a window longer than
the FILTERED pulse, not the bare one; (ii) mixing peaks of a field x field
product sit at 2x the transmitted pump's ringing frequency, a phonon-mediated
Q x Q product at 2x the phonon; with a 6 ps window (0.17 THz resolution) 3.13
vs 3.27 THz is one resolution element. Refine peak positions with 4096-pt
padding and compare with the transmitted single-pulse spectral maximum and its
late-time ringing frequency before attributing a peak to the phonon. Also
compare the sum/difference peak SHAPE: an instantaneous E^2 of the pump
inherits the pump's whole spectrum (broad, with low-frequency companions),
a resonant Q^2 gives compact peaks.

## Single-pulse harmonic test

The fixed pulse is identical in every row: average the rows coherently
(`mean(A, 1)`) and FFT to look for 2f/3f lines. If the floor does not drop
under averaging it is systematic (filter sidelobes, detector), so the bound is
set by structure, not noise. THz-harmonic groups block the fundamental with a
filter before the detector to escape this dynamic-range limit.

## Detector vs sample: the discriminators

- Sample angle series at tau = 0: a detector nonlinearity gives the same
  NL/AB at every angle; a sample chi(2) follows the anisotropy.
- Attenuators between sample and detector: reduce detector mixing only.
- A quadratic detector term and a sample chi(2) have the SAME 2D signature;
  frequency counting cannot separate them.
