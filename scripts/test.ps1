# Dotfiles setup verification tests for Windows
# Run with: dots test (or .\test.ps1)

$ErrorActionPreference = "Continue"

# =============================================================================
# Test Framework
# =============================================================================

$script:TestsPassed = 0
$script:TestsFailed = 0
$script:TestsSkipped = 0

function Pass {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
    $script:TestsPassed++
}

function Fail {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:TestsFailed++
}

function Skip {
    param($Message)
    Write-Host "○ $Message (skipped)" -ForegroundColor Yellow
    $script:TestsSkipped++
}

function Info {
    param($Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Section {
    param($Title)
    Write-Host ""
    Write-Host "━━━ $Title ━━━" -ForegroundColor Blue
}

function Test-CommandExists {
    param($Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# =============================================================================
# Tests: Essential Commands
# =============================================================================

function Test-EssentialCommands {
    Section "Essential Commands"

    $commands = @(
        @{ Cmd = "chezmoi"; Desc = "Dotfiles manager" }
        @{ Cmd = "git"; Desc = "Version control" }
        @{ Cmd = "nvim"; Desc = "Text editor" }
    )

    foreach ($entry in $commands) {
        if (Test-CommandExists $entry.Cmd) {
            Pass "$($entry.Desc) ($($entry.Cmd))"
        } else {
            Fail "$($entry.Desc) ($($entry.Cmd)) - not installed"
        }
    }
}

# =============================================================================
# Tests: CLI Tools
# =============================================================================

function Test-CliTools {
    Section "CLI Tools"

    $tools = @(
        @{ Cmd = "bat"; Desc = "Better cat" }
        @{ Cmd = "fd"; Desc = "Better find" }
        @{ Cmd = "rg"; Desc = "Ripgrep (better grep)" }
        @{ Cmd = "fzf"; Desc = "Fuzzy finder" }
        @{ Cmd = "starship"; Desc = "Shell prompt" }
        @{ Cmd = "jq"; Desc = "JSON processor" }
    )

    foreach ($entry in $tools) {
        if (Test-CommandExists $entry.Cmd) {
            Pass "$($entry.Desc) ($($entry.Cmd))"
        } else {
            Skip "$($entry.Desc) ($($entry.Cmd))"
        }
    }
}

# =============================================================================
# Tests: Dotfiles Structure
# =============================================================================

function Test-DotfilesStructure {
    Section "Dotfiles Structure"

    $chezmoiDir = Join-Path $env:USERPROFILE ".local\share\chezmoi"
    $configDir = Join-Path $env:USERPROFILE ".config"

    if (Test-Path $chezmoiDir) {
        Pass "Chezmoi source directory exists"
    } else {
        Fail "Chezmoi source directory missing"
    }

    if (Test-Path $configDir) {
        Pass "Config directory exists"
    } else {
        Fail "Config directory missing"
    }

    # Check PowerShell profile
    if (Test-Path $PROFILE) {
        Pass "PowerShell profile exists"
    } else {
        Skip "PowerShell profile not found"
    }

    # Check dots function
    $dotsScript = Join-Path $env:USERPROFILE ".config\powershell\dots.ps1"
    if (Test-Path $dotsScript) {
        Pass "Dots function script exists"
    } else {
        Skip "Dots function script not found"
    }
}

# =============================================================================
# Tests: Git Configuration
# =============================================================================

function Test-GitConfig {
    Section "Git Configuration"

    if (-not (Test-CommandExists "git")) {
        Fail "Git not installed"
        return
    }

    $gitName = git config --global user.name 2>$null
    if ($gitName) {
        Pass "Git user.name is set ($gitName)"
    } else {
        Fail "Git user.name not set"
    }

    $gitEmail = git config --global user.email 2>$null
    if ($gitEmail) {
        Pass "Git user.email is set ($gitEmail)"
    } else {
        Fail "Git user.email not set"
    }
}

# =============================================================================
# Tests: Scoop
# =============================================================================

function Test-Scoop {
    Section "Scoop Package Manager"

    if (-not (Test-CommandExists "scoop")) {
        Skip "Scoop not installed"
        return
    }

    Pass "Scoop is installed"

    # Check scoop health
    $scoopStatus = scoop status 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "Scoop is healthy"
    } else {
        Fail "Scoop has issues (run 'scoop status')"
    }
}

# =============================================================================
# Tests: 1Password Integration
# =============================================================================

function Test-1Password {
    Section "1Password Integration"

    if (-not (Test-CommandExists "op")) {
        Skip "1Password CLI not installed"
        return
    }

    Pass "1Password CLI is installed"

    $accounts = op account list 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "1Password CLI is configured"
    } else {
        Skip "1Password CLI not signed in"
    }
}

# =============================================================================
# Tests: WSL (Windows Subsystem for Linux)
# =============================================================================

function Test-WSL {
    Section "WSL (Windows Subsystem for Linux)"

    # Check if WSL is available
    if (-not (Test-CommandExists "wsl")) {
        Skip "WSL not installed"
        return
    }

    Pass "WSL is installed"

    # Check WSL version
    try {
        $wslVersion = wsl --version 2>$null | Select-String -Pattern "WSL version"
        if ($wslVersion) {
            Pass "WSL version: $($wslVersion -replace 'WSL version: ', '')"
        }
    } catch {
        Skip "Could not determine WSL version"
    }

    # Check for default distro
    $defaultDistro = wsl -l -q 2>$null | Select-Object -First 1
    if ($defaultDistro) {
        Pass "Default WSL distro: $($defaultDistro.Trim())"
    } else {
        Skip "No WSL distro installed"
        return
    }

    # Check if dotfiles are set up in WSL
    $wslChezmoiDir = wsl test -d ~/.local/share/chezmoi 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "Chezmoi initialized in WSL"
    } else {
        Skip "Chezmoi not initialized in WSL"
    }

    # Check if tmux is available in WSL (required for shell-sage)
    $wslTmux = wsl which tmux 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "tmux available in WSL (required for shell-sage)"
    } else {
        Skip "tmux not installed in WSL"
    }

    # Check if shell-sage is available in WSL
    $wslShellSage = wsl which ssage 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "shell-sage available in WSL"
    } else {
        Skip "shell-sage not installed in WSL"
    }
}

# =============================================================================
# Tests: Chezmoi State
# =============================================================================

function Test-ChezmoiState {
    Section "Chezmoi State"

    if (-not (Test-CommandExists "chezmoi")) {
        Fail "Chezmoi not installed"
        return
    }

    $chezmoiDir = Join-Path $env:USERPROFILE ".local\share\chezmoi"
    if (Test-Path $chezmoiDir) {
        Pass "Chezmoi is initialized"
    } else {
        Fail "Chezmoi not initialized"
        return
    }

    $status = chezmoi status 2>$null
    if ([string]::IsNullOrEmpty($status)) {
        Pass "Chezmoi status is clean"
    } else {
        Info "Chezmoi has pending changes:"
        $status | Select-Object -First 5
        Skip "Chezmoi has uncommitted changes"
    }

    $doctorResult = chezmoi doctor 2>$null
    if ($LASTEXITCODE -eq 0) {
        Pass "Chezmoi doctor passes"
    } else {
        Fail "Chezmoi doctor found issues"
    }
}

# =============================================================================
# Main
# =============================================================================

function Main {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║      Dotfiles Setup Verification Tests     ║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Blue

    Test-EssentialCommands
    Test-CliTools
    Test-DotfilesStructure
    Test-GitConfig
    Test-Scoop
    Test-1Password
    Test-WSL
    Test-ChezmoiState

    Section "Summary"
    Write-Host "Passed:  $script:TestsPassed" -ForegroundColor Green
    Write-Host "Failed:  $script:TestsFailed" -ForegroundColor Red
    Write-Host "Skipped: $script:TestsSkipped" -ForegroundColor Yellow
    Write-Host ""

    if ($script:TestsFailed -gt 0) {
        Write-Host "Some tests failed. Review the output above." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "All tests passed!" -ForegroundColor Green
        exit 0
    }
}

Main
