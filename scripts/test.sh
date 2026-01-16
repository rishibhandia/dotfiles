#!/bin/bash
# Dotfiles setup verification tests
# Run with: dots test (or bash ~/.local/share/chezmoi/scripts/test.sh)

set -euo pipefail

# =============================================================================
# Test Framework
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Test result functions
pass() {
    printf "${GREEN}✓${NC} %s\n" "$1"
    ((TESTS_PASSED++))
}

fail() {
    printf "${RED}✗${NC} %s\n" "$1"
    ((TESTS_FAILED++))
}

skip() {
    printf "${YELLOW}○${NC} %s (skipped)\n" "$1"
    ((TESTS_SKIPPED++))
}

info() {
    printf "${BLUE}ℹ${NC} %s\n" "$1"
}

section() {
    echo ""
    printf "${BLUE}━━━ %s ━━━${NC}\n" "$1"
}

# =============================================================================
# Test Helpers
# =============================================================================

command_exists() {
    command -v "$1" &>/dev/null
}

file_exists() {
    [[ -f "$1" ]]
}

dir_exists() {
    [[ -d "$1" ]]
}

is_macos() {
    [[ "$(uname -s)" == "Darwin" ]]
}

is_linux() {
    [[ "$(uname -s)" == "Linux" ]] && ! is_wsl
}

is_wsl() {
    [[ -f /proc/version ]] && grep -qi "microsoft\|wsl" /proc/version 2>/dev/null
}

# =============================================================================
# Tests: Essential Commands
# =============================================================================

test_essential_commands() {
    section "Essential Commands"

    local commands=(
        "chezmoi:Dotfiles manager"
        "git:Version control"
        "zsh:Shell"
        "nvim:Text editor"
    )

    for entry in "${commands[@]}"; do
        local cmd="${entry%%:*}"
        local desc="${entry#*:}"
        if command_exists "$cmd"; then
            pass "$desc ($cmd)"
        else
            fail "$desc ($cmd) - not installed"
        fi
    done
}

# =============================================================================
# Tests: CLI Tools
# =============================================================================

test_cli_tools() {
    section "CLI Tools"

    local tools=(
        "bat:Better cat"
        "fd:Better find"
        "rg:Ripgrep (better grep)"
        "fzf:Fuzzy finder"
        "tmux:Terminal multiplexer"
        "starship:Shell prompt"
        "jq:JSON processor"
    )

    for entry in "${tools[@]}"; do
        local cmd="${entry%%:*}"
        local desc="${entry#*:}"
        if command_exists "$cmd"; then
            pass "$desc ($cmd)"
        else
            skip "$desc ($cmd)"
        fi
    done
}

# =============================================================================
# Tests: Dotfiles Structure
# =============================================================================

test_dotfiles_structure() {
    section "Dotfiles Structure"

    # Check XDG directories
    local xdg_dirs=(
        "$HOME/.config:XDG_CONFIG_HOME"
        "$HOME/.local/share:XDG_DATA_HOME"
        "$HOME/.local/share/chezmoi:Chezmoi source directory"
    )

    for entry in "${xdg_dirs[@]}"; do
        local dir="${entry%%:*}"
        local desc="${entry#*:}"
        if dir_exists "$dir"; then
            pass "$desc exists"
        else
            fail "$desc missing ($dir)"
        fi
    done

    # Check key dotfiles
    local dotfiles=(
        "$HOME/.zshenv:Zsh environment"
        "$HOME/.config/zsh/.zshrc:Zsh config"
        "$HOME/.config/git/config:Git config"
        "$HOME/.config/nvim/init.vim:Neovim config"
    )

    for entry in "${dotfiles[@]}"; do
        local file="${entry%%:*}"
        local desc="${entry#*:}"
        if file_exists "$file"; then
            pass "$desc exists"
        else
            fail "$desc missing ($file)"
        fi
    done
}

# =============================================================================
# Tests: Environment Variables
# =============================================================================

test_environment_variables() {
    section "Environment Variables"

    # Check XDG variables
    if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
        pass "XDG_CONFIG_HOME is set ($XDG_CONFIG_HOME)"
    else
        fail "XDG_CONFIG_HOME not set"
    fi

    if [[ -n "${XDG_DATA_HOME:-}" ]]; then
        pass "XDG_DATA_HOME is set ($XDG_DATA_HOME)"
    else
        fail "XDG_DATA_HOME not set"
    fi

    # Check editor
    if [[ -n "${EDITOR:-}" ]]; then
        pass "EDITOR is set ($EDITOR)"
    else
        fail "EDITOR not set"
    fi

    # Check ZDOTDIR
    if [[ -n "${ZDOTDIR:-}" ]]; then
        pass "ZDOTDIR is set ($ZDOTDIR)"
    else
        skip "ZDOTDIR not set (using default)"
    fi
}

# =============================================================================
# Tests: Shell Configuration
# =============================================================================

test_shell_config() {
    section "Shell Configuration"

    # Check if zsh is default shell
    if [[ "$SHELL" == *"zsh"* ]]; then
        pass "Zsh is default shell"
    else
        fail "Zsh is not default shell (current: $SHELL)"
    fi

    # Check for syntax highlighting
    local syntax_hl=""
    if is_macos; then
        syntax_hl="/opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
        if [[ ! -f "$syntax_hl" ]]; then
            syntax_hl="/usr/local/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
        fi
    elif is_wsl; then
        # WSL can use system package or Homebrew
        syntax_hl="/usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
        if [[ ! -f "$syntax_hl" ]]; then
            syntax_hl="/home/linuxbrew/.linuxbrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
        fi
    else
        syntax_hl="/home/linuxbrew/.linuxbrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
    fi

    if file_exists "$syntax_hl"; then
        pass "Zsh syntax highlighting available"
    else
        skip "Zsh syntax highlighting not found"
    fi

    # Check starship config
    if file_exists "$HOME/.config/starship/config.toml"; then
        pass "Starship config exists"
    else
        skip "Starship config not found"
    fi
}

# =============================================================================
# Tests: Git Configuration
# =============================================================================

test_git_config() {
    section "Git Configuration"

    # Check git user
    local git_name
    git_name=$(git config --global user.name 2>/dev/null || echo "")
    if [[ -n "$git_name" ]]; then
        pass "Git user.name is set ($git_name)"
    else
        fail "Git user.name not set"
    fi

    local git_email
    git_email=$(git config --global user.email 2>/dev/null || echo "")
    if [[ -n "$git_email" ]]; then
        pass "Git user.email is set ($git_email)"
    else
        fail "Git user.email not set"
    fi

    # Check git config file
    if file_exists "$HOME/.config/git/config"; then
        pass "Git config in XDG location"
    elif file_exists "$HOME/.gitconfig"; then
        pass "Git config exists (legacy location)"
    else
        fail "Git config not found"
    fi
}

# =============================================================================
# Tests: Homebrew (macOS/Linux)
# =============================================================================

test_homebrew() {
    section "Homebrew"

    if ! command_exists brew; then
        skip "Homebrew not installed"
        return
    fi

    pass "Homebrew is installed"

    # Check brew health
    if brew doctor &>/dev/null; then
        pass "Homebrew is healthy"
    else
        fail "Homebrew has issues (run 'brew doctor')"
    fi

    # Check if Brewfile exists
    if file_exists "$HOME/.Brewfile" || file_exists "$HOME/.local/share/chezmoi/dot_Brewfile"; then
        pass "Brewfile exists"
    else
        skip "Brewfile not found"
    fi
}

# =============================================================================
# Tests: 1Password Integration (optional)
# =============================================================================

test_1password() {
    section "1Password Integration"

    if ! command_exists op; then
        skip "1Password CLI not installed"
        return
    fi

    pass "1Password CLI is installed"

    # Check if signed in (without actually authenticating)
    if op account list &>/dev/null; then
        pass "1Password CLI is configured"
    else
        skip "1Password CLI not signed in"
    fi
}

# =============================================================================
# Tests: macOS Specific
# =============================================================================

test_macos_specific() {
    if ! is_macos; then
        return
    fi

    section "macOS Specific"

    # Check Xcode CLI tools
    if xcode-select -p &>/dev/null; then
        pass "Xcode Command Line Tools installed"
    else
        fail "Xcode Command Line Tools not installed"
    fi

    # Check screenshots directory
    local screenshot_dir
    screenshot_dir=$(defaults read com.apple.screencapture location 2>/dev/null || echo "")
    if [[ -n "$screenshot_dir" ]] && dir_exists "$screenshot_dir"; then
        pass "Screenshot directory configured ($screenshot_dir)"
    else
        skip "Screenshot directory not configured"
    fi
}

# =============================================================================
# Tests: WSL Specific
# =============================================================================

test_wsl_specific() {
    if ! is_wsl; then
        return
    fi

    section "WSL Specific"

    # Check WSL version
    local wsl_version
    if [[ -f /proc/version ]]; then
        if grep -qi "WSL2" /proc/version 2>/dev/null; then
            pass "Running WSL2"
        else
            pass "Running WSL1"
        fi
    fi

    # Check Windows interop
    if [[ -x /mnt/c/Windows/System32/cmd.exe ]]; then
        pass "Windows interop available"
    else
        skip "Windows interop not available"
    fi

    # Check tmux (required for shell-sage)
    if command_exists tmux; then
        pass "tmux installed (required for shell-sage)"
    else
        fail "tmux not installed (required for shell-sage)"
    fi

    # Check shell-sage
    if command_exists ssage; then
        pass "shell-sage installed"
    else
        skip "shell-sage not installed"
    fi

    # Check if Windows Terminal is the host
    if [[ -n "${WT_SESSION:-}" ]]; then
        pass "Running in Windows Terminal"
    else
        skip "Not running in Windows Terminal"
    fi
}

# =============================================================================
# Tests: Chezmoi State
# =============================================================================

test_chezmoi_state() {
    section "Chezmoi State"

    if ! command_exists chezmoi; then
        fail "Chezmoi not installed"
        return
    fi

    # Check if initialized
    if dir_exists "$HOME/.local/share/chezmoi"; then
        pass "Chezmoi is initialized"
    else
        fail "Chezmoi not initialized"
        return
    fi

    # Check for uncommitted changes
    local status
    status=$(chezmoi status 2>/dev/null || echo "error")
    if [[ -z "$status" ]]; then
        pass "Chezmoi status is clean"
    elif [[ "$status" == "error" ]]; then
        fail "Chezmoi status check failed"
    else
        info "Chezmoi has pending changes:"
        echo "$status" | head -5
        skip "Chezmoi has uncommitted changes"
    fi

    # Run chezmoi doctor
    if chezmoi doctor &>/dev/null; then
        pass "Chezmoi doctor passes"
    else
        fail "Chezmoi doctor found issues"
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    printf "${BLUE}╔════════════════════════════════════════════╗${NC}\n"
    printf "${BLUE}║      Dotfiles Setup Verification Tests     ║${NC}\n"
    printf "${BLUE}╚════════════════════════════════════════════╝${NC}\n"

    # Run all tests
    test_essential_commands
    test_cli_tools
    test_dotfiles_structure
    test_environment_variables
    test_shell_config
    test_git_config
    test_homebrew
    test_1password
    test_macos_specific
    test_wsl_specific
    test_chezmoi_state

    # Summary
    section "Summary"
    printf "${GREEN}Passed:${NC}  %d\n" "$TESTS_PASSED"
    printf "${RED}Failed:${NC}  %d\n" "$TESTS_FAILED"
    printf "${YELLOW}Skipped:${NC} %d\n" "$TESTS_SKIPPED"
    echo ""

    if [[ $TESTS_FAILED -gt 0 ]]; then
        printf "${RED}Some tests failed. Review the output above.${NC}\n"
        exit 1
    else
        printf "${GREEN}All tests passed!${NC}\n"
        exit 0
    fi
}

main "$@"
