# Dotfiles bootstrap script for Windows
# Usage: iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex
#
# Or run locally: .\install.ps1
#
# Environment variables:
#   $env:DOTFILES_DEBUG = 1     - Enable debug output
#   $env:DOTFILES_BRANCH = "xxx" - Use a specific branch (default: main)

#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# Configuration
$GITHUB_USER = "rishibhandia"
$BRANCH = if ($env:DOTFILES_BRANCH) { $env:DOTFILES_BRANCH } else { "main" }

# Colors
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Debug {
    param($Message)
    if ($env:DOTFILES_DEBUG -eq "1") { Write-Host "[DEBUG] $Message" }
}

# Check if running as admin
function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if command exists
function Test-Command {
    param($Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Install Scoop package manager
function Install-Scoop {
    if (Test-Command "scoop") {
        Write-Success "Scoop already installed"
        return
    }

    Write-Info "Installing Scoop package manager..."

    # Set execution policy for current user if needed
    $policy = Get-ExecutionPolicy -Scope CurrentUser
    if ($policy -eq "Restricted") {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    }

    # Install Scoop
    Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

    Write-Success "Scoop installed"
}

# Install Git via Scoop
function Install-Git {
    if (Test-Command "git") {
        Write-Success "Git already installed"
        return
    }

    Write-Info "Installing Git..."
    scoop install git
    Write-Success "Git installed"
}

# Install chezmoi
function Install-Chezmoi {
    if (Test-Command "chezmoi") {
        Write-Success "chezmoi already installed"
        return
    }

    Write-Info "Installing chezmoi..."
    scoop install chezmoi
    Write-Success "chezmoi installed"
}

# Install common tools via Scoop
function Install-CommonTools {
    Write-Info "Installing common tools..."

    # Add extras bucket for more applications
    scoop bucket add extras 2>$null

    $tools = @(
        "neovim",
        "starship",
        "fzf",
        "ripgrep",
        "fd",
        "bat",
        "jq",
        "curl"
    )

    foreach ($tool in $tools) {
        if (-not (Test-Command $tool)) {
            Write-Info "Installing $tool..."
            scoop install $tool 2>$null
        } else {
            Write-Debug "$tool already installed"
        }
    }

    Write-Success "Common tools installed"
}

# Initialize dotfiles
function Initialize-Dotfiles {
    Write-Info "Initializing dotfiles from github.com/$GITHUB_USER/dotfiles (branch: $BRANCH)..."

    $chezmoiDir = Join-Path $env:USERPROFILE ".local\share\chezmoi"

    if (Test-Path $chezmoiDir) {
        Write-Warn "chezmoi source directory already exists"
        Write-Info "Running chezmoi apply..."
        & chezmoi apply --keep-going
    } else {
        & chezmoi init --apply $GITHUB_USER --branch $BRANCH --keep-going
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Some errors occurred. Run 'chezmoi apply' again after fixing issues."
    }

    Write-Success "Dotfiles initialized"
}

# Configure PowerShell profile
function Set-PowerShellProfile {
    Write-Info "Configuring PowerShell profile..."

    # Ensure profile directory exists
    $profileDir = Split-Path $PROFILE -Parent
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }

    # Add dotfiles profile (includes PATH setup, starship, zoxide, and dots functions)
    $profileScript = Join-Path $env:USERPROFILE ".config\powershell\profile.ps1"
    if (-not (Test-Path $PROFILE) -or -not (Select-String -Path $PROFILE -Pattern "profile.ps1" -Quiet)) {
        $profileContent = @(
            "",
            "# Dotfiles profile (PATH, starship, zoxide, dots functions)",
            "if (Test-Path `"$profileScript`") { . `"$profileScript`" }"
        )
        Add-Content -Path $PROFILE -Value ($profileContent -join "`n")
        Write-Success "Added dotfiles profile to PowerShell profile"
    } else {
        Write-Debug "Dotfiles profile already in PowerShell profile"
    }
}

# Print next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "Dotfiles installation complete!" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Restart your terminal (PowerShell)"
    Write-Host ""
    Write-Host "  2. If errors occurred, run: chezmoi apply --keep-going"
    Write-Host ""
    Write-Host "  3. For 1Password integration:"
    Write-Host "     - Install 1Password from: https://1password.com/downloads"
    Write-Host "     - Enable CLI in 1Password > Settings > Developer"
    Write-Host "     - Sign in: op signin"
    Write-Host "     - Re-run: chezmoi apply"
    Write-Host ""
    Write-Host "Useful commands:"
    Write-Host "  chezmoi diff      - Preview changes"
    Write-Host "  chezmoi apply     - Apply changes"
    Write-Host "  chezmoi cd        - Go to dotfiles source"
    Write-Host "  chezmoi edit FILE - Edit a dotfile"
    Write-Host "  chezmoi update    - Pull and apply latest changes"
    Write-Host ""
    Write-Host "Windows-specific:"
    Write-Host "  scoop update *    - Update all Scoop packages"
    Write-Host "  scoop list        - List installed packages"
    Write-Host ""
}

# Main function
function Main {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Dotfiles Bootstrap Script (Windows)" -ForegroundColor Cyan
    Write-Host "  github.com/$GITHUB_USER/dotfiles" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    $arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "x86" }
    Write-Info "Detected OS: Windows, Architecture: $arch"

    # Check for admin rights (optional, warn only)
    if (-not (Test-Admin)) {
        Write-Warn "Running without administrator privileges. Some operations may require elevation."
    }

    # Step 1: Install Scoop
    Install-Scoop

    # Step 2: Install Git
    Install-Git

    # Step 3: Install chezmoi
    Install-Chezmoi

    # Step 4: Install common tools
    Install-CommonTools

    # Step 5: Initialize dotfiles
    Initialize-Dotfiles

    # Step 6: Configure PowerShell
    Set-PowerShellProfile

    # Step 7: Show next steps
    Show-NextSteps
}

# Run main function
Main
