// Xiaoer VideoLab — toolbar button → POST the current tab URL to the local daemon.
const DAEMON = "http://127.0.0.1:7788";
const APP = "Xiaoer VideoLab";

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

function flashBadge(text, color) {
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
