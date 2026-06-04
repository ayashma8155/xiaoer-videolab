# Changelog

## 1.0.0 — 2026-06-03

First public release.

- One-click toolbar download of the current page's video via a local yt-dlp daemon.
- macOS `launchd` background service with a generated LaunchAgent (portable paths).
- Configurable via `VIDEOLAB_*` environment variables: port, download dir, yt-dlp
  path, filename prefix, max height, cookies-from-browser, app name.
- Toolbar badge states (`…` / `✓` / `✕` / `!`) and native macOS notifications.
- MV3 extension works in Chrome, Arc, Edge, Brave and other Chromium browsers.
