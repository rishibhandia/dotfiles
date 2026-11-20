"""Antigravity PreToolUse hook: block arbitrary .md/.txt file creation.

Mirrors the Claude Code Write guardrail in dot_claude/create_settings.json.tmpl,
while allowing Antigravity's own artifact directory (artifactDirectoryPath /
.gemini/antigravity*/brain/), skills/, memory/, rules/, and standard doc names.
"""

from __future__ import annotations

import json
import os
import re
import sys

ALLOWED_NAMES = re.compile(
    r"^(README|CLAUDE|AGENTS|GEMINI|CONTRIBUTING|SKILL|MEMORY)\.(md|txt)$",
    re.IGNORECASE,
)
ALLOWED_DIR_SEGMENTS = {"skills", "memory", "rules"}
BRAIN_MARKER = re.compile(
    r"[/\\]\.gemini[/\\]antigravity(?:-cli|-ide)?[/\\]brain[/\\]",
    re.IGNORECASE,
)


def emit(decision: str, reason: str | None = None) -> None:
    payload: dict[str, str] = {"decision": decision}
    if reason:
        payload["reason"] = reason
    sys.stdout.write(json.dumps(payload) + "\n")


def is_under_dir(path: str, directory: str) -> bool:
    if not directory:
        return False
    try:
        target = os.path.abspath(os.path.expanduser(path))
        base = os.path.abspath(os.path.expanduser(directory))
        return os.path.commonpath([target, base]) == base
    except ValueError:
        return False


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        emit("allow")
        return 0

    tool_call = data.get("toolCall") or {}
    args = tool_call.get("args") or {}
    file_path = args.get("Path") or args.get("TargetFile") or ""
    if not isinstance(file_path, str) or not file_path:
        emit("allow")
        return 0

    lower = file_path.lower()
    if not lower.endswith((".md", ".txt")):
        emit("allow")
        return 0

    basename = os.path.basename(file_path)
    if ALLOWED_NAMES.match(basename):
        emit("allow")
        return 0

    artifact_dir = data.get("artifactDirectoryPath") or ""
    if isinstance(artifact_dir, str) and is_under_dir(file_path, artifact_dir):
        emit("allow")
        return 0

    if BRAIN_MARKER.search(file_path):
        emit("allow")
        return 0

    parts = {p.lower() for p in re.split(r"[/\\]+", file_path) if p}
    if parts & ALLOWED_DIR_SEGMENTS:
        emit("allow")
        return 0

    emit(
        "deny",
        f"[Hook] BLOCKED: arbitrary documentation file: {file_path}. "
        "Use README.md, CLAUDE.md, AGENTS.md, GEMINI.md, or CONTRIBUTING.md instead.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
