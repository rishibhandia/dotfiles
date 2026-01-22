# Dotfiles Uninstaller for Windows
# Removes all chezmoi-managed files for clean departure from work machines
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

# Paths to remove
$ToRemove = @(
    (Join-Path $env:USERPROFILE ".local\bin"),           # Portable binaries
    (Join-Path $env:USERPROFILE ".local\share\chezmoi"), # Chezmoi source
    (Join-Path $env:USERPROFILE ".config\chezmoi"),      # Chezmoi config
    (Join-Path $env:USERPROFILE ".config\powershell"),   # PowerShell config
    (Join-Path $env:USERPROFILE ".config\starship.toml"),# Starship config
    (Join-Path $env:USERPROFILE ".config\git"),          # Git config
    (Join-Path $env:USERPROFILE ".config\nvim"),         # Neovim config
    (Join-Path $env:USERPROFILE ".gitconfig"),           # Git config (legacy location)
    (Join-Path $env:USERPROFILE ".claude"),              # Claude Code config/data
    (Join-Path $env:LOCALAPPDATA "Claude"),              # Claude Code app data
    (Join-Path $env:APPDATA "Claude"),                   # Claude Code roaming data
    (Join-Path $env:USERPROFILE ".cargo"),               # Rust/Cargo (if installed by script)
    (Join-Path $env:USERPROFILE ".rustup")               # Rustup (if installed by script)
)

# Check what exists
$ExistingPaths = $ToRemove | Where-Object { Test-Path $_ }

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
Write-Host "1. Remove dotfiles profile from PowerShell profile:"
Write-Host "   notepad `$PROFILE"
Write-Host "   # Delete the line that sources profile.ps1"
Write-Host ""
Write-Host "2. Uninstall chezmoi:"
Write-Host "   - Scoop:  scoop uninstall chezmoi"
Write-Host "   - winget: winget uninstall twpayne.chezmoi"
Write-Host ""
Write-Host "3. Uninstall Claude Code (if npm installed):"
Write-Host "   npm uninstall -g @anthropic-ai/claude-code"
Write-Host ""
