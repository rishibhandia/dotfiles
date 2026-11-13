# PowerShell from Bash on Windows: $_ Mangling and desktop.ini

**Extracted:** 2026-05-10
**Context:** Windows lab machine where Claude Code uses bash as the
default shell but most useful operations (Get-ChildItem with filters,
Rename-Item, structured output) require PowerShell.

## Problem

Running `powershell -Command "..."` from bash, the bash shell strips
or rewrites `$_` (the PowerShell pipeline variable) before PowerShell
sees it. Symptoms:

```
extglob.Name : The term 'extglob.Name' is not recognized as the name
of a cmdlet, function, script file, or operable program.
```

`$_` becomes `extglob` (a leftover shell builtin name), so any
`ForEach-Object { $_.Name }` or `Where-Object { $_.LastWriteTime ... }`
inline expression fails. Other PowerShell variables (`$base`, `$path`)
get stripped to empty strings, producing follow-on parser errors like
`Missing variable name` or `You must provide a value expression
following the '+' operator`.

## Solution

**Write the PowerShell logic to a `.ps1` file and invoke it.** Don't
inline pipeline expressions through `bash → powershell -Command`.

```powershell
# _list_recent.ps1
Get-ChildItem 'C:\path\to\dir' -Filter '*.txt' -File |
    Where-Object { $_.LastWriteTime -ge (Get-Date '2026-05-10') } |
    Sort-Object LastWriteTime |
    ForEach-Object { Write-Host ($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm') + '  ' + $_.Name) }
```

```bash
powershell -Command "& 'C:\path\to\_list_recent.ps1'; Remove-Item 'C:\path\to\_list_recent.ps1'"
```

The `& 'path'` invocation respects the system execution policy —
**do NOT** use `-ExecutionPolicy Bypass`, which Claude Code's
permission system refuses as a "weaken sandbox" action.

For one-off invocations without `$_` (string paths, single cmdlets),
inline `powershell -Command` is still fine.

## desktop.ini blocks empty-directory removal

Windows-managed directories (especially `Sample_Images/`, themed
folders) silently contain a hidden `desktop.ini`. After moving all
visible files out, the directory looks empty (`Get-ChildItem` shows
nothing) but `Remove-Item` fails with `PermissionDenied`.

```powershell
# Force-list including hidden, then clear, then remove
Get-ChildItem $dir -Force | Remove-Item -Force
Remove-Item $dir -Force -Recurse
```

Also: Windows Explorer / the search indexer briefly hold handles after
files move, producing transient "Cannot remove item" errors that
disappear on a second attempt. Wrap dir removal in `try` + retry, or
just accept that one extra `Remove-Item` call may be needed.

## When to Use

- Any bash session on Windows that needs to filter files by metadata
  (date, name pattern, attributes)
- Bulk file renames / moves / inventories from MATLAB project sessions
- After scientific data hygiene operations (renaming "_BAD" files,
  combining sample-image folders) that leave near-empty directories
