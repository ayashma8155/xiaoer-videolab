#!/usr/bin/env python3
"""Xiaoer VideoLab daemon — receive a URL from the browser extension, download it via yt-dlp.

Pure Python standard library. No third-party packages. Listens on localhost only.

Configuration is via environment variables (all optional):

    VIDEOLAB_PORT             TCP port to listen on            (default: 7788)
    VIDEOLAB_DOWNLOADS        download directory               (default: ~/Downloads)
    VIDEOLAB_YT_DLP           path to the yt-dlp binary        (default: auto-detect)
    VIDEOLAB_PREFIX           filename prefix                  (default: "" / none)
    VIDEOLAB_MAX_HEIGHT       max video height in pixels       (default: 1080)
    VIDEOLAB_COOKIES_BROWSER  pull cookies from this browser   (default: "" / off)
                              e.g. "chrome", "brave", "firefox", "edge", "safari"
                              — needed for login-gated / private videos.
    VIDEOLAB_APP_NAME         name shown in macOS notifications (default: "Xiaoer VideoLab")
"""

import json
import os
import shlex
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse


def _detect_yt_dlp() -> str:
    # Prefer a nightly build when present. Fast-moving sites (notably Bilibili)
    # roll out anti-bot changes that stable yt-dlp releases lag behind — the
    # symptom is "HTTP Error 412: Precondition Failed". Nightly ships extractor
    # fixes within days, so auto-detect it ahead of stable. See the FAQ.
    nightly = shutil.which("yt-dlp-nightly") or str(Path.home() / ".local" / "bin" / "yt-dlp-nightly")
    if Path(nightly).is_file():
        return nightly
    found = shutil.which("yt-dlp")
    if found:
        return found
    for cand in ("/opt/homebrew/bin/yt-dlp", "/usr/local/bin/yt-dlp"):
        if Path(cand).is_file():
            return cand
    return "yt-dlp"  # last resort; relies on PATH at exec time


PORT = int(os.environ.get("VIDEOLAB_PORT", "7788"))
HOST = "127.0.0.1"
DOWNLOADS = Path(os.environ.get("VIDEOLAB_DOWNLOADS", str(Path.home() / "Downloads")))
YT_DLP = os.environ.get("VIDEOLAB_YT_DLP") or _detect_yt_dlp()
PREFIX = os.environ.get("VIDEOLAB_PREFIX", "")
MAX_HEIGHT = int(os.environ.get("VIDEOLAB_MAX_HEIGHT", "1080"))
COOKIES_BROWSER = os.environ.get("VIDEOLAB_COOKIES_BROWSER", "").strip()
APP_NAME = os.environ.get("VIDEOLAB_APP_NAME", "Xiaoer VideoLab")
LOG_FILE = Path.home() / "Library" / "Logs" / "xiaoer-videolab.log"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(f"{msg}\n")
    print(msg, flush=True)


def notify(title: str, message: str) -> None:
    """macOS desktop notification. Silently no-ops on non-macOS systems."""
    if not shutil.which("osascript"):
        return
    safe_title = title.replace('"', "'")
    safe_msg = message.replace('"', "'").replace("\n", " ")
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{safe_msg}" with title "{safe_title}"'],
            check=False, timeout=5,
        )
    except Exception as e:
        log(f"notify failed: {e}")


def download(url: str) -> None:
    log(f"[start] {url}")
    notify(APP_NAME, f"Downloading {url[:80]}")
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    name_prefix = f"{PREFIX}" if PREFIX else ""
    output_tpl = str(DOWNLOADS / f"{name_prefix}%(title).160s [%(id)s].%(ext)s")
    fmt = (
        f"bv*[height<={MAX_HEIGHT}][ext=mp4]+ba[ext=m4a]/"
        f"b[height<={MAX_HEIGHT}][ext=mp4]/"
        f"bv*[height<={MAX_HEIGHT}]+ba/"
        f"b[height<={MAX_HEIGHT}]/best"
    )
    cmd = [
        YT_DLP,
        "--no-playlist",
        "--no-mtime",
        "-f", fmt,
        "--merge-output-format", "mp4",
        "--replace-in-metadata", "title", r"[\\/:*?\"<>|]", "_",
        "--output", output_tpl,
    ]
    if COOKIES_BROWSER:
        cmd += ["--cookies-from-browser", COOKIES_BROWSER]
    cmd.append(url)

    log("$ " + " ".join(shlex.quote(c) for c in cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        tail = (result.stdout + result.stderr).strip().splitlines()
        if result.returncode == 0:
            log(f"[done] {url}")
            for line in tail[-15:]:
                log("  " + line)
            filename = ""
            for line in reversed(tail):
                if "[download] Destination:" in line:
                    filename = line.split("Destination:", 1)[1].strip()
                    break
                if "has already been downloaded" in line:
                    filename = line.split("]", 1)[1].split(" has already")[0].strip()
                    break
                if "[Merger]" in line and "into" in line:
                    filename = line.split('"')[-2] if '"' in line else ""
                    break
            short = Path(filename).name if filename else "Done"
            notify(f"{APP_NAME} ✅", short)
        else:
            log(f"[fail] {url} rc={result.returncode}")
            for line in tail[-15:]:
                log("  " + line)
            err = tail[-1] if tail else f"rc={result.returncode}"
            notify(f"{APP_NAME} ❌", err[:120])
    except subprocess.TimeoutExpired:
        log(f"[timeout] {url}")
        notify(f"{APP_NAME} ⏱", "Download timed out (1 hour)")
    except Exception as e:
        log(f"[err] {url}: {e}")
        notify(f"{APP_NAME} ❌", str(e)[:120])


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true,"service":"xiaoer-videolab"}')
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/download":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        # Security: stop drive-by downloads. A real web page that tries to call us
        # carries an http(s) Origin header — refuse those. The extension sends
        # Origin: chrome-extension://..., and curl/CLI send none — both allowed.
        origin = self.headers.get("Origin", "")
        if origin.startswith(("http://", "https://")):
            self.send_response(403)
            self._cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"forbidden: web-page origins cannot trigger downloads")
            log(f"[blocked] web origin {origin} tried to POST /download")
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            data = json.loads(raw)
            url = data["url"]
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise ValueError("url must be http(s)")
        except Exception as e:
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"bad request: {e}".encode())
            return

        threading.Thread(target=download, args=(url,), daemon=True).start()

        self.send_response(202)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"queued":true}')

    def log_message(self, fmt, *args) -> None:
        log("http: " + (fmt % args))


def main() -> None:
    log(f"{APP_NAME} daemon listening on http://{HOST}:{PORT}  (yt-dlp: {YT_DLP})")
    server = HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("daemon stopping")
        server.shutdown()


if __name__ == "__main__":
    main()
