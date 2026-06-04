<div align="center">

# 🎬 Xiaoer VideoLab

### One click. Any video. Local.

Press one toolbar button and the video on the current page lands in your `~/Downloads`.
Powered by a tiny local [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) daemon — **1800+ sites** out of the box
(YouTube · Bilibili · X/Twitter · TikTok · Vimeo · Twitch · Weibo …).

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Manifest V3](https://img.shields.io/badge/Chrome-MV3-4285F4?logo=googlechrome&logoColor=white)
![Python stdlib only](https://img.shields.io/badge/Python-stdlib%20only-3776AB?logo=python&logoColor=white)
![No tracking](https://img.shields.io/badge/network-localhost%20only-27ae60)

**English** · [简体中文](README.zh-CN.md)

</div>

---

## Why

Browser video downloaders are a swamp of sketchy extensions that beg for "read everything on every site"
permissions and phone home. Xiaoer VideoLab takes the opposite bet:

- **The extension does almost nothing.** It only reads the *current tab's URL* when you click it, and POSTs
  that one string to `127.0.0.1`. No page scraping, no content scripts, no remote servers.
- **The download happens locally.** A small Python daemon hands the URL to `yt-dlp`, the
  battle-tested open-source downloader. All the smarts live in a tool you can audit.
- **Nothing leaves your machine** except the request `yt-dlp` makes to fetch the video you asked for.

## How it works

```
 ┌─────────────────────┐   click    ┌──────────────────────────┐         ┌──────────┐
 │  Browser toolbar     │ ─────────► │  daemon @ 127.0.0.1:7788 │ ──────► │  yt-dlp  │ ──► ~/Downloads
 │  (Chrome MV3 ext.)   │  POST url  │  (Python stdlib, launchd)│  spawn  └──────────┘        │
 └─────────────────────┘            └──────────────────────────┘                              ▼
        ▲   badge: … ✓ ✕ !                       │                                   macOS notification
        └───────────────────────────────────────┘                                     "✅ <filename>"
```

- **daemon** — Python standard-library `http.server`, listens on `127.0.0.1:7788`, started at login by `launchd`.
- **extension** — Chrome MV3, a single toolbar button, grabs `tab.url` and POSTs it to the daemon.
- **output** — `~/Downloads/<title> [<id>].mp4` (≤1080p mp4 by default; configurable).
- **log** — `~/Library/Logs/xiaoer-videolab.log`

## Requirements

- **macOS** (the background service uses `launchd`; the daemon itself is cross-platform if you run it by hand)
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) and `ffmpeg`:
  ```bash
  brew install yt-dlp ffmpeg
  ```
- A Chromium-based browser (Chrome, Arc, Edge, Brave, Dia …)

## Install

```bash
git clone https://github.com/Jane-xiaoer/xiaoer-videolab.git
cd xiaoer-videolab
./scripts/install.sh
```

The installer **generates** a LaunchAgent for your own paths and starts the daemon. Then load the extension:

1. Open `chrome://extensions/`
2. Turn on **Developer mode** (top-right)
3. Click **Load unpacked** → choose the `extension/` folder
4. Pin the icon to your toolbar

## Use

Open any video page → click the toolbar button → you'll get a "Downloading…" notification, then
"✅ &lt;filename&gt;" when it's done.

| Badge | Meaning |
|:---:|---|
| `…` | request sent, downloading |
| `✓` | daemon accepted the job (download continues in the background) |
| `✕` | can't reach the daemon |
| `!` | daemon returned an error (check the notification / log) |

## Configuration

All optional — set them and re-run `./scripts/install.sh` to bake them into the service:

| Variable | Default | What it does |
|---|---|---|
| `VIDEOLAB_PORT` | `7788` | daemon port |
| `VIDEOLAB_DOWNLOADS` | `~/Downloads` | where files land |
| `VIDEOLAB_YT_DLP` | auto-detect | path to the `yt-dlp` binary |
| `VIDEOLAB_PREFIX` | _(none)_ | filename prefix, e.g. `小耳-` |
| `VIDEOLAB_MAX_HEIGHT` | `1080` | max video height (set `2160` for 4K) |
| `VIDEOLAB_COOKIES_BROWSER` | _(off)_ | pull cookies from a browser (`chrome`/`brave`/`firefox`/`edge`/`safari`) for **login-gated / private** videos |
| `VIDEOLAB_APP_NAME` | `Xiaoer VideoLab` | name in notifications |

```bash
# example: 4K, pull login cookies from Chrome, brand the filenames
VIDEOLAB_MAX_HEIGHT=2160 VIDEOLAB_COOKIES_BROWSER=chrome VIDEOLAB_PREFIX="小耳-" ./scripts/install.sh
```

## Commands

```bash
# is the daemon alive?
curl http://127.0.0.1:7788/health

# tail the log
tail -f ~/Library/Logs/xiaoer-videolab.log

# restart the daemon
launchctl unload ~/Library/LaunchAgents/com.xiaoer.videolab.plist
launchctl load   ~/Library/LaunchAgents/com.xiaoer.videolab.plist

# download without the extension
curl -X POST http://127.0.0.1:7788/download \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# uninstall the service
./scripts/uninstall.sh
```

## Security

- The daemon binds to `127.0.0.1` only — it is not reachable from your network.
- CORS is `*` because it's a localhost-only port with no secrets. If you want to stop *other local
  processes* from posting to it, add a shared `X-Token` header check in `daemon/server.py`.
- The extension's only host permission is `http://127.0.0.1:7788/*`.

## FAQ

**It says "can't reach the daemon" (`✕`).** Run `curl http://127.0.0.1:7788/health`. If that fails,
check `tail ~/Library/Logs/xiaoer-videolab.err.log` and confirm `yt-dlp` is installed.

**A video downloads at low quality / audio only.** Some sites split streams; make sure `ffmpeg` is
installed so `yt-dlp` can merge them.

**A private / members-only video fails.** Set `VIDEOLAB_COOKIES_BROWSER` to the browser where you're
logged in, then re-install.

**Not on macOS?** The extension is cross-platform; the *installer* is macOS-only. On Linux/Windows just
run `python3 daemon/server.py` yourself (any process manager works).

## Contributing

Issues and PRs welcome. The whole thing is ~400 lines of stdlib Python + vanilla JS — easy to read,
easy to fork. If you add support for a workflow you care about (a new format profile, a Firefox
manifest, a Linux service file), send it over.

## Author

**Jane** · 小耳 / Xiaoer — *a family of little tools that listen, read, find, and organize.*

- GitHub: [@Jane-xiaoer](https://github.com/Jane-xiaoer)
- Email: xiaoerzhan@gmail.com

Part of the **Xiaoer** toolbox, alongside
[Xiaoer Ask](https://github.com/Jane-xiaoer/xiaoer-ask) and
[Smart Rename](https://github.com/Jane-xiaoer/smart-rename).

## Acknowledgements

Standing entirely on the shoulders of [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) — this project is
just a friendly one-click button in front of it. Please support and respect the yt-dlp project.

## License

[MIT](LICENSE) © 2026 Jane (小耳 / Xiaoer)

> Download only content you have the right to download. You are responsible for respecting the terms of
> service of the sites you use this on, and applicable copyright law.
