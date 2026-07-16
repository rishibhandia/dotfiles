# ai-parity: Annotated Code Walkthrough

An annotated tour of the Claude ↔ Codex parity system. Written against commit
`897e14f` (2026-07-16); line numbers refer to that revision and will drift as
files change. The normative documents are [`ai-parity/SPEC.md`](../ai-parity/SPEC.md)
(full spec, 16 invariants) and [`ai-parity/README.md`](../ai-parity/README.md)
(operator's guide) — this walkthrough explains *how the code implements them*.

## One-sentence mental model

A deterministic, transactional generator (`ai-parity/scripts/ai_parity.py`,
~1990 lines, stdlib-only, run via `uv run --script`, wrapped as `dots ai`)
renders human-authored source into checked-in chezmoi source trees, records a
hash ledger, and gates every mutation behind a fixed safety envelope, schema
validation, review acknowledgements, and a crash-recoverable
lock/journal/transaction machine. It only ever writes the chezmoi *source*
repo — `chezmoi apply` to `$HOME` remains a separate human step.

## Data flow

```
ai-parity/shared/skills/<name>/     (canonical, both tools)
ai-parity/adapters/**               (tool-specific overrides / Codex-only skills)
ai-parity/contracts/**              (Codex-native config)
dot_claude/skills/{gemini-billing-blocks,learned}   (Claude-owned, also rendered)
        │
        │  dots ai sync --write        (transactional; source tree only)
        ▼
dot_claude/skills/<migrated>/       ┐
dot_agents/skills/**                ├─ generated chezmoi source (never hand-edit)
dot_codex/**                        ┘
        │
        │  chezmoi apply              (separate, explicit, human)
        ▼
~/.claude/skills/**   ~/.agents/skills/**   ~/.codex/**
```

Reverse direction: an edit found in a rendered target is **intake**, not
authority — `dots ai propose --from claude|codex NAME` turns it into a
reviewable proposal; it never overwrites the other tool directly.

## Directory map and ownership tiers

| Path | Tier | Rule |
|---|---|---|
| `ai-parity/shared/**` | human-authored | canonical cross-tool content — the default edit location |
| `ai-parity/adapters/**` | human-authored | Codex-specific SKILL.md overrides, `agents/openai.yaml` interfaces, Codex-only skills (`pdf`, `verify`, `learned-patterns`) |
| `ai-parity/contracts/**` | human-authored | Codex-native config → `dot_codex/` (AGENTS.md, profiles, agent TOML, rules) |
| `ai-parity/manifest.toml` | human-authored | ownership wiring, inventory, review digests |
| `ai-parity/schemas/**` | human-authored | 13 closed JSON schemas; hashed into the generation digest |
| `dot_codex/**`, `dot_agents/**` | **generated** | never hand-edit |
| `dot_claude/skills/{matlab,matlab-runner,zotero,pdf-chunk,llm-pdf-processing,scientific-figures}` | **generated** | migrated roots; edit the canonical source instead |
| `ai-parity/generated-state.json` | generated evidence | hash ledger; grants no authority |
| `.proposals/ .transactions/ .sync-journal.json .sync-lock` | local runtime state | git- and chezmoi-ignored; never touch by hand |

Two Claude-owned trees are *inputs* rendered to Codex without being migrated:
`dot_claude/skills/gemini-billing-blocks` and `dot_claude/skills/learned`
(→ `dot_agents/skills/learned-patterns/references`).

`dot_claude/skills/pdf` is protected licensed content — never a parity input,
adapter, or destination. The Codex `pdf` skill under `adapters/skills/pdf` is
independently authored.

## The manifest (`ai-parity/manifest.toml`)

- `[policy]` — pins protected/owned roots and the six operational paths. The
  engine refuses a manifest that tries to widen these (see envelope below).
- `[[shared_artifacts]]` (6) — `matlab` and `scientific-figures` are
  `import_mode = "direct"` (reverse edits can be accepted automatically);
  `matlab-runner`, `zotero`, `pdf-chunk`, `llm-pdf-processing` are `"review"`.
  Targets are always tree-copies to `dot_claude/skills/<name>` and
  `dot_agents/skills/<name>`. `chezmoi_mappings` declares `literal_*` script
  names; `source_overrides` points a target's `SKILL.md` at an adapter file.
- `[[artifacts]]` (14) — one-way renders: the Codex contracts, the two
  Claude-owned inputs, the Codex-only skills, and five `agents/openai.yaml`
  interface files.
- `[[reviews]]` (4) — acknowledged digests for `dot_claude/CLAUDE.md`,
  `dot_claude/skills/verify/`, and the code-reviewer/debugger agents. Editing
  any of these sources stales its digest; `dots ai verify` prints the new one
  to acknowledge after reviewing the Codex counterpart.
- `[[skills]]` (35) / `[[agents]]` (11) — the inventory. **Every** top-level
  `dot_claude/skills/` dir and `dot_claude/agents/*.md` must be classified
  (`planned`, `planned-platform-gated`, `*-explicit-pilot`); unlisted or stale
  names fail generation closed.

## Engine tour (`ai-parity/scripts/ai_parity.py`)

### Safety envelope (constants, lines 30–65)

- `CHEZMOI_PREFIXES` (34) — the chezmoi attribute denylist (`dot_`, `run_`,
  `once_`, `encrypted_`, …). Any of these inside a canonical or generated tree
  would change deployment semantics (`run_*.sh` would *execute on apply*), so
  they are rejected everywhere; only `literal_` is admitted, and only with an
  explicit `chezmoi_mappings` declaration.
- `MAX_OWNED_ROOTS`/`MAX_PROTECTED_ROOTS` (40–41) and `OPERATIONAL_PATHS`
  (42–49) — the hardcoded outer boundary. `Parity.__init__` (227–233) raises
  if the manifest's policy differs, so a compromised manifest cannot move
  writes elsewhere.

### Validation primitives

- `LocalSchemaValidator` (72–150) — a minimal offline JSON-Schema subset
  (local `$refs` only). Keeps hooks dependency-free and deterministic.
- `safe_rel()` (161–173) — the central path guard: no absolute paths,
  backslashes, `..`, non-NFC, Windows-reserved names, trailing dot/space.
- `hash_tree()` (189–209) — tree digest; rejects symlinks and **fails closed
  on runtime debris** (`.DS_Store`, `__pycache__`, `.pyc`) with the cleanup
  command in the error (this bit us: test subprocesses once wrote
  `__pycache__` into the canonical tree; tests now set
  `PYTHONDONTWRITEBYTECODE=1`).
- `_forbidden_runtime_path()` (329–349) — the Codex runtime denylist:
  credentials, sqlite, sessions, memories, logs, caches, `config.toml`,
  `packages/`, `plugins/` can never be parity destinations.
- `_validate_inventory()` (293–313) — the fail-closed skills/agents inventory
  check. Deliberately gated only on generation paths, so `doctor` and
  `proposals list` stay usable while inventory is broken.

### Rendering: `expected()` (399–555)

Computes the full expected output set from scratch on every run:

1. Plain `[[artifacts]]`: source must be under an admitted input root and
   never under an owned root (no rendering output back in).
2. `[[shared_artifacts]]`: walk the canonical tree; apply `source_overrides`
   (must resolve under `ai-parity/adapters`); enforce `literal_*` ↔
   `chezmoi_mappings` agreement both ways; unused overrides/mappings are
   errors (no dead wiring).
3. Cross-checks: decoded-target collision guard (two sources can't deploy to
   the same path), every generated `.toml` must parse, every `SKILL.md` needs
   frontmatter with `name:`/`description:`. All outputs are normalized to
   mode `0644` (552–554) — scripts deploy non-executable and run via `uv run`.

### The generation digest: `state_for()` (564–589)

`generation_id = sha(engine hash + manifest hash + schemas hash + all output
records + review digests)`. Consequences worth remembering:

- **Editing the engine or a schema stales the state** — an engine commit must
  include the regenerated `generated-state.json` (run `dots ai sync --write`).
- Reviews feed the digest, so a stale review acknowledgement also blocks sync.
- `generated-state.json` is *evidence only*: it never authorizes deletion
  (`_build_transaction` 1004–1005; obsolete files are reported for manual
  removal, never auto-deleted).

### Transactions, journal, lock (733–1188)

Every mutation follows: build transaction (exact old/new byte snapshots,
base64, per-file) → write it under `.transactions/<id>/` → write journal →
apply entries → post-verify → mark `rendered` → remove journal. A crash at
any point leaves the journal for explicit recovery:

- `repair TXN --finish|--rollback` (1095–1136) — verifies every file is in
  its recorded old *or* new state first; a manual "third state" blocks
  recovery rather than being overwritten. Finish additionally refuses if the
  sources changed since the transaction (generation drift).
- Locks (804–846) are `O_CREAT|O_EXCL` with pid/host/token; takeover requires
  the exact token and a dead owner. `_pid_alive()` (770–802) is signal-free on
  Windows (ctypes `OpenProcess`, never `os.kill(pid, 0)` which sends a real
  Ctrl-C there). Malformed locks are quarantined, never deleted (1154–1169).
- `transaction-gc` (1627–1662) prunes finished transaction backups only once
  git `HEAD` contains the matching generation.

### Proposals: reverse intake (1190–1494)

`propose()` diffs a rendered target against the ledger baseline, subtracting
nested foreign-owned files (e.g. the Codex `agents/openai.yaml` inside a
shared skill). A proposal is `applicable` (auto-acceptable) only when the
artifact is direct-shared, nothing was deleted, and neither the canonical nor
the other target drifted — otherwise `review_required`. Accepting a direct
proposal (1380–1457) is one recoverable transaction spanning canonical files,
both rendered targets, the state file, and the proposal status flip; the
change is first re-rendered in a temp overlay (1357–1378) to prove it
generates cleanly before any real write.

### Sync (1722–1787) and staged verification (1794–1855)

`sync --write`, under the lock: enforce review acks → snapshot the protected
`dot_claude` digest → compute expected → fail on unknown owned files → detect
manual edits to generated files (they must go through a proposal) → apply the
transaction → re-verify the protected digest didn't change mid-write.

`verify --staged` (the pre-commit gate): if no parity-relevant path is staged,
exit 0 (non-parity commits are never taxed). Partial staging is refused with
next-step guidance. Otherwise the staged index is materialized via
`git checkout-index` **with `core.autocrlf=false -c core.eol=lf`**
(1825–1833) — byte-faithful materialization; Git for Windows' default
autocrlf once smudged CRLF into the temp tree and misreported every text
output as edited (fixed in `0643ff9`). Staged rendered-target edits become
proposals and block (exit 2); a stale ledger prints the sync remedy (exit 1).

### Git hooks (`.githooks/`, opt-in via `dots ai hooks install`)

`pre-commit` → `verify --staged`. `post-checkout`/`post-merge` → warn on
active journal or drift (read-only). `pre-merge-commit`/`pre-rebase` → abort
if a recovery journal is active. `post-commit` → best-effort
`transaction-gc`. Hooks never sync, deploy, accept, or stage.

## Command cheat sheet

| Command | What it does |
|---|---|
| `dots ai status` / `diff` | read-only drift report / unified diffs |
| `dots ai sync` | dry run (default); `--write` renders into chezmoi source only |
| `dots ai verify` | full check: schemas, digests, inventory, reviews, outputs |
| `dots ai verify --staged` | pre-commit gate over the git index |
| `dots ai propose --from claude\|codex NAME` | turn a rendered-target edit into a proposal |
| `dots ai proposals list\|show\|accept\|resolve\|reject ID` | review intake |
| `dots ai doctor` | read-only lock/journal diagnostics (works when verify fails) |
| `dots ai repair TXN --finish\|--rollback` | recover an interrupted write |
| `dots ai unlock --orphan TOKEN` / `--quarantine-malformed` | lock recovery |
| `dots ai reconcile --after-merge` | regenerate derived files after canonical merge conflicts |
| `dots ai transaction-gc` | prune finished transaction backups (HEAD must hold the generation) |
| `dots ai memories scan --from claude\|codex` | runtime memories → review proposals |
| `dots ai docs status\|install\|remove` | Codex docs MCP with ownership marker |
| `dots ai hooks install\|uninstall` | opt-in git hooks |

## Recovery playbook

1. Something failed mid-write → `dots ai doctor` (names the transaction).
2. `dots ai repair <txn> --finish` to complete, or `--rollback` to undo.
3. Stale foreign/orphan lock → `dots ai unlock --orphan <token>`; unparseable
   lock → `--quarantine-malformed`.
4. Git merge conflict in canonical/manifest → resolve those by hand, then
   `dots ai reconcile --after-merge` regenerates the derived side.
5. `status`, `diff`, `doctor`, and proposal inspection always stay available
   while a write is blocked.

## Tests (`ai-parity/tests/`, 55 tests, all CI platforms)

- `test_ai_parity.py` — 43 integration tests over a fixture copy of the repo:
  dry-run purity, idempotent sync, fail-closed inventory/unknown files,
  state-has-no-deletion-authority, fault-injected recovery
  (`AI_PARITY_FAIL_AFTER`), lock token/quarantine rules, proposal round-trips,
  staged-verify behavior, envelope/schema/path hardening (traversal, chezmoi
  names, casefold and decoded-path collisions, Windows-reserved names), and a
  signal-free pid-probe check.
- `test_chezmoi_deploy.py` — applies only generated parity sources into an
  isolated temp `$HOME` and checks the complete deployed inventory, bytes,
  modes, `chezmoi verify`, and an idempotent second apply.
- `test_pdf_bundle.py` / `test_zotero.py` — the bundled skill scripts
  (bounded PDF ops with explicit qpdf→pypdf fallback coverage; Zotero
  read-only query semantics against a synthetic fixture).

## Gotchas that actually bit (and their guards)

1. **`run_*.sh` in a skill = code execution on every `chezmoi apply`** — now
   rejected by the chezmoi-name denylist in canonical and generated trees.
2. **CRLF smudging on Windows** broke staged verification — fixed by
   byte-faithful `checkout-index`; `.gitattributes` pins LF for all generated
   text types as defense in depth.
3. **`__pycache__` in canonical trees** from test subprocesses — `hash_tree`
   fails closed with a remedy; tests set `PYTHONDONTWRITEBYTECODE=1`;
   `.chezmoiignore` blocks `**/__pycache__` from ever deploying.
4. **Engine edits stale the ledger** — always commit the regenerated
   `generated-state.json` with any `ai_parity.py`, manifest, or schema change.
5. **New skill dirs fail closed** — creating `dot_claude/skills/<new>/`
   without a `[[skills]]` manifest entry breaks sync/verify until classified.
