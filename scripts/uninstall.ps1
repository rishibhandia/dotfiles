# Dotfiles Uninstaller for Windows
# Removes what this repo's `chezmoi apply` actually wrote - for a clean
# departure from work machines. Deliberately does NOT touch directories that
# hold data this repo never created (Claude Code credentials/history, Claude
# Desktop app data, cargo/rustup toolchains, unrelated binaries in ~\.local\bin).
#
# Usage: .\uninstall.ps1 [-Force]
#
# Options:
#   -Force    Skip confirmation prompt

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Dotfiles Uninstaller" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Chezmoi-managed configs (whole dirs/files this repo owns)
$ToRemove = @(
    (Join-Path $env:USERPROFILE ".local\share\chezmoi"),      # Chezmoi source
    (Join-Path $env:USERPROFILE ".config\chezmoi"),           # Chezmoi config
    (Join-Path $env:USERPROFILE ".config\powershell"),        # PowerShell config
    (Join-Path $env:USERPROFILE ".config\starship"),          # Starship config (config.toml lives in the dir)
    (Join-Path $env:USERPROFILE ".config\git"),               # Git config
    (Join-Path $env:USERPROFILE ".config\nvim"),              # Neovim config (Unix-style location)
    (Join-Path $env:USERPROFILE ".config\psmux"),             # psmux config
    (Join-Path $env:USERPROFILE ".config\windows-terminal"),  # WT color scheme source
    (Join-Path $env:USERPROFILE ".config\shell_sage"),        # Shell Sage config
    (Join-Path $env:USERPROFILE ".local\share\navi"),         # navi cheats
    (Join-Path $env:USERPROFILE ".gitconfig"),                # Git config (legacy location)
    (Join-Path $env:USERPROFILE ".bashrc"),                   # Git Bash config (repo-managed on Windows)
    (Join-Path $env:USERPROFILE ".bash_profile"),             # Git Bash profile
    (Join-Path $env:USERPROFILE ".Scoopfile"),                # Package manifest
    (Join-Path $env:USERPROFILE ".ssh\config"),               # repo-managed ssh config (keys untouched)
    (Join-Path $env:LOCALAPPDATA "nvim"),                     # Neovim config (Windows location) + plugins
    # Claude Code: only the chezmoi-managed pieces. ~\.claude also holds
    # credentials and history, so never delete the whole directory.
    (Join-Path $env:USERPROFILE ".claude\skills"),
    (Join-Path $env:USERPROFILE ".claude\agents"),
    (Join-Path $env:USERPROFILE ".claude\CLAUDE.md"),
    (Join-Path $env:USERPROFILE ".claude\settings.json"),
    (Join-Path $env:USERPROFILE ".claude\statusline.ps1"),
    (Join-Path $env:USERPROFILE ".claude\statusline.sh")
)

# Binaries this repo downloads into ~\.local\bin (portable mode + rtk + the
# Astral uv installer). Listed individually so unrelated user binaries survive.
$binDir = Join-Path $env:USERPROFILE ".local\bin"
$repoBins = @("rg", "fd", "bat", "fzf", "zoxide", "starship", "lsd", "jq", "yq",
    "gh", "duf", "fastfetch", "ruff", "rtk", "uv", "uvx", "uvw", "chezmoi", "claude")
$ToRemove += ($repoBins | ForEach-Object { Join-Path $binDir "$_.exe" })
$ToRemove += (Join-Path $binDir "psmux")                      # psmux install dir
# Claude Code native-installer versions (the binary store behind claude.exe;
# login/history live in ~\.claude and are kept, see above)
$ToRemove += (Join-Path $env:USERPROFILE ".local\share\claude")
# Multi-file portable installs (install.ps1 / cli-tools scripts)
$optDir = Join-Path $env:USERPROFILE ".local\opt"
$ToRemove += (Join-Path $optDir "git")                        # PortableGit (work machines)
$ToRemove += (Join-Path $optDir "pwsh")                       # PowerShell 7 zip (portable)
$ToRemove += (Join-Path $optDir "windows-terminal")           # Windows Terminal zip fallback

# User PATH entries this repo adds (install.ps1, the PowerShell profile, and
# the cli-tools script). Removed by exact segment match below.
$repoPathEntries = @(
    $binDir,
    (Join-Path $binDir "psmux"),
    (Join-Path $optDir "git\cmd"),
    (Join-Path $optDir "pwsh"),
    (Join-Path $optDir "windows-terminal")
)

# Check what exists
$ExistingPaths = @($ToRemove | Where-Object { Test-Path $_ })

if ($ExistingPaths.Count -eq 0) {
    Write-Host "Nothing to remove. Dotfiles not installed or already cleaned up." -ForegroundColor Yellow
    exit 0
}

# Show what will be removed
Write-Host "The following will be removed:" -ForegroundColor Yellow
Write-Host ""
foreach ($path in $ExistingPaths) {
    $size = ""
    if (Test-Path $path -PathType Container) {
        $sizeBytes = (Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue |
                      Measure-Object -Property Length -Sum).Sum
        if ($sizeBytes) {
            $sizeMB = [math]::Round($sizeBytes / 1MB, 1)
            $size = " ($sizeMB MB)"
        }
    }
    Write-Host "  - $path$size"
}
Write-Host ""
Write-Host "Kept on purpose: ~\.claude credentials/history, Claude Desktop data," -ForegroundColor Yellow
Write-Host "~\.cargo, ~\.rustup, and anything else in ~\.local\bin." -ForegroundColor Yellow
Write-Host ""

# Confirm unless -Force
if (-not $Force) {
    $confirm = Read-Host "Proceed with removal? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
    Write-Host ""
}

# Remove paths
$removed = 0
$failed = 0

foreach ($path in $ExistingPaths) {
    Write-Host "Removing $path..." -NoNewline
    try {
        Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
        Write-Host " OK" -ForegroundColor Green
        $removed++
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        $failed++
    }
}

# Hack Nerd Font (portable-mode per-user install): files + registry values.
# The fonts dir is shared with other per-user fonts, so remove only Hack files.
$fontDir = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
$fontReg = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
$hackFonts = @(Get-ChildItem "$fontDir\HackNerdFont*.ttf" -ErrorAction SilentlyContinue) +
             @(Get-ChildItem "$fontDir\Hack*Nerd*.ttf" -ErrorAction SilentlyContinue) |
             Sort-Object FullName -Unique
foreach ($font in $hackFonts) {
    try {
        Remove-ItemProperty -Path $fontReg -Name "$($font.BaseName) (TrueType)" -ErrorAction SilentlyContinue
        Remove-Item $font.FullName -Force -ErrorAction Stop
        Write-Host "Removed font $($font.Name)" -ForegroundColor Green
        $removed++
    } catch {
        Write-Host "Could not remove font $($font.Name) (in use? sign out and retry): $_" -ForegroundColor Red
        $failed++
    }
}

# User PATH entries added by this repo (exact segment match, so unrelated
# entries such as a different ~\.local\bin\foo survive)
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath) {
    $segments = @($userPath -split ';')
    $kept = @($segments | Where-Object { $repoPathEntries -notcontains $_ })
    if ($kept.Count -ne $segments.Count) {
        [Environment]::SetEnvironmentVariable("PATH", ($kept -join ';'), "User")
        foreach ($entry in ($segments | Where-Object { $repoPathEntries -contains $_ })) {
            Write-Host "Removed $entry from user PATH" -ForegroundColor Green
        }
    }
}

# Dotfiles hook lines install.ps1 added to the 5.1 and 7 host profiles.
# Only those two lines are removed; anything else in the profile stays.
$docs = [Environment]::GetFolderPath("MyDocuments")
foreach ($hostProfile in @(
        (Join-Path $docs "WindowsPowerShell\Microsoft.PowerShell_profile.ps1"),
        (Join-Path $docs "PowerShell\Microsoft.PowerShell_profile.ps1"))) {
    if (-not (Test-Path $hostProfile)) { continue }
    $lines = @(Get-Content $hostProfile)
    $kept = @($lines | Where-Object {
        $_ -ne "# Dotfiles profile (PATH, starship, zoxide, dots functions)" -and
        $_ -notmatch '\.config\\powershell\\profile\.ps1'
    })
    if ($kept.Count -ne $lines.Count) {
        Set-Content -Path $hostProfile -Value $kept
        Write-Host "Removed dotfiles hook from $hostProfile" -ForegroundColor Green
    }
}

# Drop ~\.local\bin and ~\.local\opt only if nothing else lives there
foreach ($dir in @($binDir, $optDir)) {
    if ((Test-Path $dir) -and -not (Get-ChildItem $dir -Force -ErrorAction SilentlyContinue)) {
        Remove-Item $dir -Force
        Write-Host "Removed empty $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host "  Removed: $removed paths"
if ($failed -gt 0) {
    Write-Host "  Failed: $failed paths" -ForegroundColor Red
}
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Additional cleanup hints
Write-Host "Additional manual cleanup:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Windows Terminal, if winget installed it (Windows 11 ships it built in):"
Write-Host "   winget uninstall Microsoft.WindowsTerminal"
Write-Host ""
Write-Host "2. Uninstall Scoop packages (or all of Scoop):"
Write-Host "   scoop uninstall chezmoi   # or: scoop uninstall scoop (removes everything)"
Write-Host "   winget uninstall twpayne.chezmoi   # if installed via winget"
Write-Host "   winget uninstall Git.Git           # if installed via winget"
Write-Host ""
Write-Host "3. Claude Code login/history was kept in ~\.claude;"
Write-Host "   delete that directory manually if this machine should keep nothing."
Write-Host ""
