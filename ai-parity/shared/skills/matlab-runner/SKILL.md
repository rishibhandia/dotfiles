---
name: matlab-runner
description: Run MATLAB scripts headlessly, capture stdout/stderr, and read exported figures. Use when the user asks to run, test, or debug a MATLAB script (.m file), or when Claude has just edited a MATLAB script and should verify it executes correctly. Also use when the user wants to see what a script produces without opening MATLAB manually.
---

# MATLAB Runner

Run MATLAB scripts headlessly via `matlab -batch`, capture all output, and read any exported figures to inspect results. Works on macOS, Linux, and Windows (Git Bash).

## MATLAB Executable

The runner script chooses the **newest installed MATLAB by default**, unless a
version is explicitly specified. Resolution order:

1. **Explicit override** (wins if set):
   - `MATLAB_BIN` — full path to the `matlab` binary, or
   - `MATLAB_VERSION` — release name, e.g. `R2026a`
2. **Newest installed versioned release** (`ls ... | sort -V | tail -1`):
   - **macOS**: `/Applications/MATLAB_R*.app/bin/matlab`
   - **Linux**: `/usr/local/MATLAB/R*/bin/matlab` or `/opt/MATLAB/R*/bin/matlab`
   - **Windows (Git Bash)**: `/c/Program Files/MATLAB/R*/bin/matlab.exe`
3. **`matlab` on PATH** (fallback, only if no versioned install is found)

Choosing the newest avoids defaulting to an older or broken install when several
are present (e.g. a broken `R2024b` that errors "No MATLAB bin directory for this
machine architecture (ARCH = maca64)" sitting next to a working `R2026a`).

```bash
# default: newest installed version
bash run_matlab.sh myScript.m

# force a specific version
MATLAB_VERSION=R2025a bash run_matlab.sh myScript.m
MATLAB_BIN=/Applications/MATLAB_R2026a.app/bin/matlab bash run_matlab.sh myScript.m
```

## Running a Script

Use the bundled shell script for convenience:

```bash
bash ~/.claude/skills/matlab-runner/scripts/run_matlab.sh <script_path> [working_dir]
```

Or invoke MATLAB directly (preferred for full control):

```bash
# macOS / Linux
/Applications/MATLAB_R2025a.app/bin/matlab -batch "cd('/path/to/dir'); scriptName"

# Windows (Git Bash)
"/c/Program Files/MATLAB/R2025a/bin/matlab.exe" -batch "cd('C:\path\to\dir'); scriptName"
```

**Key rules:**
- Use `-batch` (not `-r`): runs headlessly, exits automatically on completion or error, forwards all errors to stderr
- `cd()` to the script's directory first so `pwd`-relative paths in the script resolve correctly
- Do NOT include the `.m` extension in the script name passed to `-batch`
- Single quotes inside the `cd()` path must be escaped as `''`

## Workflow

1. **Run** the script with the Bash tool using the command above
2. **Read stdout** — MATLAB `disp()` and `fprintf()` output appears in the terminal
3. **Check for errors** — MATLAB errors print to stderr with file/line info; read them carefully
4. **Read exported figures** — scripts use `exportgraphics(fig, 'Figures/name.png')`; after the run, use the Read tool on those PNG paths to inspect the figures visually
5. **Iterate** — edit the script, re-run, re-inspect

## Reading Figures

After a successful run, find and read the exported PNGs:

```bash
# Find what was exported
find "<working_dir>/Figures" -name "*.png" -newer "<script_path>"
```

Then use the Read tool on each PNG path to view the figure.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Undefined function or variable` | Missing helper on MATLAB path | Ensure helper `.m` files are in the same directory or add `addpath` at top of script |
| `Unable to read file` | Wrong `pwd` | Always `cd()` to script directory in the `-batch` command |
| Exit code 1, no message | Script called `error()` | Check stderr for the error message and line number |
| Figure not exported | Script errored before `exportgraphics` | Fix the upstream error first |
| `matlab: command not found` | MATLAB not in PATH | Use the full path or run via the bundled script which auto-detects |
| `No MATLAB bin directory for this machine architecture` | A broken/old install was selected | Runner now prefers the newest install; or set `MATLAB_BIN` / `MATLAB_VERSION` to a working one |

## Notes

- `-batch` mode has no display — `figure()` calls are valid but windows won't appear; only `exportgraphics`/`saveas` outputs are accessible
- Long-running scripts may exceed the Bash tool's default 120s timeout — increase with the `timeout` parameter if needed
- On Linux, MATLAB may require a license server reachable from the machine
