#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deterministic, reviewed Claude/Codex parity generator."""

from __future__ import annotations

import argparse
import base64
import binascii
import contextlib
import difflib
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import tomllib
import unicodedata
import uuid
from pathlib import Path, PurePosixPath

RESERVED_WINDOWS = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
CHEZMOI_PREFIXES = (
    "private_", "executable_", "literal_", "create_", "modify_",
    "remove_", "symlink_", "empty_", "exact_", "readonly_",
    "encrypted_", "dot_", "run_", "once_", "onchange_", "before_", "after_",
)
CHEZMOI_SUFFIXES = (".tmpl", ".age", ".asc", ".literal")
MAX_OWNED_ROOTS = (PurePosixPath("dot_codex"), PurePosixPath("dot_agents"))
MAX_PROTECTED_ROOTS = (PurePosixPath("dot_claude"),)
OPERATIONAL_PATHS = {
    "state_file": PurePosixPath("ai-parity/generated-state.json"),
    "journal_file": PurePosixPath("ai-parity/.sync-journal.json"),
    "lock_file": PurePosixPath("ai-parity/.sync-lock"),
    "transactions_dir": PurePosixPath("ai-parity/.transactions"),
    "proposals_dir": PurePosixPath("ai-parity/.proposals"),
    "docs_marker": PurePosixPath("ai-parity/.docs-mcp-install.json"),
}
ADAPTER_ROOT = PurePosixPath("ai-parity/adapters")
SCHEMA_FILES = {
    ("manifest", 3): "manifest-v3.schema.json",
    ("generated-state", 3): "generated-state-v3.schema.json",
    ("transaction", 3): "transaction-v3.schema.json",
    ("journal", 3): "journal-v3.schema.json",
    ("lock", 3): "lock-v3.schema.json",
    ("proposal", 3): "proposal-v3.schema.json",
    ("docs-marker", 2): "docs-marker-v2.schema.json",
    ("generated-state", 2): "generated-state-v2.schema.json",
    ("transaction", 2): "transaction-v2.schema.json",
    ("journal", 2): "journal-v2.schema.json",
    ("lock", 2): "lock-v2.schema.json",
    ("proposal", 2): "proposal-v2.schema.json",
    ("docs-marker", 1): "docs-marker-v1.schema.json",
}


class ParityError(RuntimeError):
    pass


class LocalSchemaValidator:
    """Small offline validator for the deliberately limited checked-in schemas."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.cache: dict[str, dict] = {}

    def validate(self, value: object, kind: str, version: int) -> None:
        filename = SCHEMA_FILES.get((kind, version))
        if filename is None:
            raise ParityError(f"unsupported {kind} schema version {version}")
        if filename not in self.cache:
            try:
                schema = json.loads((self.directory / filename).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ParityError(f"cannot load local schema {filename}: {exc}") from exc
            if not isinstance(schema, dict):
                raise ParityError(f"local schema is not an object: {filename}")
            self.cache[filename] = schema
        root = self.cache[filename]
        self._check(value, root, root, kind)

    def _check(self, value: object, schema: dict, root: dict, path: str) -> None:
        if "$ref" in schema:
            reference = schema["$ref"]
            if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
                raise ParityError(f"unsupported schema reference at {path}")
            name = reference.removeprefix("#/$defs/")
            try:
                target = root["$defs"][name]
            except KeyError as exc:
                raise ParityError(f"missing schema definition {name}") from exc
            self._check(value, target, root, path)
            return
        if "const" in schema and value != schema["const"]:
            raise ParityError(f"{path} must equal {schema['const']!r}")
        if "enum" in schema and value not in schema["enum"]:
            raise ParityError(f"{path} has unsupported value {value!r}")
        declared = schema.get("type")
        if declared is not None:
            types = declared if isinstance(declared, list) else [declared]
            matches = any(self._matches_type(value, item) for item in types)
            if not matches:
                raise ParityError(f"{path} has wrong type; expected {types}")
        if isinstance(value, dict) and (declared == "object" or "object" in (declared or [])):
            required = schema.get("required", [])
            missing = [key for key in required if key not in value]
            if missing:
                raise ParityError(f"{path} is missing required fields: {', '.join(missing)}")
            properties = schema.get("properties", {})
            additional = schema.get("additionalProperties", True)
            unknown = [key for key in value if key not in properties]
            if additional is False and unknown:
                raise ParityError(f"{path} has unknown fields: {', '.join(sorted(unknown))}")
            for key, item in value.items():
                child = properties.get(key, additional if isinstance(additional, dict) else None)
                if child is not None:
                    self._check(item, child, root, f"{path}.{key}")
        if isinstance(value, list) and (declared == "array" or "array" in (declared or [])):
            if len(value) < schema.get("minItems", 0):
                raise ParityError(f"{path} has too few items")
            if "items" in schema:
                for index, item in enumerate(value):
                    self._check(item, schema["items"], root, f"{path}[{index}]")
        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0):
                raise ParityError(f"{path} is too short")
            if "pattern" in schema and __import__("re").fullmatch(schema["pattern"], value) is None:
                raise ParityError(f"{path} does not match its required pattern")
        if type(value) is int and "minimum" in schema and value < schema["minimum"]:
            raise ParityError(f"{path} is below its minimum")

    @staticmethod
    def _matches_type(value: object, expected: str) -> bool:
        return {
            "object": isinstance(value, dict), "array": isinstance(value, list),
            "string": isinstance(value, str), "integer": type(value) is int,
            "boolean": type(value) is bool, "null": value is None,
        }.get(expected, False)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def safe_rel(raw: str, label: str) -> PurePosixPath:
    if not raw or "\\" in raw or "\x00" in raw or raw.startswith(("/", "//")):
        raise ParityError(f"unsafe {label}: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ParityError(f"unsafe {label}: {raw!r}")
    for part in path.parts:
        if unicodedata.normalize("NFC", part) != part or part.endswith((" ", ".")):
            raise ParityError(f"non-portable {label}: {raw!r}")
        stem = part.split(".", 1)[0].upper()
        if stem in RESERVED_WINDOWS or any(ord(char) < 32 or char in '<>:"|?*' for char in part):
            raise ParityError(f"Windows-reserved {label}: {raw!r}")
    return path


def decoded_literal_path(path: PurePosixPath) -> PurePosixPath:
    parts = []
    for part in path.parts:
        if part.startswith("literal_"):
            decoded = part[len("literal_"):]
            if not decoded:
                raise ParityError(f"empty literal_ chezmoi path component: {path}")
            parts.append(decoded)
        else:
            parts.append(part)
    return PurePosixPath(*parts)


def hash_tree(path: Path) -> str:
    if path.is_symlink():
        raise ParityError(f"symlinks are not allowed in sources: {path}")
    if path.is_file():
        return sha(b"file\0" + path.read_bytes())
    if not path.is_dir():
        raise ParityError(f"missing source: {path}")
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
        rel = item.relative_to(path).as_posix().encode()
        if item.is_symlink():
            raise ParityError(f"symlinks are not allowed in sources: {item}")
        if item.name == ".DS_Store" or "__pycache__" in item.parts or item.suffix == ".pyc":
            raise ParityError(f"local runtime artifact found in source: {item}")
        if item.is_file():
            digest.update(b"file\0" + rel + b"\0" + item.read_bytes() + b"\0")
    return digest.hexdigest()


class Parity:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.schemas_dir = self.root / "ai-parity/schemas"
        self.schemas = LocalSchemaValidator(self.schemas_dir)
        manifest_path = self.root / "ai-parity/manifest.toml"
        self.manifest_path = manifest_path
        try:
            self.manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ParityError(f"cannot read manifest: {exc}") from exc
        self.schemas.validate(self.manifest, "manifest", self.manifest.get("schema_version"))
        for section in ("shared_artifacts", "artifacts", "reviews", "skills", "agents"):
            self._assert_unique_namespace([item["name"] for item in self.manifest[section]], section)
        policy = self.manifest["policy"]
        self.owned = tuple(safe_rel(x, "owned root") for x in policy["owned_roots"])
        self.protected = tuple(safe_rel(x, "protected root") for x in policy["protected_roots"])
        if self.owned != MAX_OWNED_ROOTS or self.protected != MAX_PROTECTED_ROOTS:
            raise ParityError("manifest cannot redefine the engine filesystem safety envelope")
        for key, required in OPERATIONAL_PATHS.items():
            if safe_rel(policy[key], key.replace("_", " ")) != required:
                raise ParityError(f"manifest cannot redefine operational path {key}")
        self.state_path = self.root / OPERATIONAL_PATHS["state_file"]
        self.journal_path = self.root / OPERATIONAL_PATHS["journal_file"]
        self.lock_path = self.root / OPERATIONAL_PATHS["lock_file"]
        self.transactions_dir = self.root / OPERATIONAL_PATHS["transactions_dir"]
        self.proposals_dir = self.root / OPERATIONAL_PATHS["proposals_dir"]
        self.docs_marker = self.root / OPERATIONAL_PATHS["docs_marker"]
        self.shared = {item["name"]: item for item in self.manifest.get("shared_artifacts", [])}
        if len(self.shared) != len(self.manifest.get("shared_artifacts", [])):
            raise ParityError("duplicate shared artifact name")
        self.shared_roots = tuple(
            safe_rel(target["destination"], "shared target")
            for item in self.shared.values() for target in item.get("targets", [])
        )
        self.managed_roots = self.owned + self.shared_roots
        canonical_roots = []
        for artifact in self.shared.values():
            name = safe_rel(artifact["name"], "shared artifact name")
            if len(name.parts) != 1:
                raise ParityError(f"shared artifact name must be one path component: {name}")
            canonical = safe_rel(artifact["canonical"], "canonical source")
            required_canonical = PurePosixPath("ai-parity/shared/skills") / name
            if canonical != required_canonical:
                raise ParityError(f"canonical source is outside its fixed safety envelope: {canonical}")
            canonical_roots.append(canonical)
            if artifact.get("import_mode") not in ("direct", "review"):
                raise ParityError(f"invalid import mode for {name}")
            seen_sides = set()
            for target in artifact.get("targets", []):
                side = target.get("side")
                if side in seen_sides:
                    raise ParityError(f"duplicate {side} target for shared artifact {name}")
                seen_sides.add(side)
                expected_root = (
                    PurePosixPath("dot_claude/skills") if side == "claude"
                    else PurePosixPath("dot_agents/skills") if side == "codex"
                    else None
                )
                destination = safe_rel(target["destination"], "shared target")
                if expected_root is None or destination != expected_root / name:
                    raise ParityError(f"shared {side} target is outside its fixed safety envelope: {destination}")
        self.canonical_roots = tuple(canonical_roots)
        for index, left in enumerate(self.owned):
            for right in self.owned[index + 1:]:
                if left == right or left in right.parents or right in left.parents:
                    raise ParityError(f"owned roots overlap: {left}, {right}")
            if any(left == p or left in p.parents or p in left.parents for p in self.protected):
                raise ParityError(f"owned and protected roots overlap: {left}")
        self._validate_inventory()

    def _assert_no_symlink_components(self, path: Path, label: str) -> None:
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise ParityError(f"{label} is outside repository: {path}") from exc
        current = self.root
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                raise ParityError(f"{label} traverses symlink: {current}")

    def _validate_inventory(self) -> None:
        actual_skills = {p.name for p in (self.root / "dot_claude/skills").iterdir() if p.is_dir()}
        listed_skills = [x["name"] for x in self.manifest.get("skills", [])]
        actual_agents = {p.stem for p in (self.root / "dot_claude/agents").glob("*.md")}
        listed_agents = [x["name"] for x in self.manifest.get("agents", [])]
        for kind, actual, listed in (
            ("skills", actual_skills, listed_skills), ("agents", actual_agents, listed_agents)
        ):
            self._assert_unique_namespace(listed, kind)
            duplicates = sorted({x for x in listed if listed.count(x) > 1})
            if duplicates or actual != set(listed):
                raise ParityError(
                    f"{kind} inventory mismatch; missing={sorted(actual-set(listed))}, "
                    f"stale={sorted(set(listed)-actual)}, duplicates={duplicates}"
                )

    @staticmethod
    def _assert_unique_namespace(values: list[str], label: str) -> None:
        folded = {}
        for value in values:
            if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
                raise ParityError(f"non-NFC {label} identifier: {value!r}")
            key = value.casefold()
            if key in folded:
                raise ParityError(f"case-folded {label} collision: {folded[key]!r}, {value!r}")
            folded[key] = value

    def _under_owned(self, path: PurePosixPath) -> bool:
        return any(path == root or root in path.parents for root in self.managed_roots)

    def _forbidden_runtime_path(self, rel: PurePosixPath) -> bool:
        parts = rel.parts
        if not parts or parts[0] not in ("dot_codex", "dot_agents"):
            return False
        tail = PurePosixPath(*parts[1:]).as_posix()
        name = parts[-1]
        if name in {
            "installation_id", "auth.json", "credentials.json", "identity.json",
            "token.json", "tokens.json", "history.jsonl", "models_cache.json",
            "version.json", ".personality_migration", "dot_personality_migration",
        } or name.endswith(".sqlite") or ".sqlite-" in name:
            return True
        runtime_roots = (
            "sessions", "archived_sessions", "memories", "goals", "log", "logs",
            "shell_snapshots", "tmp", "cache", "skills/.system", "skills/dot_system",
        )
        return any(tail == root or tail.startswith(root + "/") for root in runtime_roots)

    def _assert_destination_safe(self, rel: PurePosixPath) -> None:
        if not self._under_owned(rel):
            raise ParityError(f"destination is outside owned roots: {rel}")
        # Chezmoi interprets attribute prefixes, attribute suffixes, and
        # `.chezmoi*` special names anywhere in its source tree: `run_` files
        # are executed, `.tmpl` files are template-executed, `dot_` renames,
        # and subdirectory `.chezmoiignore`/`.chezmoiremove` change deployment.
        # Only `literal_` is admitted (validated against manifest mappings).
        for part in rel.parts[1:]:
            if part.startswith(".chezmoi"):
                raise ParityError(f"chezmoi special name in generated path: {rel}")
            if part.endswith(CHEZMOI_SUFFIXES):
                raise ParityError(f"chezmoi attribute suffix in generated path: {rel}")
            if part.startswith(CHEZMOI_PREFIXES) and not part.startswith("literal_"):
                raise ParityError(f"chezmoi attribute prefix in generated path: {rel}")
        if self._forbidden_runtime_path(rel):
            raise ParityError(f"destination is Codex-owned runtime state: {rel}")
        protected = any(rel == p or p in rel.parents for p in self.protected)
        opted_in = any(rel == root or root in rel.parents for root in self.shared_roots)
        if protected and not opted_in:
            raise ParityError(f"destination overlaps protected root: {rel}")
        self._assert_no_symlink_components(self.root / rel, "destination")

    def _assert_mutation_path(self, path: Path) -> PurePosixPath:
        try:
            rel = PurePosixPath(path.relative_to(self.root).as_posix())
        except ValueError as exc:
            raise ParityError(f"mutation is outside repository: {path}") from exc
        exact_runtime = {
            OPERATIONAL_PATHS["state_file"], OPERATIONAL_PATHS["journal_file"],
            OPERATIONAL_PATHS["lock_file"], OPERATIONAL_PATHS["docs_marker"],
        }
        runtime_roots = (OPERATIONAL_PATHS["transactions_dir"], OPERATIONAL_PATHS["proposals_dir"])
        if rel in exact_runtime or any(root in rel.parents for root in runtime_roots):
            self._assert_no_symlink_components(path, "runtime mutation")
            return rel
        if any(rel == root or root in rel.parents for root in self.canonical_roots):
            self._assert_no_symlink_components(path, "canonical mutation")
            return rel
        self._assert_destination_safe(rel)
        return rel

    def _unlink_file(self, path: Path) -> None:
        self._assert_mutation_path(path)
        if path.is_symlink() or not path.is_file():
            raise ParityError(f"refusing to delete non-file: {path}")
        path.unlink()

    def expected(self) -> tuple[dict[str, bytes], dict[str, dict[str, str]]]:
        outputs: dict[str, bytes] = {}
        metadata: dict[str, dict[str, str]] = {}
        folded: dict[str, str] = {}
        for artifact in self.manifest.get("artifacts", []):
            source_rel = safe_rel(artifact["source"], "artifact source")
            dest_rel = safe_rel(artifact["destination"], "artifact destination")
            if any(source_rel == root or root in source_rel.parents for root in self.owned):
                raise ParityError(f"generated roots cannot be artifact sources: {source_rel}")
            admitted = (
                source_rel == PurePosixPath("dot_claude")
                or PurePosixPath("dot_claude") in source_rel.parents
                or PurePosixPath("ai-parity/contracts") in source_rel.parents
                or PurePosixPath("ai-parity/adapters") in source_rel.parents
                or PurePosixPath("ai-parity/shared") in source_rel.parents
            )
            if not admitted:
                raise ParityError(f"artifact source is outside admitted input roots: {source_rel}")
            source = self.root / source_rel
            self._assert_no_symlink_components(source, "artifact source")
            mode = artifact["mode"]
            source_digest = hash_tree(source)
            pairs: list[tuple[PurePosixPath, Path]] = []
            if mode == "copy":
                if not source.is_file():
                    raise ParityError(f"copy source is not a file: {source_rel}")
                pairs.append((dest_rel, source))
            elif mode == "tree-copy":
                if not source.is_dir():
                    raise ParityError(f"tree-copy source is not a directory: {source_rel}")
                for item in sorted(source.rglob("*")):
                    if item.is_symlink():
                        raise ParityError(f"symlinks are not allowed in sources: {item}")
                    if item.is_file():
                        child = PurePosixPath(item.relative_to(source).as_posix())
                        if any(part.startswith(CHEZMOI_PREFIXES) for part in child.parts):
                            raise ParityError(f"chezmoi-reserved source name: {source_rel / child}")
                        pairs.append((dest_rel / child, item))
            else:
                raise ParityError(f"unsupported artifact mode: {mode!r}")
            for rel, item in pairs:
                rel = safe_rel(rel.as_posix(), "generated destination")
                self._assert_destination_safe(rel)
                key = rel.as_posix()
                collision = unicodedata.normalize("NFC", key).casefold()
                if key in outputs or collision in folded:
                    raise ParityError(f"duplicate/case-folded destination: {key}")
                folded[collision] = key
                outputs[key] = item.read_bytes()
                metadata[key] = {"artifact": artifact["name"], "source": source_rel.as_posix(), "source_digest": source_digest}
        for artifact in self.shared.values():
            canonical_rel = safe_rel(artifact["canonical"], "canonical source")
            if PurePosixPath("ai-parity/shared") not in canonical_rel.parents:
                raise ParityError(f"canonical source must be under ai-parity/shared: {canonical_rel}")
            canonical = self.root / canonical_rel
            self._assert_no_symlink_components(canonical, "canonical source")
            canonical_digest = hash_tree(canonical)
            for target in artifact.get("targets", []):
                side = target["side"]
                if side not in ("claude", "codex"):
                    raise ParityError(f"invalid shared target side: {side}")
                destination = safe_rel(target["destination"], "shared destination")
                overrides = target.get("source_overrides", {})
                if not isinstance(overrides, dict):
                    raise ParityError("shared source_overrides must be a table")
                normalized_overrides = {
                    safe_rel(key, "shared override key").as_posix():
                    safe_rel(value, "shared override")
                    for key, value in overrides.items()
                }
                self._assert_unique_namespace(list(normalized_overrides), "shared override paths")
                for override in normalized_overrides.values():
                    if not (override == ADAPTER_ROOT or ADAPTER_ROOT in override.parents):
                        raise ParityError(f"shared override is outside adapter roots: {override}")
                    self._assert_no_symlink_components(self.root / override, "shared override")
                mappings = target.get("chezmoi_mappings", {})
                if not isinstance(mappings, dict):
                    raise ParityError("chezmoi_mappings must be a table")
                normalized_mappings = {
                    safe_rel(key, "chezmoi mapping source").as_posix():
                    safe_rel(value, "chezmoi mapping target").as_posix()
                    for key, value in mappings.items()
                }
                self._assert_unique_namespace(list(normalized_mappings), "chezmoi mapping paths")
                used_overrides = set()
                used_mappings = set()
                for item in sorted(canonical.rglob("*")):
                    if item.is_symlink():
                        raise ParityError(f"symlinks are not allowed in canonical sources: {item}")
                    if not item.is_file():
                        continue
                    child = PurePosixPath(item.relative_to(canonical).as_posix())
                    reserved = [part for part in child.parts if part.startswith(CHEZMOI_PREFIXES)]
                    if reserved:
                        if any(not part.startswith("literal_") for part in reserved):
                            raise ParityError(f"unsafe chezmoi attribute in canonical name: {canonical_rel / child}")
                        declared = normalized_mappings.get(child.as_posix())
                        decoded = decoded_literal_path(child).as_posix()
                        if declared != decoded:
                            raise ParityError(
                                f"undeclared or incorrect chezmoi mapping for {canonical_rel / child}; "
                                f"expected {decoded!r}"
                            )
                        used_mappings.add(child.as_posix())
                    elif child.as_posix() in normalized_mappings:
                        raise ParityError(f"chezmoi mapping does not name an attributed file: {child}")
                    override_rel = normalized_overrides.get(child.as_posix(), canonical_rel / child)
                    if child.as_posix() in normalized_overrides:
                        used_overrides.add(child.as_posix())
                    source = self.root / override_rel
                    self._assert_no_symlink_components(source, "shared source")
                    if source.is_symlink() or not source.is_file():
                        raise ParityError(f"missing shared source: {source}")
                    rel = safe_rel((destination / child).as_posix(), "shared output")
                    self._assert_destination_safe(rel)
                    key = rel.as_posix()
                    collision = unicodedata.normalize("NFC", key).casefold()
                    if key in outputs or collision in folded:
                        raise ParityError(f"duplicate/case-folded destination: {key}")
                    folded[collision] = key
                    outputs[key] = source.read_bytes()
                    metadata[key] = {
                        "artifact": artifact["name"], "canonical": canonical_rel.as_posix(),
                        "canonical_digest": canonical_digest, "side": side,
                        "source": source.relative_to(self.root).as_posix(), "source_digest": hash_tree(source),
                    }
                unused_overrides = sorted(set(normalized_overrides) - used_overrides)
                unused_mappings = sorted(set(normalized_mappings) - used_mappings)
                if unused_overrides:
                    raise ParityError("unused shared source override(s): " + ", ".join(unused_overrides))
                if unused_mappings:
                    raise ParityError("unused chezmoi mapping(s): " + ", ".join(unused_mappings))
        deployed_folded = {}
        for rel, data in outputs.items():
            decoded = decoded_literal_path(PurePosixPath(rel)).as_posix()
            collision = unicodedata.normalize("NFC", decoded).casefold()
            if collision in deployed_folded and deployed_folded[collision] != rel:
                raise ParityError(f"decoded chezmoi target collision: {deployed_folded[collision]}, {rel}")
            deployed_folded[collision] = rel
            if rel.endswith(".toml"):
                try:
                    tomllib.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
                    raise ParityError(f"invalid generated TOML: {rel}: {exc}") from exc
            if rel.endswith("/SKILL.md"):
                text = data.decode("utf-8")
                if not text.startswith("---\n") or "\nname:" not in text or "\ndescription:" not in text:
                    raise ParityError(f"invalid skill frontmatter: {rel}")
        for record in metadata.values():
            record["source_mode"] = 0o644
            record["deployed_mode"] = 0o644
        return outputs, metadata

    def review_status(self) -> list[tuple[str, str, str]]:
        result = []
        for review in self.manifest.get("reviews", []):
            source = self.root / safe_rel(review["source"], "review source")
            result.append((review["name"], review["acknowledged_digest"], hash_tree(source)))
        return result

    def state_for(self, outputs: dict[str, bytes], metadata: dict[str, dict[str, str]]) -> dict:
        records = {
            path: {**metadata[path], "sha256": sha(data)}
            for path, data in sorted(outputs.items())
        }
        generation_material = {
            "generator_version": self.manifest["generator_version"],
            "engine_sha256": sha(Path(__file__).read_bytes()),
            "manifest_sha256": sha(self.manifest_path.read_bytes()),
            "schemas_sha256": hash_tree(self.schemas_dir),
            "outputs": records,
            "reviews": [{"name": n, "digest": current} for n, _, current in self.review_status()],
        }
        state = {
            "format": "ai-parity-generated-state", "schema_version": 3,
            "generator_version": self.manifest["generator_version"],
            "generation_id": sha(canonical_json(generation_material)),
            "generator_inputs": {
                "engine_sha256": generation_material["engine_sha256"],
                "manifest_sha256": generation_material["manifest_sha256"],
                "schemas_sha256": generation_material["schemas_sha256"],
            },
            "outputs": records,
        }
        self.schemas.validate(state, "generated-state", 3)
        return state

    def load_state(self) -> dict | None:
        if not self.state_path.exists():
            return None
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParityError(f"invalid generated state: {exc}") from exc
        if value.get("schema_version") == 3:
            self.schemas.validate(value, "generated-state", 3)
        elif value.get("schema_version") == 2:
            self.schemas.validate(value, "generated-state", 2)
        else:
            raise ParityError("invalid generated state schema")
        for raw, record in value["outputs"].items():
            rel = safe_rel(raw, "state output")
            self._assert_destination_safe(rel)
            if not isinstance(record, dict) or not isinstance(record.get("sha256"), str):
                raise ParityError(f"invalid state record: {raw}")
            if len(record["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in record["sha256"]):
                raise ParityError(f"invalid state hash: {raw}")
        return value

    def _current_hash(self, rel: str) -> str | None:
        path = self.root / safe_rel(rel, "state output")
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            return "NON_FILE"
        return sha(path.read_bytes())

    def _current_mode(self, rel: str) -> int | None:
        path = self.root / safe_rel(rel, "output mode")
        if not path.is_file() or path.is_symlink():
            return None
        return stat.S_IMODE(path.stat().st_mode)

    def _unknown_owned_files(self, expected: set[str]) -> list[str]:
        unknown = set()
        for owned in self.managed_roots:
            base = self.root / owned
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_symlink() or path.is_file():
                    rel = path.relative_to(self.root).as_posix()
                    if rel not in expected:
                        unknown.add(rel)
        return sorted(unknown)

    def _protected_digest(self) -> str:
        digest = hashlib.sha256()
        for protected in self.protected:
            base = self.root / protected
            for path in sorted(base.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                rel = PurePosixPath(path.relative_to(self.root).as_posix())
                if any(rel == shared or shared in rel.parents for shared in self.shared_roots):
                    continue
                digest.update(rel.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        return digest.hexdigest()

    def problems(self) -> list[str]:
        outputs, metadata = self.expected()
        desired = self.state_for(outputs, metadata)
        state = self.load_state()
        problems = []
        for name, acknowledged, current in self.review_status():
            if acknowledged != current:
                problems.append(f"review required: {name} (current digest {current})")
        if self.journal_path.exists():
            problems.append("unfinished transaction exists; run `dots ai doctor`")
        if self.lock_path.exists():
            problems.append("sync lock exists")
        if state != desired:
            problems.append("generated-state.json is stale or missing")
        old_paths = set(state.get("outputs", {})) if state else set()
        for rel, data in outputs.items():
            if self._current_hash(rel) != sha(data):
                problems.append(f"output drift: {rel}")
            elif os.name != "nt" and self._current_mode(rel) != 0o644:
                problems.append(f"output mode drift: {rel} (expected 0644)")
        for rel in sorted(old_paths - set(outputs)):
            problems.append(f"obsolete generated output: {rel}")
        for rel in self._unknown_owned_files(set(outputs)):
            problems.append(f"unowned file under generated root: {rel}")
        return problems

    def show_status(self) -> int:
        problems = self.problems()
        if problems:
            print("AI parity is not synchronized:")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        outputs, _ = self.expected()
        print(f"AI parity is synchronized ({len(outputs)} generated files).")
        return 0

    def show_diff(self) -> int:
        outputs, _ = self.expected()
        changed = False
        for rel, wanted in sorted(outputs.items()):
            path = self.root / rel
            current = path.read_bytes() if path.is_file() and not path.is_symlink() else b""
            if current == wanted:
                continue
            changed = True
            try:
                old_text, new_text = current.decode(), wanted.decode()
                sys.stdout.writelines(difflib.unified_diff(
                    old_text.splitlines(True), new_text.splitlines(True),
                    fromfile=f"a/{rel}", tofile=f"b/{rel}",
                ))
            except UnicodeDecodeError:
                print(f"binary change: {rel} ({len(current)} -> {len(wanted)} bytes)")
        state = self.load_state()
        for rel in sorted(set(state.get("outputs", {})) - set(outputs) if state else set()):
            changed = True
            print(f"obsolete generated output (manual removal required): {rel}")
        desired_state = canonical_json(self.state_for(outputs, self.expected()[1]))
        current_state = self.state_path.read_bytes() if self.state_path.is_file() else b""
        if current_state != desired_state:
            changed = True
            print("update generated state: ai-parity/generated-state.json")
        for rel in self._unknown_owned_files(set(outputs)):
            changed = True
            print(f"unowned generated-root file (manual removal required): {rel}")
        if not changed:
            print("No generated output differences.")
        return 1 if changed else 0

    def _read_lock(self) -> dict:
        try:
            value = json.loads(self.lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParityError("malformed lock; preserve it for manual quarantine") from exc
        if not isinstance(value, dict):
            raise ParityError("invalid lock metadata; preserve it for manual quarantine")
        if value.get("schema_version") == 3:
            self.schemas.validate(value, "lock", 3)
        elif value.get("schema_version") == 2:
            self.schemas.validate(value, "lock", 2)
            legacy = {"schema_version", "pid", "host", "token", "transaction_id", "operation"}
            hardened = legacy | {"generation_id", "transaction_digest"}
            if set(value) not in (legacy, hardened):
                raise ParityError("invalid legacy lock metadata")
        else:
            raise ParityError("unsupported lock schema")
        if not isinstance(value["pid"], int) or value["pid"] <= 0:
            raise ParityError("invalid lock pid")
        if not all(isinstance(value[key], str) for key in ("host", "token", "transaction_id", "operation")):
            raise ParityError("invalid lock fields")
        if len(value["transaction_id"]) != 32 or any(c not in "0123456789abcdef" for c in value["transaction_id"]):
            raise ParityError("invalid lock transaction id")
        if len(value["token"]) != 32 or any(c not in "0123456789abcdef" for c in value["token"]):
            raise ParityError("invalid lock token")
        if value["operation"] not in ("sync", "reconcile-after-merge", "proposal-accept", "transaction-gc"):
            raise ParityError("invalid lock operation")
        for key in ("generation_id", "transaction_digest"):
            if value.get(key) is not None and not self._valid_hash(value[key]):
                raise ParityError(f"invalid lock {key}")
        return value

    def _lock_process_alive(self, lock: dict) -> bool:
        if lock["host"] != socket.gethostname():
            return False
        return self._pid_alive(lock["pid"])

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        # Never use os.kill(pid, 0) on Windows: sig 0 is signal.CTRL_C_EVENT
        # there, which delivers a real console Ctrl-C to the target process
        # group (or fails for unrelated reasons) instead of probing existence.
        if os.name == "nt":
            import ctypes

            process_query_limited_information = 0x1000
            still_active = 259
            error_access_denied = 5
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                # Access denied means the process exists but is not ours:
                # fail safe and treat it as alive.
                return ctypes.get_last_error() == error_access_denied
            try:
                code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return True
                return code.value == still_active
            finally:
                kernel32.CloseHandle(handle)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    @contextlib.contextmanager
    def lock(
        self, transaction_id: str, operation: str, generation_id: str | None = None,
        transaction_digest: str | None = None, takeover_token: str | None = None,
    ):
        token = uuid.uuid4().hex
        lock_value = {
            "format": "ai-parity-lock", "schema_version": 3,
            "pid": os.getpid(), "host": socket.gethostname(),
            "token": token, "transaction_id": transaction_id, "operation": operation,
            "generation_id": generation_id, "transaction_digest": transaction_digest,
        }
        self.schemas.validate(lock_value, "lock", 3)
        payload = canonical_json(lock_value)
        if self.lock_path.exists() and takeover_token is not None:
            existing = self._read_lock()
            if existing["token"] != takeover_token or existing["transaction_id"] != transaction_id:
                raise ParityError("locked recovery requires the matching transaction id and --token")
            if existing["operation"] != operation:
                raise ParityError("lock operation does not match recovery transaction")
            if self._lock_process_alive(existing):
                raise ParityError("refusing recovery while the lock-owning process is still alive")
            if generation_id is not None and existing.get("generation_id") not in (None, generation_id):
                raise ParityError("lock generation does not match recovery transaction")
            if transaction_digest is not None and existing.get("transaction_digest") not in (None, transaction_digest):
                raise ParityError("lock digest does not match recovery transaction")
            self._unlink_file(self.lock_path)
        try:
            fd = os.open(self.lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ParityError("another sync is running (or a stale lock exists)") from exc
        try:
            os.write(fd, payload)
            os.fsync(fd)
            os.close(fd)
            yield token
        finally:
            try:
                value = self._read_lock()
                if value.get("token") == token:
                    self._unlink_file(self.lock_path)
            except (OSError, ParityError):
                pass

    def _rewrite_owned_lock(self, token: str, transaction: dict) -> None:
        lock = self._read_lock()
        if lock["token"] != token or lock["transaction_id"] != transaction["transaction_id"]:
            raise ParityError("sync lock ownership changed")
        lock["generation_id"] = transaction["generation_id"]
        lock["transaction_digest"] = self._effective_transaction_digest(transaction)
        self._atomic_write(self.lock_path, canonical_json(lock), 0o600)

    def _snapshot(self, path: Path) -> dict:
        if path.is_symlink():
            raise ParityError(f"transaction path is a symlink: {path}")
        if not path.exists():
            return {"exists": False, "sha256": None, "mode": None, "data": None}
        if not path.is_file():
            raise ParityError(f"transaction path is not a file: {path}")
        data = path.read_bytes()
        return {
            "exists": True, "sha256": sha(data), "mode": stat.S_IMODE(path.stat().st_mode),
            "data": base64.b64encode(data).decode("ascii"),
        }

    def _new_snapshot(self, data: bytes | None, mode: int = 0o644) -> dict:
        if data is None:
            return {"exists": False, "sha256": None, "mode": None, "data": None}
        return {"exists": True, "sha256": sha(data), "mode": mode, "data": base64.b64encode(data).decode("ascii")}

    def _snapshot_matches(self, path: Path, snapshot: dict) -> bool:
        current = self._snapshot(path)
        return (
            current["exists"] == snapshot["exists"]
            and current["sha256"] == snapshot["sha256"]
            and (os.name == "nt" or not snapshot["exists"] or current["mode"] == snapshot["mode"])
        )

    def _apply_snapshot(self, path: Path, snapshot: dict) -> None:
        if snapshot["exists"]:
            self._atomic_write(path, base64.b64decode(snapshot["data"], validate=True), int(snapshot["mode"]))
        elif path.exists():
            self._unlink_file(path)

    @staticmethod
    def _valid_hash(value: object) -> bool:
        return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

    def _validate_snapshot(self, snapshot: object, label: str) -> None:
        if not isinstance(snapshot, dict) or set(snapshot) != {"exists", "sha256", "mode", "data"}:
            raise ParityError(f"invalid {label} snapshot fields")
        if snapshot["exists"] is False:
            if any(snapshot[key] is not None for key in ("sha256", "mode", "data")):
                raise ParityError(f"inconsistent absent {label} snapshot")
            return
        if snapshot["exists"] is not True or not self._valid_hash(snapshot["sha256"]):
            raise ParityError(f"invalid present {label} snapshot")
        if type(snapshot["mode"]) is not int or not 0 <= snapshot["mode"] <= 0o777:
            raise ParityError(f"invalid {label} snapshot mode")
        if not isinstance(snapshot["data"], str):
            raise ParityError(f"invalid {label} snapshot data")
        try:
            decoded = base64.b64decode(snapshot["data"], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ParityError(f"invalid {label} snapshot base64") from exc
        if base64.b64encode(decoded).decode("ascii") != snapshot["data"] or sha(decoded) != snapshot["sha256"]:
            raise ParityError(f"{label} snapshot hash/data mismatch")

    def _transaction_digest(self, transaction: dict) -> str:
        keys = ["schema_version", "transaction_id", "generation_id", "operation", "entries"]
        if transaction.get("schema_version") == 3:
            keys = ["format", *keys, "context"]
        material = {key: transaction[key] for key in keys}
        return sha(canonical_json(material))

    def _effective_transaction_digest(self, transaction: dict) -> str:
        return transaction.get("transaction_digest") or sha(canonical_json({
            key: transaction[key] for key in ("schema_version", "transaction_id", "generation_id", "entries")
        }))

    @staticmethod
    def _transaction_operation(transaction: dict) -> str:
        return transaction.get("operation", "sync")

    def _validate_transaction(self, value: object, transaction_id: str) -> dict:
        if not isinstance(value, dict):
            raise ParityError("invalid transaction fields")
        version = value.get("schema_version")
        legacy_fields = {"schema_version", "transaction_id", "status", "generation_id", "entries"}
        hardened_fields = legacy_fields | {"operation", "transaction_digest"}
        v3_fields = hardened_fields | {"format", "context"}
        if version == 3:
            self.schemas.validate(value, "transaction", 3)
            if set(value) != v3_fields:
                raise ParityError("invalid transaction-v3 fields")
        elif version == 2 and set(value) in (legacy_fields, hardened_fields):
            self.schemas.validate(value, "transaction", 2)
        else:
            raise ParityError("unsupported transaction fields or schema")
        if value["transaction_id"] != transaction_id:
            raise ParityError("invalid transaction metadata")
        if value["status"] not in ("prepared", "rendered", "rolled_back"):
            raise ParityError("invalid transaction status")
        operation = self._transaction_operation(value)
        if operation not in ("sync", "reconcile-after-merge", "proposal-accept"):
            raise ParityError("invalid transaction operation")
        if not self._valid_hash(value["generation_id"]):
            raise ParityError("invalid transaction digest metadata")
        if "transaction_digest" in value and not self._valid_hash(value["transaction_digest"]):
            raise ParityError("invalid transaction content digest")
        context = value.get("context")
        if operation == "proposal-accept":
            required_context = {"proposal_id", "artifact", "canonical_root"}
            if not isinstance(context, dict) or set(context) != required_context:
                raise ParityError("invalid proposal transaction context")
            if len(context["proposal_id"]) != 24 or any(c not in "0123456789abcdef" for c in context["proposal_id"]):
                raise ParityError("invalid proposal transaction id")
            canonical_root = safe_rel(context["canonical_root"], "proposal transaction canonical root")
            if canonical_root not in self.canonical_roots:
                raise ParityError("proposal transaction canonical root is not manifest-owned")
        elif context is not None:
            raise ParityError("non-proposal transaction context must be null")
        if not isinstance(value["entries"], list) or not value["entries"]:
            raise ParityError("transaction entries must be a non-empty list")
        seen = set()
        state_rel = OPERATIONAL_PATHS["state_file"]
        for entry in value["entries"]:
            if not isinstance(entry, dict) or set(entry) != {"path", "old", "new"}:
                raise ParityError("invalid transaction entry fields")
            rel = safe_rel(entry["path"], "transaction path")
            folded_rel = unicodedata.normalize("NFC", rel.as_posix()).casefold()
            if folded_rel in seen:
                raise ParityError(f"duplicate transaction path: {rel}")
            seen.add(folded_rel)
            if rel != state_rel:
                if operation == "proposal-accept" and (
                    rel == safe_rel(context["canonical_root"], "canonical root")
                    or safe_rel(context["canonical_root"], "canonical root") in rel.parents
                    or rel == OPERATIONAL_PATHS["proposals_dir"] / context["proposal_id"] / "proposal.json"
                ):
                    self._assert_mutation_path(self.root / rel)
                else:
                    self._assert_destination_safe(rel)
            self._validate_snapshot(entry["old"], f"old {rel}")
            self._validate_snapshot(entry["new"], f"new {rel}")
        if "transaction_digest" in value and self._transaction_digest(value) != value["transaction_digest"]:
            raise ParityError("transaction content digest mismatch")
        return value

    def _write_transaction(self, transaction: dict) -> Path:
        self._validate_transaction(transaction, transaction["transaction_id"])
        path = self.transactions_dir / transaction["transaction_id"] / "transaction.json"
        self._atomic_write(path, canonical_json(transaction), 0o600)
        return path

    def _build_transaction(
        self, outputs: dict[str, bytes], desired: dict, operation: str = "sync",
        transaction_id: str | None = None, context: dict | None = None,
    ) -> dict:
        entries = []
        # State is evidence, never deletion authority. Obsolete files must be
        # removed explicitly by a human before state can forget them.
        for rel in sorted(outputs):
            safe = safe_rel(rel, "transaction output")
            self._assert_destination_safe(safe)
            path = self.root / safe
            old_snapshot = self._snapshot(path)
            new_snapshot = self._new_snapshot(outputs[rel])
            if (old_snapshot["exists"], old_snapshot["sha256"], old_snapshot["mode"] if os.name != "nt" else None) != (
                new_snapshot["exists"], new_snapshot["sha256"], new_snapshot["mode"] if os.name != "nt" else None
            ):
                entries.append({"path": rel, "old": old_snapshot, "new": new_snapshot})
        state_rel = self.state_path.relative_to(self.root).as_posix()
        old_state = self._snapshot(self.state_path)
        new_state = self._new_snapshot(canonical_json(desired))
        if (old_state["exists"], old_state["sha256"]) != (new_state["exists"], new_state["sha256"]):
            entries.append({"path": state_rel, "old": old_state, "new": new_state})
        transaction_id = transaction_id or uuid.uuid4().hex
        transaction = {
            "format": "ai-parity-transaction", "schema_version": 3,
            "transaction_id": transaction_id, "status": "prepared",
            "generation_id": desired["generation_id"], "operation": operation,
            "context": context, "entries": entries,
        }
        transaction["transaction_digest"] = self._transaction_digest(transaction)
        return transaction

    def _load_transaction(self, transaction_id: str) -> tuple[Path, dict]:
        if len(transaction_id) != 32 or any(c not in "0123456789abcdef" for c in transaction_id):
            raise ParityError("invalid transaction id")
        path = self.transactions_dir / transaction_id / "transaction.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParityError(f"cannot read transaction {transaction_id}: {exc}") from exc
        return path, self._validate_transaction(value, transaction_id)

    def _load_journal(self) -> dict:
        try:
            value = json.loads(self.journal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParityError(f"invalid sync journal: {exc}") from exc
        if not isinstance(value, dict):
            raise ParityError("invalid sync journal fields")
        version = value.get("schema_version")
        legacy = {"schema_version", "transaction_id", "generation_id", "status"}
        hardened = legacy | {"operation", "transaction_digest"}
        current = hardened | {"format"}
        if version == 3:
            self.schemas.validate(value, "journal", 3)
            if set(value) != current:
                raise ParityError("invalid journal-v3 fields")
        elif version == 2 and set(value) in (legacy, hardened):
            self.schemas.validate(value, "journal", 2)
        else:
            raise ParityError("unsupported sync journal schema")
        if value["status"] != "prepared" or value.get("operation", "sync") not in (
            "sync", "reconcile-after-merge", "proposal-accept"
        ):
            raise ParityError("invalid sync journal status or operation")
        if not isinstance(value["transaction_id"], str) or len(value["transaction_id"]) != 32 or any(
            c not in "0123456789abcdef" for c in value["transaction_id"]
        ):
            raise ParityError("invalid sync journal transaction id")
        if not self._valid_hash(value["generation_id"]):
            raise ParityError("invalid sync journal digest metadata")
        if value.get("transaction_digest") is not None and not self._valid_hash(value["transaction_digest"]):
            raise ParityError("invalid sync journal transaction digest")
        return value

    def _journal_for(self, transaction: dict) -> dict:
        journal = {
            "format": "ai-parity-journal", "schema_version": 3,
            "transaction_id": transaction["transaction_id"],
            "generation_id": transaction["generation_id"], "operation": self._transaction_operation(transaction),
            "transaction_digest": self._effective_transaction_digest(transaction), "status": "prepared",
        }
        self.schemas.validate(journal, "journal", 3)
        return journal

    def _assert_journal_transaction(self, journal: dict, transaction: dict) -> None:
        expected = {
            "transaction_id": transaction["transaction_id"],
            "generation_id": transaction["generation_id"],
            "operation": self._transaction_operation(transaction),
            "transaction_digest": self._effective_transaction_digest(transaction),
        }
        for key, wanted in expected.items():
            if key in journal and journal[key] != wanted:
                raise ParityError(f"journal/transaction {key} mismatch")

    def repair(self, transaction_id: str, action: str, token: str | None) -> int:
        if not self.journal_path.exists():
            raise ParityError("transaction is not active; no recovery journal exists")
        journal = self._load_journal()
        if journal["transaction_id"] != transaction_id:
            raise ParityError("journal references a different transaction")
        path, transaction = self._load_transaction(transaction_id)
        self._assert_journal_transaction(journal, transaction)
        if action == "finish" and self._transaction_operation(transaction) != "proposal-accept":
            outputs, metadata = self.expected()
            if self.state_for(outputs, metadata)["generation_id"] != transaction["generation_id"]:
                raise ParityError("sources or renderers changed; rollback and create a fresh transaction")
        takeover = token if self.lock_path.exists() else None
        if self.lock_path.exists() and not token:
            raise ParityError("locked recovery requires the matching transaction id and --token")
        with self.lock(
            transaction_id, self._transaction_operation(transaction), transaction["generation_id"],
            self._effective_transaction_digest(transaction), takeover_token=takeover,
        ):
            journal = self._load_journal()
            path, transaction = self._load_transaction(transaction_id)
            self._assert_journal_transaction(journal, transaction)
            desired_side = "new" if action == "finish" else "old"
            conflicts = []
            for entry in transaction["entries"]:
                file_path = self.root / safe_rel(entry["path"], "repair path")
                if not (self._snapshot_matches(file_path, entry["old"]) or self._snapshot_matches(file_path, entry["new"])):
                    conflicts.append(entry["path"])
            if conflicts:
                raise ParityError("third-state files block recovery: " + ", ".join(conflicts))
            for entry in transaction["entries"]:
                file_path = self.root / safe_rel(entry["path"], "repair path")
                if not (self._snapshot_matches(file_path, entry["old"]) or self._snapshot_matches(file_path, entry["new"])):
                    raise ParityError(f"third-state file appeared during recovery: {entry['path']}")
                self._apply_snapshot(file_path, entry[desired_side])
            transaction["status"] = "rendered" if action == "finish" else "rolled_back"
            self._atomic_write(path, canonical_json(transaction), 0o600)
            if self._load_journal() != journal:
                raise ParityError("sync journal changed during recovery")
            self._unlink_file(self.journal_path)
        print(f"Transaction {transaction_id} {transaction['status']}.")
        return 0

    def unlock_orphan(self, token: str) -> int:
        if not self.lock_path.exists():
            raise ParityError("no lock exists")
        lock = self._read_lock()
        if lock.get("token") != token:
            raise ParityError("lock token does not match")
        if self._lock_process_alive(lock):
            raise ParityError("refusing to remove a lock whose process is still alive")
        transaction_id = lock.get("transaction_id", "")
        transaction_path = self.transactions_dir / transaction_id / "transaction.json"
        if transaction_path.exists() or self.journal_path.exists():
            raise ParityError("lock belongs to a recoverable transaction; use repair --finish or --rollback")
        self._unlink_file(self.lock_path)
        print("Explicitly removed orphan lock.")
        return 0

    def quarantine_malformed_lock(self) -> int:
        if not self.lock_path.exists():
            raise ParityError("no lock exists")
        try:
            self._read_lock()
        except (OSError, ParityError):
            quarantine = self.transactions_dir / "quarantine" / f"lock-{uuid.uuid4().hex}.json"
            quarantine.parent.mkdir(parents=True, exist_ok=True)
            with contextlib.suppress(OSError):
                os.chmod(quarantine.parent, 0o700)
            self._assert_mutation_path(self.lock_path)
            self._assert_mutation_path(quarantine)
            os.replace(self.lock_path, quarantine)
            print(f"Preserved malformed lock at {quarantine.relative_to(self.root)}.")
            return 0
        raise ParityError("lock is valid; use its token and the matching repair/unlock command")

    def doctor(self) -> int:
        print("AI parity recovery diagnostics")
        if self.lock_path.exists():
            try:
                lock = self._read_lock()
                print(f"Lock: transaction={lock.get('transaction_id')} host={lock.get('host')} pid={lock.get('pid')} token={lock.get('token')}")
            except (OSError, json.JSONDecodeError):
                print(f"Lock: malformed ({self.lock_path})")
        else:
            print("Lock: none")
        if self.journal_path.exists():
            try:
                print(json.dumps(self._load_journal(), indent=2, sort_keys=True))
            except ParityError as exc:
                print(f"Active transaction: malformed ({exc})")
        else:
            print("Active transaction: none")
        return 0

    def _shared_target(self, artifact_name: str, side: str) -> tuple[dict, dict]:
        artifact = self.shared.get(artifact_name)
        if artifact is None:
            raise ParityError(f"unknown shared artifact: {artifact_name}")
        for target in artifact.get("targets", []):
            if target["side"] == side:
                return artifact, target
        raise ParityError(f"artifact {artifact_name} has no {side} target")

    def _capture_tree(self, base: Path) -> dict[str, dict]:
        if not base.is_dir():
            raise ParityError(f"missing target tree: {base}")
        result = {}
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                raise ParityError(f"proposal source contains symlink: {path}")
            if path.is_file():
                data = path.read_bytes()
                result[path.relative_to(base).as_posix()] = {
                    "sha256": sha(data), "mode": stat.S_IMODE(path.stat().st_mode),
                    "data": base64.b64encode(data).decode("ascii"),
                }
        return result

    def propose(self, artifact_name: str, side: str, source_root: Path | None = None) -> str | None:
        artifact, target = self._shared_target(artifact_name, side)
        source_root = (source_root or self.root).resolve()
        destination = safe_rel(target["destination"], "proposal target")
        current = self._capture_tree(source_root / destination)
        state = self.load_state()
        if state is None:
            raise ParityError("generate parity state before creating proposals")
        # A separately declared artifact may intentionally live below a shared
        # target (for example Codex-only agents/openai.yaml metadata). It is
        # verified through its own generated-state record and must not appear as
        # reverse-intake drift for the enclosing shared artifact.
        foreign_owned = {
            PurePosixPath(path).relative_to(destination).as_posix()
            for path, record in state["outputs"].items()
            if PurePosixPath(path).is_relative_to(destination)
            and record.get("artifact") != artifact_name
        }
        current = {rel: record for rel, record in current.items() if rel not in foreign_owned}
        base_records = {
            PurePosixPath(path).relative_to(destination).as_posix(): record
            for path, record in state["outputs"].items()
            if record.get("artifact") == artifact_name and record.get("side") == side
        }
        changed = sorted(
            rel for rel in set(current) | set(base_records)
            if current.get(rel, {}).get("sha256") != base_records.get(rel, {}).get("sha256")
        )
        if not changed:
            return None
        deleted = [rel for rel in changed if rel not in current]
        canonical = self.root / safe_rel(artifact["canonical"], "proposal canonical")
        baseline_digest = next((r.get("canonical_digest") for r in base_records.values()), None)
        canonical_digest = hash_tree(canonical)
        other_target_drift = any(
            self._hash_at(source_root / safe_rel(path, "other shared target")) != record["sha256"]
            for path, record in state["outputs"].items()
            if record.get("artifact") == artifact_name and record.get("side") not in (None, side)
        )
        status = "applicable" if (
            artifact["import_mode"] == "direct" and not deleted
            and canonical_digest == baseline_digest and not other_target_drift
        ) else "review_required"
        material = {
            "artifact": artifact_name, "side": side, "state_generation": state["generation_id"],
            "canonical_digest": canonical_digest, "baseline_canonical_digest": baseline_digest,
            "changed": changed, "current": current,
        }
        proposal_id = sha(canonical_json(material))[:24]
        proposal = {
            "format": "ai-parity-proposal", "schema_version": 3,
            "proposal_id": proposal_id, "kind": "artifact",
            "status": status, **material,
        }
        self._validate_proposal(proposal, proposal_id)
        path = self.proposals_dir / proposal_id / "proposal.json"
        self._atomic_write(path, canonical_json(proposal), 0o600)
        return proposal_id

    def _hash_at(self, path: Path) -> str | None:
        if path.is_symlink() or not path.is_file():
            return None
        return sha(path.read_bytes())

    def propose_all(self, source_root: Path | None = None) -> list[str]:
        created = []
        for name, artifact in self.shared.items():
            for target in artifact.get("targets", []):
                proposal_id = self.propose(name, target["side"], source_root)
                if proposal_id:
                    created.append(proposal_id)
        return created

    def _load_proposal(self, proposal_id: str) -> tuple[Path, dict]:
        if len(proposal_id) != 24 or any(c not in "0123456789abcdef" for c in proposal_id):
            raise ParityError("invalid proposal id")
        path = self.proposals_dir / proposal_id / "proposal.json"
        try:
            proposal = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParityError(f"cannot read proposal {proposal_id}: {exc}") from exc
        return path, self._validate_proposal(proposal, proposal_id)

    def _validate_proposal(self, proposal: object, proposal_id: str) -> dict:
        if not isinstance(proposal, dict) or proposal.get("proposal_id") != proposal_id:
            raise ParityError("invalid proposal metadata")
        if proposal.get("schema_version") == 3:
            self.schemas.validate(proposal, "proposal", 3)
        elif proposal.get("schema_version") != 2:
            raise ParityError("unsupported proposal schema")
        else:
            self.schemas.validate(proposal, "proposal", 2)
        common = {"proposal_id", "kind", "status", "schema_version"}
        if proposal.get("status") not in (
            "applicable", "review_required", "accepted_pending_render", "resolved", "rejected"
        ):
            raise ParityError("invalid proposal status")
        if proposal.get("schema_version") == 3:
            common.add("format")
        if proposal.get("kind") == "artifact":
            fields = common | {
                "artifact", "side", "state_generation", "canonical_digest",
                "baseline_canonical_digest", "changed", "current",
            }
            if set(proposal) != fields or proposal.get("side") not in ("claude", "codex"):
                raise ParityError("invalid artifact proposal fields")
            if not all(self._valid_hash(proposal[key]) for key in ("state_generation", "canonical_digest")):
                raise ParityError("invalid artifact proposal digest")
            baseline = proposal["baseline_canonical_digest"]
            if baseline is not None and not self._valid_hash(baseline):
                raise ParityError("invalid artifact proposal baseline")
            if not isinstance(proposal["changed"], list) or not isinstance(proposal["current"], dict):
                raise ParityError("invalid artifact proposal changes")
            for raw, record in proposal["current"].items():
                safe_rel(raw, "proposal child")
                if not isinstance(record, dict) or set(record) != {"sha256", "mode", "data"}:
                    raise ParityError("invalid proposal file record")
                snapshot = {"exists": True, **record}
                self._validate_snapshot(snapshot, f"proposal {raw}")
            if sorted(set(proposal["changed"])) != proposal["changed"]:
                raise ParityError("proposal changed paths must be sorted and unique")
            self._assert_unique_namespace(proposal["changed"], "proposal changed paths")
            for raw in proposal["changed"]:
                safe_rel(raw, "proposal changed path")
            material = {key: proposal[key] for key in (
                "artifact", "side", "state_generation", "canonical_digest",
                "baseline_canonical_digest", "changed", "current",
            )}
            if sha(canonical_json(material))[:24] != proposal_id:
                raise ParityError("proposal id/content mismatch")
        elif proposal.get("kind") == "memory":
            fields = common | {"source", "origin", "content_sha256", "content"}
            if set(proposal) != fields or proposal.get("source") not in ("claude", "codex"):
                raise ParityError("invalid memory proposal fields")
            if not isinstance(proposal.get("content"), str) or sha(proposal["content"].encode()) != proposal.get("content_sha256"):
                raise ParityError("memory proposal hash/content mismatch")
            expected = sha((proposal["source"] + "\0" + proposal["origin"] + "\0" + proposal["content"]).encode())[:24]
            if expected != proposal_id:
                raise ParityError("memory proposal id/content mismatch")
        else:
            raise ParityError("invalid proposal kind")
        return proposal

    def _render_proposal_overlay(self, proposal: dict, origin_current: dict) -> tuple[dict[str, bytes], dict, dict[str, bytes]]:
        with tempfile.TemporaryDirectory(prefix="ai-parity-proposal-render-") as temporary:
            stage = Path(temporary).resolve()
            shutil.copytree(
                self.root / "ai-parity", stage / "ai-parity",
                ignore=shutil.ignore_patterns(
                    ".transactions", ".proposals", ".sync-lock", ".sync-journal.json",
                    ".docs-mcp-install.json", "generated-state.json", "__pycache__", "tests",
                ),
            )
            shutil.copytree(self.root / "dot_claude", stage / "dot_claude")
            staged = Parity(stage)
            artifact = staged.shared[proposal["artifact"]]
            canonical = stage / safe_rel(artifact["canonical"], "staged proposal canonical")
            canonical_changes = {}
            for rel in proposal["changed"]:
                record = origin_current[rel]
                data = base64.b64decode(record["data"], validate=True)
                staged._atomic_write(canonical / safe_rel(rel, "staged proposal file"), data, int(record["mode"]))
                canonical_changes[rel] = data
            outputs, metadata = staged.expected()
            return outputs, staged.state_for(outputs, metadata), canonical_changes

    def _accept_proposal(self, proposal_path: Path, proposal: dict) -> int:
        transaction_id = uuid.uuid4().hex
        with self.lock(transaction_id, "proposal-accept") as lock_token:
            if self.journal_path.exists():
                raise ParityError("unfinished transaction exists; recover it before accepting a proposal")
            proposal_path, proposal = self._load_proposal(proposal["proposal_id"])
            artifact = self.shared.get(proposal["artifact"])
            if proposal["status"] != "applicable" or artifact is None or artifact["import_mode"] != "direct":
                raise ParityError("this proposal requires adapter/canonical review; use proposals resolve after editing")
            canonical = self.root / safe_rel(artifact["canonical"], "proposal canonical")
            if hash_tree(canonical) != proposal["canonical_digest"]:
                raise ParityError("canonical content changed since proposal creation")
            state = self.load_state()
            if state is None or state["generation_id"] != proposal["state_generation"]:
                raise ParityError("generated state changed since proposal creation")
            _, origin_target = self._shared_target(proposal["artifact"], proposal["side"])
            origin_current = self._capture_tree(self.root / safe_rel(origin_target["destination"], "proposal origin"))
            if {rel: item["sha256"] for rel, item in origin_current.items()} != {
                rel: item["sha256"] for rel, item in proposal["current"].items()
            }:
                raise ParityError("origin target changed since proposal creation")
            for output_path, record in state["outputs"].items():
                if record.get("artifact") == proposal["artifact"] and record.get("side") not in (None, proposal["side"]):
                    if self._current_hash(output_path) != record["sha256"]:
                        raise ParityError("another target changed since proposal creation")
            outputs, desired, canonical_changes = self._render_proposal_overlay(proposal, origin_current)
            unknown = self._unknown_owned_files(set(outputs))
            if unknown:
                raise ParityError(f"unowned files under generated roots: {', '.join(unknown)}")
            context = {
                "proposal_id": proposal["proposal_id"], "artifact": proposal["artifact"],
                "canonical_root": safe_rel(artifact["canonical"], "proposal canonical").as_posix(),
            }
            transaction = self._build_transaction(
                outputs, desired, "proposal-accept", transaction_id, context,
            )
            canonical_entries = []
            for rel, data in sorted(canonical_changes.items()):
                target = canonical / safe_rel(rel, "proposal canonical file")
                old = self._snapshot(target)
                new = self._new_snapshot(data, int(origin_current[rel]["mode"]))
                if not self._snapshot_matches(target, new):
                    canonical_entries.append({
                        "path": target.relative_to(self.root).as_posix(), "old": old, "new": new,
                    })
            resolved = {**proposal, "status": "resolved"}
            self._validate_proposal(resolved, proposal["proposal_id"])
            proposal_entry = {
                "path": proposal_path.relative_to(self.root).as_posix(),
                "old": self._snapshot(proposal_path),
                "new": self._new_snapshot(canonical_json(resolved), 0o600),
            }
            transaction["entries"] = canonical_entries + transaction["entries"] + [proposal_entry]
            transaction["transaction_digest"] = self._transaction_digest(transaction)
            transaction_path = self._write_transaction(transaction)
            self._rewrite_owned_lock(lock_token, transaction)
            journal = self._journal_for(transaction)
            self._atomic_write(self.journal_path, canonical_json(journal), 0o600)
            try:
                fail_after = int(os.environ.get("AI_PARITY_FAIL_AFTER", "0"))
                for index, entry in enumerate(transaction["entries"], start=1):
                    self._apply_snapshot(self.root / safe_rel(entry["path"], "proposal transaction path"), entry["new"])
                    if fail_after and index == fail_after:
                        raise ParityError(f"injected failure after mutation {index}")
                for entry in transaction["entries"]:
                    if not self._snapshot_matches(
                        self.root / safe_rel(entry["path"], "proposal transaction verification"), entry["new"]
                    ):
                        raise ParityError(f"post-write verification failed: {entry['path']}")
                transaction["status"] = "rendered"
                self._atomic_write(transaction_path, canonical_json(transaction), 0o600)
                if self._load_journal() != journal:
                    raise ParityError("proposal journal changed during acceptance")
                self._unlink_file(self.journal_path)
            except Exception:
                print("Proposal acceptance interrupted; journal retained for explicit recovery.", file=sys.stderr)
                raise
        return 0

    def proposal_action(self, action: str, proposal_id: str | None) -> int:
        if action == "list":
            if not self.proposals_dir.exists():
                print("No proposals.")
                return 0
            for path in sorted(self.proposals_dir.glob("*/proposal.json")):
                _, proposal = self._load_proposal(path.parent.name)
                print(f"{proposal['proposal_id']}  {proposal['status']}  {proposal.get('kind')}  {proposal.get('artifact', proposal.get('source', ''))}")
            return 0
        if proposal_id is None:
            raise ParityError(f"proposals {action} requires an id")
        path, proposal = self._load_proposal(proposal_id)
        if action == "show":
            visible = {k: v for k, v in proposal.items() if k != "current" and k != "content"}
            print(json.dumps(visible, indent=2, sort_keys=True))
            return 0
        if action == "reject":
            proposal["status"] = "rejected"
            self._validate_proposal(proposal, proposal["proposal_id"])
            self._atomic_write(path, canonical_json(proposal), 0o600)
            return 0
        if proposal.get("kind") != "artifact":
            raise ParityError("memory proposals must be promoted manually into reviewed references")
        artifact = self.shared.get(proposal["artifact"])
        if artifact is None:
            raise ParityError(f"proposal references unknown artifact: {proposal['artifact']}")
        if action == "accept":
            return self._accept_proposal(path, proposal)
        if action == "resolve":
            if self.problems():
                raise ParityError("parity must verify before resolving a review proposal")
            proposal["status"] = "resolved"
            self._validate_proposal(proposal, proposal["proposal_id"])
            self._atomic_write(path, canonical_json(proposal), 0o600)
            return 0
        raise ParityError(f"unknown proposal action: {action}")

    def scan_memories(self, source: str, project: str | None) -> int:
        candidates: list[tuple[str, str]] = []
        if source == "claude":
            claude_home = Path(os.environ.get("AI_PARITY_CLAUDE_HOME", str(Path.home() / ".claude")))
            if not project:
                raise ParityError("Claude memory scanning requires --project")
            supplied = Path(project).expanduser()
            if supplied.exists():
                memory_dirs = [supplied / "memory" if supplied.name != "memory" else supplied]
            else:
                memory_dirs = [p / "memory" for p in (claude_home / "projects").iterdir() if project in p.name]
            memory_dirs = [p for p in memory_dirs if p.is_dir()]
            if len(memory_dirs) != 1:
                raise ParityError(f"expected one Claude project memory directory, found {len(memory_dirs)}")
            for path in sorted(memory_dirs[0].glob("*.md")):
                candidates.append((str(path), path.read_text(encoding="utf-8")))
        else:
            codex_home = Path(os.environ.get("AI_PARITY_CODEX_HOME", str(Path.home() / ".codex")))
            database = codex_home / "memories_1.sqlite"
            uri = f"file:{database.as_posix()}?mode=ro&immutable=1"
            try:
                with contextlib.closing(sqlite3.connect(uri, uri=True)) as connection:
                    rows = connection.execute("SELECT thread_id, raw_memory FROM stage1_outputs ORDER BY source_updated_at, thread_id").fetchall()
            except sqlite3.Error as exc:
                raise ParityError(f"cannot read Codex memories: {exc}") from exc
            candidates.extend((f"codex:{thread_id}", raw) for thread_id, raw in rows)
        created = 0
        for origin, content in candidates:
            proposal_id = sha((source + "\0" + origin + "\0" + content).encode())[:24]
            path = self.proposals_dir / proposal_id / "proposal.json"
            if path.exists():
                continue
            proposal = {
                "format": "ai-parity-proposal", "schema_version": 3,
                "proposal_id": proposal_id, "kind": "memory",
                "status": "review_required", "source": source, "origin": origin,
                "content_sha256": sha(content.encode()), "content": content,
            }
            self._validate_proposal(proposal, proposal_id)
            self._atomic_write(path, canonical_json(proposal), 0o600)
            created += 1
        print(f"Created {created} local memory proposal(s); raw memories were not synchronized.")
        return 0

    def docs(self, action: str) -> int:
        expected_url = "https://developers.openai.com/mcp"
        result = subprocess.run(
            ["codex", "mcp", "get", "openaiDeveloperDocs", "--json"],
            cwd=self.root, text=True, capture_output=True,
        )
        configured = None
        if result.returncode == 0:
            try:
                configured = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise ParityError("Codex returned invalid MCP configuration JSON") from exc
        def contains_url(value: object) -> bool:
            if isinstance(value, str):
                return value == expected_url
            if isinstance(value, dict):
                return any(contains_url(v) for v in value.values())
            if isinstance(value, list):
                return any(contains_url(v) for v in value)
            return False
        exact = configured is not None and contains_url(configured)
        if action == "status":
            if exact:
                print("OpenAI developer documentation MCP is configured.")
                return 0
            if configured is not None:
                print("openaiDeveloperDocs exists with a different configuration.")
                return 1
            print("OpenAI developer documentation MCP is not configured.")
            return 1
        if action == "install":
            if configured is not None and not exact:
                raise ParityError("refusing to overwrite differently configured openaiDeveloperDocs")
            if configured is None:
                added = subprocess.run([
                    "codex", "mcp", "add", "openaiDeveloperDocs", "--url", expected_url,
                ], cwd=self.root)
                if added.returncode:
                    raise ParityError("codex mcp add failed")
            marker = {
                "format": "ai-parity-docs-marker", "schema_version": 2,
                "name": "openaiDeveloperDocs", "url": expected_url, "host": socket.gethostname(),
            }
            self.schemas.validate(marker, "docs-marker", 2)
            self._atomic_write(self.docs_marker, canonical_json(marker), 0o600)
            print("Documentation MCP configured. Restart Codex or start a new session.")
            return 0
        if action == "remove":
            if not self.docs_marker.exists():
                raise ParityError("refusing removal: no machine-local ai-parity ownership marker")
            try:
                marker = json.loads(self.docs_marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ParityError(f"invalid documentation ownership marker: {exc}") from exc
            if marker.get("schema_version") == 2:
                self.schemas.validate(marker, "docs-marker", 2)
            elif marker.get("schema_version") != 1 or set(marker) != {"schema_version", "name", "url", "host"}:
                raise ParityError("unsupported documentation ownership marker")
            else:
                self.schemas.validate(marker, "docs-marker", 1)
            if marker.get("url") != expected_url or not exact:
                raise ParityError("refusing removal: MCP configuration no longer matches the owned installation")
            removed = subprocess.run(["codex", "mcp", "remove", "openaiDeveloperDocs"], cwd=self.root)
            if removed.returncode:
                raise ParityError("codex mcp remove failed")
            self._unlink_file(self.docs_marker)
            print("Documentation MCP removed.")
            return 0
        raise ParityError(f"unknown docs action: {action}")

    def transaction_gc(self) -> int:
        if not self.transactions_dir.exists():
            print("No transaction backups.")
            return 0
        with self.lock(uuid.uuid4().hex, "transaction-gc"):
            if self.journal_path.exists():
                raise ParityError("transaction backups retained while a recovery journal exists")
            head = git(self.root, "show", "HEAD:ai-parity/generated-state.json")
            if head.returncode:
                print("No committed generated state; transaction backups retained.")
                return 0
            try:
                committed_state = json.loads(head.stdout)
                if committed_state.get("schema_version") == 3:
                    self.schemas.validate(committed_state, "generated-state", 3)
                elif committed_state.get("schema_version") not in (1, 2):
                    raise ParityError("unsupported committed generated state")
                committed_generation = committed_state["generation_id"]
                current_generation = self.load_state()["generation_id"]
            except (KeyError, TypeError, json.JSONDecodeError):
                raise ParityError("cannot compare committed generated state")
            removed = 0
            if committed_generation == current_generation:
                for path in self.transactions_dir.glob("*/transaction.json"):
                    transaction_id = path.parent.name
                    try:
                        _, transaction = self._load_transaction(transaction_id)
                    except ParityError:
                        print(f"Retained legacy or invalid transaction backup {transaction_id}.")
                        continue
                    if transaction["status"] in ("rendered", "rolled_back"):
                        self._assert_mutation_path(path)
                        shutil.rmtree(path.parent)
                        removed += 1
        print(f"Removed {removed} committed transaction backup(s).")
        return 0

    def reconcile_after_merge(self) -> int:
        unresolved_result = git(self.root, "diff", "--name-only", "--diff-filter=U")
        if unresolved_result.returncode:
            raise ParityError(unresolved_result.stderr.strip())
        unresolved = {line for line in unresolved_result.stdout.splitlines() if line}
        if not unresolved:
            print("No unresolved Git merge paths.")
            return 0
        if "ai-parity/manifest.toml" in unresolved or any(path.startswith("ai-parity/shared/") for path in unresolved):
            raise ParityError("resolve canonical and manifest conflicts before reconciling derived outputs")
        outputs, metadata = self.expected()
        desired = self.state_for(outputs, metadata)
        allowed = set(outputs) | {self.state_path.relative_to(self.root).as_posix()}
        unexpected = sorted(unresolved - allowed)
        if unexpected:
            raise ParityError("non-derived merge conflicts require manual resolution: " + ", ".join(unexpected))
        transaction_id = uuid.uuid4().hex
        with self.lock(transaction_id, "reconcile-after-merge") as lock_token:
            if self.journal_path.exists():
                raise ParityError("unfinished transaction exists; reconcile cannot replace its journal")
            transaction = self._build_transaction(
                outputs, desired, "reconcile-after-merge", transaction_id,
            )
            entries = transaction["entries"]
            if not entries:
                print("Derived merge paths already match expected outputs.")
                return 0
            transaction_path = self._write_transaction(transaction)
            self._rewrite_owned_lock(lock_token, transaction)
            self._atomic_write(self.journal_path, canonical_json(self._journal_for(transaction)), 0o600)
            for entry in entries:
                self._apply_snapshot(self.root / safe_rel(entry["path"], "reconcile path"), entry["new"])
            transaction["status"] = "rendered"
            self._atomic_write(transaction_path, canonical_json(transaction), 0o600)
            self._unlink_file(self.journal_path)
        print("Regenerated derived merge paths. Review and stage them explicitly.")
        return 0

    def _atomic_write(self, path: Path, data: bytes, mode: int = 0o644) -> None:
        self._assert_mutation_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.proposals_dir in path.parents or self.transactions_dir in path.parents:
            with contextlib.suppress(OSError):
                os.chmod(path.parent, 0o700)
        if path.is_symlink():
            raise ParityError(f"refusing to replace symlink: {path}")
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, mode)
            os.replace(temporary, path)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary)

    def sync(self, write: bool, recover: bool = False) -> int:
        if not write:
            print("Dry run: no files will be changed.")
            return self.show_diff()
        if recover:
            raise ParityError("use `dots ai repair <transaction> --finish|--rollback`")
        transaction_id = uuid.uuid4().hex
        with self.lock(transaction_id, "sync") as lock_token:
            reviews = self.review_status()
            stale_reviews = [(name, current) for name, acknowledged, current in reviews if acknowledged != current]
            if stale_reviews:
                details = ", ".join(f"{name}={digest}" for name, digest in stale_reviews)
                raise ParityError(f"review acknowledgement required: {details}")
            protected_before = self._protected_digest()
            outputs, metadata = self.expected()
            unknown = self._unknown_owned_files(set(outputs))
            if unknown:
                raise ParityError(f"unowned files under generated roots: {', '.join(unknown)}")
            desired = self.state_for(outputs, metadata)
            old = self.load_state()
            old_records = old.get("outputs", {}) if old else {}
            if self.journal_path.exists():
                raise ParityError("unfinished transaction exists; run `dots ai doctor`")
            for rel, record in old_records.items():
                current = self._current_hash(rel)
                desired_hash = sha(outputs[rel]) if rel in outputs else None
                if current is not None and current not in (record["sha256"], desired_hash):
                    raise ParityError(f"manual edit to generated file: {rel}; create an import proposal")
            for rel, data in outputs.items():
                if rel not in old_records and self._current_hash(rel) not in (None, sha(data)):
                    raise ParityError(f"unowned destination already exists: {rel}")
            transaction = self._build_transaction(outputs, desired, "sync", transaction_id)
            if not transaction["entries"]:
                print(f"AI parity already synchronized ({len(outputs)} generated files).")
                return 0
            transaction_path = self._write_transaction(transaction)
            self._rewrite_owned_lock(lock_token, transaction)
            self._atomic_write(self.journal_path, canonical_json(self._journal_for(transaction)), 0o600)
            try:
                protected_after = self._protected_digest()
                if protected_after != protected_before:
                    raise ParityError("protected Claude source changed during sync")
                fail_after = int(os.environ.get("AI_PARITY_FAIL_AFTER", "0"))
                mutation_count = 0
                for entry in transaction["entries"]:
                    self._apply_snapshot(self.root / safe_rel(entry["path"], "transaction apply"), entry["new"])
                    mutation_count += 1
                    if fail_after and mutation_count == fail_after:
                        raise ParityError(f"injected failure after mutation {mutation_count}")
                if self._protected_digest() != protected_before:
                    raise ParityError("protected Claude source changed during output writes")
                for entry in transaction["entries"]:
                    if not self._snapshot_matches(
                        self.root / safe_rel(entry["path"], "transaction verification"), entry["new"]
                    ):
                        raise ParityError(f"post-write verification failed: {entry['path']}")
                if self._unknown_owned_files(set(outputs)):
                    raise ParityError("unowned files appeared during sync")
                transaction["status"] = "rendered"
                self._atomic_write(transaction_path, canonical_json(transaction), 0o600)
                self._unlink_file(self.journal_path)
            except Exception:
                print("Sync interrupted; journal retained for explicit recovery.", file=sys.stderr)
                raise
        print(f"Synchronized {len(outputs)} generated files (source tree only).")
        return 0


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def verify_staged(root: Path) -> int:
    staged_result = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    unstaged_result = git(root, "diff", "--name-only", "--diff-filter=ACMR")
    untracked_result = git(root, "ls-files", "--others", "--exclude-standard")
    for result in (staged_result, unstaged_result, untracked_result):
        if result.returncode:
            raise ParityError(result.stderr.strip() or "cannot inspect Git staging state")
    relevant_prefixes = ("ai-parity/", "dot_claude/", "dot_codex/", "dot_agents/", ".githooks/")
    relevant_files = {
        ".chezmoiignore", ".gitattributes", ".gitignore", ".github/workflows/test.yml",
        "dot_bashrc.tmpl", "dot_config/powershell/dots.ps1", "dot_config/zsh/scripts.zsh.tmpl",
    }
    def relevant(name: str) -> bool:
        return name in relevant_files or name.startswith(relevant_prefixes)
    staged = {x for x in staged_result.stdout.splitlines() if relevant(x)}
    remaining = {
        x for x in (unstaged_result.stdout + untracked_result.stdout).splitlines() if relevant(x)
    }
    if staged and remaining:
        raise ParityError("partial parity staging refused; remaining paths: " + ", ".join(sorted(remaining)))
    prefix_base = Path(tempfile.mkdtemp(prefix="ai-parity-index-"))
    try:
        prefix = str(prefix_base) + os.sep
        result = git(root, "checkout-index", "--all", f"--prefix={prefix}")
        if result.returncode:
            raise ParityError(result.stderr.strip() or "git checkout-index failed")
        script = prefix_base / "ai-parity/scripts/ai_parity.py"
        if not script.exists():
            raise ParityError("staged index does not contain the parity verifier")
        created = Parity(root).propose_all(prefix_base)
        if created:
            print("AI parity created staged import proposal(s): " + ", ".join(created), file=sys.stderr)
            print("Review them with `dots ai proposals list`; the commit is blocked.", file=sys.stderr)
            return 2
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([sys.executable, str(script), "--snapshot", "verify"], cwd=prefix_base, env=env).returncode
    finally:
        shutil.rmtree(prefix_base, ignore_errors=True)


def hooks(root: Path, action: str) -> int:
    configured = git(root, "config", "--local", "--get", "core.hooksPath")
    current = configured.stdout.strip() if configured.returncode == 0 else ""
    marker_result = git(root, "config", "--local", "--get", "ai-parity.hooks-installed")
    marked = marker_result.returncode == 0 and marker_result.stdout.strip() == "true"
    if action == "install":
        if current and current != ".githooks":
            raise ParityError(f"core.hooksPath is already set to {current!r}")
        if current == ".githooks" and not marked:
            raise ParityError(".githooks is already configured but is not owned by ai-parity")
        if not current:
            hook_dir_result = git(root, "rev-parse", "--git-path", "hooks")
            if hook_dir_result.returncode:
                raise ParityError(hook_dir_result.stderr.strip())
            hook_dir = Path(hook_dir_result.stdout.strip())
            if not hook_dir.is_absolute():
                hook_dir = root / hook_dir
            conflicts = [p for p in hook_dir.iterdir() if p.is_file() and not p.name.endswith(".sample")]
            if conflicts:
                raise ParityError("existing hooks would be bypassed: " + ", ".join(str(p) for p in conflicts))
            result = git(root, "config", "--local", "core.hooksPath", ".githooks")
            if result.returncode:
                raise ParityError(result.stderr.strip())
            result = git(root, "config", "--local", "ai-parity.hooks-installed", "true")
            if result.returncode:
                git(root, "config", "--local", "--unset", "core.hooksPath")
                raise ParityError(result.stderr.strip())
        print("Installed repository-local AI parity hooks.")
    else:
        if current and current != ".githooks":
            raise ParityError(f"refusing to remove unrelated hooksPath {current!r}")
        if current == ".githooks" and not marked:
            raise ParityError("refusing to remove .githooks without ai-parity ownership marker")
        if current == ".githooks":
            result = git(root, "config", "--local", "--unset", "core.hooksPath")
            if result.returncode:
                raise ParityError(result.stderr.strip())
            git(root, "config", "--local", "--unset", "ai-parity.hooks-installed")
        print("Removed repository-local AI parity hooks.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="store_true", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("diff")
    sync_parser = sub.add_parser("sync")
    sync_parser.add_argument("--write", action="store_true")
    sync_parser.add_argument("--recover", action="store_true")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--staged", action="store_true")
    hooks_parser = sub.add_parser("hooks")
    hooks_parser.add_argument("action", choices=("install", "uninstall"))
    propose_parser = sub.add_parser("propose")
    propose_parser.add_argument("--from", dest="source", choices=("claude", "codex"), required=True)
    propose_parser.add_argument("artifact")
    proposals_parser = sub.add_parser("proposals")
    proposals_parser.add_argument("action", choices=("list", "show", "accept", "resolve", "reject"))
    proposals_parser.add_argument("proposal_id", nargs="?")
    memories_parser = sub.add_parser("memories")
    memories_parser.add_argument("action", choices=("scan",))
    memories_parser.add_argument("--from", dest="source", choices=("claude", "codex"), required=True)
    memories_parser.add_argument("--project")
    docs_parser = sub.add_parser("docs")
    docs_parser.add_argument("action", choices=("status", "install", "remove"))
    sub.add_parser("doctor")
    repair_parser = sub.add_parser("repair")
    repair_parser.add_argument("transaction_id")
    repair_group = repair_parser.add_mutually_exclusive_group(required=True)
    repair_group.add_argument("--finish", action="store_true")
    repair_group.add_argument("--rollback", action="store_true")
    repair_parser.add_argument("--token")
    unlock_parser = sub.add_parser("unlock")
    unlock_group = unlock_parser.add_mutually_exclusive_group(required=True)
    unlock_group.add_argument("--orphan", dest="token")
    unlock_group.add_argument("--quarantine-malformed", action="store_true")
    reconcile_parser = sub.add_parser("reconcile")
    reconcile_parser.add_argument("--after-merge", action="store_true", required=True)
    sub.add_parser("transaction-gc")
    args = parser.parse_args()
    root = Path.cwd() if args.snapshot else Path(__file__).resolve().parents[2]
    if args.command == "verify" and args.staged:
        return verify_staged(root)
    if args.command == "hooks":
        return hooks(root, args.action)
    parity = Parity(root)
    if args.command == "status" or args.command == "verify":
        return parity.show_status()
    if args.command == "diff":
        return parity.show_diff()
    if args.command == "sync":
        if args.recover and not args.write:
            raise ParityError("--recover requires --write")
        return parity.sync(args.write, args.recover)
    if args.command == "propose":
        proposal_id = parity.propose(args.artifact, args.source)
        if proposal_id:
            print(f"Created proposal {proposal_id}.")
            return 1
        print("No target changes to propose.")
        return 0
    if args.command == "proposals":
        return parity.proposal_action(args.action, args.proposal_id)
    if args.command == "memories":
        return parity.scan_memories(args.source, args.project)
    if args.command == "docs":
        return parity.docs(args.action)
    if args.command == "doctor":
        return parity.doctor()
    if args.command == "repair":
        return parity.repair(args.transaction_id, "finish" if args.finish else "rollback", args.token)
    if args.command == "unlock":
        return parity.quarantine_malformed_lock() if args.quarantine_malformed else parity.unlock_orphan(args.token)
    if args.command == "reconcile":
        return parity.reconcile_after_merge()
    if args.command == "transaction-gc":
        return parity.transaction_gc()
    raise AssertionError(args.command)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ParityError as exc:
        print(f"ai-parity: {exc}", file=sys.stderr)
        raise SystemExit(2)
