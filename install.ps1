# Dotfiles bootstrap script for Windows
# Usage: iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex
#
# Or run locally: .\install.ps1
#
# Environment variables:
#   $env:DOTFILES_DEBUG = 1     - Enable debug output
#   $env:DOTFILES_BRANCH = "xxx" - Use a specific branch (default: main)
#
# This script automatically detects the best installation method:
#   1. If Scoop is available → use Scoop for all packages
#   2. If winget is available → use winget for chezmoi, portable binaries for tools
#   3. Otherwise → download portable chezmoi, portable binaries for tools

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

# Check if command exists
function Test-Command {
    param($Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Detect installation mode
function Get-InstallMode {
    if (Test-Command "scoop") {
        return "scoop"
    }
    if (Test-Command "winget") {
        return "winget"
    }
    return "portable"
}

# Install chezmoi via the best available method
function Install-Chezmoi {
    if (Test-Command "chezmoi") {
        Write-Success "chezmoi already installed"
        return
    }

    $mode = Get-InstallMode

    switch ($mode) {
        "scoop" {
            Write-Info "Installing chezmoi via Scoop..."
            scoop install chezmoi
            Write-Success "chezmoi installed via Scoop"
        }
        "winget" {
            Write-Info "Installing chezmoi via winget..."
            winget install twpayne.chezmoi --accept-source-agreements --accept-package-agreements
            # Refresh PATH
            $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Success "chezmoi installed via winget"
        }
        "portable" {
            Write-Info "Installing chezmoi (portable binary)..."
            $chezmoiBin = Join-Path $env:USERPROFILE ".local\bin\chezmoi.exe"
            $chezmoiDir = Split-Path $chezmoiBin -Parent

            # Create directory
            if (-not (Test-Path $chezmoiDir)) {
                New-Item -ItemType Directory -Path $chezmoiDir -Force | Out-Null
            }

            # Download latest chezmoi
            $downloadUrl = "https://github.com/twpayne/chezmoi/releases/latest/download/chezmoi-windows-amd64.exe"
            try {
                Invoke-WebRequest -Uri $downloadUrl -OutFile $chezmoiBin -UseBasicParsing
                Write-Success "chezmoi installed to $chezmoiBin"
            } catch {
                Write-Err "Failed to download chezmoi: $_"
                exit 1
            }

            # Add to PATH for this session
            $env:PATH = "$chezmoiDir;$env:PATH"
        }
    }
}

# Install Git if needed (required for chezmoi init)
function Install-Git {
    if (Test-Command "git") {
        Write-Success "Git already installed"
        return
    }

    $mode = Get-InstallMode

    switch ($mode) {
        "scoop" {
            Write-Info "Installing Git via Scoop..."
            scoop install git
            Write-Success "Git installed via Scoop"
        }
        "winget" {
            Write-Info "Installing Git via winget..."
            winget install Git.Git --accept-source-agreements --accept-package-agreements
            # Refresh PATH
            $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Success "Git installed via winget"
        }
        "portable" {
            Write-Warn "Git not found and no package manager available."
            Write-Warn "Please install Git manually from: https://git-scm.com/download/win"
            Write-Warn "Or install winget/Scoop first."
            exit 1
        }
    }
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
    $mode = Get-InstallMode

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "Dotfiles installation complete!" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Installation mode: $mode" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Restart your terminal (PowerShell)"
    Write-Host ""
    Write-Host "  2. If errors occurred, run: chezmoi apply --keep-going"
    Write-Host ""

    if ($mode -eq "portable" -or $mode -eq "winget") {
        Write-Host "  3. Tools were installed as portable binaries to ~/.local/bin"
        Write-Host "     They will be available after restarting your terminal."
        Write-Host ""
    }

    Write-Host "Useful commands:"
    Write-Host "  chezmoi diff      - Preview changes"
    Write-Host "  chezmoi apply     - Apply changes"
    Write-Host "  chezmoi cd        - Go to dotfiles source"
    Write-Host "  chezmoi edit FILE - Edit a dotfile"
    Write-Host "  chezmoi update    - Pull and apply latest changes"
    Write-Host ""

    if ($mode -eq "scoop") {
        Write-Host "Package management (Scoop):"
        Write-Host "  scoop update *    - Update all packages"
        Write-Host "  scoop list        - List installed packages"
        Write-Host ""
    }

    Write-Host "To uninstall (when leaving this machine):"
    Write-Host "  ~/.local/share/chezmoi/scripts/uninstall.ps1"
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
    $mode = Get-InstallMode

    Write-Info "Detected: Windows $arch, Install mode: $mode"

    # Step 1: Install Git (required for chezmoi init)
    Install-Git

    # Step 2: Install chezmoi
    Install-Chezmoi

    # Step 3: Initialize dotfiles
    # This will:
    # - Prompt for personal/work/ephemeral settings
    # - If Scoop available: run Scoop install scripts
    # - If portable mode: pull binaries via .chezmoiexternal
    Initialize-Dotfiles

    # Step 4: Configure PowerShell profile
    Set-PowerShellProfile

    # Step 5: Show next steps
    Show-NextSteps
}

# Run main function
Main
