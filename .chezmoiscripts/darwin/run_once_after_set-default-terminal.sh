#!/bin/bash
# Set Ghostty as the default terminal application
# This runs once after dotfiles are applied

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

info() { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
success() { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }

GHOSTTY_BUNDLE_ID="com.mitchellh.ghostty"

# Check if duti is installed
if ! command -v duti &>/dev/null; then
    warn "duti not installed, skipping default terminal setup"
    exit 0
fi

# Check if Ghostty is installed
if ! mdfind "kMDItemCFBundleIdentifier == '$GHOSTTY_BUNDLE_ID'" 2>/dev/null | grep -q .; then
    warn "Ghostty not installed, skipping default terminal setup"
    exit 0
fi

info "Setting Ghostty as default terminal handler..."

# Set Ghostty as the default handler for shell scripts and terminal files
# UTI: public.shell-script - Generic shell scripts (.sh, etc.)
duti -s "$GHOSTTY_BUNDLE_ID" public.shell-script all 2>/dev/null || true

# UTI: public.bash-script - Bash scripts
duti -s "$GHOSTTY_BUNDLE_ID" public.bash-script all 2>/dev/null || true

# UTI: public.zsh-script - Zsh scripts
duti -s "$GHOSTTY_BUNDLE_ID" public.zsh-script all 2>/dev/null || true

# UTI: com.apple.terminal.shell-script - Terminal.app shell scripts (.command)
duti -s "$GHOSTTY_BUNDLE_ID" com.apple.terminal.shell-script all 2>/dev/null || true

success "Ghostty set as default terminal handler"
