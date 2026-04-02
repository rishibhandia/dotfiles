#!/usr/bin/env pwsh
# Claude Code statusline for Windows
# Format: user@host dir [git_branch ●●●] [ctx:N%] [Model] [rl:N%]

$data = $Input | Out-String | ConvertFrom-Json

$ESC     = [char]27
$Green   = "$ESC[32m"
$Yellow  = "$ESC[33m"
$Red     = "$ESC[31m"
$Blue    = "$ESC[34m"
$Cyan    = "$ESC[36m"
$White   = "$ESC[37m"
$Reset   = "$ESC[0m"

$cwd = $data.workspace.current_dir ?? $data.cwd

# --- Context usage ---
$contextInfo = ""
$usage = $data.context_window.current_usage
$size  = $data.context_window.context_window_size
if ($null -ne $usage -and $null -ne $size -and $size -gt 0) {
  $current = ($usage.input_tokens ?? 0) + ($usage.cache_creation_input_tokens ?? 0) + ($usage.cache_read_input_tokens ?? 0)
  $pct = [math]::Floor($current * 100 / $size)
  $color = if ($pct -lt 50) { $Green } elseif ($pct -lt 80) { $Yellow } else { $Red }
  $contextInfo = " $color[ctx:$pct%]"
}

# --- Model ---
$modelInfo = ""
$model = $data.model.display_name ?? $data.model.id
if (-not [string]::IsNullOrEmpty($model)) {
  $modelInfo = " $Cyan[$model]"
}

# --- 5-hour rate limit (Max/Pro) ---
$rlInfo = ""
$rlPct = $data.rate_limits.five_hour.used_percentage
if ($null -ne $rlPct) {
  $rlInt = [math]::Round($rlPct)
  $rlColor = if ($rlInt -lt 50) { $Green } elseif ($rlInt -lt 80) { $Yellow } else { $Red }
  $rlInfo = " $rlColor[rl:$rlInt%]"
}

# --- User / host / dir ---
$username   = $env:USERNAME
$hostname   = $env:COMPUTERNAME
$dirDisplay = Split-Path -Leaf $cwd

# --- Git info ---
$gitInfo = ""
Push-Location $cwd
try {
  git rev-parse --git-dir 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $branch = git branch --show-current 2>$null
    if ([string]::IsNullOrEmpty($branch)) { $branch = "detached" }

    $gitStatus = git --no-optional-locks status --porcelain 2>$null
    $staged = ""; $unstaged = ""; $untracked = ""
    foreach ($line in ($gitStatus -split "`n")) {
      if ($line -match '^[MADRCU]') { $staged   = "$Green●" }
      if ($line -match '^.[MD]')    { $unstaged  = "$Yellow●" }
      if ($line -match '^\?\?')     { $untracked = "$Red●" }
    }
    $gitInfo = " [$Green$branch$staged$unstaged$untracked$Blue]"
  }
} finally {
  Pop-Location
}

Write-Host -NoNewline "$White$username@$hostname $dirDisplay$gitInfo$contextInfo$modelInfo$rlInfo$Reset"
