# Changelog

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
