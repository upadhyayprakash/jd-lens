/* Applications: the dedicated full-page view. Dashboard counts, filters, sort, application cards, and for one application
 * its information, files, gaps, interview rounds, status update and status history. Reads and writes through the local helper
 * (tools/jobs.py); without the helper it shows a read-only snapshot. */
(() => {
  'use strict';
  const J = window.JDV;
  const { A, h, ic, LOGO, fmtDate, STATUSES, SCALES, SCALE_LABELS, params } = J;
  const FILTERS = ['all', 'applied', 'interviewing', 'considering', 'screening', 'offer', 'rejected', 'withdrawn'];
  const DASH = [['all', 'Total saved'], ['considering', 'Considering'], ['applied', 'Applied'], ['screening', 'Screening'], ['interviewing', 'Interviewing'], ['offer', 'Offers'], ['rejected', 'Rejected'], ['withdrawn', 'Withdrawn']];
  const state = { apps: [], filter: FILTERS.includes(params.get('filter')) ? params.get('filter') : 'all', sort: ['recent', 'best', 'added'].includes(params.get('sort')) ? params.get('sort') : 'recent', q: '', selected: (location.hash || '').slice(1) || null, detail: null, gaps: '', helper: null, readonly: false,
                  settings: { textScale: 1, theme: 'system' }, toast: '', error: '', roundForm: false, statusNote: '', repo: '', del: null };
  let toastTimer = null;

  const toast = (m) => { state.toast = m; render(); clearTimeout(toastTimer); toastTimer = setTimeout(() => { state.toast = ''; render(); }, 2400); };
  // Terminal fallbacks: with your data folder apart from the engine, run in the data folder and point Claude and the tools at the engine.
  const cmd = (inner) => {
    const dataDir = state.repo || '/path/to/jd-lens', engine = (state.helper && state.helper.ok && state.helper.engine) || '';
    let c = inner;
    if (engine && dataDir && engine !== dataDir) c = c.replace(/\btools\/([\w./-]+)/g, (m, f) => `"${engine}/tools/${f}"`).replace(/\bclaude "/g, `claude --add-dir "${engine}" "`);
    return `cd "${dataDir}" && ${c}`;
  };
  async function copy(t) { await J.copyText(t); toast('Copied. Paste it in a terminal.'); }
  async function openFile(p) { if (!(await J.openFile(p))) toast('Could not open it from here. Path copied.'); }

  // ---- data ----------------------------------------------------------------------------------------
  async function load() {
    const ping = await A.host('ping');
    state.helper = ping; state.readonly = !ping.ok; state.repo = ping.repo || '';
    if (ping.ok) { const r = await A.host('list'); state.apps = r.ok ? r.applications : []; }
    else {
      const fb = await A.loadJSON('data/applications.json');
      state.apps = (fb && fb.applications) || [];
      const prof = await A.loadJSON('data/profile.json'); state.repo = (prof && prof.repo_path) || '';
    }
    if (state.selected && !state.apps.find((a) => a.slug === state.selected)) state.selected = null;
    if (state.selected) await select(state.selected, true);
  }
  async function select(slug, quiet) {
    state.selected = slug; state.roundForm = false; state.statusNote = '';
    if (!quiet) history.replaceState(null, '', '#' + slug);
    if (state.readonly) { state.detail = Object.assign({ rounds: [], history: [], files: {} }, state.apps.find((a) => a.slug === slug)); state.gaps = ''; state.fit = ''; state.brag = ''; render(); return; }
    const r = await A.host('show', { slug });
    if (!r.ok) { state.error = r.error; render(); return; }
    state.detail = r.application;
    const g = await A.host('read_section', { slug, section: 'Gaps vs JD' });
    state.gaps = g.ok && g.found ? g.text : '';
    const f = await A.host('read_section', { slug, section: 'Fit' });
    state.fit = f.ok && f.found ? f.text : '';
    const bs = await A.host('read_section', { slug, section: 'Brag Sheet' });
    state.brag = bs.ok && bs.found ? bs.text : '';
    render();
  }
  const fmtBytes = (b) => (b < 1024 ? b + ' B' : (b / 1024).toFixed(b < 10240 ? 1 : 0) + ' KB');
  async function askDelete(d) {
    const r = await A.host('delete_preview', { slug: d.slug });
    if (!r.ok) { state.error = r.error; render(); return; }
    state.error = ''; state.del = { slug: d.slug, company: d.company, role: d.role, items: r.items, busy: false }; render();
  }
  function closeDelete() { if (state.del && !state.del.busy) { state.del = null; render(); } }
  async function doDelete() {
    const x = state.del; if (!x || x.busy) return;
    x.busy = true; render();
    const r = await A.host('delete_app', { slug: x.slug, confirm: x.slug });
    state.del = null;
    if (!r.ok) { state.error = r.error; render(); return; }
    state.error = ''; state.selected = null; state.detail = null; history.replaceState(null, '', location.pathname + location.search);
    await reload(); toast('Deleted ' + x.company + '. Kept in ' + r.trash + ' until you remove that folder.');
  }
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDelete(); });
  async function reload() { const r = await A.host('list'); if (r.ok) state.apps = r.applications; if (state.selected) await select(state.selected, true); else render(); }
  async function setStatus(slug, status) {
    const r = await A.host('status', { slug, status, note: state.statusNote || undefined });
    if (!r.ok) { state.error = r.error; render(); return; }
    state.statusNote = ''; await reload(); toast('Status: ' + status);
  }
  async function saveSettings(patch) {
    Object.assign(state.settings, patch); await A.settings.set(state.settings);
    J.applyTheme(state.settings); J.applyScale(state.settings, 520); render();
  }
  async function bump(dir) {
    const cur = SCALES.includes(state.settings.textScale) ? SCALES.indexOf(state.settings.textScale) : 1;
    await saveSettings({ textScale: dir === 0 ? 1 : SCALES[Math.min(SCALES.length - 1, Math.max(0, cur + dir))] });
  }
  J.bindZoomKeys(bump);
  window.addEventListener('resize', () => J.applyScale(state.settings, 520));
  window.addEventListener('hashchange', () => { const s = (location.hash || '').slice(1); if (s && s !== state.selected) select(s, true); });

  // ---- derived -------------------------------------------------------------------------------------
  const counts = () => { const c = { all: state.apps.length }; STATUSES.forEach((s) => { c[s] = state.apps.filter((a) => a.status === s).length; }); return c; };
  const matchOf = (a) => (a.fit_score != null ? a.fit_score : a.quick_score);
  function visible() {
    let v = state.apps.filter((a) => state.filter === 'all' || a.status === state.filter);
    if (state.q.trim()) { const q = state.q.toLowerCase(); v = v.filter((a) => (a.company + ' ' + a.role + ' ' + (a.location || '')).toLowerCase().includes(q)); }
    const key = { recent: (a) => a.last_activity || '', best: (a) => (matchOf(a) == null ? -1 : matchOf(a)), added: (a) => a.added || '' }[state.sort];
    return v.slice().sort((a, b) => (key(b) > key(a) ? 1 : key(b) < key(a) ? -1 : a.slug.localeCompare(b.slug)));
  }

  // ---- views ---------------------------------------------------------------------------------------
  function head() {
    return h('div', { class: 'apps-head' }, h('div', { class: 'brand', html: LOGO + '<span>JD Lens</span>' }), h('h1', { style: 'margin-left:.75rem' }, 'Applications'), h('div', { class: 'spacer' }),
      h('button', { class: 'ibtn', 'aria-label': 'Smaller text', on: { click: () => bump(-1) } }, 'A-'), h('button', { class: 'ibtn', 'aria-label': 'Larger text', on: { click: () => bump(1) } }, 'A+'),
      h('div', { class: 'segmented', role: 'group', 'aria-label': 'Theme' }, [['system', 'System'], ['light', 'Light'], ['dark', 'Dark']].map(([v, l]) => h('button', { 'aria-pressed': String(state.settings.theme === v), on: { click: () => saveSettings({ theme: v }) } }, l))));
  }
  function dashboard() {
    const c = counts();
    return h('div', { class: 'dash', role: 'group', 'aria-label': 'Application counts' }, DASH.map(([k, label]) => h('button', { 'aria-pressed': String(state.filter === k), on: { click: () => { state.filter = k; render(); } } }, h('b', null, String(c[k])), h('span', null, label))));
  }
  function toolbar() {
    return h('div', { class: 'toolbar' },
      h('div', { class: 'filters', role: 'group', 'aria-label': 'Filter by status' }, FILTERS.map((f) => h('button', { 'aria-pressed': String(state.filter === f), on: { click: () => { state.filter = f; render(); } } }, f[0].toUpperCase() + f.slice(1)))),
      h('select', { 'aria-label': 'Sort', on: { change: (e) => { state.sort = e.target.value; render(); } } }, [['recent', 'Most recent activity'], ['best', 'Best match'], ['added', 'Date added']].map(([v, l]) => h('option', { value: v, selected: state.sort === v ? true : null }, l))),
      h('input', { type: 'search', placeholder: 'Search company or role', 'aria-label': 'Search', value: state.q, on: { input: (e) => { state.q = e.target.value; render(); const i = document.querySelector('input[type=search]'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); } } }));
  }
  function card(a) {
    const m = matchOf(a);
    return h('button', { class: 'appcard', 'aria-current': String(state.selected === a.slug), on: { click: () => select(a.slug) } },
      h('div', { class: 'between' }, h('span', { class: 'co' }, a.company), h('span', { class: 'pill ' + a.status }, a.status)),
      h('div', { class: 'ti' }, a.role),
      h('div', { class: 'meta' }, m != null ? h('span', { class: 'score-chip', title: a.fit_score != null ? 'Full score' : 'Keyword score' }, (a.fit_score != null ? 'Match ' : 'Keyword ') + m) : h('span', null, 'Not scored'),
        h('span', null, 'Added ' + (fmtDate(a.added) || 'n/a')), a.applied ? h('span', null, 'Applied ' + fmtDate(a.applied)) : null, a.location ? h('span', null, a.location.length > 36 ? a.location.slice(0, 34) + '...' : a.location) : null));
  }
  function infoCard(d) {
    const rows = [['Company', d.company], ['Role', d.role], ['Location', d.location || 'not stated'], ['Posting date', d.posted ? fmtDate(d.posted) : 'unknown'],
      ['Match', (d.fit_score != null ? `${d.fit_score} (full score)` : 'not fully scored') + (d.quick_score != null ? ` · keyword ${d.quick_score}` : '')], ['Added', fmtDate(d.added) || 'n/a'], ['Applied', d.applied ? fmtDate(d.applied) : 'not applied']];
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('briefcase'), 'Job information'),
      h('div', { class: 'between', style: 'margin-bottom:.75rem' }, h('span', { class: 'pill ' + d.status }, d.status), d.source && d.source.startsWith('http') ? h('button', { class: 'link-btn', on: { click: () => A.openUrl(d.source) } }, 'Original posting', ic('ext')) : null),
      h('dl', { class: 'kv' }, rows.map(([k, v]) => [h('dt', null, k), h('dd', null, v)])));
  }
  function filesCard(d) {
    const f = d.files || {};
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('doc'), 'Files'),
      h('div', { class: 'files' }, h('button', { class: 'btn', disabled: d.resume_exists ? null : true, on: { click: () => openFile(f.resume) } }, 'Resume submitted (PDF)'),
        h('button', { class: 'btn', disabled: d.source && d.source.startsWith('http') ? null : true, on: { click: () => A.openUrl(d.source) } }, 'Original job posting'),
        h('button', { class: 'btn', disabled: f.details_html ? null : true, on: { click: () => openFile(f.details_html) } }, 'Full job details (HTML)'),
        h('button', { class: 'btn', disabled: f.application ? null : true, on: { click: () => copy(f.application) } }, 'Copy file path')));
  }
  function roundsCard(d) {
    const rounds = d.rounds || [];
    return h('div', { class: 'card' }, h('div', { class: 'between' }, h('div', { class: 'card-title', style: 'margin:0' }, ic('people'), 'Interview rounds'),
        state.roundForm || state.readonly ? null : h('button', { class: 'link-btn', on: { click: () => { state.roundForm = true; render(); } } }, 'Add round', ic('arrow'))),
      rounds.length ? h('div', { style: 'overflow:auto;margin-top:.5rem' }, h('table', { class: 'tbl' }, h('thead', null, h('tr', null, ['Date', 'Round', 'Interviewer', 'Notes', 'Outcome'].map((x) => h('th', null, x)))),
        h('tbody', null, rounds.map((r) => h('tr', null, [r[0], r[1], r[2] || '-', r[3] || '-', r[4] || '-'].map((x) => h('td', null, x))))))) : h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'No rounds logged yet.'),
      state.roundForm ? roundForm(d.slug) : null);
  }
  function roundForm(slug) {
    const f = { round: '', date: '', interviewer: '', notes: '', result: '' };
    const field = (k, label, type, cls) => h('div', { class: cls || '' }, h('label', { class: 'field' }, label), type === 'area' ? h('textarea', { 'aria-label': label, on: { input: (e) => { f[k] = e.target.value; } } }) : h('input', { type: type || 'text', 'aria-label': label, on: { input: (e) => { f[k] = e.target.value; } } }));
    return h('div', null, h('div', { class: 'formgrid' }, field('round', 'Round or interview type (for example Technical)'), field('date', 'Date', 'date'), field('interviewer', 'Interviewer'), field('result', 'Outcome'), field('notes', 'Notes', 'area', 'wide2')),
      h('div', { class: 'row', style: 'margin-top:.75rem;max-width:24rem' }, h('button', { class: 'btn primary', on: { click: async () => {
        if (!f.round.trim()) { toast('Add a round name'); return; }
        const r = await A.host('round', { slug, round: f.round, date: f.date || undefined, interviewer: f.interviewer, notes: f.notes, result: f.result });
        if (!r.ok) { state.error = r.error; render(); return; }
        state.roundForm = false; await reload(); toast('Round logged');
      } } }, 'Save round'), h('button', { class: 'btn', on: { click: () => { state.roundForm = false; render(); } } }, 'Cancel')));
  }
  function statusCard(d) {
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Update status'),
      h('div', { class: 'filters' }, STATUSES.map((s) => h('button', { 'aria-pressed': String(d.status === s), disabled: d.status === s || state.readonly ? true : null, on: { click: () => setStatus(d.slug, s) } }, s))),
      h('label', { class: 'field' }, 'Optional note for the history'), h('input', { type: 'text', value: state.statusNote, placeholder: 'For example: Recruiter replied', 'aria-label': 'Status note', on: { input: (e) => { state.statusNote = e.target.value; } } }),
      h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Changes are added to the status history. Nothing is overwritten, and the previous file is kept in applications/.history.'),
      h('details', { class: 'terminal' }, h('summary', null, 'Or in a terminal'), h('div', { class: 'cmd' }, h('code', null, cmd(`claude "/job status ${d.slug} screening"`)), h('button', { class: 'btn small', on: { click: () => copy(cmd(`claude "/job status ${d.slug} screening"`)) } }, 'Copy')),
        h('div', { class: 'cmd' }, h('code', null, cmd(`claude "/interview prep ${d.slug.split('-')[0]}"`)), h('button', { class: 'btn small', on: { click: () => copy(cmd(`claude "/interview prep ${d.slug.split('-')[0]}"`)) } }, 'Copy'))));
  }
  function historyCard(d) {
    const hist = (d.history || []).slice().reverse();
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('list'), 'Status history'),
      hist.length ? h('ul', { class: 'timeline' }, hist.map((x) => h('li', null, h('div', { class: 'when' }, fmtDate(x[0]) || x[0]), h('div', null, x[1] && x[1] !== '-' ? [h('span', { class: 'pill ' + x[1] }, x[1]), ' → '] : 'Added as ', h('span', { class: 'pill ' + x[2] }, x[2])), x[3] ? h('div', { class: 'faint' }, x[3]) : null)))
        : h('div', { class: 'faint' }, 'No status changes recorded yet. The next change starts the history.'));
  }
  function assessmentCard(d) {
    const when = d.fit_scored ? ` on ${fmtDate(d.fit_scored)}` : '';
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('sparkle'), "Claude's assessment"),
      state.fit ? [h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, `${d.fit_score != null ? 'Full score ' + d.fit_score + when + '. ' : ''}Latest run, from the application file.`),
        h('div', { class: 'proposal md-wrap', style: 'max-height:none' }, window.JDV.renderMarkdown(state.fit))]
        : h('div', { class: 'faint' }, 'No written assessment yet. Open this JD in the panel and run Get the full score.'));
  }
  async function openBrag(slug) {
    const r = await A.host('brag_view', { slug });
    if (!r.ok || !r.found) { state.error = r.error || 'The Brag Sheet page could not be built.'; render(); return; }
    await openFile(r.html);
  }
  function bragCard(d) {
    return h('div', { class: 'card' }, h('div', { class: 'between' }, h('div', { class: 'card-title', style: 'margin:0' }, ic('crown'), 'Brag Sheet'),
        state.brag ? h('button', { class: 'btn small', on: { click: () => openBrag(d.slug) } }, 'Open full page') : null),
      state.brag ? h('div', { class: 'proposal md-wrap', style: 'max-height:none;margin-top:.5rem' }, window.JDV.renderMarkdown(state.brag))
        : h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Not made yet. Open this JD in the panel and choose Make Brag Sheet.'));
  }
  function dangerCard(d) {
    return h('div', { class: 'card danger-card' },
      h('div', { class: 'card-title' }, ic('warn'), 'Danger zone'),
      h('div', { class: 'danger-row' },
        h('div', null, h('b', null, 'Delete this JD and all its data'), h('div', { class: 'faint' }, 'Removes the application file, its backups, the tailored resume folder and the Brag Sheet page, so you can start the workflow again from a fresh capture.')),
        h('button', { class: 'btn danger', disabled: state.readonly ? true : null, title: state.readonly ? 'Needs the local helper' : null, on: { click: () => askDelete(d) } }, ic('trash'), 'Delete JD and data')));
  }
  function deleteDialog() {
    const x = state.del; if (!x) return null;
    const total = x.items.reduce((n, i) => n + i.bytes, 0);
    return h('div', { class: 'scrim', on: { mousedown: (e) => { if (e.target === e.currentTarget) closeDelete(); } } },
      h('div', { class: 'modal danger', role: 'alertdialog', 'aria-modal': 'true', 'aria-labelledby': 'del-title', 'aria-describedby': 'del-body' },
        h('div', { class: 'modal-head' }, ic('warn'), h('h2', { id: 'del-title' }, 'Delete ' + x.company + ' and all its data?')),
        h('div', { id: 'del-body' },
          h('p', { class: 'muted' }, x.role + '. This will remove everything below (' + fmtBytes(total) + ') and take the JD off the Applications list.'),
          h('ul', { class: 'del-list' }, x.items.map((i) => h('li', null, h('b', null, i.label), h('span', { class: 'faint' }, ' ' + fmtBytes(i.bytes)), h('div', { class: 'mono faint' }, i.paths.length > 2 ? i.paths[0] + ' and ' + (i.paths.length - 1) + ' more' : i.paths.join(', '))))),
          h('p', { class: 'faint' }, 'Nothing is erased: the files move to a .trash folder in your repo, so you can put them back by hand. Your interview answers and stories are not touched.')),
        h('div', { class: 'modal-actions' },
          h('button', { class: 'btn', 'data-autofocus': '1', disabled: x.busy ? true : null, on: { click: closeDelete } }, 'Cancel'),
          h('button', { class: 'btn danger solid', disabled: x.busy ? true : null, on: { click: doDelete } }, ic('trash'), x.busy ? 'Deleting...' : 'Delete everything'))));
  }
  function detailPane() {
    const d = state.detail;
    if (!d) return h('div', { class: 'detail' }, h('div', { class: 'card empty-state' }, 'Select an application to see its details.'));
    return h('div', { class: 'detail' }, h('button', { class: 'btn back', on: { click: () => { state.selected = null; state.detail = null; history.replaceState(null, '', location.pathname + location.search); render(); } } }, ic('back'), 'All applications'),
      h('div', { class: 'card' }, h('div', { class: 'company-name', style: 'font-size:1.25rem;font-weight:700' }, d.company), h('div', { class: 'muted' }, d.role)),
      infoCard(d), assessmentCard(d), bragCard(d), filesCard(d), h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Gaps noted'), h('div', { class: state.gaps ? 'proposal md-wrap' : 'faint' }, state.gaps ? window.JDV.renderMarkdown(state.gaps) : 'None recorded in the application file.')),
      roundsCard(d), statusCard(d), historyCard(d), dangerCard(d));
  }
  function render() {
    const root = document.getElementById('app');
    root.replaceChildren(head());
    if (state.error) root.append(h('div', { class: 'banner bad', role: 'alert' }, h('div', { class: 'grow' }, h('b', null, 'Something went wrong. '), state.error)));
    if (state.readonly) root.append(h('div', { class: 'banner warn stack' }, h('div', null, h('b', null, 'Local helper not connected. '), 'Showing the last saved snapshot, read only. Install the helper once to see live data and make changes:'), h('div', { class: 'cmd' }, h('code', null, cmd('python3 tools/jobd/install.py')), h('button', { class: 'btn small', on: { click: () => copy(cmd('python3 tools/jobd/install.py')) } }, 'Copy'))));
    const list = visible();
    root.append(dashboard(), toolbar(), h('div', { class: 'apps-grid' + (state.selected ? ' has-selection' : '') },
      h('div', { class: 'applist' }, list.length ? list.map(card) : h('div', { class: 'card empty-state' }, state.apps.length ? 'No applications match this filter.' : 'No applications yet. Open a job page and use Save JD in the side panel.')), detailPane()));
    const dlg = deleteDialog(); if (dlg) { root.append(dlg); const f = dlg.querySelector('[data-autofocus]'); if (f) f.focus(); }
    if (state.toast) root.append(h('div', { class: 'toast', role: 'status' }, state.toast));
    document.body.dataset.overflow = String(document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    document.body.dataset.ready = '1';
  }
  (async function boot() {
    state.settings = Object.assign(state.settings, await A.settings.get());
    J.applyTheme(state.settings); J.applyScale(state.settings, 520);
    render();
    await load(); render();
    if (params.get('opendel') && state.detail) await askDelete(state.detail);
  })();
})();
