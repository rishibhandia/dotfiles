#!/usr/bin/env bash
# run_matlab.sh — Run a MATLAB script headlessly, cross-platform
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

if [ -z "$SCRIPT_PATH" ]; then
  echo "Usage: run_matlab.sh <script_path> [working_dir]" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Find MATLAB executable (checked in order of preference)
# ---------------------------------------------------------------------------
find_matlab() {
  local uname candidates last p
  uname="$(uname -s)"

  # 0. Explicit override wins: MATLAB_BIN (full path to the matlab binary) or
  #    MATLAB_VERSION (release name, e.g. R2026a). Lets a caller force a version.
  if [ -n "$MATLAB_BIN" ]; then
    if [ -x "$MATLAB_BIN" ]; then echo "$MATLAB_BIN"; return; fi
    echo "Warning: MATLAB_BIN=$MATLAB_BIN is not executable; ignoring." >&2
  fi
  if [ -n "$MATLAB_VERSION" ]; then
    case "$uname" in
      Darwin) p="/Applications/MATLAB_${MATLAB_VERSION}.app/bin/matlab" ;;
      Linux)  p="/usr/local/MATLAB/${MATLAB_VERSION}/bin/matlab"; [ -x "$p" ] || p="/opt/MATLAB/${MATLAB_VERSION}/bin/matlab" ;;
      MINGW*|MSYS*|CYGWIN*) p="/c/Program Files/MATLAB/${MATLAB_VERSION}/bin/matlab.exe" ;;
    esac
    if [ -n "$p" ] && [ -x "$p" ]; then echo "$p"; return; fi
    echo "Warning: MATLAB_VERSION=$MATLAB_VERSION not found; falling back to newest install." >&2
  fi

  # 1. Prefer the NEWEST installed versioned MATLAB (sort -V | tail -1). This avoids
  #    defaulting to an older/broken install when several are present — e.g. an R2024b
  #    that errors "No MATLAB bin directory for this machine architecture (ARCH = maca64)"
  #    sitting alongside a working R2026a.
  case "$uname" in
    Darwin)
      candidates=$(ls -d /Applications/MATLAB_*.app/bin/matlab 2>/dev/null | sort -V) ;;
    Linux)
      candidates=$(ls -d /usr/local/MATLAB/*/bin/matlab /opt/MATLAB/*/bin/matlab 2>/dev/null | sort -V) ;;
    MINGW*|MSYS*|CYGWIN*)
      candidates=$(ls -d "/c/Program Files/MATLAB/"*/bin/matlab.exe 2>/dev/null | sort -V) ;;
  esac
  last="$(echo "$candidates" | tail -1)"
  if [ -n "$last" ] && [ -x "$last" ]; then
    echo "$last"
    return
  fi

  # 2. Fallback: matlab on PATH, only if no versioned install was found.
  if command -v matlab &>/dev/null; then
    command -v matlab
    return
  fi
}

MATLAB_EXE="$(find_matlab)"

if [ -z "$MATLAB_EXE" ]; then
  echo "Error: MATLAB not found. Ensure 'matlab' is in PATH or installed at a standard location:" >&2
  echo "  macOS:   /Applications/MATLAB_R20XXx.app/bin/matlab" >&2
  echo "  Linux:   /usr/local/MATLAB/R20XXx/bin/matlab" >&2
  echo "  Windows: C:\\Program Files\\MATLAB\\R20XXx\\bin\\matlab.exe" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Path handling — Windows requires native backslash paths for MATLAB cd()
# ---------------------------------------------------------------------------
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*)
  WORKDIR="$(cygpath -w "$WORKING_DIR" 2>/dev/null || echo "$WORKING_DIR")"
  ;;
*)
  WORKDIR="$WORKING_DIR"
  ;;
esac

# Strip .m extension and escape single quotes for MATLAB string literal
SCRIPT_NAME="$(basename "$SCRIPT_PATH" .m)"
WORKDIR_ESC="${WORKDIR//\'/\'\'}"

"$MATLAB_EXE" -batch "cd('${WORKDIR_ESC}'); ${SCRIPT_NAME}"
