---
name: brew cask upgrades quit the app before the sudo step that fails
description: In a non-interactive shell, `brew upgrade --cask` for pkg/system-extension casks (tailscale-app, macfuse) quits the running app, THEN dies at a sudo prompt it cannot answer -- leaving the service down and the upgrade incomplete. Never delegate these on an always-on host.
type: feedback
---

Do not run `brew upgrade --cask <name>` from an agent/non-interactive shell for casks that
install a pkg or a system extension (`tailscale-app`, `macfuse`, anything with an
`uninstall pkgutil:`/`uninstall delete:` stanza). Hand the user a `! sudo -v && brew upgrade --cask <name>`
to run themselves.

**Why:** Homebrew's cask upgrade is uninstall-then-reinstall, and it orders the steps as
*quit app → remove files (via `sudo`) → install new version*. In a shell with no TTY the
sudo step fails:

```
==> Quitting application 'io.tailscale.ipn.macsys'...
Application 'io.tailscale.ipn.macsys' quit successfully.
==> Uninstalling packages with `sudo` (which may request your password)...
sudo: a terminal is required to read the password
Error: tailscale-app: Failure while executing; `/usr/bin/sudo -E -- ...` exited with 1
```

The app is already stopped by then, and brew purges the staged new version on failure — so
you end up **worse than before you started**: old version still recorded, service down, no
upgrade. On an always-on host (media server, DNS box, VPN node) that's a live outage, and
the failure message says nothing about the app it just killed.

Hit 2026-08-02 on the Mac mini: `tailscale-app` upgrade took the node off the tailnet.
`open -a Tailscale` was not enough to recover — the CLI kept returning
`Tailscale.CLIError error 1` because stale system extensions from prior versions were still
registered. A reboot cleared them and it came back clean.

**How to apply:**
- Before upgrading any cask on a service host, check the blast radius first:
  `brew info --cask <name> | grep -iE "pkg|extension|sudo"`, and ask what depends on the box.
- Prefer `! sudo -v && brew upgrade --cask <name>` (user-run, TTY available) over doing it yourself.
- After any system-extension version change, check `systemextensionsctl list` — entries reading
  `[terminated waiting to uninstall on reboot]` mean a reboot is pending and the CLI may
  misbehave until then.
- Capture recoverable state *before* upgrading so you can verify restoration afterward
  (e.g. `tailscale serve status` → the port/path mappings).
- **`brew outdated --cask --greedy` lies about self-updating casks.** Apps that auto-update
  (`auto_updates: true`) drift ahead of Homebrew's install receipt, so brew reports an
  "upgrade" that is really a downgrade-then-sidegrade. Confirm the real version from the app
  itself (`tailscale version`, `systemextensionsctl list`) before acting: brew claimed
  1.62.1 → 1.98.10 while the running app was already 1.98.8.
