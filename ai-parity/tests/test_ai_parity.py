from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class ParityIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(
            REPO / "ai-parity", self.root / "ai-parity",
            ignore=shutil.ignore_patterns(".transactions", ".proposals", ".sync-lock", ".sync-journal.json", "__pycache__"),
        )
        shutil.copytree(REPO / "dot_claude", self.root / "dot_claude")
        self.script = self.root / "ai-parity/scripts/ai_parity.py"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_parity(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, str(self.script), "--snapshot", *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        return result

    def tree_fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                relative = path.relative_to(self.root).as_posix()
                if relative.startswith(("ai-parity/.transactions/", "ai-parity/.proposals/")):
                    continue
                digest.update(relative.encode())
                digest.update(path.read_bytes())
        return digest.hexdigest()

    def interrupt_sync(self, fail_after: int = 1) -> tuple[str, dict]:
        self.run_parity("sync", "--write")
        contract = self.root / "ai-parity/contracts/AGENTS.md"
        contract.write_text(contract.read_text() + "\nInterrupted transaction fixture.\n")
        old = os.environ.get("AI_PARITY_FAIL_AFTER")
        os.environ["AI_PARITY_FAIL_AFTER"] = str(fail_after)
        try:
            self.run_parity("sync", "--write", expected=2)
        finally:
            if old is None:
                os.environ.pop("AI_PARITY_FAIL_AFTER", None)
            else:
                os.environ["AI_PARITY_FAIL_AFTER"] = old
        journal = json.loads((self.root / "ai-parity/.sync-journal.json").read_text())
        return journal["transaction_id"], journal

    def test_dry_run_does_not_write(self) -> None:
        before = self.tree_fingerprint()
        self.run_parity("sync", expected=1)
        self.assertEqual(before, self.tree_fingerprint())

    def test_sync_is_idempotent_and_detects_manual_edits(self) -> None:
        self.run_parity("sync", "--write")
        first = self.tree_fingerprint()
        self.run_parity("sync", "--write")
        self.assertEqual(first, self.tree_fingerprint())
        generated = self.root / "dot_codex/AGENTS.md"
        generated.write_text(generated.read_text() + "\nmanual edit\n")
        result = self.run_parity("sync", "--write", expected=2)
        self.assertIn("manual edit", result.stderr)

    def test_unclassified_skill_fails_closed(self) -> None:
        (self.root / "dot_claude/skills/new-skill").mkdir()
        result = self.run_parity("status", expected=2)
        self.assertIn("inventory mismatch", result.stderr)

    def test_explicit_transaction_rollback_and_finish(self) -> None:
        transaction_id, _ = self.interrupt_sync()
        self.run_parity("repair", transaction_id, "--rollback")
        self.run_parity("verify", expected=1)
        transaction_id, _ = self.interrupt_sync()
        self.run_parity("repair", transaction_id, "--finish")
        self.run_parity("verify")

    def test_unknown_owned_file_fails_closed(self) -> None:
        self.run_parity("sync", "--write")
        runtime_file = self.root / "dot_codex/installation_id"
        runtime_file.write_text("must-not-deploy")
        result = self.run_parity("verify", expected=1)
        self.assertIn("unowned file", result.stdout)
        result = self.run_parity("sync", "--write", expected=2)
        self.assertIn("unowned files", result.stderr)
        self.assertTrue(runtime_file.exists())

    def test_state_cannot_authorize_deletion_outside_owned_roots(self) -> None:
        self.run_parity("sync", "--write")
        state_path = self.root / "ai-parity/generated-state.json"
        json_module = __import__("json")
        state = json_module.loads(state_path.read_text())
        protected = self.root / "dot_claude/CLAUDE.md"
        state["outputs"]["dot_claude/CLAUDE.md"] = {
            "sha256": hashlib.sha256(protected.read_bytes()).hexdigest()
        }
        state_path.write_text(json_module.dumps(state))
        result = self.run_parity("sync", "--write", expected=2)
        self.assertIn("generated-state", result.stderr)
        self.assertTrue(protected.exists())

    def test_foreign_lock_requires_exact_explicit_token(self) -> None:
        transaction_id, journal = self.interrupt_sync()
        token = "a" * 32
        (self.root / "ai-parity/.sync-lock").write_text(json.dumps({
            "schema_version": 2, "pid": 1, "host": "some-other-host", "token": token,
            "transaction_id": transaction_id, "operation": journal["operation"],
            "generation_id": journal["generation_id"],
            "transaction_digest": journal["transaction_digest"],
        }))
        result = self.run_parity("repair", transaction_id, "--rollback", expected=2)
        self.assertIn("--token", result.stderr)
        self.run_parity("repair", transaction_id, "--rollback", "--token", token)

    def test_third_state_blocks_repair(self) -> None:
        transaction_id, _ = self.interrupt_sync()
        generated = self.root / "dot_codex/AGENTS.md"
        generated.write_text(generated.read_text() + "\nthird state\n")
        result = self.run_parity("repair", transaction_id, "--rollback", expected=2)
        self.assertIn("third-state", result.stderr)
        self.assertIn("third state", generated.read_text())

    def test_injected_failures_recover_before_and_after_state_write(self) -> None:
        self.run_parity("sync", "--write")
        contract = self.root / "ai-parity/contracts/AGENTS.md"
        contract.write_text(contract.read_text() + "\nTransaction failure pilot.\n")
        for fail_after, action in ((1, "--rollback"), (2, "--finish")):
            old = os.environ.get("AI_PARITY_FAIL_AFTER")
            os.environ["AI_PARITY_FAIL_AFTER"] = str(fail_after)
            try:
                result = self.run_parity("sync", "--write", expected=2)
            finally:
                if old is None:
                    os.environ.pop("AI_PARITY_FAIL_AFTER", None)
                else:
                    os.environ["AI_PARITY_FAIL_AFTER"] = old
            self.assertIn("injected failure", result.stderr)
            journal = json.loads((self.root / "ai-parity/.sync-journal.json").read_text())
            self.run_parity("repair", journal["transaction_id"], action)
        self.run_parity("verify")

    def test_orphan_lock_requires_exact_token(self) -> None:
        lock = self.root / "ai-parity/.sync-lock"
        token = "b" * 32
        lock.write_text(json.dumps({
            "schema_version": 2, "pid": 1, "host": "foreign", "token": token,
            "transaction_id": "f" * 32, "operation": "sync", "generation_id": None,
            "transaction_digest": None,
        }))
        self.run_parity("unlock", "--orphan", "wrong", expected=2)
        self.assertTrue(lock.exists())
        self.run_parity("unlock", "--orphan", token)
        self.assertFalse(lock.exists())

    def test_malformed_lock_is_quarantined_not_deleted(self) -> None:
        lock = self.root / "ai-parity/.sync-lock"
        lock.write_text("not-json")
        self.run_parity("unlock", "--quarantine-malformed")
        self.assertFalse(lock.exists())
        quarantined = list((self.root / "ai-parity/.transactions/quarantine").glob("lock-*.json"))
        self.assertEqual(1, len(quarantined))
        self.assertEqual("not-json", quarantined[0].read_text())

    def test_direct_codex_edit_round_trips_through_proposal(self) -> None:
        self.run_parity("sync", "--write")
        codex = self.root / "dot_agents/skills/matlab/style-guide.md"
        codex.write_text(codex.read_text() + "\nCodex-originated pilot note.\n")
        result = self.run_parity("propose", "--from", "codex", "matlab", expected=1)
        proposal_id = result.stdout.split()[2].rstrip(".")
        self.run_parity("proposals", "accept", proposal_id)
        canonical = self.root / "ai-parity/shared/skills/matlab/style-guide.md"
        claude = self.root / "dot_claude/skills/matlab/style-guide.md"
        self.assertEqual(codex.read_bytes(), canonical.read_bytes())
        self.assertEqual(codex.read_bytes(), claude.read_bytes())
        self.run_parity("verify")

    def test_direct_claude_edit_round_trips_through_proposal(self) -> None:
        self.run_parity("sync", "--write")
        claude = self.root / "dot_claude/skills/matlab/plotting.md"
        claude.write_text(claude.read_text() + "\nClaude-originated pilot note.\n")
        result = self.run_parity("propose", "--from", "claude", "matlab", expected=1)
        proposal_id = result.stdout.split()[2].rstrip(".")
        self.run_parity("proposals", "accept", proposal_id)
        canonical = self.root / "ai-parity/shared/skills/matlab/plotting.md"
        codex = self.root / "dot_agents/skills/matlab/plotting.md"
        self.assertEqual(claude.read_bytes(), canonical.read_bytes())
        self.assertEqual(claude.read_bytes(), codex.read_bytes())

    def test_staged_generated_edit_creates_proposal_and_blocks(self) -> None:
        self.run_parity("sync", "--write")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Parity Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.root, check=True)
        generated = self.root / "dot_agents/skills/matlab/fft.md"
        generated.write_text(generated.read_text() + "\nstaged proposal\n")
        subprocess.run(["git", "add", str(generated)], cwd=self.root, check=True)
        result = self.run_parity("verify", "--staged", expected=2)
        self.assertIn("created staged import proposal", result.stderr)
        self.assertTrue(any((self.root / "ai-parity/.proposals").glob("*/proposal.json")))

    def test_nested_codex_interface_is_not_shared_reverse_drift(self) -> None:
        self.run_parity("sync", "--write")
        result = self.run_parity("propose", "--from", "codex", "scientific-figures")
        self.assertIn("No target changes", result.stdout)
        interface = self.root / "dot_agents/skills/scientific-figures/agents/openai.yaml"
        interface.write_text(interface.read_text() + "\n# manual metadata drift\n")
        result = self.run_parity("propose", "--from", "codex", "scientific-figures")
        self.assertIn("No target changes", result.stdout)
        result = self.run_parity("verify", expected=1)
        self.assertIn("output drift", result.stdout)

    def test_adapted_runner_edit_requires_review(self) -> None:
        self.run_parity("sync", "--write")
        runner = self.root / "dot_agents/skills/matlab-runner/SKILL.md"
        runner.write_text(runner.read_text() + "\nReview this semantic change.\n")
        result = self.run_parity("propose", "--from", "codex", "matlab-runner", expected=1)
        proposal_id = result.stdout.split()[2].rstrip(".")
        result = self.run_parity("proposals", "accept", proposal_id, expected=2)
        self.assertIn("requires adapter/canonical review", result.stderr)

    def test_memory_scans_create_local_proposals_without_syncing(self) -> None:
        claude_home = self.root / "fake-claude"
        memory = claude_home / "projects/project-one/memory"
        memory.mkdir(parents=True)
        (memory / "MEMORY.md").write_text("A reviewed candidate")
        old = os.environ.get("AI_PARITY_CLAUDE_HOME")
        os.environ["AI_PARITY_CLAUDE_HOME"] = str(claude_home)
        try:
            self.run_parity("memories", "scan", "--from", "claude", "--project", "project-one")
        finally:
            if old is None:
                os.environ.pop("AI_PARITY_CLAUDE_HOME", None)
            else:
                os.environ["AI_PARITY_CLAUDE_HOME"] = old
        proposals = list((self.root / "ai-parity/.proposals").glob("*/proposal.json"))
        self.assertEqual(1, len(proposals))
        self.assertEqual("memory", json.loads(proposals[0].read_text())["kind"])

        codex_home = self.root / "fake-codex"
        codex_home.mkdir()
        database = codex_home / "memories_1.sqlite"
        with contextlib.closing(sqlite3.connect(database)) as connection:
            connection.execute("CREATE TABLE stage1_outputs (thread_id TEXT, raw_memory TEXT, source_updated_at INTEGER)")
            connection.execute("INSERT INTO stage1_outputs VALUES ('thread-1', 'Codex candidate', 1)")
            connection.commit()
        old = os.environ.get("AI_PARITY_CODEX_HOME")
        os.environ["AI_PARITY_CODEX_HOME"] = str(codex_home)
        try:
            self.run_parity("memories", "scan", "--from", "codex")
        finally:
            if old is None:
                os.environ.pop("AI_PARITY_CODEX_HOME", None)
            else:
                os.environ["AI_PARITY_CODEX_HOME"] = old
        self.assertEqual(2, len(list((self.root / "ai-parity/.proposals").glob("*/proposal.json"))))

    def test_manifest_cannot_redefine_write_envelope_or_runtime_paths(self) -> None:
        manifest = self.root / "ai-parity/manifest.toml"
        original = manifest.read_text()
        manifest.write_text(original.replace(
            'owned_roots = ["dot_codex", "dot_agents"]',
            'owned_roots = ["dot_codex", "private_dot_ssh"]',
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("safety envelope", result.stderr)
        manifest.write_text(original.replace(
            'state_file = "ai-parity/generated-state.json"',
            'state_file = "dot_claude/CLAUDE.md"',
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("operational path", result.stderr)
        manifest.write_text(original.replace(
            'canonical = "ai-parity/shared/skills/matlab"',
            'canonical = "dot_claude"',
            1,
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("canonical source is outside", result.stderr)

    def test_chezmoi_mapping_and_adapter_roots_are_explicit(self) -> None:
        manifest = self.root / "ai-parity/manifest.toml"
        original = manifest.read_text()
        manifest.write_text(original.replace(
            '"scripts/literal_run_matlab.sh" = "scripts/run_matlab.sh"',
            '"scripts/literal_run_matlab.sh" = "scripts/wrong.sh"',
            1,
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("incorrect chezmoi mapping", result.stderr)
        manifest.write_text(original.replace(
            '"SKILL.md" = "ai-parity/adapters/skills/matlab-runner/SKILL.md"',
            '"SKILL.md" = "dot_claude/CLAUDE.md"',
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("outside adapter roots", result.stderr)

    def test_generated_state_alone_cannot_schedule_deletion(self) -> None:
        self.run_parity("sync", "--write")
        obsolete = self.root / "dot_codex/obsolete.txt"
        obsolete.write_text("keep until explicitly removed")
        state_path = self.root / "ai-parity/generated-state.json"
        state = json.loads(state_path.read_text())
        state["outputs"]["dot_codex/obsolete.txt"] = {
            "sha256": hashlib.sha256(obsolete.read_bytes()).hexdigest(),
        }
        state_path.write_text(json.dumps(state))
        result = self.run_parity("sync", "--write", expected=2)
        self.assertIn("unowned files", result.stderr)
        self.assertEqual("keep until explicitly removed", obsolete.read_text())

    def test_repair_rejects_mismatched_journal_and_tampered_transaction(self) -> None:
        transaction_id, journal = self.interrupt_sync()
        journal_path = self.root / "ai-parity/.sync-journal.json"
        journal["transaction_id"] = "f" * 32
        journal_path.write_text(json.dumps(journal))
        result = self.run_parity("repair", transaction_id, "--rollback", expected=2)
        self.assertIn("different transaction", result.stderr)
        self.assertTrue(journal_path.exists())

        journal["transaction_id"] = transaction_id
        journal_path.write_text(json.dumps(journal))
        transaction_path = self.root / f"ai-parity/.transactions/{transaction_id}/transaction.json"
        transaction = json.loads(transaction_path.read_text())
        transaction["entries"][0]["old"]["data"] = "AAAA"
        transaction_path.write_text(json.dumps(transaction))
        result = self.run_parity("repair", transaction_id, "--rollback", expected=2)
        self.assertIn("hash/data mismatch", result.stderr)
        self.assertTrue(journal_path.exists())

    def test_repair_refuses_live_lock_and_gc_retains_active_transaction(self) -> None:
        transaction_id, journal = self.interrupt_sync()
        lock = self.root / "ai-parity/.sync-lock"
        token = "c" * 32
        lock.write_text(json.dumps({
            "schema_version": 2, "pid": os.getpid(), "host": __import__("socket").gethostname(),
            "token": token, "transaction_id": transaction_id,
            "operation": journal["operation"], "generation_id": journal["generation_id"],
            "transaction_digest": journal["transaction_digest"],
        }))
        result = self.run_parity(
            "repair", transaction_id, "--rollback", "--token", token, expected=2,
        )
        self.assertIn("still alive", result.stderr)
        lock.unlink()
        result = self.run_parity("transaction-gc", expected=2)
        self.assertIn("recovery journal", result.stderr)
        self.assertTrue((self.root / f"ai-parity/.transactions/{transaction_id}/transaction.json").exists())

    def test_codex_runtime_destinations_are_forbidden(self) -> None:
        manifest = self.root / "ai-parity/manifest.toml"
        manifest.write_text(manifest.read_text().replace(
            'destination = "dot_codex/AGENTS.md"',
            'destination = "dot_codex/history.jsonl"',
            1,
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("runtime state", result.stderr)

    def test_closed_schemas_reject_unknown_and_future_fields(self) -> None:
        manifest = self.root / "ai-parity/manifest.toml"
        manifest.write_text(manifest.read_text() + "\nunexpected_policy_escape = true\n")
        result = self.run_parity("status", expected=2)
        self.assertIn("unknown fields", result.stderr)

        manifest.write_text((REPO / "ai-parity/manifest.toml").read_text())
        self.run_parity("sync", "--write")
        state_path = self.root / "ai-parity/generated-state.json"
        state = json.loads(state_path.read_text())
        state["unexpected"] = True
        state_path.write_text(json.dumps(state))
        result = self.run_parity("verify", expected=2)
        self.assertIn("unknown fields", result.stderr)

    def test_legacy_transaction_v2_can_recover_after_upgrade(self) -> None:
        transaction_id, journal = self.interrupt_sync()
        transaction_path = self.root / f"ai-parity/.transactions/{transaction_id}/transaction.json"
        transaction = json.loads(transaction_path.read_text())
        for key in ("format", "operation", "context", "transaction_digest"):
            transaction.pop(key)
        transaction["schema_version"] = 2
        transaction_path.write_text(json.dumps(transaction))
        legacy_journal = {
            "schema_version": 2, "transaction_id": transaction_id,
            "generation_id": journal["generation_id"], "status": "prepared",
        }
        (self.root / "ai-parity/.sync-journal.json").write_text(json.dumps(legacy_journal))
        self.run_parity("repair", transaction_id, "--rollback")
        recovered = json.loads(transaction_path.read_text())
        self.assertEqual(2, recovered["schema_version"])
        self.assertNotIn("format", recovered)

        transaction_id, journal = self.interrupt_sync()
        transaction_path = self.root / f"ai-parity/.transactions/{transaction_id}/transaction.json"
        transaction = json.loads(transaction_path.read_text())
        transaction.pop("format")
        transaction.pop("context")
        transaction["schema_version"] = 2
        material = {key: transaction[key] for key in (
            "schema_version", "transaction_id", "generation_id", "operation", "entries",
        )}
        transaction["transaction_digest"] = hashlib.sha256(
            (json.dumps(material, indent=2, sort_keys=True) + "\n").encode()
        ).hexdigest()
        transaction_path.write_text(json.dumps(transaction))
        hardened_journal = {
            "schema_version": 2, "transaction_id": transaction_id,
            "generation_id": journal["generation_id"], "operation": transaction["operation"],
            "transaction_digest": transaction["transaction_digest"], "status": "prepared",
        }
        (self.root / "ai-parity/.sync-journal.json").write_text(json.dumps(hardened_journal))
        self.run_parity("repair", transaction_id, "--finish")
        self.run_parity("verify")

    def test_schema_catalog_is_local_parseable_and_uniquely_identified(self) -> None:
        schemas = self.root / "ai-parity/schemas"
        identifiers = set()
        for path in sorted(schemas.glob("*.schema.json")):
            schema = json.loads(path.read_text())
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertNotIn(schema["$id"], identifiers)
            identifiers.add(schema["$id"])
            stack = [schema]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    if "$ref" in value:
                        self.assertTrue(value["$ref"].startswith("#/$defs/"))
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)
        self.assertGreaterEqual(len(identifiers), 12)

    def test_schema_changes_are_generation_inputs(self) -> None:
        self.run_parity("sync", "--write")
        schema = self.root / "ai-parity/schemas/journal-v3.schema.json"
        schema.write_text(schema.read_text() + "\n")
        result = self.run_parity("status", expected=1)
        self.assertIn("generated-state.json is stale", result.stdout)

    def test_proposal_acceptance_is_transactional_and_recoverable(self) -> None:
        self.run_parity("sync", "--write")
        canonical = self.root / "ai-parity/shared/skills/matlab/style-guide.md"
        canonical_before = canonical.read_bytes()
        origin = self.root / "dot_agents/skills/matlab/style-guide.md"
        origin.write_text(origin.read_text() + "\nTransactional proposal fixture.\n")
        result = self.run_parity("propose", "--from", "codex", "matlab", expected=1)
        proposal_id = result.stdout.split()[2].rstrip(".")

        os.environ["AI_PARITY_FAIL_AFTER"] = "1"
        try:
            self.run_parity("proposals", "accept", proposal_id, expected=2)
        finally:
            os.environ.pop("AI_PARITY_FAIL_AFTER", None)
        journal = json.loads((self.root / "ai-parity/.sync-journal.json").read_text())
        self.assertEqual("proposal-accept", journal["operation"])
        self.run_parity("repair", journal["transaction_id"], "--rollback")
        self.assertEqual(canonical_before, canonical.read_bytes())
        proposal_path = self.root / f"ai-parity/.proposals/{proposal_id}/proposal.json"
        self.assertEqual("applicable", json.loads(proposal_path.read_text())["status"])

        os.environ["AI_PARITY_FAIL_AFTER"] = "2"
        try:
            self.run_parity("proposals", "accept", proposal_id, expected=2)
        finally:
            os.environ.pop("AI_PARITY_FAIL_AFTER", None)
        journal = json.loads((self.root / "ai-parity/.sync-journal.json").read_text())
        self.run_parity("repair", journal["transaction_id"], "--finish")
        self.assertEqual(origin.read_bytes(), canonical.read_bytes())
        self.assertEqual("resolved", json.loads(proposal_path.read_text())["status"])
        self.run_parity("verify")

    def test_portable_namespaces_and_decoded_targets_fail_closed(self) -> None:
        manifest = self.root / "ai-parity/manifest.toml"
        manifest.write_text(manifest.read_text() + '''

[[artifacts]]
name = "GLOBAL-AGENTS"
source = "ai-parity/contracts/AGENTS.md"
destination = "dot_codex/duplicate.md"
mode = "copy"
''')
        result = self.run_parity("status", expected=2)
        self.assertIn("case-folded artifacts collision", result.stderr)

        manifest.write_text((REPO / "ai-parity/manifest.toml").read_text())
        duplicate_target = self.root / "ai-parity/shared/skills/matlab-runner/scripts/run_matlab.sh"
        duplicate_target.write_text("duplicate decoded target")
        result = self.run_parity("status", expected=2)
        self.assertIn("decoded chezmoi target collision", result.stderr)

        duplicate_target.unlink()
        manifest.write_text(manifest.read_text().replace(
            'destination = "dot_codex/AGENTS.md"', 'destination = "dot_codex/CON"', 1,
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("Windows-reserved", result.stderr)

    def test_proposal_schema_rejects_unknown_fields(self) -> None:
        self.run_parity("sync", "--write")
        origin = self.root / "dot_agents/skills/matlab/fft.md"
        origin.write_text(origin.read_text() + "\nschema fixture\n")
        result = self.run_parity("propose", "--from", "codex", "matlab", expected=1)
        proposal_id = result.stdout.split()[2].rstrip(".")
        path = self.root / f"ai-parity/.proposals/{proposal_id}/proposal.json"
        proposal = json.loads(path.read_text())
        proposal["unexpected"] = True
        path.write_text(json.dumps(proposal))
        result = self.run_parity("proposals", "show", proposal_id, expected=2)
        self.assertIn("unknown fields", result.stderr)

    def test_path_traversal_is_rejected(self) -> None:
        manifest = self.root / "ai-parity/manifest.toml"
        manifest.write_text(manifest.read_text().replace(
            'destination = "dot_codex/AGENTS.md"',
            'destination = "dot_codex/../CLAUDE.md"',
            1,
        ))
        result = self.run_parity("status", expected=2)
        self.assertIn("unsafe artifact destination", result.stderr)


if __name__ == "__main__":
    unittest.main()
