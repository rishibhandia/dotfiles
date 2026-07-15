# AI parity

For the complete ownership, propagation, recovery, and usability specification,
see [`SPEC.md`](SPEC.md).

This directory is the reviewed compatibility layer between Claude Code and
Codex. Shared artifacts live under `shared/`; target-specific adapters live
under `adapters/`. Only manifest-declared targets are generated.

Most Claude configuration remains protected. An artifact becomes
bidirectional only after it is explicitly moved to `[[shared_artifacts]]`.
Edits made in either rendered target are intake candidates, not an instruction
to overwrite the other tool.

## What you edit

- Shared Claude/Codex behavior: `shared/**`
- Tool-specific expression of shared behavior: `adapters/**`
- Codex-native configuration: `contracts/**`
- Ownership and mappings: `manifest.toml`
- Legacy Claude content not listed as shared: its existing `dot_claude/**` path

Do not edit `generated-state.json`, `.transactions`, `.proposals`, the journal,
or the lock. Their schemas are enforced automatically by the normal commands.

## Workflow

```text
Claude edit --\
               proposal -> reviewed canonical source -> Claude + Codex render
Codex edit  --/
```

```sh
dots ai status
dots ai diff
dots ai propose --from claude matlab
dots ai propose --from codex matlab
dots ai proposals list
dots ai proposals show ID
dots ai proposals accept ID
dots ai proposals resolve ID
dots ai proposals reject ID
dots ai sync                 # dry run
dots ai sync --write         # chezmoi source only; never applies it
```

Direct-share proposals may be accepted only when canonical content still
matches their baseline and no deletion was inferred. Adapted artifacts create
review-only proposals; update their canonical content or adapter, synchronize,
and then resolve the proposal.

Direct proposal acceptance is one recoverable transaction: canonical source,
both rendered targets, proposal status, and generated state either finish or
roll back together.

The pre-commit hook evaluates the Git index, writes an idempotent local proposal
for staged rendered-target edits, and blocks that commit. Proposals are ignored,
mode `0600`, and never accepted, staged, or synchronized by a hook.

## Transactions and recovery

Every write first stores exact old/new bytes and modes under the ignored
`.transactions/` directory. The generated state is written last. Successful
backups remain until Git `HEAD` contains the matching generation.

```sh
dots ai doctor
dots ai repair TRANSACTION --finish [--token LOCK_TOKEN]
dots ai repair TRANSACTION --rollback [--token LOCK_TOKEN]
dots ai unlock --orphan LOCK_TOKEN
dots ai unlock --quarantine-malformed
dots ai reconcile --after-merge
```

Finish and rollback apply only to the transaction named by the active journal.
They validate transaction identity, digest, generation, paths, modes, encoded
bytes, and old/new hashes before taking an exclusive recovery lock. A
third-state/manual edit blocks recovery without overwriting it. A live
same-host lock is never reclaimed, and foreign-host or malformed locks still
require explicit token or quarantine handling. `status`, `diff`, `doctor`, and
proposal inspection remain available while a write is blocked.

The current engine writes transaction v3 and retains readers for both earlier
transaction-v2 layouts. Old active recovery evidence is interpreted in memory
and is never migrated in place.

## Schemas

Versioned schemas live in `schemas/` and are included in the generation digest.
The engine uses a fixed local registry and a small stdlib-only validator, so
hooks remain offline and deterministic. There is no schema command to remember.
Shape validation is followed by semantic checks for hashes, path authority,
case/NFC collisions, modes, and transaction relationships.

Resolve canonical and manifest Git conflicts manually. After that,
`reconcile --after-merge` regenerates only declared derived conflicts inside a
recoverable transaction and does not stage them.

## MATLAB pilot

- `matlab` is direct-shared from `shared/skills/matlab`.
- `matlab-runner` keeps a shared launcher and Claude-compatible canonical
  content, with a concise Codex adapter under `adapters/skills/matlab-runner`.
- The initial Claude render is byte-identical to the pre-migration tree.
- `literal_run_matlab.sh` is explicitly admitted so chezmoi renders the intended
  `run_matlab.sh` target without guessing filename semantics.
- The shared MATLAB skill requires analysis and figure-building entry points to
  remain sectioned scripts with local helpers at the end, rather than monolithic
  wrapper functions.

## Scientific figures

- `scientific-figures` is direct-shared from
  `shared/skills/scientific-figures` and renders to both Claude and Codex.
- Its faithful-data rules are tool-neutral; Codex-only discovery metadata stays
  under `adapters/skills/scientific-figures`.
- Edit the canonical shared skill, not either rendered target. Direct target
  edits must return through the proposal workflow before synchronization.

## Zotero pilot

- Canonical Zotero content and the query script live in
  `shared/skills/zotero`; the Claude render remains byte-identical to the
  pre-migration skill.
- Codex gets an adapted `SKILL.md` with `~/.agents` paths plus Codex-only
  `agents/openai.yaml` interface metadata.
- The query script is shared byte-for-byte, and reverse intake is review-only
  because the two instruction files intentionally differ.
- Chezmoi deploys both Zotero skill targets only for `personal = true`. Neither
  parity synchronization nor deployment reads the Zotero database; script tests
  use a synthetic SQLite fixture and verify temporary-copy cleanup.

## PDF bundle

- `pdf-chunk` is review-shared for bounded inspection, extraction, and optional
  local OCR; `llm-pdf-processing` is review-shared for attributable multi-PDF
  analysis.
- Codex also receives an independently authored `pdf` adapter for reading,
  merging, selecting, and rotating pages. The licensed Claude `pdf` skill is
  protected legacy content and is never copied, adapted, or generated.
- LiteParse, Poppler, qpdf, and Tesseract are optional runtime backends. The
  skills detect them when present but parity never installs them or uses remote
  OCR. Pinned Python libraries run through `uv` as portable fallbacks.
- Edit shared behavior under `shared/skills/pdf-chunk` or
  `shared/skills/llm-pdf-processing`; edit Codex routing and transforms under
  `adapters/skills/pdf*`; then preview and write with `dots ai sync`.
- Chezmoi source scripts use declared `literal_*.py` names and deploy as normal
  non-executable `.py` files, invoked with `uv run`.

## Deployment proof

`test_chezmoi_deploy.py` applies only generated parity source paths into a fresh
temporary home using a personal-but-portable test profile. It verifies decoded
paths, the complete file inventory, bytes, types, Unix modes, `chezmoi verify`,
and an idempotent second apply. This exercises personal-gated Zotero outputs
without reading a database or enabling secret-backed files. The test runs on
macOS, Ubuntu, and Windows and never writes the user's real home.

## Memory proposals

```sh
dots ai memories scan --from claude --project PROJECT_OR_MEMORY_PATH
dots ai memories scan --from codex
```

Claude scanning reads one current project `memory/*.md` directory and excludes
premigration backups. Codex scanning opens `~/.codex/memories_1.sqlite` in
immutable read-only mode and reads `stage1_outputs`. Both create local review
proposals. Raw runtime memories are never mirrored or managed by chezmoi.

## Official documentation

```sh
dots ai docs status
dots ai docs install
dots ai docs remove
```

Installation uses `codex mcp add openaiDeveloperDocs --url
https://developers.openai.com/mcp` and records a machine-local ownership marker.
It never manages the complete Codex `config.toml`. Removal requires both that
marker and an exact URL match.

## Runtime limits

The stdlib-only engine runs through `uv` on macOS, Linux, native Windows, and
Git Bash. Native Windows and WSL have separate homes and therefore separate
applied configurations. Runtime-owned Codex system skills, identities, sessions,
authentication, caches, and memory databases are forbidden chezmoi sources.
The same denylist covers SQLite state, history, sessions, archived sessions,
logs, shell snapshots, goals, runtime caches, and system-managed skills.
