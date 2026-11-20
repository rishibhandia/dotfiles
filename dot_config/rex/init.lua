-- Rex terminal multiplexer configuration (managed by chezmoi: dot_config/rex/init.lua)
--
-- Migrated from tmux, Ghostty, and iTerm2:
-- - All 11 Ghostty tab/window/split bindings match Rex's built-in defaults.
-- - cmd+k intentionally kept as Rex's default session picker (session.switch).
-- - Add custom rex.bind(...) / rex.action{...} overrides below as needed.

-- Remote Rex servers (use with `rex -S <label> ...` or the client's host picker).
-- Rex's built-in Tailscale node serves the API over HTTPS on :443 under its
-- MagicDNS name. Use the hostname, not the 100.x IP: the TLS cert only covers
-- the name, and a bare IP makes Rex fall back to :7297, where nothing listens.
rex.host{
  label = "mini",
  endpoints = { "https://rishis-mac-mini-2020-rex.dropbear-bitterling.ts.net" },
}
