# AI parity state schemas

These immutable JSON Schemas are infrastructure policy, not user-managed state.
The stdlib-only parity engine selects them from a fixed local registry and
validates documents automatically during normal `status`, `sync`, proposal,
recovery, documentation, and garbage-collection operations.

There is intentionally no separate schema-validation command. Human edits go
to `manifest.toml`, `shared/`, `adapters/`, or `contracts/`; the engine owns
generated state, journals, locks, transactions, proposals, and markers.

Each document kind has an independent version. A constraint change creates a
new immutable schema file rather than silently changing an existing version.
References are local `#/$defs/...` references only; validation never fetches a
remote schema or requires a package download.

Current write versions:

| Document | Write version | Compatible read versions |
|---|---:|---:|
| Manifest | 3 | 3 |
| Generated state | 3 | 2, 3 |
| Transaction | 3 | 2, 3 |
| Journal | 3 | 2, 3 |
| Lock | 3 | 2, 3 |
| Proposal | 3 | 2, 3 |
| Documentation marker | 2 | 1, 2 |

Schema validation checks document shape. Code-level semantic checks remain
authoritative for filesystem containment, normalized/case-folded collisions,
decoded base64 hashes, transaction and journal relationships, state
transitions, and manifest-derived path authority.
