#!/usr/bin/env bash
# Xiaoer VideoLab — install the daemon as a macOS launchd background service.
# The LaunchAgent plist is GENERATED here so the paths match wherever you cloned the repo.
#
# Optional config (export before running, or prefix the command):
#   VIDEOLAB_COOKIES_BROWSER=brave ./scripts/install.sh   # for login-gated videos
#   VIDEOLAB_PREFIX="小耳-" ./scripts/install.sh           # filename prefix
#   VIDEOLAB_MAX_HEIGHT=2160 ./scripts/install.sh          # allow 4K
#   VIDEOLAB_DOWNLOADS="$HOME/Movies" ./scripts/install.sh # change download dir
set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
  echo "✗ This installer is macOS-only (it uses launchd)." >&2
  echo "  On Linux/Windows you can still run the daemon manually:" >&2
  echo "    python3 daemon/server.py" >&2
  exit 1
fi

LABEL="com.xiaoer.videolab"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER="$PROJECT_DIR/daemon/server.py"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"

# Prefer the system python3 (stdlib only — no venv surprises under launchd).
if [[ -x /usr/bin/python3 ]]; then
  PYTHON=/usr/bin/python3
else
  PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PYTHON" ]] || { echo "✗ python3 not found." >&2; exit 1; }

YT_DLP="$(command -v yt-dlp || true)"
if [[ -z "$YT_DLP" ]]; then
  echo "✗ yt-dlp not found. Install it first:  brew install yt-dlp" >&2
  exit 1
fi
YT_DLP_DIR="$(dirname "$YT_DLP")"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

# Build the optional <EnvironmentVariables> entries from any VIDEOLAB_* that are set.
ENV_XML="    <key>PATH</key><string>${YT_DLP_DIR}:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key><string>${HOME}</string>
    <key>VIDEOLAB_YT_DLP</key><string>${YT_DLP}</string>"
for var in VIDEOLAB_PORT VIDEOLAB_DOWNLOADS VIDEOLAB_PREFIX VIDEOLAB_MAX_HEIGHT VIDEOLAB_COOKIES_BROWSER VIDEOLAB_APP_NAME; do
  val="${!var:-}"
  if [[ -n "$val" ]]; then
    ENV_XML+=$'\n'"    <key>${var}</key><string>${val}</string>"
  fi
done

if launchctl list | grep -q "$LABEL"; then
  echo "→ Existing service found, unloading first."
  launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

cat > "$PLIST_DST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON}</string>
        <string>${SERVER}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>5</integer>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/xiaoer-videolab.out.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/xiaoer-videolab.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
${ENV_XML}
    </dict>
</dict>
</plist>
PLIST

launchctl load "$PLIST_DST"

echo "→ Waiting for the daemon to come up..."
for _ in $(seq 1 10); do
  if curl -fsS http://127.0.0.1:7788/health >/dev/null 2>&1; then
    echo "✓ Daemon running at http://127.0.0.1:7788"
    echo "  Log: ~/Library/Logs/xiaoer-videolab.log"
    echo
    echo "Next: load the browser extension"
    echo "  1. Open chrome://extensions/  (Chrome / Arc / Edge / Brave — any MV3 browser)"
    echo "  2. Turn on 'Developer mode'"
    echo "  3. Click 'Load unpacked'"
    echo "  4. Select: $PROJECT_DIR/extension/"
    echo "  5. Pin the icon to the toolbar."
    exit 0
  fi
  sleep 0.5
done

echo "✗ Daemon did not start. Check the log:" >&2
echo "  tail ~/Library/Logs/xiaoer-videolab.err.log" >&2
exit 1
