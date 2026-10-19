# Dotfiles bootstrap script for Windows
# Usage: iwr -useb https://raw.githubusercontent.com/rishibhandia/dotfiles/main/install.ps1 | iex
#
# Or run locally: .\install.ps1
#
# Environment variables:
#   $env:DOTFILES_DEBUG = 1      - Enable debug output
#   $env:DOTFILES_BRANCH = "xxx" - Use a specific branch (default: main)
#   $env:DOTFILES_PORTABLE = 1   - Skip Scoop install, force portable mode
#   $env:DOTFILES_WORK = 1       - Work machine (skip the personal/work prompt)
#   $env:DOTFILES_PERSONAL = 1   - Personal machine (skip the prompt)
#
# Installation method:
#   0. Decide personal vs. work first (env var, previous chezmoi answer, or
#      prompt). Unknown/non-interactive machines are treated as work.
#   Work: never touches Scoop. git/chezmoi via winget --scope user, else
#      portable binaries; chezmoi then installs portable tools to ~/.local.
#      No admin rights and no execution-policy changes needed.
#   Personal: install Scoop if missing (unless DOTFILES_PORTABLE=1), use it
#      for git/chezmoi, and let chezmoi run the Scoopfile package scripts.
#      If Scoop can't be installed, fall back to the portable path.

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

# Machine type ("personal" or "work"), set once by Get-MachineType in Main
$script:MachineType = "work"

# Decide personal vs. work BEFORE any package-manager step: work machines
# must never get Scoop. Order: env override, the answer cached by a previous
# chezmoi init, then an interactive prompt. Non-interactive with no override
# is treated as work (chezmoi profiles it ephemeral+work the same way).
# The answer is exported as DOTFILES_WORK / DOTFILES_PERSONAL, which
# .chezmoi.toml.tmpl reads, so chezmoi init doesn't ask again.
function Get-MachineType {
    if (($env:DOTFILES_WORK -eq "1") -and ($env:DOTFILES_PERSONAL -eq "1")) {
        Write-Err "DOTFILES_WORK and DOTFILES_PERSONAL are both set; set only one."
        exit 1
    }
    if ($env:DOTFILES_WORK -eq "1") { return "work" }
    if ($env:DOTFILES_PERSONAL -eq "1") { return "personal" }

    $answer = $null
    $config = Join-Path $env:USERPROFILE ".config\chezmoi\chezmoi.toml"
    $cached = if (Test-Path $config) { Select-String -Path $config -Pattern '^\s*personal\s*=\s*(true|false)' | Select-Object -First 1 } else { $null }
    if ($cached) {
        $answer = if ($cached.Matches[0].Groups[1].Value -eq "true") { "personal" } else { "work" }
        Write-Info "Using machine type '$answer' from $config"
        Write-Info "(set DOTFILES_WORK=1 or DOTFILES_PERSONAL=1 to change it)"
    } elseif ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
        $reply = Read-Host "Is this a personal machine (has 1Password, personal secrets)? [y/N]"
        $answer = if ($reply -match '^(y|yes)$') { "personal" } else { "work" }
    } else {
        Write-Info "Non-interactive and no DOTFILES_WORK/DOTFILES_PERSONAL set - treating as work"
        return "work"
    }

    if ($answer -eq "personal") { $env:DOTFILES_PERSONAL = "1" } else { $env:DOTFILES_WORK = "1" }
    return $answer
}

# Detect installation mode. Work machines never use Scoop, even if present.
function Get-InstallMode {
    if (($script:MachineType -eq "personal") -and (Test-Command "scoop")) {
        return "scoop"
    }
    if (Test-Command "winget") {
        return "winget"
    }
    return "portable"
}

# Add a directory to the user PATH (persisted) and to this session
function Add-UserPath {
    param($Dir)
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    $segments = if ([string]::IsNullOrEmpty($userPath)) { @() } else { $userPath -split ';' }
    if ($segments -notcontains $Dir) {
        $newPath = if ([string]::IsNullOrEmpty($userPath)) { $Dir } else { "$userPath;$Dir" }
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    }
    if (($env:PATH -split ';') -notcontains $Dir) {
        $env:PATH = "$Dir;$env:PATH"
    }
}

# winget install; personal machines keep the default (machine) scope,
# work machines use --scope user so no admin/UAC is ever needed.
# Returns $true on success.
function Install-WithWinget {
    param($Id)
    $wingetArgs = @("install", "--id", $Id, "--exact", "--accept-source-agreements", "--accept-package-agreements")
    if ($script:MachineType -eq "work") { $wingetArgs += @("--scope", "user") }
    # EAP=Stop doesn't catch native-command failures; check the exit code.
    # Out-Host keeps winget's output out of this function's return value.
    & winget @wingetArgs | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "winget failed to install $Id (exit $LASTEXITCODE)"
        return $false
    }
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    return $true
}

# Install Scoop so chezmoi init detects the full (non-portable) profile.
# chezmoi sets portable=true whenever scoop is missing at init time, so
# without this step a fresh machine always lands in portable mode.
# Set $env:DOTFILES_PORTABLE = 1 to skip Scoop and force portable mode.
function Install-Scoop {
    if ($script:MachineType -eq "work") {
        Write-Info "Work machine - skipping Scoop (portable mode)"
        return
    }
    if (Test-Command "scoop") {
        Write-Success "Scoop already installed"
        return
    }
    if ($env:DOTFILES_PORTABLE -eq "1") {
        Write-Info "DOTFILES_PORTABLE=1 set - skipping Scoop (portable mode)"
        return
    }

    # Scoop's shims are .ps1 scripts, so a policy that blocks scripts makes
    # Scoop unusable in every later shell even if the installer is forced
    # through. Check first instead of changing the machine's policy.
    $policy = (Get-ExecutionPolicy).ToString()
    if ($policy -notin @("Unrestricted", "RemoteSigned", "Bypass")) {
        Write-Warn "Execution policy is '$policy'; Scoop needs RemoteSigned or looser."
        Write-Warn "To use Scoop, run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
        Write-Warn "then re-run this script. Continuing in portable mode."
        return
    }

    Write-Info "Installing Scoop (user-scope package manager)..."
    # get.scoop.sh aborts with a bare `break` when run through iex (its
    # Exit-Install), which unwinds through any try/catch and silently ends
    # this whole script. Run it as a -File child process instead: there
    # Exit-Install uses `exit`, so only the child ends and we get an exit
    # code. -ExecutionPolicy Bypass applies to that one process only.
    $installer = Join-Path $env:TEMP "scoop-install-$PID.ps1"
    try {
        Invoke-WebRequest -Uri "https://get.scoop.sh" -OutFile $installer -UseBasicParsing
        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
            ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        $childArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $installer)
        # get.scoop.sh refuses elevated shells unless -RunAsAdmin is passed
        if ($isAdmin) { $childArgs += "-RunAsAdmin" }
        $hostExe = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
        & $hostExe @childArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "Scoop installer exited with code $LASTEXITCODE"
        }
    } catch {
        Write-Warn "Scoop installation failed: $_"
    } finally {
        Remove-Item $installer -Force -ErrorAction SilentlyContinue
    }

    # The installer updates the user PATH; make shims visible to this session
    $shims = Join-Path $env:USERPROFILE "scoop\shims"
    if ((Test-Path $shims) -and ($env:PATH -notlike "*$shims*")) {
        $env:PATH = "$env:PATH;$shims"
    }

    if (Test-Command "scoop") {
        Write-Success "Scoop installed"
    } else {
        Write-Warn "Scoop unavailable - continuing in portable mode"
    }
}

# Install chezmoi via the best available method
function Install-Chezmoi {
    if (Test-Command "chezmoi") {
        Write-Success "chezmoi already installed"
        return
    }

    $mode = Get-InstallMode

    if ($mode -eq "scoop") {
        Write-Info "Installing chezmoi via Scoop..."
        scoop install chezmoi
        Write-Success "chezmoi installed via Scoop"
        return
    }
    if ($mode -eq "winget") {
        Write-Info "Installing chezmoi via winget..."
        if (Install-WithWinget "twpayne.chezmoi") {
            Write-Success "chezmoi installed via winget"
            return
        }
        Write-Warn "Falling back to the portable chezmoi binary"
    }

    Write-Info "Installing chezmoi (portable binary)..."
    $chezmoiDir = Join-Path $env:USERPROFILE ".local\bin"
    $chezmoiBin = Join-Path $chezmoiDir "chezmoi.exe"
    if (-not (Test-Path $chezmoiDir)) {
        New-Item -ItemType Directory -Path $chezmoiDir -Force | Out-Null
    }
    $downloadUrl = "https://github.com/twpayne/chezmoi/releases/latest/download/chezmoi-windows-amd64.exe"
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $chezmoiBin -UseBasicParsing
        Write-Success "chezmoi installed to $chezmoiBin"
    } catch {
        Write-Err "Failed to download chezmoi: $_"
        exit 1
    }
    Add-UserPath $chezmoiDir
}

# Install Git if needed (required for chezmoi init)
function Install-Git {
    if (Test-Command "git") {
        Write-Success "Git already installed"
        return
    }

    $mode = Get-InstallMode

    if ($mode -eq "scoop") {
        Write-Info "Installing Git via Scoop..."
        scoop install git
        Write-Success "Git installed via Scoop"
        return
    }
    if ($mode -eq "winget") {
        Write-Info "Installing Git via winget..."
        if (Install-WithWinget "Git.Git") {
            Write-Success "Git installed via winget"
            return
        }
        Write-Warn "Falling back to portable Git"
    }
    Install-PortableGit
}

# Portable Git for Windows (self-extracting PortableGit archive from the
# official git-for-windows releases) into ~\.local\opt\git. No admin needed.
function Install-PortableGit {
    Write-Info "Installing Git (PortableGit from github.com/git-for-windows)..."
    $gitDir = Join-Path $env:USERPROFILE ".local\opt\git"
    try {
        $release = Invoke-RestMethod "https://api.github.com/repos/git-for-windows/git/releases/latest" -UseBasicParsing
        $asset = $release.assets | Where-Object { $_.name -like "PortableGit-*-64-bit.7z.exe" } | Select-Object -First 1
        if (-not $asset) { throw "no PortableGit asset in release $($release.tag_name)" }
        $sfx = Join-Path $env:TEMP $asset.name
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $sfx -UseBasicParsing
        Write-Info "$($asset.name) SHA256: $((Get-FileHash $sfx -Algorithm SHA256).Hash)"
        New-Item -ItemType Directory -Path $gitDir -Force | Out-Null
        # 7-Zip SFX: -o<dir> extracts there, -y answers yes to every prompt
        Start-Process -FilePath $sfx -ArgumentList "-o`"$gitDir`"", "-y" -Wait
        Remove-Item $sfx -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Err "Failed to install portable Git: $_"
        Write-Err "Install Git manually from https://git-scm.com/download/win and re-run."
        exit 1
    }
    Add-UserPath (Join-Path $gitDir "cmd")
    if (-not (Test-Command "git")) {
        Write-Err "Portable Git extracted to $gitDir but git.exe was not found"
        exit 1
    }
    Write-Success "Git installed to $gitDir"
}

# Initialize dotfiles
function Initialize-Dotfiles {
    Write-Info "Initializing dotfiles from github.com/$GITHUB_USER/dotfiles (branch: $BRANCH)..."

    $chezmoiDir = Join-Path $env:USERPROFILE ".local\share\chezmoi"

    if (Test-Path $chezmoiDir) {
        # Re-run the config template (not just apply) so the machine type
        # decided above, and work => portable, take effect on re-runs too.
        Write-Warn "chezmoi source directory already exists - regenerating config"
        & chezmoi init --apply --keep-going
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

    # Hook both Windows PowerShell 5.1 and PowerShell 7 (psmux's default shell
    # where pwsh is installed): each reads its own profile under Documents.
    $docs = [Environment]::GetFolderPath("MyDocuments")
    $profiles = @(
        (Join-Path $docs "WindowsPowerShell\Microsoft.PowerShell_profile.ps1"),
        (Join-Path $docs "PowerShell\Microsoft.PowerShell_profile.ps1")
    )

    # Add dotfiles profile (includes PATH setup, starship, zoxide, and dots functions)
    $profileScript = Join-Path $env:USERPROFILE ".config\powershell\profile.ps1"
    foreach ($hostProfile in $profiles) {
        $profileDir = Split-Path $hostProfile -Parent
        if (-not (Test-Path $profileDir)) {
            New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
        }
        if (-not (Test-Path $hostProfile) -or -not (Select-String -Path $hostProfile -Pattern "profile.ps1" -Quiet)) {
            $profileContent = @(
                "",
                "# Dotfiles profile (PATH, starship, zoxide, dots functions)",
                "if (Test-Path `"$profileScript`") { . `"$profileScript`" }"
            )
            Add-Content -Path $hostProfile -Value ($profileContent -join "`n")
            Write-Success "Added dotfiles profile to $hostProfile"
        } else {
            Write-Debug "Dotfiles profile already in $hostProfile"
        }
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

    # Step 0: Machine type decides whether Scoop is allowed at all
    $script:MachineType = Get-MachineType
    $mode = Get-InstallMode
    Write-Info "Detected: Windows $arch, machine: $($script:MachineType), install mode: $mode"

    # Step 1: Install Scoop (personal only; work machines stay portable)
    Install-Scoop
    $mode = Get-InstallMode
    Write-Info "Install mode after Scoop bootstrap: $mode"

    # Step 2: Install Git (required for chezmoi init)
    Install-Git

    # Step 3: Install chezmoi
    Install-Chezmoi

    # Step 4: Initialize dotfiles
    # This will:
    # - Personal/work already answered via DOTFILES_WORK/DOTFILES_PERSONAL;
    #   only the ephemeral question is asked
    # - Personal with Scoop: run Scoop install scripts
    # - Work, or no Scoop: portable binaries via .chezmoiexternal
    Initialize-Dotfiles

    # Step 5: Configure PowerShell profile
    Set-PowerShellProfile

    # Step 6: Show next steps
    Show-NextSteps
}

# Run main function
Main
