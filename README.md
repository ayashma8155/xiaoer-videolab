<div align="center">

# 🎬 Xiaoer VideoLab

### One click. Any video. Local.

Press one toolbar button and the video on the current page lands in your `~/Downloads`.
Powered by a tiny local [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) daemon — **1800+ sites** out of the box
(YouTube · Bilibili · X/Twitter · TikTok · Vimeo · Twitch · Weibo …).

[![CI](https://github.com/Jane-xiaoer/xiaoer-videolab/actions/workflows/ci.yml/badge.svg)](https://github.com/Jane-xiaoer/xiaoer-videolab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey)
![Manifest V3](https://img.shields.io/badge/Chrome-MV3-4285F4?logo=googlechrome&logoColor=white)
![Python stdlib only](https://img.shields.io/badge/Python-stdlib%20only-3776AB?logo=python&logoColor=white)
![No tracking](https://img.shields.io/badge/network-localhost%20only-27ae60)

[![English](https://img.shields.io/badge/lang-English-2563eb)](README.md)&nbsp;
[![简体中文](https://img.shields.io/badge/lang-简体中文-lightgrey)](README.zh-CN.md)

</div>

---

## 🙏 Thanks to our contributors / 致谢贡献者

**This project is better because of these people — thank you! / 本项目因他们而更好,衷心感谢!**

- [**@ttmouse**](https://github.com/ttmouse) — popup history panel, **cancel a stuck download**, play / open-folder, one-click daemon start ([#4](https://github.com/Jane-xiaoer/xiaoer-videolab/pull/4))
  <br>弹出历史面板、**取消卡住的下载**、播放 / 打开文件夹、一键启动服务
- [**@jzq1212 (林以恒)**](https://github.com/jzq1212) — **Windows support**: cross-platform daemon + PowerShell install scripts ([#1](https://github.com/Jane-xiaoer/xiaoer-videolab/pull/1))
  <br>**Windows 支持**:跨平台 daemon + PowerShell 安装脚本
- [**@alick-zhang**](https://github.com/alick-zhang) — raised the Windows request that kicked it off ([#3](https://github.com/Jane-xiaoer/xiaoer-videolab/issues/3))
  <br>提出 Windows 需求,促成了上面的 Windows 支持

> Issues & PRs welcome — your name goes here too. / 欢迎提 issue 和 PR,你的名字也会出现在这里。

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

## TL;DR (if you've done this before)

```bash
brew install yt-dlp ffmpeg
git clone https://github.com/Jane-xiaoer/xiaoer-videolab.git
cd xiaoer-videolab && ./scripts/install.sh
# then load extension/ as an unpacked extension at chrome://extensions/
```

---

## Installation — step by step

First time? Follow every step below. It takes about 5 minutes and you only do it once.

### What you need

- **macOS** (background service via `launchd`) **or Windows 10/11** (via Task Scheduler).
- A Chromium-based browser — Chrome, Arc, Edge, Brave, or Dia.
- About 5 minutes.

> **On Windows?** Parts A & B below are for macOS. Jump to **[🪟 On Windows](#-on-windows-do-this-instead-of-parts-a--b)**, then come back for Part C.

You do **not** need to know how to code. You will copy-paste a few commands.

### Part A · Install the engine (one-time)

This tool is a friendly button in front of [`yt-dlp`](https://github.com/yt-dlp/yt-dlp), the open-source
downloader that does the real work. So you install that first.

**A1.** Open the **Terminal** app. (Press `⌘ Space`, type `Terminal`, hit Enter.)

<!-- 截图位: docs/images/01-terminal.png -->

**A2.** Install **Homebrew** (a package manager for Mac). If you already have it, skip to A3.
Paste this into Terminal and press Enter, then follow its prompts:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**A3.** Install `yt-dlp` and `ffmpeg`:

```bash
brew install yt-dlp ffmpeg
```

> `ffmpeg` matters — without it some sites give you audio-only or low quality, because the video and
> audio come as separate streams that `ffmpeg` merges back together.

### Part B · Install Xiaoer VideoLab

**B1.** Still in Terminal, paste these three lines:

```bash
git clone https://github.com/Jane-xiaoer/xiaoer-videolab.git
cd xiaoer-videolab
./scripts/install.sh
```

**B2.** When it works, the last lines you see will look like this:

```
✓ Daemon running at http://127.0.0.1:7788
  Log: ~/Library/Logs/xiaoer-videolab.log

Next: load the browser extension
  1. Open chrome://extensions/
  ...
```

<!-- 截图位: docs/images/02-install-success.png -->

That means the background downloader is installed and will start automatically every time you log in.
You never touch the Terminal again.

### 🪟 On Windows? (do this instead of Parts A & B)

The browser steps (Part C & D) are identical on every OS — only the engine + service install differs.

**W1.** Install the engine. Open **PowerShell** and run (uses [winget](https://aka.ms/getwinget), built into Win 10/11):

```powershell
winget install Python.Python.3.11 yt-dlp.yt-dlp ffmpeg
```

**W2.** Install Xiaoer VideoLab. Either grab the code with the green **Code → Download ZIP** button (then unzip), or in PowerShell:

```powershell
git clone https://github.com/Jane-xiaoer/xiaoer-videolab.git
cd xiaoer-videolab
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

The installer registers a **login-start task** and asks which browser to pull cookies from (`edge`/`chrome`).
To uninstall later: `powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1`.

Now continue with **Part C** below — loading the toolbar button is the same everywhere.

### Part C · Add the toolbar button

The browser button isn't on the Chrome Web Store (yet), so you load it manually. This is normal and safe.

> The screenshot below marks every step in this part (labels are in Chinese, but the red arrows
> point at exactly the right buttons): **① open the address · ② turn on Developer mode ·
> ③ click "Load unpacked" · ④ flip the extension's switch on.**

![Four steps to load the extension: open the address, enable Developer mode, Load unpacked, toggle on](docs/images/load-extension-steps.png)

**C1.** Open a new browser tab and go to: `chrome://extensions/`
(On Edge it's `edge://extensions/`, on Arc/Brave the same `chrome://extensions/`.)

**C2.** Turn on **Developer mode** — the switch in the **top-right** corner.

<!-- 截图位: docs/images/03-developer-mode.png -->

**C3.** Click the **Load unpacked** button (top-left). A folder picker opens.

<!-- 截图位: docs/images/04-load-unpacked.png -->

**C4.** Navigate to where you cloned the repo and select the **`extension`** folder inside it
(e.g. `xiaoer-videolab/extension`). Click **Select**.

A card titled **Xiaoer VideoLab** now appears in your extensions list.

<!-- 截图位: docs/images/05-extension-card.png -->

**C5.** Click the **puzzle-piece icon** in your toolbar, find **Xiaoer VideoLab**, and click the **pin**
so its icon stays on the toolbar.

<!-- 截图位: docs/images/06-pin-toolbar.png -->

### Part D · Download your first video

**D1.** Open any video page (YouTube, Bilibili, X, TikTok …).

**D2.** Click the **Xiaoer VideoLab** icon in your toolbar.

<!-- 截图位: docs/images/07-click-button.png -->

**D3.** You'll get a **"Downloading…"** notification, then a **"✅ &lt;filename&gt;"** notification when it's done.
The icon also shows a little badge:

| Badge | Meaning |
|:---:|---|
| `…` | request sent, downloading |
| `✓` | daemon accepted the job (download continues in the background) |
| `✕` | can't reach the daemon |
| `!` | daemon returned an error (check the notification / log) |

<!-- 截图位: docs/images/08-notification.png -->

**D4.** Find your video in the **`~/Downloads`** folder. 🎉

<!-- 截图位: docs/images/09-downloads-folder.png -->

That's it — from now on it's just **open a video → click the button**.

## Configuration

All optional — set them and re-run `./scripts/install.sh` to bake them into the service:

| Variable | Default | What it does |
|---|---|---|
| `VIDEOLAB_PORT` | `7788` | daemon port — ⚠️ if you change it, also edit `extension/background.js` (`DAEMON`) **and** `extension/manifest.json` (`host_permissions`) to the same port, or the button can't reach the daemon |
| `VIDEOLAB_DOWNLOADS` | `~/Downloads` | where files land |
| `VIDEOLAB_YT_DLP` | auto-detect | path to the `yt-dlp` binary (auto-detect prefers a `yt-dlp-nightly` build if one is installed — see FAQ on `HTTP Error 412`) |
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

# update everything (latest code + newest yt-dlp engine), keeping your settings
./scripts/update.sh

# uninstall the service
./scripts/uninstall.sh
```

## Security

- The daemon binds to `127.0.0.1` only — it is not reachable from your network.
- **No drive-by downloads.** `/download` rejects any request carrying an `http(s)` `Origin` header,
  so a malicious web page's JavaScript cannot make the daemon download files behind your back. The
  extension (`chrome-extension://`) and command-line calls (no Origin) are allowed.
- The extension's only host permission is `http://127.0.0.1:7788/*`. It reads only the current tab's
  URL when you click — no page content, no content scripts.
- If you also want to block *other local processes*, add a shared `X-Token` header check in `daemon/server.py`.

## FAQ

**It says "can't reach the daemon" (`✕`).** Run `curl http://127.0.0.1:7788/health`. If that fails,
check `tail ~/Library/Logs/xiaoer-videolab.err.log` and confirm `yt-dlp` is installed.

**A video downloads at low quality / audio only.** Some sites split streams; make sure `ffmpeg` is
installed so `yt-dlp` can merge them.

**A private / members-only video fails.** Set `VIDEOLAB_COOKIES_BROWSER` to the browser where you're
logged in, then re-install.

**A site that used to work now fails — Bilibili returns `HTTP Error 412`, or a site throws extractor
errors.** The site tightened its anti-bot defenses and your `yt-dlp` is older than the fix. Update it
first (`yt-dlp --update`, or `brew upgrade yt-dlp`). Stable releases can lag days-to-weeks behind
fast-moving sites like Bilibili — if updating stable isn't enough, install the **nightly** build, which
VideoLab auto-detects and prefers over stable:

```bash
# self-contained nightly binary (macOS) — VideoLab picks it up automatically, no config needed
mkdir -p ~/.local/bin
curl -L -o ~/.local/bin/yt-dlp-nightly \
  https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp_macos
chmod +x ~/.local/bin/yt-dlp-nightly
# update it any time it falls behind again:
~/.local/bin/yt-dlp-nightly --update-to nightly
```

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

## 📱 关注作者 / Follow Me

如果这个仓库对你有帮助，欢迎关注我。后面我会持续更新更多 AI Skill、做网站、自动化工作流和创意项目。

If this repo helped you, follow me for more AI skills, website building, automation workflows, and creative projects.

- X (Twitter): [@xiaoerzhan](https://x.com/xiaoerzhan)
- 微信公众号 / WeChat Official Account: 扫码关注 / Scan to follow

<p align="center">
  <img src="./follow-wechat-qrcode.jpg" alt="Jane WeChat Official Account QR code" width="300" />
</p>

<p align="center"><strong>中文：</strong>欢迎关注我的公众号，一起研究 AI Skill、网站搭建、自动化流程和创意实验。</p>

<p align="center"><strong>English:</strong> Follow my WeChat Official Account for more AI skills, website building, automation workflows, and creative experiments.</p>

## Acknowledgements

Standing entirely on the shoulders of [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) — this project is
just a friendly one-click button in front of it. Please support and respect the yt-dlp project.

## License

[MIT](LICENSE) © 2026 Jane (小耳 / Xiaoer)

> Download only content you have the right to download. You are responsible for respecting the terms of
> service of the sites you use this on, and applicable copyright law.
