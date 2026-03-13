#!/usr/bin/env bash
# run_matlab.sh — Run a MATLAB script headlessly and capture output
#
# Usage:
#   bash run_matlab.sh <script_path> [working_dir]
#
# Arguments:
#   script_path   Absolute path to the .m file to run
#   working_dir   Directory to cd into before running (defaults to script's directory)
#
# Output:
#   stdout/stderr from MATLAB are printed directly.
#   Exit code mirrors MATLAB's exit code (0 = success).

SCRIPT_PATH="$1"
WORKING_DIR="${2:-$(dirname "$SCRIPT_PATH")}"
MATLAB_EXE="/c/Program Files/MATLAB/R2025a/bin/matlab.exe"

if [ -z "$SCRIPT_PATH" ]; then
  echo "Usage: run_matlab.sh <script_path> [working_dir]" >&2
  exit 1
fi

# Convert to Windows-style paths for MATLAB
WIN_SCRIPT=$(cygpath -w "$SCRIPT_PATH" 2>/dev/null || echo "$SCRIPT_PATH")
WIN_WORKDIR=$(cygpath -w "$WORKING_DIR" 2>/dev/null || echo "$WORKING_DIR")

# Strip .m extension for the run() call
SCRIPT_NAME=$(basename "$SCRIPT_PATH" .m)

"$MATLAB_EXE" -batch "cd('${WIN_WORKDIR//\'/\'\'}'); ${SCRIPT_NAME}"
