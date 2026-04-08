# TA Coherent Phonon Sideband Analysis

**Extracted:** 2026-04-08
**Context:** Analyzing coherent phonon sidebands in broadband transient absorption spectra

## Problem
Identifying and characterizing vibrational sideband signatures in broadband TA data requires a systematic multi-step workflow.

## Solution

### Workflow
1. **Find probe center** — Determine the central probe wavelength/energy from the reference (ground-state) spectrum
2. **Compute oscillatory power per pixel** — For each probe wavelength, FFT the kinetic trace and integrate power in the phonon frequency band of interest
3. **Find sideband peaks** — Locate peaks in the oscillatory power spectrum as a function of probe wavelength; these are the sideband positions
4. **Compute shifts** — Calculate the energy/frequency shift of each sideband from the probe center (report in THz or cm^-1)
5. **Phase comparison** — Extract the FFT phase at the phonon frequency for probe wavelengths at symmetric offsets from center; anti-Stokes and Stokes sidebands should show characteristic phase relationships (e.g., pi phase flip)

## When to Use
- Broadband TA datasets showing oscillatory signals from coherent phonons
- When the user asks about vibrational sidebands, phonon coupling, or oscillatory TA features
