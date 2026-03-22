# Qt Test Hang: window.close() Triggers Blocking Shutdown Sequence

**Extracted:** 2026-03-22
**Context:** Testing Qt main windows that have a hardware shutdown sequence in closeEvent

## Problem

Calling `window.close()` in a pytest test hangs the entire test suite when the window's `closeEvent` contains a blocking wait (e.g., waiting for hardware to warm up, a threading.Event with a long timeout).

In this session: `AndorSpectrometerWindow.closeEvent` calls `_start_shutdown_with_dialog()` which waits up to 360 seconds for the camera to warm up. When `window.close()` was called in `test_main_window_has_ta_tab`, the full test suite stopped at 54% — all subsequent tests never ran.

The symptom is subtle: the test appears to hang silently. Verbose mode shows it stuck on that one test. The other tests in the same file pass when run in isolation because the test order differs.

## Solution

**Never call `window.close()` in tests** when the window has a hardware shutdown sequence. Use `deleteLater()` instead — it schedules the object for GC without triggering `closeEvent`:

```python
# WRONG — triggers closeEvent → blocking shutdown
window.close()
window.deleteLater()

# CORRECT — schedules GC, skips closeEvent
window.deleteLater()
```

If you need to test the shutdown path itself, patch the blocking method:

```python
with patch.object(window, "_start_shutdown_with_dialog"):
    window.close()
```

## When to Use

- Any test that instantiates a full main window (`AndorSpectrometerWindow` or similar)
- If the full test suite hangs at a specific percentage and the culprit test passes when run in isolation
- Pattern: test suite runs fine up to N%, then stops — check the last test that ran for a blocking call
