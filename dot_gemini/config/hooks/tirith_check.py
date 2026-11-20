"""Antigravity PreToolUse hook: vet run_command calls with tirith.

Mirrors the Claude Code tirith PreToolUse Bash guardrail.
- If tirith is not installed (e.g. portable Windows), passes through.
- Exit 0 (action=allow) -> decision: allow
- Exit 2 (action=warn)  -> decision: ask (surface warning for confirmation)
- Exit 1 (action=block) or unexpected error -> decision: deny (fail-closed,
  unless TIRITH_FAIL_OPEN=1).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys


def emit(decision: str, reason: str | None = None) -> None:
    payload: dict[str, str] = {"decision": decision}
    if reason:
        payload["reason"] = reason
    sys.stdout.write(json.dumps(payload) + "\n")


def summarize_findings(stdout: str, stderr: str) -> str:
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        text = (stdout or stderr).strip()
        return text[:400] if text else "command flagged by tirith"

    findings = parsed.get("findings") or []
    if not findings:
        action = parsed.get("action") or "flagged"
        return f"tirith verdict: {action}"

    parts = []
    for item in findings[:3]:
        rule = item.get("rule_id") or "rule"
        title = item.get("title") or item.get("description") or "security finding"
        parts.append(f"{rule}: {title}")
    return "; ".join(parts)


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        emit("allow")
        return 0

    tool_call = data.get("toolCall") or {}
    args = tool_call.get("args") or {}
    command_line = args.get("CommandLine") or args.get("command") or ""
    if not isinstance(command_line, str) or not command_line.strip():
        emit("allow")
        return 0

    tirith_bin = shutil.which("tirith")
    if not tirith_bin:
        emit("allow")
        return 0

    shell_type = "powershell" if os.name == "nt" else "posix"
    fail_open = os.environ.get("TIRITH_FAIL_OPEN") == "1"

    try:
        proc = subprocess.run(
            [
                tirith_bin,
                "check",
                "--non-interactive",
                "--offline",
                "--shell",
                shell_type,
                "--format",
                "json",
                "--",
                command_line,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        if fail_open:
            emit("allow")
        else:
            emit("deny", f"[Hook] tirith check failed (fail-closed): {exc}")
        return 0

    if proc.returncode == 0:
        emit("allow")
        return 0

    summary = summarize_findings(proc.stdout, proc.stderr)
    if proc.returncode == 2:
        emit("ask", f"[Hook] tirith warning: {summary}")
        return 0

    if fail_open and proc.returncode not in (1, 4):
        emit("allow")
        return 0

    emit("deny", f"[Hook] tirith blocked command: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
