// Xiaoer VideoLab — toolbar button → POST the current tab URL to the local daemon.
// Note: When default_popup is set in manifest.json, onClicked won't fire on toolbar click.
// This handler is kept as a fallback for programmatic triggers and future enhancements.
const DAEMON = "http://127.0.0.1:7788";
const APP = "Xiaoer VideoLab";
const STORAGE_KEY = "videolab_pending";

if (chrome.action) {
  chrome.action.onClicked.addListener(async (tab) => {
    if (!tab?.url || !/^https?:/.test(tab.url)) {
      flashBadge("✕", "#c0392b");
      notify(APP, "This page is not an http(s) page.");
      return;
    }

    flashBadge("…", "#666");

    try {
      const res = await fetch(`${DAEMON}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: tab.url }),
      });
      if (res.status === 202) {
        flashBadge("✓", "#27ae60");
        // Persist pending
        const { [STORAGE_KEY]: pending = [] } = await chrome.storage.local.get(STORAGE_KEY);
        pending.unshift({ id: simpleHash(tab.url), url: tab.url, status: "queued", timestamp: new Date().toISOString() });
        await chrome.storage.local.set({ [STORAGE_KEY]: pending });
      } else {
        const txt = await res.text();
        flashBadge("!", "#e67e22");
        notify(APP, `daemon ${res.status}: ${txt.slice(0, 200)}`);
      }
    } catch (e) {
      flashBadge("✕", "#c0392b");
      notify(
        APP,
        `Can't reach the daemon (${e.message}). Make sure the daemon is running.`
      );
    }
  });
}

function flashBadge(text, color) {
  if (!chrome.action) return;
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3500);
}

function notify(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icon-128.png",
    title,
    message,
  });
}

// NOTE: also duplicated in popup.js — keep in sync
function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const c = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + c;
    hash |= 0;
  }
  return Math.abs(hash).toString(36).slice(0, 8);
}
