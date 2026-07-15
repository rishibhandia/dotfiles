# Windows Phantom USB Device Recovery

**Extracted:** 2026-04-09
**Context:** Andor camera/spectrograph USB devices showing as Unknown/Phantom in Device Manager

## Problem
When USB instruments are plugged into different ports (or after force-kill corrupts
the driver state), Windows creates phantom PnP entries with `CM_PROB_PHANTOM` status.
The SDK sees zero devices even though hardware is powered on and connected.

## Solution

### Diagnose
```powershell
Get-PnpDevice | Where-Object { $_.FriendlyName -match 'Andor|Shamrock' } |
    Select-Object Status, FriendlyName, InstanceId, ConfigManagerErrorCode
```
Look for `Status: Unknown` and `CM_PROB_PHANTOM`.

### Fix
1. Open admin PowerShell
2. Remove phantom entries:
   ```powershell
   pnputil /remove-device "USB\VID_136E&PID_0017\B094YZDM"  # Shamrock
   pnputil /remove-device "USB\VID_136E&PID_0005\7&1B1B23EC&0&3"  # Newton phantom
   ```
3. Unplug and replug the USB cable
4. If device shows as raw FTDI chip (`FT245R USB FIFO`):
   - Device Manager → right-click → Update driver → Browse → point to:
     `C:\Program Files\Andor SDK\ATSpectrograph USB drivers` (parent folder)

### Prevent
Always plug instruments into the **same USB ports** — phantoms appear when ports change.

## When to Use
When Andor SDK initialization fails with "No devices found" but hardware is powered on.
