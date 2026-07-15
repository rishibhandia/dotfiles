# Andor SDK DLL Lifecycle Management

**Extracted:** 2026-04-09
**Context:** Working with Andor Newton (atmcd64d.dll) and Shamrock/Kymera (ShamrockCIF.dll) on Windows

## Problem
Force-killing python processes that hold Andor SDK handles locks the DLLs exclusively.
Subsequent launches get `DRV_NOT_AVAILABLE` (20992) or `No spectrograph devices found`.
Recovery requires USB cable replug, power cycling hardware, or full reboot.

## Solution
1. **Never force-kill** (`Stop-Process`, SIGKILL) python holding SDK handles
2. Always call `camera.shutdown()` and `spectrograph.shutdown()` before exit
3. Test scripts MUST use `try/finally` to ensure shutdown on error
4. To restart the app, ask user to close via X button (runs shutdown dialog)
5. `EnableKeepCleans()` requires idle camera — check `GetStatus()` first, skip if `DRV_ACQUIRING`
6. `GetImages16` returning 20024 (`DRV_NO_NEW_DATA`) is transient — retry, don't crash

## Example
```python
# CORRECT: always shutdown in finally block
cam = None
sp = None
try:
    cam = AndorCamera(sdk_path=r'C:\Program Files\Andor SDK')
    cam.initialize()
    # ... do work ...
except Exception as e:
    print(f'FAILED: {e}')
finally:
    if cam: cam.shutdown()
    if sp: sp.shutdown()
```

## When to Use
Any script or test that initializes Andor camera or spectrograph hardware.
