# AI Parity Ownership and Workflow Specification

## Purpose

AI parity keeps selected Claude Code and Codex configuration semantically aligned
without treating their configuration directories as interchangeable mirrors.

The system has four layers:

```text
Human-authored source
        │
        ▼
Manifest-directed rendering
        │
        ▼
Chezmoi source outputs
        │
        ▼
Applied home-directory configuration
```

The principal rule is:

> Edit canonical intent or target-specific source. Treat rendered directories as
> compiled output, except for explicitly identified legacy Claude-owned content.

Bidirectional support means that a change discovered in either rendered tool
tree can be proposed back into canonical source. It does not mean that Claude
and Codex are independent, competing sources of truth.

## Directory ownership

### Authoritative source

These paths are intentionally edited by a human:

| Path | Owner | Purpose |
|---|---|---|
| `ai-parity/shared/**` | Human | Canonical content intended for both tools |
| `ai-parity/adapters/**` | Human | Target-specific variants of shared content |
| `ai-parity/contracts/**` | Human | Standalone Codex configuration with no shared file format |
| `ai-parity/manifest.toml` | Human | Ownership, mappings, render policy, and review acknowledgements |
| `ai-parity/schemas/**` | Human-reviewed infrastructure | Immutable document contracts consumed by the engine |
| Non-migrated `dot_claude/**` | Human | Transitional Claude-owned source |

`shared/` expresses portable intent. It should not contain Claude- or
Codex-specific paths, tool names, permission syntax, or runtime state unless the
concept genuinely applies to both tools.

`adapters/` contains the differences needed to express shared intent for a
specific target. The Codex MATLAB Runner and Zotero `SKILL.md` files use Codex
paths and capability names. Zotero also keeps Codex-only `agents/openai.yaml`
interface metadata below its adapter; that metadata is rendered only to Codex.

`contracts/` contains Codex-native configuration such as `AGENTS.md`, profiles,
agent TOML, and execution rules. These files are authoritative source even
though they apply to only one tool.

The manifest is the authoritative answer to questions such as:

- Is this artifact shared, adapted, Claude-owned, Codex-owned, or merely planned?
- Which source renders which destination?
- Is reverse intake direct or review-only?
- Which Claude inputs require a reviewed digest acknowledgement?
- Which destinations inside the engine's fixed safety envelope are generated?

The manifest does not define the outer security boundary. The engine fixes
generated ownership to `dot_codex`, `dot_agents`, and exact declared shared
skill roots under `dot_claude/skills`. It also fixes every operational-state
path under `ai-parity`. A manifest change cannot redirect those writes into
another repository directory.

### Generated, checked-in source

These paths are written by the parity engine and checked into Git:

| Path | Owner | Purpose |
|---|---|---|
| `dot_codex/**` | Generator | Chezmoi source for `~/.codex/**` |
| `dot_agents/**` | Generator | Chezmoi source for `~/.agents/**` |
| Migrated portions of `dot_claude/**` | Generator | Chezmoi source for shared Claude artifacts |
| `ai-parity/generated-state.json` | Generator | Non-secret generation and ownership ledger |

Currently, these Claude skill roots are migrated and generated:

```text
dot_claude/skills/matlab/**
dot_claude/skills/matlab-runner/**
dot_claude/skills/zotero/**
dot_claude/skills/pdf-chunk/**
dot_claude/skills/llm-pdf-processing/**
dot_claude/skills/scientific-figures/**
```

Other Claude skills remain human-owned until the manifest explicitly migrates
them. This makes `dot_claude/**` a transitional mixed-ownership tree. Do not infer
ownership from the top-level directory alone; consult `[[shared_artifacts]]` and
the skill classification in the manifest.

Generated files should not normally be edited directly. If a useful change is
made there, import it through a proposal instead of treating that rendered file
as a new source of truth.

### Local operational state

These paths are ignored by Git and chezmoi:

| Path | Owner | Purpose |
|---|---|---|
| `ai-parity/.proposals/**` | Parity runtime | Local import and memory-review proposals |
| `ai-parity/.transactions/**` | Parity runtime | Old/new bytes used for finish and rollback |
| `ai-parity/.sync-lock` | Parity runtime | Exclusive write ownership |
| `ai-parity/.sync-journal.json` | Parity runtime | Active transaction pointer |
| `ai-parity/.docs-mcp-install.json` | Parity runtime | Machine-local documentation MCP ownership marker |

This state is deliberately local. Proposals may contain raw memory content, and
transactions may contain previous file versions. Neither belongs in Git or in a
home-directory deployment.

### Schema and state contracts

Every persisted document kind has an independent format identifier and version.
New documents are written as manifest 3, generated state 3, transaction 3,
journal 3, lock 3, proposal 3, and documentation marker 2. Compatibility
readers accept generated state 2, both transaction/journal/lock 2 layouts,
proposal 2, and documentation marker 1 where recovery or safe ownership checks
require them.

The engine selects schemas from a fixed local registry. Documents cannot choose
their own validator, remote references are forbidden, and hooks do not download
a validation dependency. Every normal read is shape-validated and then checked
semantically. Semantic checks include:

- normalized path containment and symlink ancestry;
- NFC and case-fold uniqueness;
- decoded chezmoi target uniqueness;
- strict base64 decoding and content-hash equality;
- old/new snapshot and mode consistency;
- proposal and transaction content-derived identifiers;
- exact journal, lock, generation, operation, and transaction relationships;
- manifest-derived write authority.

Schemas are infrastructure policy rather than another user workflow. There is
no standalone schema command, and users never edit operational state to make it
validate. Changing a contract creates a new immutable schema version and a
reader/migration policy.

| Document | Current write | Compatible reads | Upgrade behavior |
|---|---:|---:|---|
| Manifest | 3 | 3 | Human-authored and changed with the engine |
| Generated state | 3 | 2, 3 | Regenerated transactionally |
| Transaction | 3 | 2, 3 | Active v2 evidence remains in its original form |
| Journal | 3 | 2, 3 | Bound to its transaction before recovery |
| Lock | 3 | 2, 3 | Legacy locks require the same explicit takeover rules |
| Proposal | 3 | 2, 3 | Status writes preserve the loaded proposal version |
| Documentation marker | 2 | 1, 2 | Removal still requires exact external configuration |

## State preservation and recovery model

“State” has several meanings in this system. They are deliberately separated so
that losing or corrupting one ledger cannot silently redefine source ownership.

| State class | Examples | Preservation mechanism | Authority |
|---|---|---|---|
| Human-authored intent | `shared/**`, `adapters/**`, `contracts/**`, `manifest.toml` | Tracked in Git | Primary source of truth |
| Generated source and ledger | `dot_codex/**`, `dot_agents/**`, migrated `dot_claude/**`, `generated-state.json` | Deterministic rendering and Git | Evidence of the last reviewed generation |
| Active recovery evidence | Journal, lock, transaction snapshots | Local ignored files with restricted permissions | May finish or roll back only its bound transaction |
| Review intake | Proposals | Local ignored files with restricted permissions | Evidence awaiting a human decision |
| Applied tool runtime | `~/.claude`, `~/.codex`, `~/.agents` | Managed separately by chezmoi and the tools | Consumer state, never parity authority |

The authority order is:

```text
fixed engine safety envelope
        ▼
immutable schema + semantic invariants
        ▼
human manifest and canonical source
        ▼
freshly derived expected outputs
        ▼
generated state and transaction records as evidence only
```

Neither `generated-state.json` nor an ignored transaction may grant permission
to write a path outside the engine safety envelope and current manifest-owned
roots. Generated state never authorizes deletion. If an old output is no longer
declared, the engine reports it and requires explicit human removal before the
ledger forgets it.

### Normal synchronization timeline

A mutating synchronization follows this sequence:

```text
acquire exclusive lock
        ▼
validate manifest, schemas, reviews, inputs, outputs, and current ledger
        ▼
capture complete old/new bytes, hashes, and modes in transaction.json
        ▼
bind lock + journal + transaction id + generation + operation + digest
        ▼
write the active journal
        ▼
write declared outputs, then generated-state.json
        ▼
re-read and verify every resulting snapshot and the unknown-file inventory
        ▼
mark transaction rendered
        ▼
remove only the matching journal, then release only the matching lock
```

The transaction is written before the journal, and the journal is written
before the first managed mutation. Each file replacement uses a temporary file
in the destination directory, flushes and `fsync`s its contents, applies the
recorded mode, and atomically replaces the destination. A transaction stores
the complete previous and intended bytes rather than only a reverse patch, so
finish and rollback do not depend on reconstructing an intermediate diff.

Before recovery changes anything, all transaction snapshots are structurally
and semantically validated. Every current file must match either its recorded
old snapshot or its intended new snapshot, including mode on Unix. Recovery
then rechecks each file immediately before replacing it. A manual “third state”
matching neither side stops recovery without overwriting that file.

### Transactional proposal acceptance

Direct proposal acceptance uses the same state machine with operation
`proposal-accept`. The engine renders the proposed canonical tree in a temporary
repository first. It then records one transaction containing:

1. the affected canonical files;
2. all changed Claude and Codex rendered outputs;
3. `generated-state.json`; and
4. the proposal record changing to `resolved`.

The proposal bytes used for canonical changes are reconstructed from the still-
current origin target and checked against the proposal hashes. They are not
trusted merely because they were stored in the proposal. A crash at any write
boundary leaves the journal active, and `repair --finish` or `--rollback`
completes the whole set consistently.

### What survives a crash

The active journal is the sole pointer to executable recovery authority. It
must match the selected transaction’s id, generation, operation, and content
digest. A surviving lock must additionally match the transaction and explicit
token; a same-host lock cannot be reclaimed while its PID is alive. Repair takes
a new exclusive lock, preventing two repairs or a repair and synchronization
from interleaving.

If the process exits after some files are replaced, the journal and complete
transaction snapshots remain. If it exits after the transaction is marked
rendered but before journal removal, the unchanged transaction content digest
still binds that journal, so finish or rollback remains available. Garbage
collection refuses to run while any journal exists and never removes the
transaction referenced by active recovery.

Successful and rolled-back transaction directories are retained until Git
`HEAD` contains the same generated-state generation. The post-commit hook then
invokes guarded garbage collection. Legacy, malformed, or unrecognized backups
are retained rather than guessed at or deleted.

### Upgrade and branch behavior

New writes use transaction, journal, and lock version 3. The current engine has
explicit readers for both original and digest-bound version-2 recovery records.
An active v2 transaction is interpreted in memory and written back in its
original format if its status changes; recovery never migrates the only rollback
evidence in place.

The pre-merge-commit and pre-rebase hooks refuse those operations while a
journal is active. Git has no standard pre-checkout hook, so post-checkout warns
immediately; the forward-compatible reader is what preserves an older active
transaction across an upgrade checkout. Downgrading to an older engine that
predates a newer state format is not guaranteed.

### Missing, stale, or damaged state

- If `generated-state.json` is missing but every generated output already
  matches freshly derived content, `sync --write` recreates the ledger inside a
  normal transaction without rewriting unrelated files.
- If the ledger is stale, synchronization derives the desired state from
  canonical inputs and replaces it transactionally.
- If the checked-in ledger is malformed, validation fails closed. Restore its
  reviewed Git version first; do not hand-edit hashes to make it pass.
- If an active journal or transaction is malformed, automatic recovery refuses
  to mutate files and preserves the evidence for inspection.
- If ignored transactions and proposals are lost, current configuration can be
  regenerated from Git, but local rollback history and unreviewed proposal
  content cannot be reconstructed.

### Scope of the guarantee

Recovery evidence is local to one checkout. Git preserves canonical source,
schemas, generated outputs, and the generated ledger across machines; it does
not transfer transactions, journals, locks, or raw proposals. This avoids
committing old file contents or private memory proposals, but it means an
interrupted checkout must be recovered on the machine where it occurred.

The atomic replacement protocol protects against process interruption and most
ordinary crashes. File contents are `fsync`ed, but parent-directory entries are
not explicitly `fsync`ed after every replace or unlink. The system therefore
does not claim database-grade durability against sudden power loss at an exact
filesystem metadata boundary. In that rare case, snapshot validation still
fails closed on any mixed or third state.

Finally, parity synchronization preserves only the chezmoi source repository.
It never applies the result to the real home directory. Home deployment remains
the separate, explicit `chezmoi diff` and `chezmoi apply` review boundary.

### Applied runtime state

Chezmoi deploys the checked-in output trees as follows:

```text
dot_claude/**  ──► ~/.claude/**
dot_codex/**   ──► ~/.codex/**
dot_agents/**  ──► ~/.agents/**
```

The deployed home directories are runtime consumers, not parity source. Codex
and Claude may create sessions, caches, system skills, identities, databases,
and memories there. Those runtime files must never be copied into the chezmoi
source tree.

## Propagation directions

### Canonical shared artifact

The normal path for a shared artifact is one-to-many:

```text
ai-parity/shared/skills/matlab
                 │
                 ▼
          parity renderer
            ┌────┴────┐
            ▼         ▼
  dot_claude/skills  dot_agents/skills
       /matlab            /matlab
```

Both rendered targets are generator-owned. Human changes begin in `shared/` and
flow outward.

### Shared artifact with an adapter

When a target needs different wording or structure:

```text
Canonical shared content ───────────────► Claude output
          │
          └──► Codex adapter ───────────► Codex output
```

The adapter is human-authored source. The final target is still generated.

MATLAB Runner and Zotero currently use complete Codex `SKILL.md` overrides.
Consequently, a general change to either canonical Claude-compatible `SKILL.md`
must also be reviewed against its Codex adapter. Their bundled scripts remain
shared byte-for-byte. Zotero's Codex-only `agents/openai.yaml` is a separate
manifest artifact because it has no Claude counterpart.

### Codex-only contract

Codex-native configuration follows a one-way path:

```text
ai-parity/contracts/** ──► dot_codex/** ──► ~/.codex/**
```

Contracts may be semantically reviewed against Claude configuration, but there
is no requirement that both tools consume the same file or syntax.

### Legacy Claude-owned artifact

Until migrated, a Claude skill remains the source:

```text
dot_claude/skills/NAME
             │
             ├──► Claude deployment
             └──► optional Codex copy or adapter
```

Some legacy artifacts have a Codex mapping; others are classified as `planned`
and remain Claude-only. Migration to `shared/` is explicit and per artifact.

### Change originating in rendered output

Rendered changes travel inward only through review:

```text
Rendered Claude or Codex edit
             │
             ▼
        local proposal
             │
       ┌─────┴─────┐
       ▼           ▼
 direct accept   manual adapter review
       │           │
       └─────┬─────┘
             ▼
      canonical source
             │
             ▼
       render both sides
```

A direct proposal is acceptable only when:

- The artifact is declared `import_mode = "direct"`.
- Canonical content has not changed since the last render.
- The other rendered target has not changed.
- The proposal does not infer a deletion.
- The origin target still matches the proposal snapshot.

Otherwise, the proposal is review-only. The system never automatically merges
two independently changed targets.

### Memory intake

Runtime memories flow only into local review proposals:

```text
Claude project memory ─┐
                      ├──► local proposal ──► optional curated shared reference
Codex memory database ─┘
```

Raw memory is never rendered into the other tool, checked into Git, or managed
by chezmoi. Promotion requires human curation.

## Expected workflows

### Modify a direct-shared skill

For MATLAB:

```sh
$EDITOR ai-parity/shared/skills/matlab/SKILL.md
dots ai diff
dots ai sync --write
dots ai verify
chezmoi diff
```

Run `chezmoi apply` only after reviewing the deployment diff.

### Modify an adapted skill

For MATLAB Runner or Zotero, edit canonical content and the Codex adapter when
relevant:

```sh
$EDITOR ai-parity/shared/skills/matlab-runner/SKILL.md
$EDITOR ai-parity/adapters/skills/matlab-runner/SKILL.md
# Zotero follows the same pattern under shared/skills/zotero and
# adapters/skills/zotero.
dots ai diff
dots ai sync --write
dots ai verify
```

If only a bundled script changes, edit the shared script. If paths, tool names,
or Codex-specific behavior change, review the adapter explicitly. Zotero is
review-only for reverse intake, so a rendered Claude or Codex edit becomes a
proposal that must be curated into the shared source and/or adapter.

### Modify a Codex-only contract

```sh
$EDITOR ai-parity/contracts/AGENTS.md
dots ai diff
dots ai sync --write
dots ai verify
```

The generated `dot_codex/AGENTS.md` should not be edited directly.

### Modify a legacy Claude skill

```sh
$EDITOR dot_claude/skills/NAME/SKILL.md
dots ai diff
dots ai sync --write
dots ai verify
```

If the skill is `planned`, no Codex output is expected. If it has an adapter or
review acknowledgement, update that source and acknowledgement after review.

### Import an edit made in Codex or Claude output

If the edit was made in the deployed home directory (`~/.claude`, `~/.codex`,
`~/.agents`) rather than in the repository's rendered tree, first bring it into
the source repository — for example `dots add ~/.claude/skills/matlab` — and
then create the proposal. `propose` reads only the repository; home-directory
edits are otherwise invisible and will be overwritten by the next
`chezmoi apply`.

```sh
dots ai propose --from codex matlab
# or: dots ai propose --from claude matlab

dots ai proposals list
dots ai proposals show PROPOSAL_ID
dots ai proposals accept PROPOSAL_ID
dots ai verify
```

Acceptance is atomic across the canonical files, proposal status, both rendered
targets, and generated state. If interrupted, `doctor` reports a
`proposal-accept` transaction and the same `repair --finish` or `--rollback`
commands complete one side consistently.

For an adapted artifact:

```sh
dots ai propose --from codex matlab-runner
dots ai proposals show PROPOSAL_ID
# Update shared content and/or the adapter manually.
dots ai sync --write
dots ai verify
dots ai proposals resolve PROPOSAL_ID
```

Reject a proposal when the rendered edit should be discarded:

```sh
dots ai proposals reject PROPOSAL_ID
git restore -- <the edited rendered paths>
dots ai sync --write
```

Rejection records the review decision; it does not discard working-tree content
on the user's behalf.

### Curate a runtime memory

```sh
dots ai memories scan --from claude --project PROJECT_OR_MEMORY_PATH
dots ai memories scan --from codex
dots ai proposals list
dots ai proposals show PROPOSAL_ID
```

Memory proposals cannot be accepted automatically. Rewrite the useful lesson as
a concise canonical reference, synchronize, and then resolve or reject the
proposal.

### Recover an interrupted write

Start with read-only diagnosis:

```sh
dots ai doctor
```

Then explicitly choose one outcome:

```sh
dots ai repair TRANSACTION_ID --finish
dots ai repair TRANSACTION_ID --rollback
```

Repair applies only to the transaction referenced by the active journal. It
validates the journal, transaction content digest, generation, operation,
snapshot hashes, strict base64 data, paths, and modes before taking an
exclusive recovery lock. A completed archival transaction without an active
journal is not executable recovery authority.

If a lock remains, provide the exact token reported by `doctor`:

```sh
dots ai repair TRANSACTION_ID --finish --token LOCK_TOKEN
```

An orphan lock with no transaction can be removed only by exact token, and a
same-host lock is retained while its PID is still alive:

```sh
dots ai unlock --orphan LOCK_TOKEN
```

A malformed lock is preserved for inspection:

```sh
dots ai unlock --quarantine-malformed
```

Finish and rollback refuse to overwrite a third-state file that matches neither
the old nor intended transaction hash.

### Resolve a Git merge

1. Resolve `ai-parity/manifest.toml` and `ai-parity/shared/**` manually.
2. Leave derived-output conflicts for regeneration.
3. Run:

```sh
dots ai reconcile --after-merge
dots ai verify
git add <reviewed derived paths>
```

Reconciliation writes only manifest-declared derived files and never stages
them.

### Deploy

Parity generation and home-directory deployment are separate operations:

```sh
dots ai verify
chezmoi diff
chezmoi apply
```

`dots ai sync --write` changes only the chezmoi source repository. It never
applies configuration to the home directory.

CI additionally applies only the manifest-generated parity source paths into a
fresh temporary home. The harness checks chezmoi's decoded target paths before
writing, then checks the complete deployed file inventory, bytes, regular-file
types, Unix modes, `chezmoi verify`, and a second idempotent apply. It supplies a
personal-but-portable test profile so personal-gated generated skills such as
Zotero are exercised while secret-backed files remain disabled. Config, cache,
state, HOME, and XDG paths are isolated, so the harness neither reads an actual
Zotero database nor mutates the runner's real home.

## Hooks

Hooks are optional and are not installed automatically:

```sh
dots ai hooks install
```

Their responsibilities are intentionally narrow:

- `pre-commit` verifies the exact Git index when the commit stages
  parity-relevant paths; commits staging no parity-relevant path are neither
  verified nor blocked. For parity commits it creates an ignored proposal for a
  staged rendered-target edit and blocks stale or partial parity commits, and
  every refusal prints the next command (`dots ai sync --write`, or how to
  complete or split the staging).
- `post-checkout` and `post-merge` warn about drift but never synchronize.
- `pre-merge-commit` and `pre-rebase` block history changes while a recovery
  journal is active; `post-checkout` warns immediately because Git has no
  standard pre-checkout hook.
- `post-commit` removes transaction backups only after `HEAD` contains the
  matching generated state. Without installed hooks, backups accumulate; run
  `dots ai transaction-gc` periodically after committing.

Hook installation refuses to replace an existing hook configuration it does
not own. Hooks never accept proposals, stage files, run `chezmoi apply`, or
silently reclaim locks.

## Documentation MCP

The official documentation server is a machine-level Codex resource:

```sh
dots ai docs status
dots ai docs install
dots ai docs remove
```

Installation delegates to `codex mcp add` and records a local ownership marker.
Parity does not generate or replace the complete Codex `config.toml`. Removal is
allowed only when the marker exists and the configured URL still matches.

## Usability and ergonomics decisions

### Canonical-first editing

There is one preferred place to make a normal cross-tool change: `shared/`.
Bidirectional proposals exist as an escape hatch, not as an invitation to
maintain two masters.

### Dry run by default

`dots ai sync` does not write. Mutation requires `--write`. Deployment is a
separate `chezmoi apply`, creating two review boundaries.

### Task-oriented commands

Users should not need to manipulate state files manually. Commands are named
for intent: `propose`, `verify`, `doctor`, `repair`, and `reconcile`.

### Actionable failure messages

Drift reports identify the exact path. Review failures print the current digest.
Lock diagnosis reports the transaction, host, PID, and recovery token. A blocked
operation points to the next command rather than guessing a resolution.

### Safe hooks rather than magical hooks

Hooks detect, propose, warn, and clean verified backups. They do not synchronize
or deploy. This avoids surprising worktree mutations during Git operations.

### No automatic semantic merge

Claude and Codex instructions can differ meaningfully even when their Markdown
looks similar. Concurrent changes and adapted artifacts therefore require
review rather than an automatic text merge.

### Recovery remains available while blocked

An active or stale lock blocks new writes, but `status`, `diff`, `doctor`, and
proposal inspection remain usable. A lock cannot trap the user without a
diagnostic path. Inventory-classification failures likewise must not block
`doctor`, proposal inspection, or lock and journal diagnosis; they block only
generation, verification, and synchronization.

### Cross-platform filename handling

The engine rejects unsafe and case-colliding paths. Chezmoi source-name
semantics are denied by default in every canonical tree and every rendered
destination component, including single-file `copy` destinations. The denied
set covers all attribute **prefixes** — `private_`, `executable_`, `create_`,
`modify_`, `remove_`, `symlink_`, `empty_`, `exact_`, `readonly_`,
`encrypted_`, `dot_`, and the script family `run_`, `once_`, `onchange_`,
`before_`, `after_` — all attribute **suffixes** (`.tmpl`, `.age`, `.asc`,
`.literal`), and all chezmoi **special names** (any component beginning
`.chezmoi`, such as `.chezmoiignore`, `.chezmoiremove`, `.chezmoitemplates`,
`.chezmoiscripts`). Script prefixes are denied because chezmoi executes `run_`
sources found anywhere in the source tree; `.tmpl` is denied because chezmoi
template-executes it; special names are denied because chezmoi interprets them
in the directory in which they appear. Only `literal_` is admitted, and only
through an exact manifest `chezmoi_mappings` entry whose value equals the
decoded target.
MATLAB Runner declares `literal_run_matlab.sh` mapping to `run_matlab.sh`.
PDF Chunk similarly declares `literal_pdf_stats.py` and
`literal_extract_pages.py`, which chezmoi decodes to ordinary `0644` Python
files. The skills invoke them with `uv run`; executable source attributes are
neither required nor admitted.
Identifiers and source paths must be NFC-normalized and unique after case
folding. Generated source paths must also remain unique after chezmoi decodes
literal attributes. Generated state records both the expected source and
deployed mode; the isolated harness checks `0644` on Unix and regular-file type
on every platform.

### Runtime privacy

Codex databases and Claude project memories are read only for explicit scans.
Memory scans copy the Codex database (with any `-wal`/`-shm` sidecars) to a
private temporary location and read the copy; the live database is never
opened while Codex may be writing it. Raw content stays in ignored,
permission-restricted proposals and is never silently promoted.

The Zotero skill deploys only when chezmoi data sets `personal = true`. Its
script reads `~/Zotero/zotero.sqlite` only when explicitly invoked, copies the
database to a uniquely named temporary file, opens the copy read-only, and
deletes it in `finally`. Tests use a synthetic SQLite fixture and an isolated
temporary directory; parity generation and deployment never read the library.

### PDF ownership and backend policy

`pdf-chunk` and `llm-pdf-processing` are user-owned shared artifacts with
review-only reverse intake. Their canonical content is under `shared/skills`;
the Codex-specific `pdf-chunk` instruction file and OpenAI interface metadata
are adapters. The Codex-only `pdf` skill is independently authored under
`adapters/skills/pdf`.

The existing `dot_claude/skills/pdf` tree is protected, proprietary legacy
content. It is not a canonical input, adapter input, generated destination, or
review source. Preservation is checked with Git diff and tracked-file modes;
the parity manifest cannot grant itself authority over that directory.

The runtime backend order is local and deterministic: metadata prefers
`pdfinfo`; extraction tries LiteParse without OCR, Poppler `pdftotext`, then
Python; OCR tries local LiteParse, then `pdftoppm` plus Tesseract; transforms
prefer qpdf and otherwise use Python. A selected backend failure is explicit.
No package manager entry, silent installer, remote OCR endpoint, or automatic
document upload is part of synchronization or deployment.

## Invariants

The implementation must preserve these rules:

1. No undeclared file may be written or deleted.
2. Unknown files under generated roots fail closed and are never deleted.
3. Non-migrated Claude content remains protected.
4. Generated state contains hashes and metadata, not secrets or raw memories.
5. Transactions are prepared before mutations; generated state follows rendered
   outputs, and proposal status follows generated state during proposal intake.
6. Recovery overwrites only recorded old or intended content.
7. Hooks never synchronize, deploy, accept proposals, or stage files.
8. Raw runtime memories never become direct synchronization inputs.
9. `chezmoi apply` remains an explicit user action.
10. Direct reverse import is allowed only for declared direct-shared artifacts.
11. Generated state is evidence only and can never schedule deletion; obsolete
    files require explicit human removal.
12. Recovery may remove only the journal and lock that match its transaction.
13. Adapter overrides remain below `ai-parity/adapters` and every override must
    name an existing canonical child.
14. Codex credentials, identity, SQLite state, history, sessions, logs,
    snapshots, caches, memories, goals, packages, plugins, the top-level
    `config.toml`, and system-managed skills are forbidden generated
    destinations and ignored deployment sources.
15. Direct proposal acceptance changes canonical source, rendered outputs,
    proposal status, and generated state in one recoverable transaction.
16. Every current state document passes its local structural schema and
    code-level semantic validation before it can authorize a mutation.

## Current limitations and future simplification

- The repository is transitional: MATLAB, MATLAB Runner, Scientific Figures,
  Zotero, PDF Chunk, and LLM PDF Processing are canonical; most Claude skills
  remain legacy-owned.
- MATLAB Runner, Zotero, and PDF Chunk use full Codex `SKILL.md` overrides, so general
  documentation changes must be reviewed in two files per adapted skill.
- The parity engine is currently monolithic. Splitting manifest, rendering,
  proposal, transaction, and CLI modules would improve maintainability.
- Transactions store complete bytes. Large binary-heavy skills may eventually
  need a content-addressed backup store.
- Proposals are local and are not transferred between machines through Git.
- Documentation MCP installation and home deployment remain explicit machine
  operations rather than automatic convergence.
- The offline validator intentionally implements only the JSON Schema keywords
  used by the checked-in contracts. Adding a new keyword requires validator and
  negative-fixture coverage in the same change.

The directory layout may eventually be simplified from separate `adapters/` and
`contracts/` trees to target-oriented source trees:

```text
ai-parity/
├── shared/
├── targets/
│   ├── claude/
│   └── codex/
└── manifest.toml
```

That physical simplification would not change the ownership model. Shared
intent, target-specific source, declarative wiring, generated chezmoi outputs,
and runtime state must remain distinct.

## Quick decision guide

```text
What are you changing?

Shared behavior used by both tools?
  -> Edit ai-parity/shared/**

Codex- or Claude-specific expression of shared behavior?
  -> Edit ai-parity/adapters/**

Standalone Codex configuration?
  -> Edit ai-parity/contracts/**

Legacy Claude skill not yet migrated?
  -> Edit dot_claude/skills/NAME/**

Useful edit already made in generated output?
  -> Create a proposal; do not make that output authoritative

Runtime memory worth retaining?
  -> Scan into a local proposal and curate it manually

Interrupted or conflicted write?
  -> Diagnose first, then explicitly finish, rollback, or reconcile
```
