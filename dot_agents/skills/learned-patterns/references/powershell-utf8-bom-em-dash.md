---
name: PowerShell 5.1 mangles UTF-8 without BOM
description: Em-dashes (and other multi-byte chars) in .ps1 files corrupt parsing under Windows PowerShell 5.1 when the file has no UTF-8 BOM. Stick to ASCII in PowerShell templates.
type: feedback
---

Use ASCII only in `.ps1` and `.ps1.tmpl` files -- no em-dashes (`--`), curly quotes, or other non-ASCII characters. Use `--` or `-` instead of `--`.

**Why:** chezmoi writes rendered scripts as UTF-8 *without* a BOM. When `chezmoi apply` on Windows shells out to `powershell.exe` (Windows PowerShell 5.1), it decodes the file using the ANSI codepage (Windows-1252), not UTF-8. The em-dash byte sequence `E2 80 94` becomes `a-tilde, euro, right-double-quote (0x94)`. That trailing `"` closes any active double-quoted string mid-statement, cascading "Missing closing '}'" parse errors through the rest of the file.

PowerShell 7+ (`pwsh.exe`) defaults to UTF-8, so the bug only triggers under 5.1 -- which is exactly what chezmoi uses on stock Windows.

**How to apply:**
- Before committing any `*.ps1.tmpl` change, grep for non-ASCII: `Grep '[^\x00-\x7F]' --glob='*.ps1.tmpl'`
- If em-dashes are unavoidable (e.g. user-facing string), test parse under 5.1 explicitly: `powershell.exe -NoProfile -Command "[scriptblock]::Create((Get-Content rendered.ps1 -Raw))"`
- The same hazard applies to other multi-byte UTF-8 chars: smart quotes, ellipsis, bullets, accented letters.
- Comments are NOT safe either: the byte sequence breaks even inside a `#` comment if the decoded `"` lands inside or before a string elsewhere -- avoid them everywhere.
