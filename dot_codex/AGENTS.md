# Global Codex working agreements

These are concise cross-repository defaults. Repository `AGENTS.md` files own
their exact build, lint, test, and release commands.

## Before acting

- Inspect the repository instructions and relevant source before proposing work.
- For a change request, make the smallest change that satisfies the request.
- For a review or diagnosis request, do not edit unless the user also asks for a fix.
- Preserve unrelated user changes in a dirty worktree.
- Plan before executing any change and wait for approval when the user requests a plan-first workflow.

## Secrets

- Never print secret values, private keys, tokens, passwords, or passphrases.
- Inspect secret-bearing data only through field names, presence booleans, hashes,
  or public fingerprints.
- If a secret enters model-visible output, report the exposure immediately and
  recommend rotation.
- Never hardcode credentials. Use environment variables or the repository's
  established secret manager.

## Python

- Use `uv` instead of `pip` for package operations.
- Prefer existing project environments and lockfiles.
- For standalone scripts with dependencies, use PEP 723 inline metadata and
  execute with `uv run --script`.

## Debugging

Before changing code to fix a failure:

1. Capture the exact error and reproduction command.
2. Trace the relevant execution path.
3. Rank plausible causes against evidence.
4. State the root cause and smallest proposed fix.
5. Run the narrow reproduction, then the repository's broader verification.

## Verification

- Do not claim completion without running the relevant available checks.
- Report exact commands and outcomes.
- If a required check cannot run, explain why and identify the remaining risk.
- Treat generated artifacts as incomplete until their consumer can parse or open them.

## Git and destructive operations

- Keep commits atomic when the user asks for commits.
- Never force-push, hard-reset, delete user work, or rewrite history without
  explicit authorization.
- Do not commit or push unless requested.

## Scientific visualization

- Do not mirror, symmetrize, interpolate, or invent measured data unless the
  user explicitly requests that transformation.
- Clearly distinguish measured points from derived or fitted values.

## AI parity repository

When working in the chezmoi repository:

- Treat `dot_claude/**` as read-only unless the user explicitly requests a
  Claude change or accepts a proposal for a manifest-declared shared artifact.
- Edit canonical sources (`ai-parity/shared/**`, `ai-parity/adapters/**`,
  `ai-parity/contracts/**`), never `dot_codex/**`, `dot_agents/**`, or the
  migrated `dot_claude/skills` roots — rendered trees are compiled output.
- Never create files or directories under `dot_codex/` or `dot_agents/` as a
  side effect (temp files, `tmp/` scratch dirs). Parity verification fails
  closed on any unowned file or directory under a generated root.
- New skill files must avoid chezmoi-semantic names: no `run_`, `dot_`,
  `encrypted_`, `once_`, `onchange_`, `before_`, `after_` (or other attribute)
  prefixes, no `.tmpl`/`.age`/`.asc`/`.literal` suffixes, no `.chezmoi*`
  names. A deployed file whose real name needs a reserved prefix uses a
  `literal_` source name plus a manifest `chezmoi_mappings` entry.
- A new `dot_claude/skills/<name>` directory requires a `[[skills]]` entry in
  `ai-parity/manifest.toml` (`mode = "planned"` unless reviewed for Codex);
  generation is blocked until the inventory is classified.
- Import rendered Claude/Codex edits with `dots ai propose`; canonical shared
  content is the source of truth. Edits made in the deployed home directories
  must be re-added to the repository (`dots add`) before proposing.
- Use `dots ai diff` before `dots ai sync --write`.
- Parity-relevant commits stage the complete set: canonical edits, regenerated
  outputs, and `ai-parity/generated-state.json` (run `dots ai sync --write`
  first). Partial parity staging is refused.
- `~/.codex` runtime state (`config.toml`, `packages/`, `plugins/`, sessions,
  `*.sqlite`, `.tmp/`) is never parity- or chezmoi-managed; do not propose
  managing it.
- Never synchronize AI parity from a Git or chezmoi hook.
- Run `dots ai verify` before reporting parity work complete.
- Use `dots ai doctor` and an explicit transaction finish or rollback after an
  interrupted write; never remove a lock speculatively.
