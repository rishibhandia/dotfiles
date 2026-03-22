# MagicMock Attribute Default Trap with getattr

**Extracted:** 2026-03-22
**Context:** Passing a MagicMock as a dependency and using getattr with a fallback default

## Problem

`getattr(mock_obj, "attribute", default)` does NOT return the default when the object is a `MagicMock`. MagicMock auto-creates any attribute access as another MagicMock, so the default is never used. The code silently proceeds with a MagicMock object instead of the intended fallback.

```python
# BROKEN: hw is MagicMock — hw.wavelengths is auto-created as MagicMock
wavelengths = getattr(hw, "wavelengths", np.array([]))
np.asarray(wavelengths)  # → 0-d array containing MagicMock, not empty array
```

In this session: the TA engine used `getattr(hw, "wavelengths", np.array([]))` to get wavelengths from the hardware manager. Since `hw` was a MagicMock in tests, it silently passed a MagicMock to `np.asarray()`, producing a 0-d object array. The live display's OD spectrum curve received bad data and stayed empty despite the signal being emitted correctly.

## Solution

Check for a **callable method** instead of an attribute:

```python
# CORRECT: check if the method exists and is callable
get_wl = getattr(hw, "get_wavelengths", None)
wavelengths = np.asarray(get_wl()) if callable(get_wl) else np.array([])
```

This works correctly for both real objects (where the method exists) and MagicMocks (where it's callable but returns a MagicMock — handle that separately if needed, or configure the mock's return value).

## When to Use

- Any time you use `getattr(obj, name, default)` and the object might be a MagicMock
- Especially when the fallback is a numpy array, list, or other non-truthy empty container
- When debugging: "signal emitted but plot not updating" — check that data passed through signals is actually the right type, not a MagicMock
