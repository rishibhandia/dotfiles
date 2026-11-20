---
name: rex-servers
description: >-
  How the user's Rex (Superlogical) terminal multiplexer is set up across their
  Macs: the server/client/host/home model, reaching one Mac's Rex from another
  over Rex's built-in Tailscale node, declaring hosts with rex.host{} in the
  chezmoi-managed init.lua, and the auto-reload on dots update. Use when adding
  or debugging a Rex remote host, "Nothing is listening at 100.x:7297", hosts not
  appearing after dots update, rex not on PATH, or ssage/ShellSage inside Rex.
  For general Rex CLI usage defer to Rex's own built-in `rex` skill.
---

# Rex — servers, remote hosts, and how the dotfiles wire it

Rex (Superlogical) is the terminal multiplexer used on the Macs. This page covers
how its server model works, how to reach one Mac's Rex from another, what chezmoi
automates, and the gotchas hit while setting it up (2026-11).

Upstream docs: <https://www.superlogical.com/rex/docs/> (also searchable from Claude Code,
Codex, and agy via the `superlogical` MCP: `search_docs`, `search_feedback`, `search_changelog`).

## Mental model

| Piece | What it is |
|---|---|
| **Rex Server** | Owns the sessions/blocks. On macOS it runs bundled inside the app (`rex.server.run-mode = bundled`), listening on a local Unix socket (`~/Library/Application Support/rex/server.sock`). |
| **Client** | The Rex Mac/iOS app, or the `rex` CLI. Connects to *a* server — local by default, remote with `-S`. |
| **Host** | A named entry for *another* Rex server (`rex hosts`), so you can say `rex -S mini …` or pick it in the app. |
| **Home** | The server a device reads its host list (and shortcuts) from. Defaults to the machine itself (`rex home`). A machine's own `init.lua` hosts always count too. |
| **Tailscale node** | Rex runs its **own** tailnet node per Mac (`<name>-rex`), separate from the OS-level Tailscale node, and serves the API over **HTTPS on :443** there. |

Scope split for config: `~/.config/rex/init.lua` (chezmoi-managed) holds keybindings,
modes, actions, event handlers, and **hosts**. Theme, font, Tailscale toggle, etc. live
in the app's Settings (`Cmd+,`) / `com.superlogical.rex.plist` and have no Lua API.

## Current machines

| Label | Rex tailnet node | Endpoint |
|---|---|---|
| `mini` | `rishis-mac-mini-2020-rex` (100.113.42.43) | `https://rishis-mac-mini-2020-rex.dropbear-bitterling.ts.net` |
| — | `lambda-rex` (100.77.127.88) | `https://lambda-rex.dropbear-bitterling.ts.net` |

The OS-level `mini` node (100.117.214.99) is a *different* device — Rex does not
listen there.

## Setting up a Mac as a reachable server

1. Install Rex, launch it once (the app starts the bundled server).
2. Turn on its tailnet node — **Settings → Tailscale** in the app, or:
   ```bash
   rex server tailscale login   # prints a sign-in link; sign in to the same tailnet
   rex server tailscale on
   rex server tailscale rename <name>   # optional; then re-check the name in `rex server status`
   ```
3. Confirm the endpoint:
   ```bash
   rex server status            # look for: tailscale: running · <node>.<tailnet>.ts.net
   ```
4. Declare it as a host for every Mac — add to `dot_config/rex/init.lua`:
   ```lua
   rex.host{
     label = "mini",
     endpoints = { "https://<node>.dropbear-bitterling.ts.net" },
   }
   ```
   Fields: `label` (required), `endpoints` (list, tried in order) or `endpoint`,
   optional `id` (stable identity across renames) and `icon`.
5. Commit, push, `dots update` on each Mac. The reload script (below) makes the
   running server pick it up — no restart needed.

One-off alternative without chezmoi: `rex hosts add LABEL ENDPOINT` (stored in your
home's host list), or `rex server tailscale pair` on the server to show a QR code for
another device.

Rex on the mini depends on the mini being **logged in** (auto-login) since the server
runs inside the app — same constraint as the other LaunchAgents in the reboot table in
the dotfiles repo's `CLAUDE.md`.

## What chezmoi automates

Paths are in the dotfiles source, `~/.local/share/chezmoi` (`chezmoi source-path`).

| File | Does |
|---|---|
| `dot_config/rex/init.lua` → `~/.config/rex/init.lua` | Keybindings + `rex.host{}` declarations. macOS-only (`.chezmoiignore`). |
| `.chezmoiscripts/darwin/run_onchange_after_reload-rex-config.sh.tmpl` | Runs `rex config reload` whenever `init.lua`'s hash changes. Finds `rex` in the app bundle if it isn't on PATH; skips quietly if no server is running; never fails the apply. |
| `dot_config/zsh/scripts.zsh.tmpl` → `ssage()` wrapper | Feeds Rex pane scrollback to ShellSage (see below). |

## Using it

```bash
rex hosts                     # list hosts and where each came from (e.g. init.lua:12)
rex hosts check               # which hosts are reachable from here
rex -S mini ls                # list sessions on the mini
rex -S mini new               # start a session there
rex home                      # which server this device follows for hosts
rex config check              # validate init.lua (prints warnings with line numbers)
rex config reload             # make the running server re-read init.lua (local only)
```

## Gotchas (all hit in practice)

- **Use the hostname, never the 100.x IP.** The Rex node's TLS cert only covers its
  MagicDNS name, so `https://<IP>` fails the handshake (`tls: internal error`) and Rex
  then falls back to `:7297`, giving the misleading **"Nothing is listening at
  100.x.x.x:7297."** Nothing ever listens on 7297 for a Tailscale-served Rex.
- **`dots update` alone didn't use to apply host changes.** The server reads
  `init.lua` only at start or on `rex config reload`, and **reload is refused over the
  tailnet** (`requires the local Unix socket`), so you can't fix another Mac remotely.
  The `run_onchange` reload script exists for exactly this.
- **`rex` may not be on PATH** outside a Rex pane (scripts, cron, a plain terminal). The
  binary lives at `~/Library/Application Support/com.superlogical.rex/RexServer/Versions/Current/Rex Server.app/Contents/MacOS/rex`.
  The path has spaces — tirith's Bash hook may refuse to run it by that path; symlinking
  it somewhere space-free works around that.
- **Editing a host with `rex hosts edit`** stores an override that silently shadows the
  `init.lua` declaration; the Lua line stays but stops having an effect. Prefer editing
  `init.lua`.
- A host added by hand with the same label as a declared one is a conflict — remove the
  manual one (`rex hosts remove LABEL`).
- Read-only API over the tailnet works for debugging another Mac without SSH:
  `rex -S https://<node>.ts.net server status` and
  `rex -S https://<node>.ts.net api call hosts.list`.

## ShellSage (`ssage`) inside Rex

ShellSage reads terminal history only via `tmux capture-pane` when `$TMUX` is set. In a
Rex pane (outside tmux) the `ssage()` zsh wrapper pipes `rex capture` output in as
context instead. `--pid current|all|<block>` works as under tmux; `SSAGE_REX_LINES`
caps lines per pane (default 2000). Explicit pipes and tmux panes pass straight through.

If `ssage` dies with **`bad interpreter: …/uv/tools/shell-sage/bin/python3`**, Homebrew
removed the Python its venv was built on. Fix:
```bash
uv tool install shell-sage --reinstall --managed-python
```
The install script now uses `--managed-python` and checks with `ssage --help`, so new
installs don't depend on Homebrew's Python.
