#!/usr/bin/env pwsh
# Claude Code statusline script for Windows
# Shows: user@host dir [git_branch status_dots] [context_pct%]
# PowerShell equivalent of statusline.sh

# Read stdin JSON input
$input = $Input | Out-String | ConvertFrom-Json

# Extract current working directory
$cwd = $input.workspace.current_dir

# ANSI escape codes for colors
$ESC = [char]27
$Green = "$ESC[32m"
$Yellow = "$ESC[33m"
$Red = "$ESC[31m"
$Blue = "$ESC[34m"
$White = "$ESC[37m"
$Reset = "$ESC[0m"

# Calculate context usage percentage
$contextInfo = ""
$usage = $input.context_window.current_usage
if ($null -ne $usage) {
    $current = $usage.input_tokens + $usage.cache_creation_input_tokens + $usage.cache_read_input_tokens
    $size = $input.context_window.context_window_size

    if ($null -ne $current -and $null -ne $size -and $size -gt 0) {
        $pct = [math]::Floor($current * 100 / $size)

        # Color code based on usage: green (<50%), yellow (50-80%), red (>80%)
        if ($pct -lt 50) {
            $color = $Green
        } elseif ($pct -lt 80) {
            $color = $Yellow
        } else {
            $color = $Red
        }

        $contextInfo = " $color[$pct%]"
    }
}

# Get username and hostname
$username = $env:USERNAME
$hostname = $env:COMPUTERNAME

# Get directory name (basename of current path)
$dirDisplay = Split-Path -Leaf $cwd

# Get git information if in a git repository
$gitInfo = ""
Push-Location $cwd
try {
    $gitDir = git rev-parse --git-dir 2>$null
    if ($LASTEXITCODE -eq 0) {
        # Get branch name
        $branch = git branch --show-current 2>$null
        if ([string]::IsNullOrEmpty($branch)) {
            $branch = "detached"
        }

        # Check for changes
        $gitStatus = git --no-optional-locks status --porcelain 2>$null

        # Determine status indicators with colors
        $staged = ""
        $unstaged = ""
        $untracked = ""

        if ($gitStatus) {
            foreach ($line in $gitStatus -split "`n") {
                if ($line -match '^[MADRCU]') {
                    $staged = "$Green●"
                }
                if ($line -match '^.[MD]') {
                    $unstaged = "$Yellow●"
                }
                if ($line -match '^\?\?') {
                    $untracked = "$Red●"
                }
            }
        }

        # Build git info string with colors
        $gitInfo = " [$Green$branch$staged$unstaged$untracked$Blue]"
    }
} finally {
    Pop-Location
}

# Build the status line
# Format: white(username@hostname dir) git_info context_info
Write-Host -NoNewline "$White$username@$hostname $dirDisplay$gitInfo$contextInfo$Reset"
