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
import datetime
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional


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
HISTORY_FILE = Path.home() / "Library" / "Logs" / "xiaoer-videolab-history.jsonl"
_history_lock = threading.Lock()


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


# Track active download processes so they can be cancelled.
_active_downloads: dict[str, subprocess.Popen] = {}
_active_downloads_lock = threading.Lock()


def _simple_hash(url: str) -> str:
    """Short deterministic hash for a URL (used as history entry id)."""
    h = 0
    for c in url:
        h = ((h << 5) - h) + ord(c)
        h &= 0xFFFFFFFF
    return f"dl_{abs(h):08x}"[:16]


def _append_history(entry: dict) -> None:
    """Thread-safe append to the JSONL history file."""
    with _history_lock:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cancel_download(url: str) -> bool:
    """Kill a running download process by URL. Returns True if a process was killed."""
    with _active_downloads_lock:
        proc = _active_downloads.get(url)
        if proc and proc.poll() is None:
            proc.kill()
            log(f"[cancelled] {url}")
            return True
    return False


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
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        with _active_downloads_lock:
            _active_downloads[url] = proc
        try:
            stdout, stderr = proc.communicate(timeout=3600)
            result = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
        finally:
            with _active_downloads_lock:
                _active_downloads.pop(url, None)
        tail = (result.stdout + result.stderr).strip().splitlines()
        timestamp = datetime.datetime.now().isoformat()

        def _parse_filepath() -> str:
            for line in reversed(tail):
                if "[download] Destination:" in line:
                    return line.split("Destination:", 1)[1].strip()
                if "has already been downloaded" in line:
                    return line.split("]", 1)[1].split(" has already")[0].strip()
                if "[Merger]" in line and "into" in line:
                    parts = line.split('"')
                    return parts[-2] if len(parts) >= 2 else ""
            return ""

        def _parse_filesize() -> Optional[int]:
            for line in tail:
                if "[download]" in line and "% of" in line and "in" in line:
                    m = re.search(r"(\d+\.?\d*)\s*(KiB|MiB|GiB)", line)
                    if m:
                        val = float(m.group(1))
                        unit = m.group(2)
                        multipliers = {"KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}
                        return int(val * multipliers.get(unit, 1))
            return None

        def _extract_title(filepath: str) -> str:
            name = Path(filepath).stem  # filename without extension
            # Remove trailing [id] like " [abc123]"
            cleaned = re.sub(r"\s\[[\w-]+\]$", "", name)
            return cleaned if cleaned else name

        if result.returncode == 0:
            log(f"[done] {url}")
            for line in tail[-15:]:
                log("  " + line)
            filepath = _parse_filepath()
            filesize = _parse_filesize()
            title = _extract_title(filepath) if filepath else "Unknown"
            short = Path(filepath).name if filepath else "Done"
            notify(f"{APP_NAME} ✅", short)

            history_entry = {
                "id": _simple_hash(url),
                "url": url,
                "title": title,
                "filename": Path(filepath).name if filepath else "",
                "filepath": str(Path(filepath).resolve()) if filepath else "",
                "filesize": filesize,
                "timestamp": timestamp,
                "status": "done",
            }
            _append_history(history_entry)
        else:
            log(f"[fail] {url} rc={result.returncode}")
            for line in tail[-15:]:
                log("  " + line)
            err = tail[-1] if tail else f"rc={result.returncode}"
            notify(f"{APP_NAME} ❌", err[:120])
            _append_history({
                "id": _simple_hash(url),
                "url": url,
                "title": "",
                "filename": "",
                "filepath": "",
                "filesize": None,
                "timestamp": timestamp,
                "status": "failed",
            })
    except subprocess.TimeoutExpired:
        log(f"[timeout] {url}")
        notify(f"{APP_NAME} ⏱", "Download timed out (1 hour)")
        _append_history({
            "id": _simple_hash(url),
            "url": url,
            "title": "",
            "filename": "",
            "filepath": "",
            "filesize": None,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "failed",
        })
    except Exception as e:
        log(f"[err] {url}: {e}")
        notify(f"{APP_NAME} ❌", str(e)[:120])
        _append_history({
            "id": _simple_hash(url),
            "url": url,
            "title": "",
            "filename": "",
            "filepath": "",
            "filesize": None,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "failed",
        })


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _handle_open_or_reveal(self, cmd: str, flag: Optional[str] = None) -> None:
        """Open a file with macOS `open`, optionally with a flag like `-R`."""
        origin = self.headers.get("Origin", "")
        if origin.startswith(("http://", "https://")):
            self.send_response(403)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            data = json.loads(raw)
            filepath = data.get("path", "")
            if not filepath or not Path(filepath).is_file():
                raise ValueError(f"file not found")
        except Exception as e:
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"bad request: {e}".encode())
            return

        argv = [cmd]
        if flag:
            argv.append(flag)
        argv.append(filepath)
        subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"opened":true}')

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
        elif path == "/probe":
            params = parse_qs(urlparse(self.path).query)
            target_url = params.get("url", [None])[0]
            if not target_url:
                self.send_response(400)
                self._cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"missing url"}')
                return

            try:
                result = subprocess.run(
                    [YT_DLP, "--dump-json", "--no-playlist", "--playlist-items", "1", target_url],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    info = json.loads(result.stdout.splitlines()[0])
                    data = {
                        "has_video": True,
                        "title": info.get("title"),
                        "duration": info.get("duration"),
                        "extractor": info.get("extractor_key"),
                    }
                else:
                    data = {"has_video": False}
            except subprocess.TimeoutExpired:
                data = {"has_video": False, "error": "timeout"}
            except Exception as e:
                data = {"has_video": False, "error": str(e)[:100]}

            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/history":
            entries = []
            if HISTORY_FILE.is_file():
                with _history_lock:
                    lines = HISTORY_FILE.read_text().strip().splitlines()
                for line in lines[-50:]:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            entries.reverse()
            body = json.dumps(entries, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/open":
            self._handle_open_or_reveal("open")
            return
        if path == "/reveal":
            self._handle_open_or_reveal("open", flag="-R")
            return
        if path == "/cancel":
            self._handle_cancel()
            return
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

    def _handle_cancel(self) -> None:
        """Cancel a running download by URL."""
        origin = self.headers.get("Origin", "")
        if origin.startswith(("http://", "https://")):
            self.send_response(403)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            data = json.loads(raw)
            url = data["url"]
        except Exception as e:
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"bad request: {e}".encode())
            return

        killed = cancel_download(url)
        body = json.dumps({"cancelled": killed}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
