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
  # 1. PATH — works on all platforms if matlab is symlinked or in PATH
  if command -v matlab &>/dev/null; then
    command -v matlab
    return
  fi

  local uname
  uname="$(uname -s)"

  # 2. macOS: /Applications/MATLAB_R20XXx.app/bin/matlab
  if [ "$uname" = "Darwin" ]; then
    local candidates
    candidates=$(ls -d /Applications/MATLAB_*.app/bin/matlab 2>/dev/null | sort -V)
    local last
    last=$(echo "$candidates" | tail -1)
    if [ -n "$last" ] && [ -x "$last" ]; then
      echo "$last"
      return
    fi
  fi

  # 3. Linux: /usr/local/MATLAB/R*/bin/matlab or /opt/MATLAB/R*/bin/matlab
  if [ "$uname" = "Linux" ]; then
    local candidates
    candidates=$(ls -d /usr/local/MATLAB/*/bin/matlab /opt/MATLAB/*/bin/matlab 2>/dev/null | sort -V)
    local last
    last=$(echo "$candidates" | tail -1)
    if [ -n "$last" ] && [ -x "$last" ]; then
      echo "$last"
      return
    fi
  fi

  # 4. Windows (Git Bash / MSYS2 / Cygwin): /c/Program Files/MATLAB/R*/bin/matlab.exe
  case "$uname" in MINGW*|MSYS*|CYGWIN*)
    local candidates
    candidates=$(ls -d "/c/Program Files/MATLAB/"*/bin/matlab.exe 2>/dev/null | sort -V)
    local last
    last=$(echo "$candidates" | tail -1)
    if [ -n "$last" ] && [ -x "$last" ]; then
      echo "$last"
      return
    fi
    ;;
  esac
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
