/* Shared by the side panel (panel.js) and the full-page Applications view (apps.js): the API layer (real Chrome or the
 * mock used for design screenshots and tests), a tiny DOM helper, icons, and small utilities. No network access. */
(() => {
  'use strict';
  const HOST = 'com.jdlens.helper';
  const params = new URLSearchParams(location.search);
  const MOCK = params.has('mock');
  const STATUSES = ['considering', 'applied', 'screening', 'interviewing', 'offer', 'rejected', 'withdrawn'];

  const realApi = {
    settings: {
      get: () => chrome.storage.local.get('settings').then((r) => r.settings || {}),
      set: (v) => chrome.storage.local.set({ settings: v }),
    },
    host: (op, args) => new Promise((resolve) => {
      try {
        chrome.runtime.sendNativeMessage(HOST, { op, args: args || {} }, (res) => {
          if (chrome.runtime.lastError) resolve({ ok: false, helper_missing: true, error: chrome.runtime.lastError.message });
          else resolve(res || { ok: false, error: 'empty response' });
        });
      } catch (e) { resolve({ ok: false, helper_missing: true, error: String(e) }); }
    }),
    rescan: () => chrome.runtime.sendMessage({ type: 'rescan' }),
    lastScan: () => chrome.storage.session.get('lastScan').then((r) => r.lastScan || null),
    onScan: (cb) => chrome.runtime.onMessage.addListener((m) => { if (m && m.type === 'scan') cb(m.scan); }),
    activeTab: () => chrome.tabs.query({ active: true, lastFocusedWindow: true }).then((t) => (t[0] && t[0].id != null ? t[0].id : null)).catch(() => null),
    tabScan: (id) => chrome.storage.session.get('tabScans').then((r) => (r.tabScans || {})[id] || null).catch(() => null),
    onTab: (cb) => chrome.runtime.onMessage.addListener((m) => { if (m && m.type === 'tab') cb(m); }),
    openUrl: (url) => chrome.tabs.create({ url }),
    openPanelTab: () => chrome.tabs.create({ url: chrome.runtime.getURL('panel.html?tab=1') }),
    openApps: (slug) => chrome.tabs.create({ url: chrome.runtime.getURL('applications.html') + (slug ? '#' + slug : '') }),
    loadJSON: (p) => fetch(chrome.runtime.getURL(p), { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    connect: () => { try { chrome.runtime.connect({ name: 'panel' }); } catch (e) { /* ignore */ } },
    requestAutoScan: () => chrome.permissions.request({ origins: ['https://*/*', 'http://*/*'] }),
    hasAutoScan: () => chrome.permissions.contains({ origins: ['https://*/*', 'http://*/*'] }),
  };
  const A = MOCK ? window.MockApi : realApi;
  // Profile and resume data: from the helper first (works for a store install, which has no data/ folder), else the packaged files
  async function loadData(names) {
    if (!MOCK) { const r = await A.host('get_data', { names }); if (r && r.ok && r.data) return r.data; }
    const out = {};
    for (const n of names) out[n] = await A.loadJSON('data/' + n + '.json');
    return out;
  }

  // ---- tiny DOM helper -----------------------------------------------------------------------------
  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k === 'on') for (const [ev, fn] of Object.entries(v)) el.addEventListener(ev, fn);
      else if (k === 'html') el.innerHTML = v;
      else if (k === 'text') el.textContent = v;
      else if (k === 'value') el.value = v;
      else if (k === 'title') el.setAttribute('data-tip', v); // shown by our own tooltip, not the slow system one
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return el;
  }
  const S = (inner) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;
  const ICONS = {
    doc: S('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>'),
    user: S('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
    refresh: S('<path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'),
    gear: S('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
    pin: S('<path d="M12 17v5"/><path d="M9 3h6l-1 7 3 3v2H7v-2l3-3z"/>'),
    x: S('<path d="M18 6L6 18M6 6l12 12"/>'),
    sparkle: S('<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 3v4M17 5h4"/>'),
    briefcase: S('<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>'),
    bolt: S('<path d="M13 2L3 14h9l-1 8 10-12h-9z"/>'),
    bulb: S('<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>'),
    crown: S('<path d="M3 7l4 4 5-7 5 7 4-4-2 12H5z"/>'),
    info: S('<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>'),
    chart: S('<path d="M18 20V10M12 20V4M6 20v-6"/>'),
    ext: S('<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/>'),
    arrow: S('<path d="M5 12h14M12 5l7 7-7 7"/>'),
    check: S('<path d="M20 6L9 17l-5-5"/>'),
    up: S('<path d="M12 19V5M5 12l7-7 7 7"/>'),
    down: S('<path d="M12 5v14M19 12l-7 7-7-7"/>'),
    chev: S('<path d="M9 18l6-6-6-6"/>'),
    back: S('<path d="M15 18l-6-6 6-6"/>'),
    people: S('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>'),
    list: S('<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>'),
    minus: S('<path d="M5 12h14"/>'),
    half: S('<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>'),
    trash: S('<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6"/>'),
    warn: S('<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/>'),
    cross: S('<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/>'),
  };
  const ic = (name, cls) => h('span', { class: 'ic' + (cls ? ' ' + cls : ''), html: ICONS[name] || '' });
  const LOGO = '<svg viewBox="0 0 128 128" aria-hidden="true"><defs> <linearGradient id="lgx" x1="8" y1="6" x2="122" y2="124" gradientUnits="userSpaceOnUse"><stop offset="0" style="stop-color:var(--grad-text-a)"/><stop offset="1" style="stop-color:var(--grad-text-b)"/></linearGradient> <mask id="lmx-sheet" maskUnits="userSpaceOnUse" x="0" y="0" width="128" height="128"><rect width="128" height="128" fill="#fff"/><circle cx="70" cy="70" r="42" fill="#000"/><path d="M94 94l20 20" stroke="#000" stroke-width="22" stroke-linecap="round"/></mask> <mask id="lmx-lens" maskUnits="userSpaceOnUse" x="0" y="0" width="128" height="128"><rect width="128" height="128" fill="#fff"/><circle cx="70" cy="58" r="10" fill="#000"/><path d="M50 92a20 17 0 0 1 40 0z" fill="#000"/></mask> </defs> <rect class="logo-tile" width="128" height="128" rx="30" fill="#1B1722"/> <g mask="url(#lmx-sheet)" fill="none" stroke="url(#lgx)" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"> <path d="M34 10H70a16 16 0 0 1 16 16V92a16 16 0 0 1-16 16H26a16 16 0 0 1-16-16V34z"/> <path d="M34 10V34H10" stroke-width="7"/> </g> <g class="lens-anim"><circle cx="70" cy="70" r="34" fill="url(#lgx)" mask="url(#lmx-lens)"/> <path d="M94 94l20 20" stroke="url(#lgx)" stroke-width="13" stroke-linecap="round"/></g></svg>';
  function ring(pct) {
    const r = 34, c = 2 * Math.PI * r, p = Math.max(0, Math.min(100, pct || 0));
    return h('span', { class: 'ring', html: `<svg viewBox="0 0 88 88" width="100%" height="100%" role="img" aria-label="match ${p} percent"><defs><linearGradient id="rg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#D95F55"/><stop offset="1" stop-color="#CF7F24"/></linearGradient></defs><circle cx="44" cy="44" r="${r}" fill="none" stroke="var(--track)" stroke-width="10"/><circle cx="44" cy="44" r="${r}" fill="none" stroke="url(#rg)" stroke-width="10" stroke-linecap="round" stroke-dasharray="${(c * p / 100).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 44 44)"/></svg>` });
  }

  // ---- utilities -----------------------------------------------------------------------------------
  const slugify = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  const ym = (d) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
  const normUrl = (u) => { try { const x = new URL(u); return (x.origin + x.pathname).toLowerCase().replace(/\/+$/, ''); } catch (e) { return (u || '').toLowerCase(); } };
  const fmtDate = (iso) => { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); };
  const years = (start) => { const m = /^(\d{4})-(\d{2})/.exec(start || ''); if (!m) return 0; const n = new Date(); return Math.floor(((n.getFullYear() - +m[1]) * 12 + (n.getMonth() + 1 - +m[2])) / 12); };
  const daysAgoDate = (days) => { const d = new Date(); d.setDate(d.getDate() - days); return d.toISOString().slice(0, 10); };

  // Chrome's side panel has no page zoom (Cmd +/- only zoom the tab), so the pages scale themselves: every size is in rem.
  const SCALES = [0.9, 1, 1.15, 1.3, 1.5, 1.75, 2];
  const SCALE_LABELS = { 0.9: 'Small', 1: 'Default', 1.15: 'Medium', 1.3: 'Large', 1.5: 'Larger', 1.75: 'Huge', 2: 'Max' };
  function applyTheme(settings) {
    const t = settings.theme;
    if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
    if (MOCK && params.get('theme')) document.documentElement.dataset.theme = params.get('theme');
  }
  function applyScale(settings, narrowBelow) {
    const sc = SCALES.includes(settings.textScale) ? settings.textScale : 1;
    document.documentElement.style.fontSize = (16 * sc) + 'px';
    const width = (document.getElementById('app') || document.body).clientWidth || window.innerWidth;
    document.documentElement.classList.toggle('narrow', width / sc < (narrowBelow || 330));
  }
  function bindZoomKeys(bump) {
    window.addEventListener('keydown', (e) => {
      if (!(e.metaKey || e.ctrlKey) || e.altKey) return;
      if (e.key === '=' || e.key === '+') bump(1);
      else if (e.key === '-' || e.key === '_') bump(-1);
      else if (e.key === '0') bump(0);
      else return;
      e.preventDefault();
    });
  }
  async function copyText(text) {
    try { await navigator.clipboard.writeText(text); }
    catch (e) { const t = h('textarea', { style: 'position:fixed;opacity:0' }); t.value = text; document.body.append(t); t.select(); document.execCommand('copy'); t.remove(); }
  }
  async function openFile(path) {
    try { await A.openUrl('file://' + encodeURI(path)); return true; }
    catch (e) { await copyText(path); return false; }
  }

  // ---- our own tooltip: quick, rounded, larger text (replaces the system tooltip, which lags) -----------
  let tipEl = null, tipTimer = null;
  function showTip(target) {
    const text = target.getAttribute('data-tip');
    if (!text) return;
    if (!tipEl) { tipEl = h('div', { class: 'tip', role: 'tooltip', id: 'jd-tip' }); document.body.append(tipEl); }
    tipEl.textContent = text;
    tipEl.style.maxWidth = Math.min(280, window.innerWidth - 16) + 'px';
    tipEl.classList.add('on');
    const r = target.getBoundingClientRect(), t = tipEl.getBoundingClientRect();
    let left = Math.max(8, Math.min(window.innerWidth - t.width - 8, r.left + r.width / 2 - t.width / 2));
    let top = r.bottom + 8;
    if (top + t.height > window.innerHeight - 8) top = Math.max(8, r.top - t.height - 8);
    tipEl.style.left = left + 'px'; tipEl.style.top = top + 'px';
    target.setAttribute('aria-describedby', 'jd-tip');
  }
  function hideTip() { clearTimeout(tipTimer); if (tipEl) tipEl.classList.remove('on'); document.querySelectorAll('[aria-describedby="jd-tip"]').forEach((n) => n.removeAttribute('aria-describedby')); }
  document.addEventListener('mouseover', (e) => { const t = e.target.closest && e.target.closest('[data-tip]'); if (!t) return; clearTimeout(tipTimer); tipTimer = setTimeout(() => showTip(t), 120); });
  document.addEventListener('mouseout', (e) => { if (e.target.closest && e.target.closest('[data-tip]')) hideTip(); });
  document.addEventListener('focusin', (e) => { const t = e.target.closest && e.target.closest('[data-tip]'); if (t) showTip(t); });
  document.addEventListener('focusout', hideTip);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideTip(); });
  document.addEventListener('click', hideTip, true);

  // ---- small, safe markdown renderer (headings, bold, italic, code, lists, tables, paragraphs) ----------
  // Builds DOM nodes with textContent only, so file content can never inject HTML.
  function mdInline(text) {
    const out = [], re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g;
    let last = 0, m;
    while ((m = re.exec(text))) {
      if (m.index > last) out.push(text.slice(last, m.index));
      const t = m[0];
      out.push(t.startsWith('**') ? h('strong', null, t.slice(2, -2)) : t.startsWith('`') ? h('code', null, t.slice(1, -1)) : h('em', null, t.slice(1, -1)));
      last = m.index + t.length;
    }
    if (last < text.length) out.push(text.slice(last));
    return out;
  }
  function renderMarkdown(src) {
    const lines = String(src || '').replace(/\r/g, '').split('\n'), root = h('div', { class: 'md' });
    const cells = (l) => l.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
    let i = 0;
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim()) { i++; continue; }
      let m = l.match(/^(#{1,6})\s+(.*)$/);
      if (m) { root.append(h('h' + Math.min(6, m[1].length + 2), null, mdInline(m[2]))); i++; continue; }
      if (/^\s*\|/.test(l) && i + 1 < lines.length && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) {
        const head = cells(l); i += 2; const rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(cells(lines[i++]));
        root.append(h('div', { class: 'md-table' }, h('table', null, h('thead', null, h('tr', null, head.map((c) => h('th', null, mdInline(c))))),
          h('tbody', null, rows.map((r) => h('tr', null, r.map((c) => h('td', null, mdInline(c)))))))));
        continue;
      }
      if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
        const ordered = /^\s*\d+\./.test(l), items = [];
        while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*([-*]|\d+\.)\s+/, ''));
        root.append(h(ordered ? 'ol' : 'ul', null, items.map((t) => h('li', null, mdInline(t)))));
        continue;
      }
      const para = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,6}\s|\s*\||\s*([-*]|\d+\.)\s+)/.test(lines[i])) para.push(lines[i++].trim());
      root.append(h('p', null, mdInline(para.join(' '))));
    }
    return root;
  }
  window.addEventListener('error', (e) => { document.body.dataset.error = e.message; });
  window.addEventListener('unhandledrejection', (e) => { document.body.dataset.error = String(e.reason); });

  // The animated logo, shown while the panel starts and while a page is being read (the lens sways over the sheet)
  const loader = (text) => h('div', { class: 'loader', role: 'status', 'aria-live': 'polite' }, h('div', { class: 'loader-logo', html: LOGO }), h('div', { class: 'loader-text' }, text || 'Reading this job...'));
  window.JDV = { HOST, loader, loadData, params, MOCK, STATUSES, A, h, S, ICONS, ic, LOGO, ring, slugify, ym, normUrl, fmtDate, years, daysAgoDate,
                 SCALES, SCALE_LABELS, applyTheme, applyScale, bindZoomKeys, copyText, openFile, renderMarkdown };
})();
