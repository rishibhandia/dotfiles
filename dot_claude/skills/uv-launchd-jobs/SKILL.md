---
name: uv-launchd-jobs
description: Scheduling a uv-managed Python script via launchd or cron. Use when writing a LaunchAgent/cron entry for a uv project, or debugging a scheduled Python job that hangs, produces no output, or exits without running — the classic `uv run` under launchd stall.
---

# Running uv Python scripts under launchd / cron

## Problem
`uv run python script.py` works instantly in an interactive shell but **hangs** (or
silently fails) under launchd/cron. Symptom: the job shows a running PID but **no child
`python` process** and a 0-byte log for a minute or more.

## Cause
`uv run` does pre-flight work before exec'ing Python: it resolves the project, checks
the lockfile, and may take a lock or hit the network to sync `.venv`. A daemon's
stripped-down environment (no TTY, minimal PATH/HOME, different network/keychain
context) stalls that step.

## Fix
Call the venv interpreter directly — it skips all of uv's machinery and runs Python
against the already-built environment:

```
/abs/path/to/project/.venv/bin/python script.py
```

- Keep using uv for dev: `uv sync` builds/updates `.venv`; the scheduled job picks up
  changes automatically next run.
- Alternative that keeps `uv run`: `uv run --no-sync python script.py` (skips the
  sync/resolve step).
- In the launchd plist: set `WorkingDirectory`, a real `PATH` (include
  `/opt/homebrew/bin` so subprocess tools like OCR binaries resolve), and
  `PYTHONUNBUFFERED=1` so logs flush immediately.
- **launchd has no shell env** — API keys from your shell profile won't be present.
  Have the script read secrets from a config file, not `os.environ` alone.

## Verify
`launchctl list <label>` shows `"LastExitStatus" = 0` and (when idle) no `"PID"`;
the log should appear within a second or two.

## When to use
Writing or debugging any launchd LaunchAgent or cron job that runs a uv-based Python tool.
