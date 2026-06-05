# Changelog

## 1.1.0 — 2026-06-04

- **Bilibili & other fast-moving sites: survive `HTTP Error 412`.** Stable `yt-dlp` releases lag
  behind sites that tighten anti-bot defenses (Bilibili in particular), causing downloads to fail
  with `HTTP Error 412: Precondition Failed`. The daemon's yt-dlp auto-detection now **prefers a
  `yt-dlp-nightly` build** (`yt-dlp-nightly` on `PATH`, or `~/.local/bin/yt-dlp-nightly`) over the
  stable binary, so installing nightly fixes these sites with zero config.
- Docs: new FAQ entry on `HTTP Error 412` / sites that stop working, with a one-liner to install and
  self-update the nightly binary.

## 1.0.1 — 2026-06-04

- **Security:** `/download` now rejects requests with an `http(s)` `Origin` header, blocking
  drive-by downloads from malicious web pages. Extension and CLI calls are unaffected.
- Docs: note that changing `VIDEOLAB_PORT` also requires editing the extension.
- CI: GitHub Actions now lints the code and smoke-tests the daemon (boot + endpoint behavior)
  on every push.

## 1.0.0 — 2026-06-03

First public release.

- One-click toolbar download of the current page's video via a local yt-dlp daemon.
- macOS `launchd` background service with a generated LaunchAgent (portable paths).
- Configurable via `VIDEOLAB_*` environment variables: port, download dir, yt-dlp
  path, filename prefix, max height, cookies-from-browser, app name.
- Toolbar badge states (`…` / `✓` / `✕` / `!`) and native macOS notifications.
- MV3 extension works in Chrome, Arc, Edge, Brave and other Chromium browsers.
