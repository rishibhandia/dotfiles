from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


REPO = Path(__file__).resolve().parents[2]
PARITY = REPO / "ai-parity/scripts/ai_parity.py"


def intended_target(source: str) -> PurePosixPath:
    path = PurePosixPath(source)
    roots = {"dot_codex": ".codex", "dot_agents": ".agents", "dot_claude": ".claude"}
    if path.parts[0] not in roots:
        raise AssertionError(f"unexpected parity source root: {source}")
    parts = [roots[path.parts[0]]]
    for part in path.parts[1:]:
        parts.append(part.removeprefix("literal_") if part.startswith("literal_") else part)
    return PurePosixPath(*parts)


class IsolatedChezmoiDeploymentTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("chezmoi"), "chezmoi is not installed")
    def test_generated_parity_sources_deploy_only_to_temporary_home(self) -> None:
        verified = subprocess.run(
            [sys.executable, str(PARITY), "verify"],
            cwd=REPO, text=True, capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(0, verified.returncode, verified.stdout + verified.stderr)
        state = json.loads((REPO / "ai-parity/generated-state.json").read_text())
        sources = sorted(state["outputs"])
        self.assertTrue(sources)

        with tempfile.TemporaryDirectory(prefix="ai-parity-chezmoi-") as temporary:
            sandbox = Path(temporary)
            destination = sandbox / "home"
            destination.mkdir()
            config = sandbox / "chezmoi.toml"
            config.write_text("", encoding="utf-8")
            base = [
                "chezmoi", "--source", str(REPO), "--destination", str(destination),
                "--config", str(config), "--config-format", "toml",
                "--cache", str(sandbox / "cache"),
                "--persistent-state", str(sandbox / "state.boltdb"),
                "--override-data", json.dumps({
                    "personal": True, "portable": True, "hostname": "ai-parity-test",
                }),
                "--no-tty", "--refresh-externals=never",
            ]
            environment = {
                **os.environ, "HOME": str(destination), "USERPROFILE": str(destination),
                "XDG_CACHE_HOME": str(sandbox / "xdg-cache"),
                "XDG_CONFIG_HOME": str(sandbox / "xdg-config"),
                "XDG_STATE_HOME": str(sandbox / "xdg-state"),
            }

            # .chezmoiignore gates some parity outputs by OS/personal (e.g.
            # keynote is darwin+personal only), so keep only sources chezmoi
            # actually manages on this platform.
            managed = subprocess.run(
                [*base, "managed", "--include=files"], cwd=REPO, text=True,
                capture_output=True, env=environment,
            )
            self.assertEqual(0, managed.returncode, managed.stdout + managed.stderr)
            managed_targets = {line for line in managed.stdout.splitlines() if line}
            sources = [
                source for source in sources
                if intended_target(source).as_posix() in managed_targets
            ]
            self.assertTrue(sources)

            target_paths = subprocess.run(
                [*base, "target-path", *sources], cwd=REPO, text=True, capture_output=True,
                env=environment,
            )
            self.assertEqual(0, target_paths.returncode, target_paths.stdout + target_paths.stderr)
            actual_targets = [Path(line) for line in target_paths.stdout.splitlines() if line]
            expected_targets = [destination / intended_target(source) for source in sources]
            self.assertEqual(expected_targets, actual_targets)
            self.assertEqual(len(actual_targets), len({str(path).casefold() for path in actual_targets}))
            for target in actual_targets:
                self.assertTrue(target.is_relative_to(destination))

            apply_command = [
                *base, "apply", "--source-path", "--parent-dirs", "--force",
                "--exclude=scripts,externals", *sources,
            ]
            first = subprocess.run(apply_command, cwd=REPO, text=True, capture_output=True, env=environment)
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)

            expected_files = set()
            first_fingerprint = hashlib.sha256()
            for source, target in zip(sources, actual_targets, strict=True):
                expected_files.add(target.relative_to(destination).as_posix())
                self.assertTrue(target.is_file() and not target.is_symlink(), target)
                self.assertEqual((REPO / source).read_bytes(), target.read_bytes(), source)
                if os.name != "nt":
                    self.assertEqual(0o644, stat.S_IMODE(target.stat().st_mode), source)
                first_fingerprint.update(target.relative_to(destination).as_posix().encode())
                first_fingerprint.update(target.read_bytes())

            deployed_files = {
                path.relative_to(destination).as_posix()
                for path in destination.rglob("*") if path.is_file() or path.is_symlink()
            }
            self.assertEqual(expected_files, deployed_files)

            verify = subprocess.run(
                [*base, "verify", "--source-path", "--exclude=scripts,externals", *sources],
                cwd=REPO, text=True, capture_output=True, env=environment,
            )
            self.assertEqual(0, verify.returncode, verify.stdout + verify.stderr)
            second = subprocess.run(apply_command, cwd=REPO, text=True, capture_output=True, env=environment)
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)
            second_fingerprint = hashlib.sha256()
            for target in actual_targets:
                second_fingerprint.update(target.relative_to(destination).as_posix().encode())
                second_fingerprint.update(target.read_bytes())
            self.assertEqual(first_fingerprint.digest(), second_fingerprint.digest())

    @unittest.skipUnless(shutil.which("chezmoi"), "chezmoi is not installed")
    def test_runtime_state_is_ignored_even_without_parity_verify(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ai-parity-runtime-ignore-") as temporary:
            sandbox = Path(temporary)
            source = sandbox / "source"
            destination = sandbox / "home"
            source.mkdir()
            destination.mkdir()
            shutil.copy2(REPO / ".chezmoiignore", source / ".chezmoiignore")
            runtime_sources = (
                "dot_codex/auth.json", "dot_codex/credentials.json",
                "dot_codex/identity.json", "dot_codex/installation_id",
                "dot_codex/memories_1.sqlite", "dot_codex/history.jsonl",
                "dot_codex/models_cache.json", "dot_codex/dot_personality_migration",
                "dot_codex/sessions/session.json", "dot_codex/logs/current.log",
                "dot_codex/shell_snapshots/snapshot.sh",
                "dot_codex/skills/dot_system/SKILL.md",
                "dot_codex/config.toml", "dot_codex/packages/pkg.json",
                "dot_codex/plugins/plugin.json", "dot_codex/dot_tmp/scratch.json",
                "dot_agents/skills/dot_system/SKILL.md",
            )
            for relative in runtime_sources:
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("must not deploy", encoding="utf-8")
            config = sandbox / "chezmoi.toml"
            config.write_text("", encoding="utf-8")
            command = [
                "chezmoi", "--source", str(source), "--destination", str(destination),
                "--config", str(config), "--config-format", "toml",
                "--cache", str(sandbox / "cache"),
                "--persistent-state", str(sandbox / "state.boltdb"),
                "--override-data", json.dumps({
                    "personal": False, "portable": True, "hostname": "ai-parity-test",
                }),
                "--no-tty", "--refresh-externals=never", "apply", "--force",
                "--exclude=scripts,externals",
            ]
            applied = subprocess.run(command, text=True, capture_output=True, cwd=source)
            self.assertEqual(0, applied.returncode, applied.stdout + applied.stderr)
            deployed = [path for path in destination.rglob("*") if path.is_file() or path.is_symlink()]
            self.assertEqual([], deployed)


if __name__ == "__main__":
    unittest.main()
