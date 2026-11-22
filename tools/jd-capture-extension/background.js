/* JD Lens service worker. Click the toolbar icon on a job page: open the side panel and read that page.
 * Nothing runs in the background and nothing is read unless the panel is open. No network access. */
importScripts('extract.js');

const HOST = 'com.jdlens.helper';
let panelOpen = false;

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false }).catch(() => {});
});

// The panel connects while it is open, so we know when auto-scan on navigation is allowed.
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== 'panel') return;
  panelOpen = true;
  port.onDisconnect.addListener(() => { panelOpen = false; });
});

async function scanTab(tabId) {
  try {
    const [res] = await chrome.scripting.executeScript({ target: { tabId }, func: extractPage });
    const data = res && res.result;
    if (!data || !data.ok) return { ok: false, error: 'Could not read this page.' };
    return Object.assign({ tabId, at: Date.now() }, data);
  } catch (e) {
    return { ok: false, tabId, error: 'Chrome did not allow reading this page. Click the JD Lens icon while the page is open (restricted pages such as chrome:// cannot be read).' };
  }
}

// Remember which page each tab was scored on (tab id -> scan), so switching back to a tab we already read can show
// its JD again without reading anything. Chrome gives no tab URLs without extra permission, so this needs none.
async function remember(scan) {
  if (!scan || !scan.ok || scan.tabId == null) return;
  const { tabScans = {} } = await chrome.storage.session.get('tabScans');
  tabScans[scan.tabId] = scan;
  const ids = Object.keys(tabScans).sort((a, c) => (tabScans[a].at || 0) - (tabScans[c].at || 0));
  while (ids.length > 20) delete tabScans[ids.shift()];
  await chrome.storage.session.set({ tabScans });
}
async function forget(tabId) {
  const { tabScans = {} } = await chrome.storage.session.get('tabScans');
  if (tabScans[tabId]) { delete tabScans[tabId]; await chrome.storage.session.set({ tabScans }); }
}

async function publish(tabId) {
  const scan = await scanTab(tabId);
  await remember(scan);
  await chrome.storage.session.set({ lastScan: scan });
  chrome.runtime.sendMessage({ type: 'scan', scan }).catch(() => {});
  return scan;
}

chrome.action.onClicked.addListener(async (tab) => {
  // sidePanel.open must run in the click's user gesture, so it comes first
  try { await chrome.sidePanel.open({ tabId: tab.id }); } catch (e) { /* already open */ }
  await publish(tab.id);
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === 'rescan') {
    chrome.tabs.query({ active: true, lastFocusedWindow: true }).then(async ([tab]) => {
      let target = tab && tab.id;
      // When the panel is open in its own tab, re-read the job page it last scanned
      if (tab && (tab.url || '').startsWith('chrome-extension://')) {
        const { lastScan } = await chrome.storage.session.get('lastScan');
        target = lastScan && lastScan.tabId;
      }
      sendResponse(target ? await publish(target) : { ok: false, error: 'No job page to read. Click the JD Lens icon on the page.' });
    });
    return true; // async response
  }
  return false;
});

// Optional: with the "read job pages automatically" permission granted in Settings, re-scan when the panel is open.
// Without it: show the JD already scored in that tab if there is one, otherwise tell the panel the tab changed.
async function onTabChange(tabId) {
  if (!panelOpen) return;
  const granted = await chrome.permissions.contains({ origins: ['https://*/*', 'http://*/*'] });
  if (granted) { await publish(tabId); return; }
  const { tabScans = {}, lastScan } = await chrome.storage.session.get(['tabScans', 'lastScan']);
  const known = tabScans[tabId];
  if (known) {
    if (!lastScan || lastScan.tabId !== tabId) await chrome.storage.session.set({ lastScan: known });
    chrome.runtime.sendMessage({ type: 'scan', scan: known, restored: true }).catch(() => {});
  } else {
    chrome.runtime.sendMessage({ type: 'tab', tabId }).catch(() => {});
  }
}
chrome.tabs.onActivated.addListener(({ tabId }) => { onTabChange(tabId); });
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (info.status === 'loading') {
    // The tab is loading another page: what we scored there is out of date
    const { tabScans = {}, lastScan } = await chrome.storage.session.get(['tabScans', 'lastScan']);
    if (tabScans[tabId] || (lastScan && lastScan.tabId === tabId)) {
      await forget(tabId);
      if (panelOpen) chrome.runtime.sendMessage({ type: 'tab', tabId, navigated: true }).catch(() => {});
    }
  }
  if (info.status === 'complete' && tab.active) onTabChange(tabId);
});
chrome.tabs.onRemoved.addListener((tabId) => { forget(tabId); });
