---
name: matlab-runner
description: Run MATLAB scripts headlessly, capture stdout/stderr, and read exported figures. Use when the user asks to run, test, or debug a MATLAB script (.m file), or when Claude has just edited a MATLAB script and should verify it executes correctly. Also use when the user wants to see what a script produces without opening MATLAB manually.
---

# MATLAB Runner

Run MATLAB scripts headlessly via `matlab -batch`, capture all output, and read any exported figures to inspect results.

## MATLAB Executable

```
/c/Program Files/MATLAB/R2025a/bin/matlab.exe
```

## Running a Script

Use the bundled shell script for convenience:

```bash
bash ~/.claude/skills/matlab-runner/scripts/run_matlab.sh <script_path> [working_dir]
```

Or invoke MATLAB directly (preferred for full control):

```bash
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

## Notes

- `-batch` mode has no display — `figure()` calls are valid but windows won't appear; only `exportgraphics`/`saveas` outputs are accessible
- Large scans (25 angles × averaging) may take 30–120 seconds; the Bash tool timeout defaults to 120s — increase with `timeout` parameter if needed
- The working directory for this project is typically `C:\Users\katsumilab\Documents\data\NbOI2_Exfoliated_Sample\<subfolder>`
