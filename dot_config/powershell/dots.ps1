# Dotfiles management functions for PowerShell
# Source this file in your PowerShell profile:
#   . "$env:USERPROFILE\.config\powershell\dots.ps1"

function dots {
    <#
    .SYNOPSIS
    Dotfiles management commands

    .DESCRIPTION
    A unified interface for managing dotfiles with chezmoi

    .PARAMETER Command
    The command to run: apply, diff, status, update, edit, add, cd, git, doctor, data, re-init, test, help

    .PARAMETER Args
    Additional arguments to pass to the command

    .EXAMPLE
    dots apply
    Apply all dotfiles

    .EXAMPLE
    dots diff
    Show what would change

    .EXAMPLE
    dots git status
    Check git status of dotfiles repo
    #>

    param(
        [Parameter(Position = 0)]
        [string]$Command,

        [Parameter(Position = 1, ValueFromRemainingArguments)]
        [string[]]$Args
    )

    $ChezmoiDir = Join-Path $env:USERPROFILE ".local\share\chezmoi"

    # Show help if no command
    if (-not $Command) {
        Write-Host @"
dots - Dotfiles management commands

Usage: dots <command> [args]

Commands:
  apply [-v]     Apply dotfiles to home directory (-v for verbose)
  diff           Show what would change
  status         Show status of managed files
  update         Pull latest changes from remote and apply
  edit [file]    Edit a dotfile (opens source in `$EDITOR)
  add <file>     Add a file to be managed by chezmoi
  cd             Change to dotfiles source directory
  git <args>     Run git commands in dotfiles directory
  doctor         Check chezmoi configuration for issues
  data           Show template data (name, email, OS, etc.)
  re-init        Re-run chezmoi init (regenerate config)
  test           Run dotfiles setup tests
  help           Show this help message

Examples:
  dots apply           # Apply all dotfiles
  dots apply -v        # Apply with verbose output
  dots diff            # Preview changes before applying
  dots edit ~/.zshrc   # Edit zshrc source file
  dots add ~/.somerc   # Start managing a new file
  dots git status      # Check git status of dotfiles repo
  dots git push        # Push dotfiles changes to remote
"@
        return
    }

    switch ($Command) {
        "apply" {
            if ($Args -contains "-v" -or $Args -contains "--verbose") {
                & chezmoi apply --verbose
            } else {
                & chezmoi apply @Args
            }
        }
        "diff" {
            & chezmoi diff @Args
        }
        "status" {
            & chezmoi status @Args
        }
        "update" {
            & chezmoi update @Args
        }
        "edit" {
            if (-not $Args) {
                # No file specified, open the source directory
                $editor = if ($env:EDITOR) { $env:EDITOR } else { "notepad" }
                & $editor $ChezmoiDir
            } else {
                & chezmoi edit @Args
            }
        }
        "add" {
            if (-not $Args) {
                Write-Host "Usage: dots add <file>" -ForegroundColor Yellow
                return
            }
            & chezmoi add @Args
        }
        "cd" {
            Set-Location $ChezmoiDir
        }
        "git" {
            & git -C $ChezmoiDir @Args
        }
        "doctor" {
            & chezmoi doctor
        }
        "data" {
            & chezmoi data
        }
        { $_ -in "re-init", "reinit" } {
            & chezmoi init
        }
        "test" {
            $testScript = Join-Path $ChezmoiDir "scripts\test.ps1"
            if (Test-Path $testScript) {
                & $testScript
            } else {
                Write-Host "No test script found at $testScript" -ForegroundColor Yellow
            }
        }
        { $_ -in "help", "--help", "-h" } {
            dots  # Call without args to show help
        }
        default {
            Write-Host "Unknown command: $Command" -ForegroundColor Red
            Write-Host "Run 'dots help' for usage information"
        }
    }
}

# Tab completion for dots command
Register-ArgumentCompleter -CommandName dots -ScriptBlock {
    param($commandName, $wordToComplete, $cursorPosition)

    $commands = @(
        @{ Name = 'apply';    Description = 'Apply dotfiles to home directory' }
        @{ Name = 'diff';     Description = 'Show what would change' }
        @{ Name = 'status';   Description = 'Show status of managed files' }
        @{ Name = 'update';   Description = 'Pull latest and apply' }
        @{ Name = 'edit';     Description = 'Edit a dotfile' }
        @{ Name = 'add';      Description = 'Add a file to chezmoi' }
        @{ Name = 'cd';       Description = 'Change to dotfiles directory' }
        @{ Name = 'git';      Description = 'Run git commands in dotfiles repo' }
        @{ Name = 'doctor';   Description = 'Check chezmoi configuration' }
        @{ Name = 'data';     Description = 'Show template data' }
        @{ Name = 're-init';  Description = 'Re-run chezmoi init' }
        @{ Name = 'test';     Description = 'Run setup tests' }
        @{ Name = 'help';     Description = 'Show help message' }
    )

    $commands | Where-Object { $_.Name -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new(
            $_.Name,
            $_.Name,
            'ParameterValue',
            $_.Description
        )
    }
}

# Aliases for common operations
Set-Alias -Name cz -Value dots -Description "Shorthand for dots command"
