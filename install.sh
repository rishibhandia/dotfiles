#!/bin/sh
# Dotfiles bootstrap script
# Usage:
#   macOS/Linux: sh -c "$(curl -fsSL https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.sh)"
#   Windows (PowerShell): iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex
#
# Environment variables:
#   DOTFILES_DEBUG=1     - Enable debug output
#   DOTFILES_SKIP_BREW=1 - Skip Homebrew installation
#   DOTFILES_SKIP_DEPS=1 - Skip system dependencies installation
#   DOTFILES_BRANCH=xxx  - Use a specific branch (default: main)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

success() {
    printf "${GREEN}[OK]${NC} %s\n" "$1"
}

warn() {
    printf "${YELLOW}[WARN]${NC} %s\n" "$1"
}

error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1" >&2
}

debug() {
    if [ "${DOTFILES_DEBUG:-0}" = "1" ]; then
        printf "[DEBUG] %s\n" "$1"
    fi
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*)  echo "darwin" ;;
        Linux*)   echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

# Detect architecture
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64) echo "amd64" ;;
        arm64|aarch64) echo "arm64" ;;
        *)            echo "unknown" ;;
    esac
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect Linux distribution
detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    else
        echo "unknown"
    fi
}

# Install Xcode Command Line Tools (macOS)
install_xcode_cli() {
    if [ "$(detect_os)" != "darwin" ]; then
        return 0
    fi

    if xcode-select -p >/dev/null 2>&1; then
        success "Xcode Command Line Tools already installed"
        return 0
    fi

    info "Installing Xcode Command Line Tools..."
    xcode-select --install 2>/dev/null || true

    # Wait for installation to complete
    info "Waiting for Xcode CLI installation (press any key when done)..."
    until xcode-select -p >/dev/null 2>&1; do
        sleep 5
    done
    success "Xcode Command Line Tools installed"
}

# Install Linux build dependencies
install_linux_deps() {
    if [ "$(detect_os)" != "linux" ]; then
        return 0
    fi

    if [ "${DOTFILES_SKIP_DEPS:-0}" = "1" ]; then
        warn "Skipping Linux dependencies (DOTFILES_SKIP_DEPS=1)"
        return 0
    fi

    local distro=$(detect_linux_distro)
    info "Detected Linux distribution: $distro"

    case "$distro" in
        ubuntu|debian|pop|linuxmint|elementary)
            info "Installing build dependencies via apt..."
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                curl \
                file \
                git \
                procps \
                zsh \
                locales
            # Generate UTF-8 locale if needed
            if ! locale -a | grep -q "en_US.utf8"; then
                sudo locale-gen en_US.UTF-8
            fi
            success "apt dependencies installed"
            ;;
        fedora)
            info "Installing build dependencies via dnf..."
            sudo dnf groupinstall -y "Development Tools"
            sudo dnf install -y \
                curl \
                file \
                git \
                procps-ng \
                zsh \
                util-linux-user
            success "dnf dependencies installed"
            ;;
        centos|rhel|rocky|almalinux)
            info "Installing build dependencies via yum..."
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y \
                curl \
                file \
                git \
                procps-ng \
                zsh \
                util-linux-user
            success "yum dependencies installed"
            ;;
        arch|manjaro|endeavouros)
            info "Installing build dependencies via pacman..."
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm --needed \
                base-devel \
                curl \
                file \
                git \
                procps-ng \
                zsh
            success "pacman dependencies installed"
            ;;
        opensuse*|suse*)
            info "Installing build dependencies via zypper..."
            sudo zypper install -y -t pattern devel_basis
            sudo zypper install -y \
                curl \
                file \
                git \
                procps \
                zsh
            success "zypper dependencies installed"
            ;;
        alpine)
            info "Installing build dependencies via apk..."
            sudo apk add --no-cache \
                build-base \
                curl \
                file \
                git \
                procps \
                zsh \
                bash \
                shadow
            success "apk dependencies installed"
            ;;
        *)
            warn "Unknown Linux distribution: $distro"
            warn "Please manually install: build-essential, curl, git, zsh"
            ;;
    esac
}

# Install Homebrew
install_homebrew() {
    if [ "${DOTFILES_SKIP_BREW:-0}" = "1" ]; then
        warn "Skipping Homebrew installation (DOTFILES_SKIP_BREW=1)"
        return 0
    fi

    local os=$(detect_os)
    if [ "$os" != "darwin" ] && [ "$os" != "linux" ]; then
        debug "Homebrew not supported on $os"
        return 0
    fi

    if command_exists brew; then
        success "Homebrew already installed"
        return 0
    fi

    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for this session
    if [ "$(detect_os)" = "darwin" ]; then
        if [ "$(detect_arch)" = "arm64" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    fi

    success "Homebrew installed"
}

# Install chezmoi
install_chezmoi() {
    if command_exists chezmoi; then
        success "chezmoi already installed"
        return 0
    fi

    info "Installing chezmoi..."

    local bin_dir="${HOME}/.local/bin"
    mkdir -p "$bin_dir"

    if command_exists curl; then
        sh -c "$(curl -fsSL https://get.chezmoi.io)" -- -b "$bin_dir"
    elif command_exists wget; then
        sh -c "$(wget -qO- https://get.chezmoi.io)" -- -b "$bin_dir"
    else
        error "curl or wget is required to install chezmoi"
        exit 1
    fi

    # Add to PATH for this session
    export PATH="$bin_dir:$PATH"

    success "chezmoi installed to $bin_dir"
}

# Initialize dotfiles with chezmoi
init_dotfiles() {
    local branch="${DOTFILES_BRANCH:-main}"
    local github_user="rishibhandia"

    info "Initializing dotfiles from github.com/$github_user/dotfiles (branch: $branch)..."

    if [ -d "${HOME}/.local/share/chezmoi" ]; then
        warn "chezmoi source directory already exists"
        info "Running chezmoi apply..."
        chezmoi apply --keep-going || {
            warn "Some errors occurred during apply. Run 'chezmoi apply' again after fixing issues."
        }
    else
        chezmoi init --apply "$github_user" --branch "$branch" --keep-going || {
            warn "Some errors occurred during init. Run 'chezmoi apply' again after fixing issues."
        }
    fi

    success "Dotfiles initialized"
}

# Post-installation message
print_next_steps() {
    local os=$(detect_os)

    echo ""
    echo "=============================================="
    printf "${GREEN}Dotfiles installation complete!${NC}\n"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo "  1. Restart your terminal or run:"
    echo "     source ~/.zshenv && source ~/.config/zsh/.zshrc"
    echo ""
    echo "  2. If errors occurred, run: chezmoi apply --keep-going"
    echo ""

    # Only show 1Password instructions if not signed in
    if ! command_exists op || ! op whoami >/dev/null 2>&1; then
        echo "  3. For 1Password integration (required for API keys):"
        if [ "$os" = "darwin" ]; then
            echo "     - Install 1Password from App Store or: brew install --cask 1password"
            echo "     - Enable CLI integration in 1Password > Settings > Developer"
        else
            echo "     - Install 1Password CLI: https://1password.com/downloads/command-line/"
        fi
        echo "     - Sign in: op signin"
        echo "     - Re-run: chezmoi apply"
        echo ""
    fi

    if [ "$os" = "linux" ]; then
        echo "  3. Log out and back in for shell change to take effect"
        echo ""
    fi

    echo "Useful commands:"
    echo "  chezmoi diff      - Preview changes"
    echo "  chezmoi apply     - Apply changes"
    echo "  chezmoi cd        - Go to dotfiles source"
    echo "  chezmoi edit FILE - Edit a dotfile"
    echo "  chezmoi update    - Pull and apply latest changes"
    echo ""

    if [ "$os" = "darwin" ]; then
        echo "macOS-specific:"
        echo "  make macos        - Apply macOS system preferences"
        echo ""
    fi
}

# Setup 1Password CLI
setup_onepassword() {
    # Check if op is installed (should be after Brewfile packages are installed)
    if ! command_exists op; then
        warn "1Password CLI (op) not found. Skipping 1Password setup."
        warn "Some dotfiles templates require 1Password for API keys."
        return 0
    fi

    # Check if already signed in
    if op whoami >/dev/null 2>&1; then
        success "1Password CLI already signed in"
        return 0
    fi

    echo ""
    info "1Password CLI is installed but not signed in."
    info "Your dotfiles use 1Password to securely store API keys."
    echo ""

    # Ask user if they want to sign in now
    printf "${YELLOW}Would you like to sign in to 1Password now? [Y/n] ${NC}"
    read -r response

    case "$response" in
        [nN][oO]|[nN])
            warn "Skipping 1Password sign-in."
            warn "Run 'op signin' and then 'chezmoi apply' later to complete setup."
            return 0
            ;;
        *)
            info "Starting 1Password sign-in..."
            echo ""
            echo "If you haven't added an account yet, run: op account add"
            echo "Otherwise, signing in now..."
            echo ""

            if op signin; then
                success "1Password sign-in successful"

                info "Re-applying dotfiles with 1Password integration..."
                chezmoi apply --keep-going || {
                    warn "Some errors occurred during apply."
                }
                success "Dotfiles re-applied with 1Password secrets"
            else
                warn "1Password sign-in failed or was cancelled."
                warn "Run 'op signin' and then 'chezmoi apply' later to complete setup."
            fi
            ;;
    esac
}

# Change default shell to zsh
set_zsh_default() {
    if [ "$(detect_os)" = "windows" ]; then
        return 0
    fi

    if [ "$SHELL" = "$(command -v zsh)" ]; then
        success "zsh is already the default shell"
        return 0
    fi

    if ! command_exists zsh; then
        warn "zsh not found, skipping shell change"
        return 0
    fi

    local zsh_path=$(command -v zsh)

    # Add zsh to /etc/shells if not present
    if ! grep -q "$zsh_path" /etc/shells 2>/dev/null; then
        info "Adding zsh to /etc/shells..."
        echo "$zsh_path" | sudo tee -a /etc/shells >/dev/null
    fi

    info "Changing default shell to zsh..."
    if command_exists chsh; then
        chsh -s "$zsh_path" || warn "Failed to change shell. Run manually: chsh -s $zsh_path"
    else
        warn "chsh not found. Please change your shell manually to: $zsh_path"
    fi
}

# Main installation flow
main() {
    echo ""
    echo "=============================================="
    echo "  Dotfiles Bootstrap Script"
    echo "  github.com/rishibhandia/dotfiles"
    echo "=============================================="
    echo ""

    local os=$(detect_os)
    local arch=$(detect_arch)
    info "Detected OS: $os, Architecture: $arch"

    # Check for Windows - redirect to PowerShell script
    if [ "$os" = "windows" ]; then
        error "This script is for macOS/Linux. For Windows, use PowerShell:"
        echo ""
        echo "  iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex"
        echo ""
        exit 1
    fi

    # Step 1: Install OS-specific prerequisites
    case "$os" in
        darwin)
            install_xcode_cli
            ;;
        linux)
            install_linux_deps
            ;;
    esac

    # Step 2: Install Homebrew (macOS and Linux)
    install_homebrew

    # Step 3: Install chezmoi
    install_chezmoi

    # Step 4: Initialize dotfiles
    init_dotfiles

    # Step 5: Setup 1Password (prompts for sign-in if needed)
    setup_onepassword

    # Step 6: Set zsh as default shell
    set_zsh_default

    # Step 7: Show next steps
    print_next_steps
}

# Run main function
main "$@"
