/* JD Lens side panel (design v2, information architecture per docs/design/jd-panel/ui-info-architecture-resume-vs-jd.md).
 *
 * Shell (always visible): header, JD | Resume, refresh, Applications (opens the full-page view), settings.
 *   JD     > Overview | Analysis | Details     (one shared job context: scan, score, matched and missing skills, application)
 *   Resume > Profile | Skills | Experience     (one shared resume context: skill profile and the readable resume)
 * Application tracking is a separate full-page view (applications.html), not squeezed into this panel.
 * Talks to the local helper (native messaging host, ADR-0002) for anything that reads or writes your files.
 * Scoring runs here with the same engine as `tools/score_jd.mjs`. No network access. */
(() => {
  'use strict';
  const J = window.JDV;
  const PANEL_TAB = new URLSearchParams(location.search).has('tab');
  const { params, MOCK, A, h, ic, LOGO, loader, ring, slugify, ym, normUrl, fmtDate, years, daysAgoDate, SCALES, SCALE_LABELS } = J;
  // Until you save your own, the threshold is this default. settings.threshold stays null until then, so saving 50 yourself
  // is different from never having chosen (null = default, a number = your choice).
  const DEFAULT_THRESHOLD = 50;
  const thresholdInfo = () => (state.settings.threshold == null ? { value: DEFAULT_THRESHOLD, isDefault: true } : { value: state.settings.threshold, isDefault: false });
  const JD_TABS = [['overview', 'Overview'], ['analysis', 'Analysis'], ['details', 'Details'], ['resources', 'Resources']];
  const RESUME_TABS = [['profile', 'Profile'], ['skills', 'Skills'], ['experience', 'Experience']];
  const LEVEL_LABEL = { listed: 'on resume', 'user-confirmed': 'confirmed', partial: 'partial', earlier: 'older resume only', none: 'no evidence' };

  // ---- state: one object, two contexts built from it per render ------------------------------------
  const screen = params.get('screen') || 'jd';
  const tabParam = params.get('tab') || params.get('sub') || '';
  const state = {
    view: ['jd', 'resume', 'settings'].includes(screen) ? screen : screen === 'profile' ? 'resume' : 'jd',
    jdTab: JD_TABS.some((t) => t[0] === tabParam) ? tabParam : (screen === 'analysis' ? 'analysis' : 'overview'),
    resumeTab: RESUME_TABS.some((t) => t[0] === tabParam) ? tabParam : 'profile',
    evTab: 'matched', expand: {}, factOpen: {}, loading: true, fit: null,
    scan: null, result: null, profile: null, resume: null, apps: [], helper: null, stale: false,
    settings: { threshold: null, theme: 'system', textScale: 1, partialCredit: 0.5, scoreHistory: {}, salaryNotes: {}, stepsDone: {}, permNudgeAt: null },
    autoScan: false, activeTab: null, navStale: false, thrDraft: null, job: null, proposal: null, saveCard: false, feedback: false, toast: '', pasted: '', pasteMeta: { company: '', role: '' },
    showProfileJson: false, error: '', pinned: null, delta: null, salaryEdit: false, descOpen: false,
  };
  let pollTimer = null, toastTimer = null;

  // ---- small helpers -------------------------------------------------------------------------------
  const repo = () => (state.profile && state.profile.repo_path) || '/path/to/jd-lens';
  // Terminal fallbacks: when your data folder is not the engine folder, run in the data folder and point Claude and the tools at the engine.
  const terminalCmd = (inner, dataDir, engine) => {
    let c = inner;
    if (engine && dataDir && engine !== dataDir) c = c.replace(/\btools\/([\w./-]+)/g, (m, f) => `"${engine}/tools/${f}"`).replace(/\bclaude "/g, `claude --add-dir "${engine}" "`);
    return `cd "${dataDir}" && ${c}`;
  };
  const engineDir = () => (state.helper && state.helper.ok && state.helper.engine) || '';
  const separate = () => !!(engineDir() && state.helper.data && engineDir() !== state.helper.data);
  const cmd = (inner) => terminalCmd(inner, repo(), engineDir());
  const jdKey = () => normUrl(state.scan && state.scan.url);
  const helperOk = () => !!(state.helper && state.helper.ok);
  const claudeBusy = () => state.job && state.job.state === 'running';
  function toast(msg) {
    state.toast = msg; render();
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { state.toast = ''; render(); }, 2400);
  }
  async function copy(text) { await J.copyText(text); toast('Copied. Paste it in a terminal.'); }
  async function openFile(path) { if (!(await J.openFile(path))) toast('Could not open it from here. Path copied.'); }

  // ---- data ----------------------------------------------------------------------------------------
  const proposedSlug = () => slugify(state.scan && state.scan.company) + '-' + ym(new Date());
  function scoreScan() {
    const s = state.scan;
    if (!s || !s.ok || !state.profile) { state.result = null; state.delta = null; return; }
    try {
      state.result = JDScorer.score(s.jd_text || '', state.profile, { salary_text: s.salary_text, posted: s.posted, location_text: s.location_text, partialCredit: state.settings.partialCredit });
      state.error = '';
      trackDelta();
    } catch (e) { state.result = null; state.error = 'Scoring failed: ' + e.message; }
  }
  // remember the last score of each JD, so a rise or fall (after you confirm a skill, say) shows as +7 or -3
  function trackDelta() {
    const s = state.scan, r = state.result;
    if (!s || !r || r.score == null || s.pasted) { state.delta = null; return; }
    const key = jdKey();
    const hist = state.settings.scoreHistory || (state.settings.scoreHistory = {});
    const prev = hist[key];
    if (prev && prev.score !== r.score) state.delta = { key, value: r.score - prev.score };
    else if (!(state.delta && state.delta.key === key)) state.delta = null;
    hist[key] = { score: r.score, at: Date.now() };
    const keys = Object.keys(hist);
    if (keys.length > 60) delete hist[keys[0]];
    A.settings.set(state.settings);
  }
  function jdTerms(r) {
    const seen = [];
    for (const u of r.units || []) for (const t of u.terms) if (!seen.includes(t.t)) seen.push(t.t);
    return seen;
  }
  function extraSkills() {
    try {
      const mentioned = new Set(JDScorer.extractTerms(state.scan.jd_text || '', JDScorer.customPatterns(state.profile)));
      const map = JDScorer.skillMap(state.profile);
      return Object.keys(map).filter((t) => !mentioned.has(t) && (map[t].level === 'listed' || map[t].level === 'user-confirmed'));
    } catch (e) { return []; }
  }
  const LADDER = [['intern', 0], ['junior', 1], ['associate', 2], ['mid', 2], ['senior', 3], ['sr', 3], ['lead', 4], ['staff', 4], ['principal', 5], ['architect', 5], ['manager', 5], ['director', 6], ['head of', 6]];
  function levelOf(text) {
    let best = null;
    for (const [w, n] of LADDER) if (new RegExp('(^|[^a-z])' + w + '([^a-z]|$)', 'i').test(text || '') && (!best || n > best[1])) best = [w, n];
    return best;
  }
  function seniority(s) {
    const asked = levelOf(s.role) || levelOf((s.jd_text || '').slice(0, 300));
    let mine = null, title = '';
    for (const c of (state.resume && state.resume.companies) || []) {
      if (/^(own products|cross-company)/i.test(c.company)) continue;
      const l = levelOf(c.title);
      if (l && (!mine || l[1] > mine[1])) { mine = l; title = c.title; }
    }
    return { asked, mine, title };
  }
  // Requirements that need the user's judgement, and other interpretive concerns (the Overview keeps only the quick facts)
  function concerns(r, ctx) {
    const out = [];
    const gaps = r.units.filter((u) => u.kind === 'must' && u.mark === 0);
    gaps.slice(0, 4).forEach((u) => out.push({ kind: 'bad', text: `Must-have not met: ${u.text}` }));
    const scoredText = new Set(r.units.map((u) => u.text));
    const soft = (r.requirements || []).filter((q) => !scoredText.has(q.text) && q.kind === 'must');
    if (soft.length) out.push({ kind: 'warn', text: `${soft.length} requirement${soft.length === 1 ? '' : 's'} need your own judgement, for example: "${soft[0].text.slice(0, 110)}${soft[0].text.length > 110 ? '...' : ''}"` });
    if (!r.structured) out.push({ kind: 'warn', text: 'This JD has no clear Requirements or Qualifications section, so the score is rougher than usual.' });
    if (!salaryText(r)) out.push({ kind: '', text: 'No salary stated. Check the band before spending time on this one.' });
    if (ctx.level.asked && ctx.level.mine && ctx.level.asked[1] > ctx.level.mine[1]) out.push({ kind: 'warn', text: `The JD asks for ${ctx.level.asked[0]} level. Your most senior title on file is "${ctx.level.title}".` });
    return out;
  }
  function matchApp() {
    const s = state.scan;
    if (!s || !s.ok) return { app: null, sameCompany: null };
    const app = state.apps.find((a) => a.source && s.url && normUrl(a.source) === normUrl(s.url)) || state.apps.find((a) => a.slug === proposedSlug()) || null;
    const sameCompany = state.apps.find((a) => a !== app && s.company && a.company.toLowerCase() === s.company.toLowerCase()) || null;
    return { app, sameCompany };
  }
  // JobContext: everything the three JD tabs need, computed once per render so the tabs can never disagree
  function jobCtx() {
    const s = state.scan, r = state.result;
    if (!s || !s.ok || !r) return null;
    const { app, sameCompany } = matchApp();
    const ctx = { scan: s, result: r, app, sameCompany, slug: app ? app.slug : proposedSlug(), terms: jdTerms(r), extra: extraSkills(), level: seniority(s) };
    ctx.concerns = concerns(r, ctx);
    ctx.salary = salaryText(r);
    ctx.full = app && app.fit_score != null ? app.fit_score : null;          // judged by Claude, stored in the application file
    ctx.primary = ctx.full != null ? ctx.full : r.score;                      // the number the threshold is compared with
    return ctx;
  }
  // ResumeContext: the skill profile and the readable resume
  const resumeCtx = () => ({ profile: state.profile, resume: state.resume, facts: (state.resume && state.resume.facts) || {} });
  const appCounts = () => {
    const c = { all: state.apps.length };
    ['considering', 'applied', 'screening', 'interviewing', 'offer', 'rejected', 'withdrawn'].forEach((k) => { c[k] = state.apps.filter((a) => a.status === k).length; });
    return c;
  };

  async function loadApps() {
    const r = await A.host('list');
    if (r.ok) { state.apps = r.applications; return; }
    const fb = await A.loadJSON('data/applications.json');
    state.apps = (fb && fb.applications) || [];
  }
  async function refreshHelper() {
    const r = await A.host('ping');
    state.helper = r;
    if (r.ok) { const ps = await A.host('profile_status'); state.stale = ps.ok && ps.current === false; const pr = await A.host('get_prefs'); if (pr.ok) state.prefs = pr.prefs; const ph = await A.host('photo_info'); state.photo = ph.ok ? ph : { has_photo: false }; }
  }
  async function setPages(v) {
    const r = await A.host('set_pref', { key: 'resume_pages', value: String(v) });
    if (!r.ok) { state.error = r.error; render(); return; }
    state.prefs = r.prefs; state.error = ''; toast(v === 'any' ? 'Tailored resumes can be any length' : `Tailored resumes target ${v} page${v === 1 ? '' : 's'}`);
  }
  // ---- open a folder in Finder ----
  async function openFolder(which) {
    const r = await A.host('open_folder', { which });
    if (!r.ok) { state.error = r.error; render(); }
  }
  const folderBtn = (which, label) => h('button', { class: 'ibtn folder-btn', 'aria-label': label, title: label, on: { click: () => openFolder(which) } }, ic('folder'));
  const pathWithOpen = (text, which, label) => h('span', { class: 'path-open' }, h('span', { class: 'path-text' }, text), helperOk() ? folderBtn(which, label) : null);

  // ---- profile photo (the With photo layout) ----
  async function choosePhoto() {
    const c = await A.host('choose_photo');
    if (!c.ok) { state.error = c.error; render(); return; }
    if (c.cancelled) return;
    const r = await A.host('set_photo', { path: c.path });
    if (!r.ok) { state.error = r.error; render(); return; }
    state.photo = r; state.error = ''; toast('Photo saved. Tailored resumes with the photo layout use it.'); render();
  }
  async function removePhoto() {
    const r = await A.host('remove_photo');
    if (!r.ok) { state.error = r.error; render(); return; }
    state.photo = r; state.error = ''; toast('Photo removed. The photo layout shows a plain avatar again.'); render();
  }
  function photoCard() {
    const ok = helperOk(), ph = state.photo || { has_photo: false };
    return h('div', { class: 'card', id: 'photo-card' }, h('div', { class: 'card-title' }, 'Profile photo'),
      h('div', { class: 'faint' }, 'Used only by the With photo layout. It stays on your computer: the picture is resized and kept as master/photo.jpg in your data folder, and is never committed or sent anywhere except into your own resume PDF.'),
      h('div', { class: 'row', style: 'margin-top:.5rem;align-items:center;gap:.75rem' },
        ph.has_photo && ph.preview ? h('img', { class: 'photo-preview', src: ph.preview, alt: 'Your profile photo' }) : h('div', { class: 'photo-preview empty', 'aria-hidden': 'true' }, ic('user')),
        h('div', { style: 'display:grid;gap:.5rem' },
          h('div', { class: 'faint' }, ph.has_photo ? 'Photo in use.' : 'No photo yet: the layout shows a plain avatar.'),
          ok ? h('div', { class: 'row' }, h('button', { class: 'btn action', on: { click: choosePhoto } }, ph.has_photo ? 'Change photo...' : 'Choose photo...'),
            ph.has_photo ? h('button', { class: 'btn small', on: { click: removePhoto } }, 'Remove photo') : null)
          : h('div', { class: 'faint' }, 'Needs the local helper (it saves the picture in your data folder).'))));
  }

  // ---- your data folder ----------------------------------------------------------------------------------------
  async function afterDataFolderChange(msg) {
    await refreshHelper(); await loadApps();
    { const d = await J.loadData(['profile', 'resume']); state.profile = d.profile; state.resume = d.resume; }
    state.dataChoice = null; state.error = ''; toast(msg); render();
  }
  async function chooseDataFolder() {
    const c = await A.host('choose_data_dir');
    if (!c.ok) { state.error = c.error; render(); return; }
    if (c.cancelled) return;
    state.dataChoice = { path: c.path, sample: true }; render();
  }
  async function applyDataFolder() {
    const ch = state.dataChoice; if (!ch) return;
    const r = await A.host('set_data_dir', { path: ch.path, sample: !!ch.sample });
    if (!r.ok) { state.error = r.error; render(); return; }
    await afterDataFolderChange(r.sample_added ? 'Using that folder. The sample master resume was added.' : r.has_master ? 'Using that folder.' : 'Using that folder. It has no master resume yet.');
  }
  async function clearDataFolder() {
    const r = await A.host('clear_data_dir');
    if (!r.ok) { state.error = r.error; render(); return; }
    await afterDataFolderChange('Using the engine folder for your data again.');
  }
  function openDataFolder() { go('settings'); setTimeout(() => { const el = document.getElementById('data-folder-card'); if (el) el.scrollIntoView({ block: 'start' }); }, 0); }
  function dataFolderCard() {
    const hp = state.helper, ok = helperOk(), ch = state.dataChoice;
    const bySource = { env: 'an environment variable', config: 'this setting', engine: 'the default: the engine folder' };
    return h('div', { class: 'card', id: 'data-folder-card' }, h('div', { class: 'card-title' }, 'Your data folder'),
      h('div', { class: 'faint' }, 'The folder that holds your master resume, applications and tailored resumes. It can be anywhere, for example your own private repo. JD Lens itself (the engine) never stores your data.'),
      ok ? h('dl', { class: 'kv', style: 'margin-top:.5rem' }, h('dt', null, 'Folder'), h('dd', null, pathWithOpen(hp.data || hp.repo, 'data', 'Open the data folder')), h('dt', null, 'Set by'), h('dd', null, bySource[hp.data_source] || 'the default'),
        h('dt', null, 'Master resume'), h('dd', null, hp.has_master === false ? h('span', { class: 'pill warn' }, 'not found') : h('span', { class: 'pill ok' }, 'found'))) : null,
      ok && ch ? h('div', { class: 'banner info stack', style: 'margin-top:.5rem' }, h('div', null, h('b', null, 'Use this folder? '), h('span', { style: 'overflow-wrap:anywhere' }, ch.path)),
        h('label', { class: 'faint', style: 'display:flex;gap:.5rem;align-items:center' }, h('input', { type: 'checkbox', checked: ch.sample ? true : null, on: { change: (e) => { ch.sample = e.target.checked; } } }), 'Add the sample master resume if the folder has none'),
        h('div', { class: 'row' }, h('button', { class: 'btn primary', on: { click: applyDataFolder } }, 'Use this folder'), h('button', { class: 'btn', on: { click: () => { state.dataChoice = null; render(); } } }, 'Cancel')))
        : ok ? h('div', { class: 'row', style: 'margin-top:.5rem' }, h('button', { class: 'btn action', on: { click: chooseDataFolder } }, 'Choose folder...'), separate() ? h('button', { class: 'btn small', on: { click: clearDataFolder } }, 'Use the engine folder') : null)
        : h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Needs the local helper (it reads and writes the folder).'));
  }
  const LAYOUTS = [['basic', 'Basic', 'One column'], ['two-column', 'Two column', 'Sidebar and main'], ['photo', 'With photo', 'Sidebar with a photo']];
  async function setLayout(v) {
    const r = await A.host('set_pref', { key: 'resume_layout', value: v });
    if (!r.ok) { state.error = r.error; render(); return; }
    state.prefs = r.prefs; state.error = ''; toast(`Tailored resumes use the ${(LAYOUTS.find((l) => l[0] === v) || [v, v])[1].toLowerCase()} layout`);
  }
  async function boot() {
    state.settings = Object.assign(state.settings, await A.settings.get());
    for (const k of ['scoreHistory', 'salaryNotes', 'stepsDone']) if (!state.settings[k]) state.settings[k] = {};
    J.applyTheme(state.settings); J.applyScale(state.settings);
    { const d = await J.loadData(['profile', 'resume']); state.profile = d.profile; state.resume = d.resume; }
    state.autoScan = await A.hasAutoScan();
    if (state.settings.permNudgeAt == null) { state.settings.permNudgeAt = Date.now(); await A.settings.set(state.settings); }   // first use: the first reminder comes a week later
    A.connect();
    render();
    await refreshHelper();
    await loadApps();
    state.scan = await A.lastScan();
    state.activeTab = PANEL_TAB ? null : await A.activeTab();
    const here = state.activeTab != null && state.activeTab !== (state.scan && state.scan.tabId) ? await A.tabScan(state.activeTab) : null;
    if (here && !state.pinned) state.scan = here;                    // this tab was scored before: show its JD
    A.onTab((m) => {
      if (PANEL_TAB) return;
      state.activeTab = m.tabId;
      if (m.navigated && state.scan && state.scan.tabId === m.tabId) state.navStale = true;
      render();
    });
    A.onScan((s) => {
      if (state.pinned && s && s.url !== state.pinned) return;       // pinned: keep showing this JD
      if (s && s.tabId != null) state.activeTab = s.tabId;
      state.navStale = false;
      state.scan = s; state.loading = false; state.saveCard = false; state.job = null; state.proposal = null; state.salaryEdit = false; scoreScan(); render();
    });
    scoreScan();
    if (!(MOCK && params.get('state') === 'loading')) {
      if (!state.scan && !MOCK && !PANEL_TAB) setTimeout(() => { if (state.loading && !state.scan) { state.loading = false; render(); } }, 3000);   // the page may still be being read
      else state.loading = false;
    }
    if (MOCK && window.MockApi.afterBoot) await window.MockApi.afterBoot(state, { loadProposal });
    render();
  }
  async function saveSettings(patch) {
    Object.assign(state.settings, patch);
    await A.settings.set(state.settings);
    J.applyTheme(state.settings); J.applyScale(state.settings);
    if ('partialCredit' in patch) scoreScan();
    render();
  }
  async function bumpScale(dir) {
    const cur = SCALES.includes(state.settings.textScale) ? SCALES.indexOf(state.settings.textScale) : 1;
    await saveSettings({ textScale: dir === 0 ? 1 : SCALES[Math.min(SCALES.length - 1, Math.max(0, cur + dir))] });
  }
  window.addEventListener('resize', () => J.applyScale(state.settings));
  J.bindZoomKeys(bumpScale);

  // ---- actions -------------------------------------------------------------------------------------
  async function rescan() {
    state.error = ''; state.loading = true; render();
    const s = await A.rescan();
    state.loading = false;
    if (s) { state.scan = s; state.saveCard = false; scoreScan(); }
    render();
  }
  async function saveJD() {
    const s = state.scan, r = state.result;
    const note = (state.settings.salaryNotes || {})[jdKey()];
    const rec = { company: s.company, company_url: s.company_url, role: s.role, url: s.pasted ? 'pasted' : s.url, jd_text: s.jd_text, captured_at: new Date().toISOString(),
                  location_text: s.location_text, salary_text: (r && r.salary && r.salary.text) || s.salary_text || note, posted: s.posted,
                  extraction: s.extraction || 'main-text', source_title: s.source_title, quick_score: r ? { score: r.score } : undefined };
    const res = await A.host('save_jd', { record: rec });
    state.saveCard = false;
    if (!res.ok) { state.error = res.error; render(); return; }
    await loadApps();
    toast('Saved as ' + res.slug);
  }
  async function setStatus(slug, status) {
    const res = await A.host('status', { slug, status });
    if (!res.ok) { state.error = res.error; render(); return; }
    await loadApps();
    toast('Status: ' + status);
  }
  const JOB_SHORT = { full_score: 'Full score', tailor: 'Proposal', brag: 'Brag Sheet', build: 'Build', answers: 'Answer', interview_prep: 'Prep' };
  const JOB_NAMES = { full_score: 'Full score', tailor: 'Resume proposal', brag: 'Brag Sheet', build: 'Resume build', answers: 'Answer draft', interview_prep: 'Interview prep' };
  async function startJob(kind, slug, extra) {
    state.error = '';
    const res = await A.host('claude_start', { kind, slug, extra });
    if (!res.ok) { state.error = res.error; render(); return; }
    state.job = { job: res.job, kind, slug, state: 'running', seconds: 0 };
    render(); poll();
  }
  function poll() {
    clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      if (!state.job || state.job.state !== 'running') { clearInterval(pollTimer); return; }
      const s = await A.host('claude_status', { job: state.job.job });
      if (!s.ok) { state.error = s.error; clearInterval(pollTimer); render(); return; }
      state.job = Object.assign(state.job, s);
      if (s.state !== 'running') {
        clearInterval(pollTimer);
        if (s.state === 'done') {
          if (state.job.kind === 'full_score') state.fit = null; if (state.job.kind === 'brag') state.brag = null;
          await loadApps(); if (state.job.kind === 'tailor') await loadProposal(state.job.slug);
          const j = state.job, clean = !(j.denied && j.denied.length) && !j.needs_input && !(j.touched_outside && j.touched_outside.length);
          if (clean) { toast(`${JOB_NAMES[j.kind] || j.kind} done${j.cost_usd ? ' (about $' + Number(j.cost_usd).toFixed(2) + ' of usage)' : ''}`); state.job = null; }
        }
      }
      render();
    }, 2000);
  }
  async function openBrag(slug) {
    const r = await A.host('brag_view', { slug });
    if (!r.ok || !r.found) { state.error = r.error || 'The Brag Sheet page could not be built. Make the Brag Sheet first.'; render(); return; }
    await openFile(r.html);
  }
  async function loadBrag(slug) {
    state.brag = { slug, text: null, loading: true };
    const r = await A.host('read_section', { slug, section: 'Brag Sheet' });
    state.brag = { slug, text: r.ok && r.found ? r.text : '', loading: false };
    render();
  }
  async function loadPdfInfo(slug, key) {
    state.pdfInfo = { key, pages: null };
    const r = await A.host('resume_info', { slug });
    state.pdfInfo = { key, pages: r.ok ? r.pages : null, bytes: r.ok ? r.bytes : null };
    render();
  }
  async function loadProposal(slug) {
    const r = await A.host('read_section', { slug, section: 'Tailoring proposal' });
    state.proposal = r.ok && r.found ? r.text : null;
    state.proposalLoadedFor = slug;
  }
  async function cancelJob() {
    if (!state.job) return;
    await A.host('claude_cancel', { job: state.job.job });
    state.job.state = 'failed'; state.job.error = 'Cancelled.'; clearInterval(pollTimer); render();
  }
  async function openMaster(pdf) {
    const r = await A.host('master_view', { pdf: !!pdf });
    if (!r.ok) { state.error = r.error; render(); return; }
    await openFile(pdf ? r.pdf : r.html);
  }
  async function rebuildProfile() {
    const r = await A.host('rebuild_profile');
    if (!r.ok) { state.error = r.error; render(); return; }
    { const d = await J.loadData(['profile', 'resume']); state.profile = d.profile; state.resume = d.resume; }
    await refreshHelper(); scoreScan(); toast('Skill profile rebuilt');
  }
  async function rescoreSaved() {
    const r = await A.host('rescore_saved');
    if (!r.ok) { state.error = r.error; render(); return; }
    await loadApps();
    const changed = r.results.filter((x) => x.new != null && x.old !== x.new).length;
    toast(`Rescored ${r.results.length} saved JD${r.results.length === 1 ? '' : 's'}, ${changed} changed`);
  }
  const go = (view) => { state.view = view; state.error = ''; render(); window.scrollTo(0, 0); };
  const goJd = (tab, evTab) => { state.view = 'jd'; state.jdTab = tab; if (evTab) state.evTab = evTab; render(); window.scrollTo(0, 0); };
  const togglePin = () => {
    state.pinned = state.pinned ? null : (state.scan && state.scan.url) || null;
    toast(state.pinned ? 'Pinned: this JD stays when you switch tabs' : 'Unpinned');
  };
  const stepKey = () => (state.apps.find((a) => a.slug === proposedSlug()) || {}).slug || jdKey();
  const isDone = (n) => !!((state.settings.stepsDone || {})[stepKey()] || {})[n];
  async function markDone(n) {
    const all = state.settings.stepsDone || (state.settings.stepsDone = {});
    const mine = all[stepKey()] || (all[stepKey()] = {});
    mine[n] = !mine[n];
    await A.settings.set(state.settings); render();
  }

  // ---- shell ---------------------------------------------------------------------------------------
  function header() {
    return h('div', { class: 'header' },
      h('div', { class: 'brand', html: LOGO + '<span>JD Lens</span>' }),
      h('div', { class: 'spacer' }),
      h('button', { class: 'ibtn', 'aria-label': 'Smaller text', title: 'Smaller text (Cmd -)', on: { click: () => bumpScale(-1) } }, 'A-'),
      h('button', { class: 'ibtn', 'aria-label': 'Larger text', title: 'Larger text (Cmd +)', on: { click: () => bumpScale(1) } }, 'A+'),
      h('button', { class: 'ibtn', 'aria-label': 'Pin this JD', 'aria-pressed': String(!!state.pinned), title: 'Pin: keep this JD when you switch tabs', on: { click: togglePin } }, ic('pin')),
      h('button', { class: 'ibtn', 'aria-label': 'Applications (full page, opens in a new tab)', title: 'Applications (full page)\nOpens in a new tab \u2197', on: { click: () => A.openApps() } }, ic('ext')),
      h('button', { class: 'ibtn', 'aria-label': 'Close', title: 'Close the panel', on: { click: () => { try { window.close(); } catch (e) { /* ignore */ } } } }, ic('x')));
  }
  function tabbar() {
    const t = (id, label, icon) => h('button', { role: 'tab', 'aria-selected': String(state.view === id), on: { click: () => go(id) } }, ic(icon), label);
    return h('div', { class: 'tabbar' },
      h('div', { class: 'seg', role: 'tablist' }, t('jd', 'JD', 'doc'), t('resume', 'Resume', 'user')),
      h('div', { class: 'ibtn-group' },
        h('button', { class: 'ibtn', 'aria-label': 'Refresh', title: 'Read the page again', on: { click: rescan } }, ic('refresh')),
        h('button', { class: 'ibtn', 'aria-label': 'Settings', title: 'Settings', 'aria-pressed': String(state.view === 'settings'), on: { click: () => go(state.view === 'settings' ? 'jd' : 'settings') } }, ic('gear'))));
  }
  function contextTabs(items, current, set) {
    return h('div', { class: 'tabs ctabs', role: 'tablist' }, items.map(([id, label]) => h('button', { class: 'tab', role: 'tab', 'aria-selected': String(current === id), on: { click: () => { set(id); render(); window.scrollTo(0, 0); } } }, label)));
  }
  function currentJobStrip() {
    const s = state.scan, r = state.result;
    if (!s || !s.ok || !r) return null;
    return h('button', { class: 'jobstrip', title: 'Back to this job', on: { click: () => go('jd') } }, ic('briefcase'),
      h('span', { class: 'grow' }, h('span', { class: 'faint' }, 'Current job: '), h('b', null, s.company), ' · ', s.role), r.score != null ? h('span', { class: 'pill match' }, String(r.score)) : null, ic('chev'));
  }
  function cmdRow(text, label) {
    return h('div', null, label ? h('div', { class: 'faint' }, label) : null,
      h('div', { class: 'cmd' }, h('code', null, text), h('button', { class: 'btn small', on: { click: () => copy(text) } }, 'Copy')));
  }
  const terminal = (text) => h('details', { class: 'terminal' }, h('summary', null, 'Run in a terminal instead'), cmdRow(text));
  function claudeAction(label, fn, disabled) {
    return h('button', { class: 'btn action', disabled: !helperOk() || claudeBusy() || disabled ? true : null, on: { click: fn } }, label, ic('arrow'));
  }
  function banners() {
    const out = [];
    if (state.error) out.push(h('div', { class: 'banner bad', role: 'alert' }, h('div', { class: 'grow' }, h('b', null, 'Something went wrong. '), state.error)));
    if (state.helper && !state.helper.ok) {
      out.push(h('div', { class: 'banner warn stack' }, h('div', null, h('b', null, 'Local helper not connected. '), 'Scoring works, but saving, status changes and Claude actions need the helper. Install it once:'), cmdRow(cmd('python3 tools/jobd/install.py'))));
    }
    if (state.helper && state.helper.ok && state.helper.has_master === false) {
      out.push(h('div', { class: 'banner info stack', id: 'first-run' }, h('div', null, h('b', null, 'No master resume in your data folder yet. '), 'Choose the folder that holds your resume data, or add the sample one to try JD Lens.'),
        h('div', { class: 'row' }, h('button', { class: 'btn small action', on: { click: openDataFolder } }, 'Choose data folder', ic('arrow')))));
    }
    const nudge = permissionNudge();
    if (nudge) out.push(nudge);
    const sw = tabSwitchBanner();
    if (sw) out.push(sw);
    if (state.stale) {
      out.push(h('div', { class: 'banner warn' }, h('div', { class: 'grow' }, h('b', null, 'Skill profile is older than your master file. '), 'Scores may be off.'), h('button', { class: 'btn small', on: { click: rebuildProfile } }, 'Rebuild now')));
    }
    return out;
  }
  // Once a week, until it is allowed: remind that automatic reading makes the panel follow your tabs
  function permissionNudge() {
    const at = state.settings.permNudgeAt;
    if (state.autoScan || PANEL_TAB || state.view !== 'jd' || at == null || Date.now() - at < 7 * 864e5) return null;
    const later = () => saveSettings({ permNudgeAt: Date.now() });
    return h('div', { class: 'banner tab-switch', role: 'status' }, ic('sparkle', 'lg'),
      h('div', { class: 'grow' }, h('b', null, 'Tip: let the panel follow your tabs.'), ' Allow automatic reading and the score updates as you switch job pages. Chrome asks you first, and you can turn it off any time.'),
      h('div', { class: 'stack-btns' }, h('button', { class: 'btn small', on: { click: async () => { state.autoScan = await A.requestAutoScan(); if (!state.autoScan) await later(); else render(); } } }, 'Allow'),
        h('button', { class: 'link-btn', on: { click: later } }, 'Not now')));
  }
  // The panel shows the JD it last read. When you are on a different tab, say so and offer to read this one.
  function tabSwitchBanner() {
    const s = state.scan;
    if (PANEL_TAB || state.pinned || !s || !s.ok || state.view !== 'jd') return null;
    const other = state.activeTab != null && state.activeTab !== s.tabId;
    if (!other && !state.navStale) return null;
    const what = [s.company, s.role].filter(Boolean).join(': ') || s.source_title || 'the last job page';
    return h('div', { class: 'banner tab-switch', role: 'status' }, ic('info', 'lg'),
      h('div', { class: 'grow' }, h('b', null, other ? 'This is a different tab.' : 'This tab opened a new page.'), ` Still showing ${what}.`,
        state.autoScan ? null : h('div', { class: 'faint' }, 'Click the JD Lens icon in the toolbar to score this page.')),
      state.autoScan ? h('button', { class: 'btn small', on: { click: rescan } }, 'Score this page') : null);
  }
  // Progress, failures and warnings only. A clean finish shows a toast and the step turns to "done"; the raw
  // markdown Claude replied with is never shown here (the real results live in the cards and the application file).
  function jobCard() {
    const j = state.job;
    if (!j) return null;
    const names = JOB_NAMES;
    if (j.state === 'running') return null;          // progress and Cancel live on the step that is running (and in the Next action bar)
    if (j.state === 'failed') return h('div', { class: 'banner bad', role: 'alert' }, h('div', { class: 'grow' }, h('b', null, `${names[j.kind] || j.kind} failed. `), j.error || 'See tools/jobd/jobs for details.'));
    const blocked = (j.denied && j.denied.length) || 0;
    if (!blocked && !j.needs_input && !(j.touched_outside && j.touched_outside.length)) return null;   // clean finish: nothing to say here
    const bits = [h('div', null, h('b', null, blocked ? `${names[j.kind] || j.kind} finished, but ${j.blocked || blocked} command${(j.blocked || blocked) === 1 ? ' was' : 's were'} blocked.` : `${names[j.kind] || j.kind} finished.`), j.cost_usd ? h('span', { class: 'faint' }, ` (about $${Number(j.cost_usd).toFixed(2)} of usage)`) : null)];
    if (blocked) bits.push(h('div', { class: 'banner warn stack', role: 'alert', style: 'margin-top:.5rem' },
      h('div', null, h('b', null, 'Claude was not allowed to run: '), 'the result may be incomplete or based on a guess. Run the step again, or use the terminal command under the step.'),
      h('ul', { class: 'bul' }, j.denied.map((c) => h('li', null, h('code', null, c))))));
    if (j.touched_outside && j.touched_outside.length) bits.push(h('div', { class: 'banner warn', style: 'margin-top:.5rem' }, h('div', null, h('b', null, 'Files changed outside the expected folders: '), j.touched_outside.join(', '), h('div', { class: 'faint' }, 'These changed while the job ran. If you edited them yourself in the meantime, ignore this.'))));
    if (j.needs_input) bits.push(questionsCard(j.slug));
    bits.push(h('div', { style: 'margin-top:.5rem' }, h('button', { class: 'link-btn', on: { click: () => { state.job = null; render(); } } }, 'Dismiss')));
    return h('div', { class: 'banner info stack' }, bits);
  }
  function questionsCard(slug) {
    const box = h('div', { style: 'margin-top:.5rem' }, h('b', null, 'Claude needs your answer first'));
    A.host('questions', { slug }).then((r) => {
      if (!r.ok || !r.questions.length) return;
      const inputs = r.questions.map((q) => h('div', null, h('label', { class: 'field' }, q.question, q.why ? h('div', { class: 'faint' }, q.why) : null), h('textarea', { 'data-q': q.id })));
      box.append(...inputs, h('button', { class: 'btn primary', style: 'margin-top:.5rem', on: { click: async () => {
        const answers = {}; box.querySelectorAll('textarea').forEach((t) => { if (t.value.trim()) answers[t.dataset.q] = t.value.trim(); });
        const res = await A.host('answer', { slug, answers });
        if (!res.ok) { state.error = res.error; render(); return; }
        toast('Saved. Run the step again to continue.'); state.job = null; render();
      } } }, 'Save answers'));
    });
    return box;
  }
  function skeleton() {
    const bar = (w, hgt) => h('div', { class: 'skel', style: `width:${w};height:${hgt || '.875rem'}` });
    return h('div', { class: 'skeleton', 'aria-busy': 'true', 'aria-label': 'Analysing this job' },
      h('div', { class: 'card' }, bar('40%'), bar('85%', '1.5rem'), bar('55%')),
      h('div', { class: 'stats' }, h('div', { class: 'stat' }, bar('45%'), bar('60%', '2.5rem')), h('div', { class: 'stat' }, bar('55%'), bar('80%', '1.5rem'))),
      h('div', { class: 'card' }, bar('35%'), bar('100%', '.625rem'), bar('70%')),
      h('div', { class: 'card' }, bar('30%'), bar('90%'), bar('75%'), bar('60%')));
  }

  // ---- JD: shared pieces ---------------------------------------------------------------------------
  function salaryText(r) {
    if (r.salary) return { text: r.salary.text, note: 'As written on the ' + r.salary.source + '. Currency and period as posted.' };
    const n = (state.settings.salaryNotes || {})[jdKey()];
    return n ? { text: n, note: 'As you noted. Not on the page.' } : null;
  }
  function postedLine(c) {
    const s = c.scan, r = c.result, d = s.posted || (r.flags.posted_days != null ? daysAgoDate(r.flags.posted_days) : '');
    return d ? `Posted ${fmtDate(d)}` + (r.flags.posted_days != null ? ` (${r.flags.posted_days} days ago)` : '') : '';
  }
  function emptyView() {
    const s = state.scan;
    return h('div', { class: 'card' },
      h('div', { class: 'empty' }, h('div', { class: 'job-title' }, 'No job description found'),
        h('p', { class: 'muted' }, s && s.error ? s.error : 'Open a job posting and click the JD Lens icon, or press Refresh. If the page hides its text, paste the JD below.')),
      h('label', { class: 'field' }, 'Paste the JD text (scored the same way)'),
      h('textarea', { 'aria-label': 'Paste JD text', value: state.pasted, on: { input: (e) => { state.pasted = e.target.value; } } }),
      h('div', { class: 'row', style: 'margin-top:.5rem' },
        h('input', { type: 'text', placeholder: 'Company', 'aria-label': 'Company', value: state.pasteMeta.company, on: { input: (e) => { state.pasteMeta.company = e.target.value; } } }),
        h('input', { type: 'text', placeholder: 'Role', 'aria-label': 'Role', value: state.pasteMeta.role, on: { input: (e) => { state.pasteMeta.role = e.target.value; } } })),
      h('div', { class: 'row', style: 'margin-top:.5rem' }, h('button', { class: 'btn', on: { click: rescan } }, ic('refresh'), 'Refresh'),
        h('button', { class: 'btn primary', on: { click: () => {
          if (state.pasted.trim().length < 50) { toast('Paste the JD text first'); return; }
          state.scan = { ok: true, pasted: true, url: 'pasted', company: state.pasteMeta.company || 'Pasted JD', role: state.pasteMeta.role || 'Role', jd_text: state.pasted, extraction: 'pasted' };
          scoreScan(); render();
        } } }, 'Score pasted text')));
  }
  // Right side of the salary row: Details (opens the application) and, once you have applied, the status. Not-yet-saved
  // needs no label: the Next action bar says "Save JD".
  function statusBits(c) {
    const { app } = c;
    if (!app) return null;
    return h('div', { class: 'jh-actions' },
      app.status && app.status !== 'considering' ? h('span', { class: 'pill ' + app.status, title: app.applied ? `Applied ${fmtDate(app.applied)}` : '' }, app.status) : null,
      h('button', { class: 'link-btn', title: 'Open this application in a new tab', 'aria-label': 'Details (opens in a new tab)', on: { click: () => A.openApps(app.slug) } }, 'Details', ic('ext')));
  }
  const sameCompanyNote = (c) => (!c.app && c.sameCompany ? h('div', { class: 'jh-note' }, `You already have an application to ${c.sameCompany.company} (${c.sameCompany.status}).`) : null);

  // ---- JD > Overview: the "Next action" panel (top of the tab) -----------------------------------------
  // Shows what to do next, derived from what already exists. With several possible actions it slides through them one at
  // a time (pauses on hover or focus; no auto-slide when the system asks for reduced motion). Each CTA scrolls to its step.
  function scrollToStep(id) {
    setTimeout(() => {
      const el = document.getElementById(id); if (!el) return;
      el.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
    }, 0);
  }
  function nextActionsFor(c) {
    const { app } = c, slug = c.slug, acts = [];
    if (claudeBusy()) { const j = state.job; return [{ label: `${JOB_SHORT[j.kind] || j.kind} running (${j.seconds || 0}s)`, busy: true, run: () => scrollToStep(STEP_OF[j.kind] || 'step-tailor') }]; }
    if (!app) return [{ label: 'Save JD', run: () => { state.saveCard = true; render(); scrollToStep('step-save'); } }];
    const go = (id) => () => scrollToStep(id);
    const propKnown = state.proposalLoadedFor === slug, bragKnown = !!(state.brag && state.brag.slug === slug && !state.brag.loading);
    const hasBrag = !!(bragKnown && state.brag.text);
    if (app.fit_score == null) acts.push({ label: 'Get full score', run: go('step-score') });
    if (propKnown && !state.proposal) acts.push({ label: 'Tailor your resume', run: go('step-tailor') });
    else if (propKnown && state.proposal && !app.resume_exists) acts.push({ label: 'Approve and build PDF', run: go('step-tailor') });
    if (bragKnown && !hasBrag) acts.push({ label: 'Make Brag Sheet', run: go('step-tailor') });
    if (app.resume_exists) acts.push({ label: 'Review your resume', run: () => { state.jdTab = 'resources'; render(); window.scrollTo(0, 0); } });
    if (c.result.missing.length && !isDone(4)) acts.push({ label: 'Add missing skills', run: go('step-missing') });
    return acts.length ? acts : [{ label: 'All steps done', done: true }];
  }
  const reduceMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  function nextCtaEl(a) {
    return a.busy ? h('button', { class: 'next-cta busy', title: 'Show the step that is running', on: { click: a.run } }, h('span', { class: 'spinner' }), a.label, ic('arrow'))
      : a.done ? h('span', { class: 'next-cta done' }, ic('check'), a.label)
      : h('button', { class: 'next-cta', on: { click: a.run } }, a.label, ic('arrow'));
  }
  // Show the current action. When animating, the old button slides out to the left while the new one slides in from the right.
  function showNextAction(stage, dotsEl, animate) {
    const acts = state.nextActions || [], i = Math.min(state.nextIdx || 0, Math.max(0, acts.length - 1)), a = acts[i];
    if (!a) { stage.replaceChildren(); dotsEl.replaceChildren(); return; }
    const el = nextCtaEl(a), old = stage.firstElementChild;
    if (animate && old && !reduceMotion()) {
      old.classList.add('out'); el.classList.add('in'); stage.append(el);
      const drop = () => { if (old.isConnected) old.remove(); el.classList.remove('in'); };
      old.addEventListener('animationend', drop, { once: true }); setTimeout(drop, 800);
    } else stage.replaceChildren(el);
    dotsEl.replaceChildren(...(acts.length > 1 ? acts.map((x, k) => h('button', { class: k === i ? 'on' : '', 'aria-label': `Show action ${k + 1} of ${acts.length}: ${x.label}`, 'aria-pressed': String(k === i), on: { click: () => { state.nextIdx = k; showNextAction(stage, dotsEl, true); } } })) : []));
  }
  function nextActionPanel(c) {
    if (c.app && (!state.brag || state.brag.slug !== c.slug)) loadBrag(c.slug);
    if (c.app && state.proposalFor !== c.slug) { state.proposalFor = c.slug; loadProposal(c.slug).then(render); }
    state.nextActions = nextActionsFor(c);
    const stage = h('div', { class: 'next-stage' }), dots = h('div', { class: 'next-dots', role: 'group', 'aria-label': 'Possible next actions' });
    showNextAction(stage, dots, false);
    return h('div', { class: 'next-panel' + (state.nextActions.length > 1 ? ' has-dots' : ''), role: 'region', 'aria-label': 'Next action', on: { mouseenter: () => { state.nextPaused = true; }, mouseleave: () => { state.nextPaused = false; }, focusin: () => { state.nextPaused = true; }, focusout: () => { state.nextPaused = false; } } },
      h('span', { class: 'next-ico', 'aria-hidden': 'true' }, ic('bolt')), h('div', { class: 'next-label' }, 'Next action'), h('div', { class: 'next-right' }, h('div', { class: 'next-cluster' }, stage, dots)));
  }
  setInterval(() => {
    const stage = document.querySelector('.next-stage'), dots = document.querySelector('.next-dots'), n = (state.nextActions || []).length;
    if (!stage || !dots || n < 2 || state.nextPaused || document.hidden || reduceMotion()) return;
    if (MOCK && !params.get('autoslide')) return;                   // static renders stay deterministic
    state.nextIdx = ((state.nextIdx || 0) + 1) % n; showNextAction(stage, dots, true);
  }, 3500);

  // ---- JD > Overview -------------------------------------------------------------------------------
  // The change in the keyword score since this JD was last scored (shown beside the match number)
  function deltaPill() {
    const t = state.delta;
    return t ? h('span', { class: 'delta ' + (t.value > 0 ? 'up' : 'down'), title: 'Change in the keyword score since you last scored this JD' }, ic(t.value > 0 ? 'up' : 'down'), (t.value > 0 ? '+' : '') + t.value) : null;
  }
  // Salary sits with the job title and company (it is a fact about the posting, not a score)
  function salaryLine(c) {
    const sal = c.salary;
    if (sal) return h('span', { class: 'jh-pill', title: sal.note }, sal.text);
    if (state.salaryEdit) {
      return h('div', { class: 'jh-salary-edit' }, h('input', { type: 'text', id: 'sal', placeholder: 'For example INR 30-40 LPA', 'aria-label': 'Salary you found' }),
        h('div', { class: 'row', style: 'margin-top:.5rem' }, h('button', { class: 'btn small primary', on: { click: () => {
          const v = document.getElementById('sal').value.trim(); state.salaryEdit = false;
          if (v) { state.settings.salaryNotes[jdKey()] = v; A.settings.set(state.settings); }
          render();
        } } }, 'Save'), h('button', { class: 'btn small', on: { click: () => { state.salaryEdit = false; render(); } } }, 'Cancel')));
    }
    return h('span', { class: 'jh-salary' }, h('span', { class: 'faint' }, 'Salary not stated '), h('button', { class: 'link-btn', on: { click: () => { state.salaryEdit = true; render(); } } }, '(Update?)'));
  }
  // Edit the threshold in Settings (one place, explicit save), then see it here as a ring on the score bar
  function openThreshold() { state.thrDraft = null; go('settings'); setTimeout(() => { const el = document.getElementById('scoring-card'); if (el) el.scrollIntoView({ block: 'start' }); }, 0); }
  function thresholdCard(c) {
    const { value: t, isDefault } = thresholdInfo(), shown = c.primary;
    const pct = shown == null ? 0 : Math.max(0, Math.min(100, shown));
    const has = shown != null, ok = has && shown >= t, strong = has && shown >= t + 20;
    const what = c.full != null ? 'the full score' : 'the keyword score, which is not a verdict';
    const kw = c.result.score, date = c.app && c.app.fit_scored ? ' on ' + fmtDate(c.app.fit_scored) : '';
    // Under the bar: what the number is (left), the keyword score or a hint (right / next line)
    const scoreInfo = !has ? h('div', { class: 'faint', style: 'margin-top:.25rem' }, 'No recognisable requirements in this JD.')
      : c.full != null
        ? h('div', { style: 'margin-top:.25rem' }, h('div', { class: 'between' }, h('b', null, 'Full score'), h('span', { class: 'faint' }, 'Keyword score: ', h('b', null, kw == null ? '--' : String(kw)), ' ', deltaPill())),
            h('div', { class: 'faint' }, 'Judged by Claude' + date + '.'))
        : h('div', { style: 'margin-top:.25rem' }, h('div', { class: 'between' }, h('b', null, 'Keyword score'), deltaPill()),
            h('div', { class: 'faint' }, c.app ? 'Run Get the full score for a judged number.' : 'Save the JD to get a full score.'));
    // The verdict is a badge in the card's top right; the long explanation is its tooltip
    const label = strong ? 'Strong match' : ok ? 'Worth a look' : 'Below your bar', cls = strong ? 'strong' : ok ? 'ok' : 'low';
    const rel = strong ? 'Well above' : ok ? 'At or above' : 'Below';
    const tip = `${rel} ${isDefault ? 'the default threshold' : 'your threshold'} of ${t}. Compared with ${what}.` + (isDefault ? ` This is the default (${DEFAULT_THRESHOLD}) until you choose your own in Settings.` : '');
    return h('div', { class: 'card' },
      h('div', { class: 'between' }, h('div', { class: 'card-title', style: 'margin:0' }, h('span', { class: 'grad-text' }, ic('crown')), 'Your match',
          h('button', { class: 'info-tip', 'aria-label': 'What is Your match?', title: 'Your match is this JD\'s score. The ring on the bar is your threshold, the minimum score you decided is worth a look. Change it in Settings; every JD shows whether it clears your bar.' }, ic('info'))),
        has ? h('button', { class: 'verdict-badge ' + cls, title: tip, 'aria-label': `${label}. ${tip}` }, label) : null),
      h('div', { class: 'between', style: 'gap:.75rem' },
        h('div', { class: 'bar thick' + (has ? ' ' + cls : ''), style: 'flex:1', role: 'img', 'aria-label': `score ${shown} on a 0 to 100 scale, ${isDefault ? 'default' : 'your'} threshold ${t}` },
          h('div', { class: 'bar-fill', style: `width:${pct}%` }),
          h('div', { class: 'bar-tick', role: 'button', tabindex: '0', style: `left:${t}%`, title: `${isDefault ? 'Default threshold' : 'Your threshold'}: ${t}. Click to change it in Settings.`, 'aria-label': `${isDefault ? 'Default threshold' : 'Your threshold'} ${t}. Open Settings to change it.`, on: { click: openThreshold, keydown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openThreshold(); } } } })),
        h('div', { class: 'match-num' }, h('b', { style: 'font-size:1.5rem', 'aria-label': (c.full != null ? 'full score ' : 'keyword score ') + shown }, shown == null ? '--' : String(shown)), h('span', { class: 'faint' }, '/ 100'))),
      scoreInfo);
  }
  function flagsCard(c) {
    const r = c.result, f = r.flags, rows = [];
    const add = (kind, text) => rows.push(h('div', { class: 'flag ' + kind }, h('span', { class: 'dot' }), h('span', null, text)));
    if (f.india === 'stated') add('ok', 'India remote is stated.');
    else if (f.india === 'listed') add('warn', 'India is listed, but "India remote" is not stated. Confirm with recruiting.');
    else add('warn', 'India is not mentioned. Confirm India hiring before applying.');
    if (f.remote === 'remote') add('ok', 'Open to remote work.');
    else if (f.remote === 'hybrid' || f.remote === 'onsite') add('warn', f.remote === 'hybrid' ? 'Hybrid role.' : 'On-site role.');
    else add('', 'No remote wording found.');
    if (f.posted_days != null && f.posted_days > 60) add('warn', `Posted ${f.posted_days} days ago. May be stale: check it is still open.`);
    if (r.years.required && r.years.have < r.years.required) add('warn', `Experience: asks ${r.years.required}+ years, you have ${r.years.have}.`);
    const gaps = r.units.filter((u) => u.kind === 'must' && u.mark === 0);
    if (gaps.length) add('bad', `${gaps.length} must-have requirement${gaps.length === 1 ? '' : 's'} not met (see Analysis).`);
    f.scam.forEach((x) => add('bad', 'Possible scam signal: ' + x + '.'));
    if (!f.scam.length) add('ok', 'No scam signals found.');
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Flags'), h('div', { class: 'flags' }, rows));
  }
  // A small summary of the skills picture; the full lists live in Analysis > Key skills match
  function openKeySkills(ev) {
    state.view = 'jd'; state.jdTab = 'analysis'; if (ev) state.evTab = ev; render();
    setTimeout(() => { const el = document.getElementById('evidence'); if (el) el.scrollIntoView({ block: 'start' }); }, 0);
  }
  function skillsBrief(c) {
    const r = c.result;
    const mentioned = r.matched.length + r.partial.length + r.missing.length + r.unconfirmed.length;
    const pill = (n, label, cls, ev) => h('button', { class: 'skill-pill ' + cls, 'aria-label': `${n} ${label}`, on: { click: () => openKeySkills(ev) } }, h('b', null, String(n)), ' ' + label);
    return h('div', { class: 'card skills-brief' },
      h('div', { class: 'between' }, h('div', { class: 'card-title', style: 'margin:0' }, ic('list'), 'Skills'),
        h('button', { class: 'link-btn', on: { click: () => openKeySkills() } }, 'Key skills match', ic('arrow'))),
      h('div', { class: 'pills', style: 'margin-top:.5rem' }, pill(r.matched.length + r.partial.length, 'matched', 'ok', 'matched'), pill(r.missing.length, 'missing', 'miss', 'missing'), pill(r.partial.length + r.unconfirmed.length, 'unconfirmed', 'unc', 'unconfirmed')),
      h('div', { class: 'faint', style: 'margin-top:.5rem' }, `The JD mentions ${mentioned} skills.`));
  }
  // The way into the whole Analysis tab (its top), outlined with the accent gradient (no fill: the Next action bar is the primary element)
  const analysisCta = () => h('button', { class: 'btn grad-outline block', on: { click: () => goJd('analysis') } }, 'View full analysis', ic('arrow'));
  function overviewTab(c) { return [nextActionPanel(c), thresholdCard(c), flagsCard(c), skillsBrief(c), analysisCta(), nextSteps(c)]; }

  // ---- JD > Analysis -------------------------------------------------------------------------------
  function chipList(names, cls, key, limit) {
    const open = state.expand[key];
    return h('div', { class: 'chips' }, (open ? names : names.slice(0, limit)).map((n) => h('span', { class: 'chip ' + (cls || '') }, n)),
      !open && names.length > limit ? h('button', { class: 'chip more', on: { click: () => { state.expand[key] = true; render(); } } }, `+${names.length - limit} more...`) : null);
  }
  function factChip(id) {
    return h('button', { class: 'chip fact', 'aria-expanded': String(!!state.factOpen[id]), title: 'Show the evidence', on: { click: () => { state.factOpen[id] = !state.factOpen[id]; render(); } } }, id);
  }
  function factText(ids) {
    const facts = (state.resume && state.resume.facts) || {};
    return ids.filter((id) => state.factOpen[id]).map((id) => h('div', { class: 'factbox' }, h('b', null, id), facts[id] ? [' · ', facts[id].where, ': ', facts[id].text] : ' (not found in the readable resume)'));
  }
  // Claude's written judgement (the `## Fit` section of the application file), loaded once per application
  async function loadFit(slug) {
    state.fit = { slug, text: null, loading: true };
    const r = await A.host('read_section', { slug, section: 'Fit' });
    state.fit = { slug, text: r.ok && r.found ? r.text : '', loading: false };
    render();
  }
  function assessmentCard(c) {
    if (c.full == null || !c.app) return null;
    if (!state.fit || state.fit.slug !== c.app.slug) loadFit(c.app.slug);
    const f = state.fit;
    const when = c.app.fit_scored ? ` on ${fmtDate(c.app.fit_scored)}` : '';
    const text = f && f.text ? f.text : '';
    const open = state.expand.fit;
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, h('span', { class: 'grad-text' }, ic('sparkle')), "Claude's assessment"),
      h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, `Full score ${c.full}${when}. The judgement behind it, written into your application file.`),
      !f || f.loading ? h('div', { class: 'faint' }, 'Loading...')
        : text ? [h('div', { class: 'proposal md-wrap', style: open ? 'max-height:none' : '' }, J.renderMarkdown(text)),
            text.length > 600 ? h('button', { class: 'link-btn', style: 'margin-top:.5rem', on: { click: () => { state.expand.fit = !open; render(); } } }, open ? 'Show less' : 'Show all', ic('arrow')) : null]
        : h('div', { class: 'faint' }, 'No written assessment in the application file yet. Run Get the full score to create one.'));
  }
  // Brag Sheet: the candidate's own quick reference for this JD (also a full page and a tab on the Applications page)
  function bragCard(c, nested) {
    if (!c.app) return null;
    if (!state.brag || state.brag.slug !== c.app.slug) loadBrag(c.app.slug);
    const b = state.brag, text = b && b.text ? b.text : '', open = state.expand.brag;
    const bragRun = runningJob('brag');
    return h('div', { class: (nested ? 'brag-inline' : 'card') + (bragRun ? ' running' : ''), id: nested ? 'step-brag' : null }, h('div', { class: 'between' }, h('div', { class: 'card-title', style: 'margin:0' }, h('span', { class: 'grad-text' }, ic('crown')), 'Brag Sheet',
        h('button', { class: 'info-tip', 'aria-label': 'What is the Brag Sheet?', title: 'Your quick reference for this job: which of your past work matters most, the proof behind it, and what to say. Read it before a screening call or interview. Only your own verified facts go in.' }, ic('info'))),
        bragRun ? progressInline(bragRun) : text ? h('div', { class: 'done-actions' }, h('button', { class: 'link-btn', on: { click: () => openBrag(c.app.slug) } }, 'Open full page', ic('arrow')), rerunBtn('Brag Sheet', () => startJob('brag', c.app.slug))) : null),
      !b || b.loading ? h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Loading...')
        : text ? [h('div', { class: 'proposal md-wrap', style: 'margin-top:.5rem;' + (open ? 'max-height:none' : '') }, J.renderMarkdown(text)),
            h('button', { class: 'link-btn', style: 'margin-top:.5rem', on: { click: () => { state.expand.brag = !open; render(); } } }, open ? 'Show less' : 'Show all', ic('arrow'))]
        : h('div', { style: 'margin-top:.5rem' }, h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, 'Not made yet. Claude picks the work that matters for this JD from your master resume, with the proof for each point.'),
            bragRun ? null : claudeAction('Make Brag Sheet', () => startJob('brag', c.app.slug))));
  }
  function experienceAlignment(c) {
    const r = c.result, L = c.level;
    const rows = [];
    if (r.years.required) rows.push(['Years of experience', `Asked ${r.years.required}+ · you ${r.years.have}`, r.years.have >= r.years.required ? 'ok' : 'warn']);
    else rows.push(['Years of experience', `Not stated · you ${r.years.have}`, '']);
    if (L.asked) rows.push(['Level in the JD', L.asked[0].replace(/^./, (m) => m.toUpperCase()), ''], ['Your titles', L.title || 'not found in your resume data', L.mine && L.mine[1] >= L.asked[1] ? 'ok' : 'warn']);
    else rows.push(['Level in the JD', 'Not stated', '']);
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('chart'), 'Experience alignment'),
      h('div', { class: 'flags' }, rows.map(([k, v, kind]) => h('div', { class: 'flag ' + kind }, h('span', { class: 'dot' }), h('span', null, h('b', null, k + ': '), v)))));
  }
  function requirementCard(c) {
    const us = c.result.units;
    if (!us.length) return null;
    const shown = state.expand.req ? us : us.slice(0, 5);
    const icon = (m) => (m === 1 ? ['check', 'ok', 'Met'] : m === 0.5 ? ['half', 'warn', 'Partial'] : ['cross', 'bad', 'Gap']);
    return h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('list'), 'Requirement comparison'),
      h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, 'Each requirement against your master resume. Tap an evidence ID to read the fact behind it.'),
      shown.map((u) => {
        const [ico, kind, label] = icon(u.mark);
        const ev = [...new Set(u.terms.flatMap((t) => t.evidence || []))].slice(0, 4);
        return h('div', { class: 'req' }, h('span', { class: 'req-ic ' + kind, title: label, 'aria-label': label }, ic(ico)),
          h('div', { class: 'req-body' }, h('div', null, u.text), h('div', { class: 'faint' }, (u.kind === 'nice' ? 'Preferred' : 'Required') + ' · ' + u.terms.map((t) => t.t).join(', ')),
            ev.length ? h('div', { class: 'chips' }, ev.map(factChip)) : null, factText(ev)));
      }),
      us.length > 5 && !state.expand.req ? h('button', { class: 'link-btn', style: 'margin-top:.5rem', on: { click: () => { state.expand.req = true; render(); } } }, `Show all ${us.length}`, ic('arrow')) : null);
  }
  // A step is done when you ticked it, or when its result already exists (derived from the saved files, so it survives a reload).
  const rerunBtn = (what, fn) => h('button', { class: 'btn icon-only', title: `Run again: ${what}\nUses Claude`, 'aria-label': `Run again: ${what}`, disabled: !helperOk() || claudeBusy() ? true : null, on: { click: fn } }, ic('refresh'));
  // The step whose Claude job is running shows the progress and the Cancel button itself
  const runningJob = (...kinds) => (state.job && state.job.state === 'running' && kinds.includes(state.job.kind) ? state.job : null);
  const progressInline = (j) => h('div', { class: 'step-progress', role: 'status' }, h('span', { class: 'spinner' }), h('span', null, `Running (${j.seconds || 0}s)`), h('button', { class: 'btn small', on: { click: cancelJob } }, 'Cancel'));
  const STEP_OF = { full_score: 'step-score', tailor: 'step-tailor', build: 'step-tailor', brag: 'step-brag' };
  const doneAction = (label, rerun) => h('div', { class: 'done-actions' }, h('span', { class: 'btn done' }, ic('check'), label), rerun);
  function stepRow(n, title, sub, action, tickable, auto) {
    const done = isDone(n) || !!auto;
    const running = !!(action && action.classList && action.classList.contains('step-progress'));
    return h('div', { class: 'step' + (done ? ' is-done' : '') + (running ? ' is-running' : '') }, h('div', { class: 'step-n' }, done ? ic('check') : String(n)),
      h('div', { class: 'step-body' }, h('div', { class: 'step-title' }, title), h('div', { class: 'step-sub' }, sub),
        tickable && !auto ? h('button', { class: 'link-btn', style: 'font-size:.75rem;margin-top:.25rem', 'aria-pressed': String(done), on: { click: () => markDone(n) } }, done ? 'Undo done' : 'Mark done') : null), action);
  }
  function tipFor(r) {
    if (r.missing.length) return `You are missing ${r.missing.length} skill${r.missing.length === 1 ? '' : 's'} (for example ${r.missing[0]}). If you really have one, confirm it in your master file so it counts.`;
    if (r.unconfirmed.length || r.partial.length) return 'Some skills are only partial or on an older resume. Confirm them in your master file to lift the score honestly.';
    return 'Strong keyword match. Lead your resume with the projects that match the first three requirements.';
  }
  function nextSteps(c) {
    const { app, slug } = c;
    if (app && state.proposalFor !== slug) { state.proposalFor = slug; loadProposal(slug).then(render); }
    const hasBrag = !!(state.brag && state.brag.slug === slug && state.brag.text);
    const s = [];
    s.push(h('div', { class: 'step-wrap', id: 'step-save' },
      stepRow(1, 'Save this JD', 'Stores the text verbatim. Nothing is applied.', app ? h('span', { class: 'btn done' }, ic('check'), 'Saved') : h('button', { class: 'btn action', disabled: helperOk() ? null : true, on: { click: () => { state.saveCard = true; render(); } } }, 'Save JD', ic('arrow')), false, !!app),
      state.saveCard && !app ? h('div', { class: 'banner info stack' }, h('div', null, h('b', null, 'Create applications/' + slug + '.md? '), `It stores the JD text for ${c.scan.company}: ${c.scan.role}, verbatim, with status "considering". Nothing is applied or sent.`),
        h('div', { class: 'row' }, h('button', { class: 'btn primary', on: { click: saveJD } }, 'Create'), h('button', { class: 'btn', on: { click: () => { state.saveCard = false; render(); } } }, 'Cancel'))) : null,
      terminal(cmd(`claude "/job add ${c.scan.pasted ? '<paste the posting URL>' : c.scan.url}"`))));
    s.push(h('div', { class: 'step-wrap' + (runningJob('full_score') ? ' running' : ''), id: 'step-score' }, stepRow(2, 'Get the full score', app && app.fit_score != null ? `Last full score: ${app.fit_score}. Adds judgement on soft requirements.` : 'Adds judgement on soft requirements.',
      app ? (runningJob('full_score') ? progressInline(state.job) : app.fit_score != null ? doneAction('Scored', rerunBtn('full score', () => startJob('full_score', slug))) : claudeAction('Use Claude', () => startJob('full_score', slug))) : h('span', { class: 'faint' }, 'Save first'), false, app && app.fit_score != null), terminal(cmd(`claude "/job score ${slug}"`))));
    s.push(h('div', { class: 'step-wrap' + (runningJob('tailor', 'build') ? ' running' : ''), id: 'step-tailor' }, stepRow(3, 'Tailor your resume', 'Tailored resume (you approve it), plus a Brag Sheet to prepare from.', app ? (runningJob('tailor') ? progressInline(state.job) : state.proposal ? doneAction('Proposed', rerunBtn('resume proposal', () => startJob('tailor', slug))) : claudeAction('Use Claude', () => startJob('tailor', slug))) : h('span', { class: 'faint' }, 'Save first'), true, !!(app && app.resume_exists)),
      app ? bragCard(c, true) : null,
      state.proposal ? h('div', { class: 'sub' }, h('div', { class: 'faint' }, 'Proposal (you approve before anything is built):'), h('div', { class: 'proposal md-wrap', style: 'margin-top:.5rem' }, J.renderMarkdown(state.proposal)),
        state.feedback
          ? h('div', { style: 'margin-top:.5rem' }, h('textarea', { id: 'fb', 'aria-label': 'What to change' }), h('div', { class: 'row', style: 'margin-top:.5rem' },
              h('button', { class: 'btn primary', on: { click: () => { const v = document.getElementById('fb').value.trim(); if (v) { state.feedback = false; startJob('tailor', slug, v); } } } }, 'Send changes'),
              h('button', { class: 'btn', on: { click: () => { state.feedback = false; render(); } } }, 'Cancel')))
          : h('div', { style: 'margin-top:.5rem;display:flex;flex-direction:column;gap:.5rem' },
              runningJob('build') ? progressInline(state.job) : app && app.resume_exists
                ? h('div', { class: 'done-actions' }, doneAction('Resume built', rerunBtn('build the PDF', () => startJob('build', slug))), h('button', { class: 'btn action', on: { click: () => openFile(((state.helper && state.helper.repo) || '') + '/' + app.resume) } }, 'Open resume (PDF)', ic('ext')))
                : h('button', { class: 'btn primary block', disabled: !helperOk() || claudeBusy() ? true : null, on: { click: () => startJob('build', slug) } }, 'Approve and build PDF', h('span', { class: 'claude' }, 'uses Claude')),
              h('button', { class: 'btn block', on: { click: () => { state.feedback = true; render(); } } }, 'Request changes'))) : null,
      terminal(cmd(`claude "/job tailor ${slug}"`))));
    s.push(h('div', { class: 'step-wrap', id: 'step-missing' }, stepRow(4, 'Add missing skills', 'Confirm skills you really have in your master file.', h('button', { class: 'btn action', on: { click: () => { state.evTab = 'missing'; render(); const el = document.getElementById('evidence'); if (el) el.scrollIntoView({ block: 'start' }); } } }, 'View gaps', ic('arrow')), true)));
    s.push(h('div', { class: 'step-wrap' }, stepRow(5, 'Review before applying', 'Make sure your resume aligns with the JD.', app && app.resume_exists ? h('span', { class: 'btn done' }, ic('check'), 'Resume built') : h('button', { class: 'btn action', on: { click: () => goJd('details') } }, 'Review JD', ic('arrow')), true),
      terminal(cmd(`claude "/job build ${slug}"`))));
    s.push(h('div', { class: 'step-wrap' }, stepRow(6, 'Not for me', 'Mark this JD as skipped (withdrawn).', app ? h('button', { class: 'btn action', disabled: helperOk() ? null : true, on: { click: () => setStatus(slug, 'withdrawn') } }, 'Skip', ic('arrow')) : h('span', { class: 'faint' }, 'Save first')),
      terminal(cmd(`claude "/job status ${slug} withdrawn"`))));
    return h('div', { class: 'card', id: 'next-steps' }, h('div', { class: 'card-title' }, ic('bolt'), 'Next steps'), h('div', { class: 'steps' }, s));
  }
  function analysisTab(c) {
    const r = c.result;
    const tabs = [['matched', 'Matched', r.matched.length + r.partial.length * 0], ['missing', 'Missing', r.missing.length], ['unconfirmed', 'Unconfirmed', r.partial.length + r.unconfirmed.length], ['extra', 'Additional', c.extra.length]];
    const lists = { matched: [r.matched, '', 'Skills in your master data that this JD asks for.'], missing: [r.missing, 'missing', 'Not in your master data. If you do have them, confirm them there.'],
      unconfirmed: [[...r.partial.map((t) => t + ' (partial)'), ...r.unconfirmed], 'unconf', 'Partial or only on an older resume. These never raise the score until you confirm them.'],
      extra: [c.extra, 'hi', 'Skills you have that this JD does not mention. They do not change the score.'] };
    const [names, cls, note] = lists[state.evTab];
    const ovNum = (v, k, label) => h('div', null, h('div', { class: 'ov-label' }, label), h('div', { class: 'ov-num ' + k }, String(v)));
    const tip = tipFor(r);
    return [
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('user'), 'Profile overview'),
        h('div', { class: 'overview' }, h('div', null, h('div', { class: 'ov-label' }, c.full != null ? 'Full score' : 'Keyword match'), h('div', { class: 'ring-row' }, h('div', { class: 'ov-num' }, c.primary == null ? '--' : c.primary + '%'), ring(c.primary)),
          c.full != null ? h('div', { class: 'faint' }, 'Keyword match ', h('b', null, r.score == null ? '--' : r.score + '%')) : null),
          ovNum(r.missing.length, 'miss', 'Missing skills'), ovNum(c.extra.length, 'extra', 'Extra skills')),
        r.score != null ? h('div', { class: 'note', style: 'margin-top:.75rem' }, `Keyword breakdown: must-haves ${r.must.met} of ${r.must.n}` + (r.must.partial ? ` (+${r.must.partial} partial)` : '') + `  •  nice-to-haves ${r.nice.met} of ${r.nice.n}` + (r.nice.partial ? ` (+${r.nice.partial} partial)` : '')) : null),
      assessmentCard(c),
      experienceAlignment(c),
      h('div', { class: 'card', id: 'evidence' }, h('div', { class: 'card-title' }, 'Key skills match'),
        h('div', { class: 'tabs', role: 'tablist' }, tabs.map(([k, label, n]) => h('button', { class: 'tab', role: 'tab', 'aria-selected': String(state.evTab === k), on: { click: () => { state.evTab = k; render(); } } }, `${label} ${n}`))),
        names.length ? chipList(names, cls, 'ev-' + state.evTab, 8) : h('div', { class: 'faint' }, 'None.'), h('div', { class: 'faint', style: 'margin-top:.5rem' }, note)),
      h('button', { class: 'protip', on: { click: () => { state.resumeTab = 'skills'; go('resume'); } } }, ic('bulb', 'ic-big'), h('div', null, h('b', { class: 'grad-text' }, 'Pro Tip'), h('span', { class: 'muted' }, tip)), ic('chev', 'chev')),
      requirementCard(c),
      c.concerns.length ? h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('info'), 'Potential concerns'), h('div', { class: 'flags' }, c.concerns.map((x) => h('div', { class: 'flag ' + x.kind }, h('span', { class: 'dot' }), h('span', null, x.text))))) : null,
    ];
  }

  // ---- JD > Details --------------------------------------------------------------------------------
  function reqList(title, items, key) {
    if (!items.length) return null;
    const shown = state.expand[key] ? items : items.slice(0, 5);
    return h('div', { style: 'margin-bottom:.75rem' }, h('div', { class: 'ov-label', style: 'font-weight:700;margin-bottom:.25rem' }, title),
      h('ul', { class: 'bul' }, shown.map((q) => h('li', null, q.text))),
      items.length > 5 && !state.expand[key] ? h('button', { class: 'link-btn', on: { click: () => { state.expand[key] = true; render(); } } }, `Show all ${items.length}`, ic('arrow')) : null);
  }
  function detailsTab(c) {
    const s = c.scan, r = c.result;
    const rows = [['Job Title', s.role], ['Company', s.company], ['Location', s.location_text], ['Posted', postedLine(c).replace(/^Posted /, '')], ['Source', s.pasted ? 'Pasted text' : s.extraction === 'jsonld' ? 'Structured data on the page' : 'Page text']].filter((x) => x[1]);
    const desc = (s.jd_text || '').replace(/\s+/g, ' ').trim();
    const short = desc.length > 240 ? desc.slice(0, 238) + '...' : desc;
    const req = (r.requirements || []).filter((q) => q.kind === 'must'), pref = (r.requirements || []).filter((q) => q.kind === 'nice');
    return [
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('briefcase'), 'Job details'),
        h('div', { class: 'sub' }, h('dl', { class: 'kv' }, rows.map(([k, v]) => [h('dt', null, k), h('dd', null, v.length > 90 ? v.slice(0, 88) + '...' : v)]))),
        !s.pasted ? h('button', { class: 'btn block', style: 'margin-top:.75rem', on: { click: () => A.openUrl(s.url) } }, 'Open the original posting', ic('ext')) : null),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, h('span', { class: 'grad-text' }, ic('sparkle')), 'JD highlights'),
        c.terms.length ? h('div', { class: 'chips' }, c.terms.slice(0, 10).map((t) => h('span', { class: 'chip hi' }, t))) : h('div', { class: 'faint' }, 'No recognisable skills in this JD.')),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('list'), 'Required skills and qualifications'),
        req.length || pref.length ? [reqList('Required', req, 'reqs'), reqList('Preferred', pref, 'prefs')] : h('div', { class: 'faint' }, 'This JD has no separate requirements section. Read the description below.')),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('doc'), 'Job description'),
        h('div', { class: 'sub' }, h('div', { class: 'desc' + (state.descOpen ? ' full' : '') }, state.descOpen ? (s.jd_text || '') : short),
          desc.length > 240 ? h('button', { class: 'link-btn', style: 'margin-top:.5rem', on: { click: () => { state.descOpen = !state.descOpen; render(); } } }, state.descOpen ? 'Show less' : 'Read more', ic('arrow')) : null)),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, h('span', { class: 'grad-text' }, ic('crown')), 'Your match'),
        h('div', { class: 'between' }, h('div', { class: 'bar thick', style: 'flex:1;margin:.25rem 0', role: 'img', 'aria-label': `match ${c.primary || 0} percent` }, h('div', { class: 'bar-fill', style: `width:${c.primary || 0}%` })), h('b', { style: 'font-size:1.25rem' }, (c.primary == null ? '--' : c.primary) + '%')),
        c.full != null ? h('div', { class: 'faint' }, 'Full score, judged by Claude. Keyword match ', h('b', null, r.score == null ? '--' : r.score + '%')) : h('div', { class: 'faint' }, 'Keyword match. Get the full score for a judged number.'),
        h('div', { class: 'card-title', style: 'margin-top:1rem' }, 'Skills overlap'), chipList([...r.matched, ...r.partial], '', 'overlap', 6),
        h('div', { class: 'note', style: 'margin-top:.75rem;display:flex;gap:.5rem;align-items:center' }, ic('info'), 'Based on your resume data and the JD text. The breakdown is in Analysis.')),
    ];
  }


  // ---- JD > Resources: the two things you take away (send the resume, revise from the Brag Sheet) ----------------
  function resourcesTab(c) {
    const app = c.app, slug = c.slug;
    if (app && (!state.brag || state.brag.slug !== slug)) loadBrag(slug);
    const repo = (state.helper && state.helper.repo) || '';
    const hasResume = !!(app && app.resume_exists), hasBrag = !!(app && state.brag && state.brag.slug === slug && state.brag.text);
    const toSteps = h('button', { class: 'link-btn', on: { click: () => { state.jdTab = 'overview'; render(); setTimeout(() => { const el = document.getElementById('next-steps'); if (el) el.scrollIntoView({ block: 'start' }); }, 0); } } }, 'Go to Next steps', ic('arrow'));
    const card = (icon, title, body) => h('div', { class: 'card' }, h('div', { class: 'card-title' }, icon, title), body);
    const path = hasResume ? repo + '/' + app.resume : '';
    if (hasResume && (!state.pdfInfo || state.pdfInfo.key !== app.resume)) loadPdfInfo(slug, app.resume);
    const info = hasResume && state.pdfInfo && state.pdfInfo.key === app.resume ? state.pdfInfo : null;
    return [
      !app ? h('div', { class: 'banner info' }, ic('info', 'lg'), h('div', { class: 'grow' }, 'Save the JD first. The resume and Brag Sheet you build for it are kept here.')) : null,
      card(ic('doc'), 'Tailored resume',
        hasResume ? h('div', null, h('div', { class: 'muted', style: 'word-break:break-all' }, app.resume.split('/').pop()),
            info && info.pages ? h('div', { class: 'res-meta' }, h('b', null, `${info.pages} page${info.pages === 1 ? '' : 's'}`), info.bytes ? ` \u2022 ${Math.max(1, Math.round(info.bytes / 1024))} KB` : '') : null,
            h('div', { class: 'faint', style: 'margin:.25rem 0 .5rem' }, 'The PDF you approved. Send it with your application.'),
            h('div', { class: 'row' }, h('button', { class: 'btn action', on: { click: () => openFile(path) } }, 'Open PDF', ic('ext')), h('button', { class: 'btn small', on: { click: () => copy(path) } }, 'Copy file path')))
          : h('div', null, h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, 'Not built yet. Approve the proposal in Next steps and Claude builds the PDF.'), app ? toSteps : null)),
      card(h('span', { class: 'grad-text' }, ic('crown')), 'Brag Sheet',
        hasBrag ? h('div', null, h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, 'Your pitch for this JD. Read it before a screening call or interview.'),
            h('div', { class: 'row' }, h('button', { class: 'btn action', on: { click: () => openBrag(slug) } }, 'Open Brag Sheet', ic('ext')), h('button', { class: 'btn small', on: { click: () => { J.copyText(state.brag.text); toast('Brag Sheet copied as text'); } } }, 'Copy as text')))
          : h('div', null, h('div', { class: 'faint', style: 'margin-bottom:.5rem' }, state.brag && state.brag.loading ? 'Loading...' : 'Not made yet. Make it from Next steps.'), app && !(state.brag && state.brag.loading) ? toSteps : null)),
    ];
  }

  // Job title (links to the posting), company (links to its website) and posting date, above the JD tabs
  // The company's mark above its name: its own favicon (loaded straight from the company's site, never a third-party
  // service) when we know the site, otherwise the initial on the brand gradient.
  const logoCache = {};        // origin -> { ok, src } | { fail } | { pending }
  function companyIcon(name, site) {
    let origin = '';
    try { origin = site ? new URL(site).origin : ''; } catch (e) { origin = ''; }
    const c = origin && !MOCK ? logoCache[origin] : null;
    if (c && c.ok) return h('span', { class: 'co-icon has-img', 'aria-hidden': 'true' }, h('img', { src: c.src, alt: '' }));
    if (origin && !MOCK && !c) {                      // load once; when it arrives, redraw (the cache then serves it at once)
      logoCache[origin] = { pending: true };
      const img = new Image(); img.alt = '';
      img.onload = () => { logoCache[origin] = img.naturalWidth >= 16 ? { ok: true, src: img.src } : { fail: true }; render(); };
      img.onerror = () => { logoCache[origin] = { fail: true }; };
      img.src = origin + '/favicon.ico';
    }
    return h('span', { class: 'co-icon', 'aria-hidden': 'true' }, (name || '?').trim().charAt(0).toUpperCase());
  }
  function jobHeader(c) {
    const s = c.scan, site = s.company_url || (c.app && c.app.company_url) || '';
    const loc = (s.location_text || '').split('|')[0].trim();
    const meta = [postedLine(c), loc.length > 44 ? loc.slice(0, 42) + '...' : loc].filter(Boolean).join('  \u2022  ');
    const open = (url) => (e) => { e.preventDefault(); A.openUrl(url); };
    const title = s.pasted || !s.url ? h('span', { class: 'jh-title', title: s.role || 'Role not found' }, s.role || 'Role not found')
      : h('a', { class: 'jh-title jh-link', href: s.url, title: `${s.role || 'Role not found'}\nOpen JD page \u2197  ${s.url.replace(/^https?:\/\/(www\.)?/, '').split(/[/?#]/)[0]}`, on: { click: open(s.url) } }, h('span', { class: 'jh-clamp' }, s.role || 'Role not found'));
    const name = s.company || 'Unknown company';
    const company = site ? h('a', { class: 'jh-company jh-link', href: site, title: name + '\nOpen company website \u2197  ' + site.replace(/^https?:\/\/(www\.)?/, ''), on: { click: open(site) } }, name)
      : h('span', { class: 'jh-company', title: name }, name);
    return h('div', { class: 'jobhead' }, h('div', { class: 'jh-top' }, companyIcon(name, site), h('div', { class: 'jh-titles' }, title, company)), meta ? h('div', { class: 'jh-meta' }, meta) : null,
      h('div', { class: 'jh-row' }, salaryLine(c), statusBits(c)), sameCompanyNote(c));
  }
  function jdView() {
    const s = state.scan;
    if (!s || !s.ok) return [emptyView()];
    if (!state.profile) return [h('div', { class: 'banner warn stack' }, h('div', null, h('b', null, 'No skill profile yet. '), 'Build it once, then press Refresh:'), cmdRow(cmd('python3 tools/build_profile.py')))];
    const c = jobCtx();
    if (!c) return [h('div', { class: 'banner bad' }, h('div', { class: 'grow' }, state.error || 'Could not score this page.'))];
    return [jobHeader(c), contextTabs(JD_TABS, state.jdTab, (id) => { state.jdTab = id; }), jobCard(), ...{ overview: overviewTab, analysis: analysisTab, details: detailsTab, resources: resourcesTab }[state.jdTab](c)];
  }

  // ---- Resume: Profile | Skills | Experience -------------------------------------------------------
  function statusPill(st) { return h('span', { class: 'pill lv-' + st }, st); }
  function profileTab(rc) {
    const rs = rc.resume, p = rc.profile, c = appCounts();
    const summary = rs && rs.summaries && (rs.summaries.find((x) => x.id === 'S-AI') || rs.summaries[0]);
    const variant = rs && rs.summaries && rs.summaries.find((x) => x !== summary);
    const mod = rs ? fmtDate(rs.master_modified) : '';
    return [
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('doc'), 'Master resume'),
        h('div', { class: 'muted' }, mod ? `Last updated ${mod}` : 'No readable resume yet.', p ? h('span', { class: 'faint' }, ` · skill profile built ${fmtDate(p.generated_at)}`) : null),
        h('div', { class: 'row', style: 'margin:.75rem 0' }, h('button', { class: 'btn', on: { click: () => openMaster(false) } }, 'Open as HTML', ic('ext')), h('button', { class: 'btn', on: { click: () => openMaster(true) } }, 'Open as PDF', ic('ext'))),
        rs ? h('div', { class: 'sub' }, h('div', { class: 'ov-label', style: 'font-weight:700' }, rs.headline), summary ? h('p', { class: 'desc', style: 'margin:.5rem 0 0' }, summary.text) : null,
          variant ? h('details', { class: 'terminal' }, h('summary', null, `Other summary: ${variant.note || variant.id}`), h('p', { class: 'desc' }, variant.text)) : null) : null),
      rs ? h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('crown'), 'Education and certifications'),
        h('div', { class: 'flags' }, h('div', { class: 'flag' }, h('span', { class: 'dot' }), h('span', null, rs.education)), (rs.certifications || []).map((f) => h('div', { class: 'flag' }, h('span', { class: 'dot' }), h('span', null, f.text)))),
        (rs.awards || []).length ? h('details', { class: 'terminal' }, h('summary', null, `Awards and patent (${rs.awards.length})`), h('ul', { class: 'bul' }, rs.awards.map((f) => h('li', null, f.text)))) : null,
        (rs.open_work || []).length ? h('details', { class: 'terminal' }, h('summary', null, 'Open work'), h('ul', { class: 'bul' }, rs.open_work.map((f) => h('li', null, f.text)))) : null) : null,
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('people'), 'Applications'),
        h('div', { class: 'evis' }, [['Saved', c.considering], ['Applied', c.applied + c.screening], ['Interviewing', c.interviewing]].map(([l, n]) => h('div', { class: 'evi static' }, h('b', null, String(n)), h('span', null, l)))),
        h('button', { class: 'btn block ghost', style: 'margin-top:.75rem', on: { click: () => A.openApps() } }, `Open Applications (${c.all})`, ic('ext'))),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('gear'), 'Profile management'),
        h('div', { class: 'faint' }, 'Your master resume is the single source of truth. A job-specific resume never overwrites it: tailored versions are built in their own folder.'),
        h('div', { class: 'row', style: 'margin:.75rem 0' }, h('button', { class: 'btn small', on: { click: rebuildProfile } }, ic('refresh'), 'Rebuild skill profile'), h('button', { class: 'btn small', disabled: helperOk() ? null : true, on: { click: rescoreSaved } }, ic('chart'), 'Rescore saved JDs')),
        h('details', { class: 'terminal' }, h('summary', null, 'How to change your profile'),
          h('div', { class: 'faint', style: 'margin:.5rem 0' }, 'A skill only counts when it has a level and evidence. Add one with the command below (it keeps a backup and rebuilds for you), then press Rescore saved JDs here and run Get the full score again.'),
          cmdRow(cmd('python3 tools/add_skill.py "<Skill>" --group <Group> --fact "<where and how you used it>"'), 'Add a skill with its evidence:'), cmdRow(`open "${repo()}/master/master-resume.md"`, 'Or open the master file:'), cmdRow(cmd('claude "update my master resume: <what changed>"'), 'Or ask Claude:'))),
    ];
  }
  function skillsTab(rc) {
    const rs = rc.resume;
    if (!rs) return [h('div', { class: 'banner warn stack' }, h('div', null, h('b', null, 'No readable resume yet. '), 'Build it once, then reopen this tab:'), cmdRow(cmd('python3 tools/build_profile.py')))];
    return [h('div', { class: 'banner info' }, ic('info'), h('div', { class: 'grow' }, 'Levels decide what counts when a JD is scored. Tap an evidence ID to read the fact behind a skill.')),
      ...rs.skills.map((g) => h('div', { class: 'card' }, h('div', { class: 'card-title' }, g.group),
        g.rows.map((row) => h('div', { class: 'skill-row' }, h('div', { class: 'between' }, h('span', { class: 'skill-name' }, row.skills), h('span', { class: 'pill lv-' + row.level }, LEVEL_LABEL[row.level] || row.level)),
          row.years ? h('div', { class: 'faint' }, 'Years: ' + row.years) : null,
          row.evidence.length ? h('div', { class: 'chips' }, row.evidence.map(factChip)) : h('div', { class: 'faint' }, 'No evidence recorded yet.'), factText(row.evidence)))))];
  }
  function experienceTab(rc) {
    const rs = rc.resume;
    if (!rs) return skillsTab(rc);
    const block = (cmp) => h('details', { class: 'company', open: state.expand['co-' + cmp.company] ? true : null, on: { toggle: (e) => { state.expand['co-' + cmp.company] = e.target.open; } } },
      h('summary', null, h('div', { class: 'between' }, h('b', null, cmp.company), h('span', { class: 'faint' }, cmp.period)), h('div', { class: 'muted' }, [cmp.title, cmp.location].filter(Boolean).join(' · '))),
      h('div', { class: 'facts' }, cmp.facts.map((f) => h('div', { class: 'fact' }, h('div', { class: 'between' }, h('span', { class: 'chip fact static' }, f.id), statusPill(f.status)), h('div', { class: 'desc' }, f.text), f.needs_confirm ? h('div', { class: 'faint' }, 'Needs your confirmation.') : null))));
    const projects = rs.companies.filter((x) => /^own products/i.test(x.company)), jobs = rs.companies.filter((x) => !/^own products/i.test(x.company));
    return [h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('briefcase'), 'Professional experience'), jobs.map(block)),
      projects.length ? h('div', { class: 'card' }, h('div', { class: 'card-title' }, ic('sparkle'), 'Projects and achievements'), projects.map(block),
        (rs.awards || []).length ? h('details', { class: 'terminal' }, h('summary', null, `Awards (${rs.awards.length})`), h('ul', { class: 'bul' }, rs.awards.map((f) => h('li', null, f.text)))) : null) : null];
  }
  function resumeView() {
    const rc = resumeCtx();
    return [currentJobStrip(), contextTabs(RESUME_TABS, state.resumeTab, (id) => { state.resumeTab = id; }), ...{ profile: profileTab, skills: skillsTab, experience: experienceTab }[state.resumeTab](rc)];
  }

  // ---- settings ------------------------------------------------------------------------------------
  function settingsView() {
    const s = state.settings, t = s.threshold, p = state.profile;
    const seg = (key, opts) => h('div', { class: 'segmented', role: 'group' }, opts.map(([v, label]) => h('button', { 'aria-pressed': String(s[key] === v), on: { click: () => saveSettings({ [key]: v }) } }, label)));
    return [currentJobStrip(), h('div', { class: 'subhead' }, h('h1', null, ic('gear', 'lg'), 'Settings')),
      h('div', { class: 'card', id: 'scoring-card' }, h('div', { class: 'card-title' }, 'Scoring'),
        h('div', { class: 'faint' }, `The score you treat as worth a look. It starts at ${DEFAULT_THRESHOLD} until you save your own, and applies to every JD: the Overview shows a ring at this value and a verdict.`),
        (() => {
          const draft = state.thrDraft != null ? state.thrDraft : (t != null ? t : DEFAULT_THRESHOLD);
          const saveBtn = h('button', { class: 'btn small', disabled: t === draft ? true : null, on: { click: () => { const v = state.thrDraft != null ? state.thrDraft : draft; state.thrDraft = null; saveSettings({ threshold: v }); toast('Threshold saved: ' + v); } } }, 'Save threshold');
          return h('div', null,
            h('div', { class: 'row', style: 'align-items:center;margin-top:.5rem' },
              h('input', { type: 'range', min: '0', max: '100', value: String(draft), 'aria-label': 'Threshold', on: { input: (e) => { state.thrDraft = Number(e.target.value); document.getElementById('thr-val').textContent = e.target.value; saveBtn.disabled = state.thrDraft === t; } } }),
              h('div', { id: 'thr-val', style: 'flex:0 0 auto;font-size:1.5rem;font-weight:700', 'aria-live': 'polite' }, String(draft))),
            h('div', { class: 'row', style: 'margin-top:.5rem;align-items:center' }, saveBtn,
              t != null ? h('button', { class: 'link-btn', on: { click: () => { state.thrDraft = null; saveSettings({ threshold: null }); toast(`Threshold reset to the default (${DEFAULT_THRESHOLD})`); } } }, `Reset to default (${DEFAULT_THRESHOLD})`) : null,
              h('span', { class: 'faint' }, t == null ? `Using the default (${DEFAULT_THRESHOLD})` : 'Saved: ' + t)));
        })(),
        h('div', { class: 'card-title', style: 'margin-top:1rem' }, 'Scoring preferences'),
        h('div', { class: 'faint' }, 'How a partial skill (a certificate, or learning only) counts toward the score. Skills only on an older resume never count until you confirm them.'),
        h('div', { style: 'margin-top:.5rem' }, h('div', { class: 'segmented', role: 'group' }, [[0.5, 'Half credit'], [0, 'No credit'], [1, 'Full credit']].map(([v, label]) => h('button', { 'aria-pressed': String(s.partialCredit === v), on: { click: () => saveSettings({ partialCredit: v }) } }, label)))),
        h('details', { class: 'terminal' }, h('summary', null, 'How the score is calculated'), h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Score = 70% of the must-have requirements met + 30% of the nice-to-haves met. Each requirement is met, partial (half) or a gap, judged against your master resume. Soft requirements such as communication are not scored.'))),
      h('div', { class: 'card', id: 'resume-length-card' }, h('div', { class: 'card-title' }, 'Tailored resume length'),
        h('div', { class: 'faint' }, 'How many pages a tailored resume should have. Claude trims to this and the build check enforces it. Choose Any length to leave it open.'),
        h('div', { style: 'margin-top:.5rem' }, h('div', { class: 'segmented', role: 'group' }, [[1, '1 page'], [2, '2 pages'], [3, '3 pages'], ['any', 'Any length']].map(([v, label]) => h('button', { 'aria-pressed': String(((state.prefs || {}).resume_pages || 2) === v), disabled: helperOk() ? null : true, on: { click: () => setPages(v) } }, label)))),
        helperOk() ? null : h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Needs the local helper (it keeps this next to your master resume).')),
      h('div', { class: 'card', id: 'resume-layout-card' }, h('div', { class: 'card-title' }, 'Tailored resume layout'),
        h('div', { class: 'faint' }, 'The look a tailored resume starts from. The previews use made-up content; your resume uses your own facts.'),
        h('div', { class: 'layout-pick', role: 'group', 'aria-label': 'Tailored resume layout', style: 'margin-top:.5rem' }, LAYOUTS.map(([v, label, hint]) => h('button', { 'aria-pressed': String(((state.prefs || {}).resume_layout || 'two-column') === v), 'aria-label': `${label} layout: ${hint}`, disabled: helperOk() ? null : true, on: { click: () => setLayout(v) } },
          h('img', { src: `layouts/${v}.png`, alt: '', loading: 'lazy' }), h('span', { class: 'layout-name' }, label), h('span', { class: 'faint' }, hint)))),
        helperOk() ? null : h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Needs the local helper (it keeps this next to your master resume).')),
      photoCard(),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Appearance'),
        h('div', { class: 'faint' }, 'Theme'), h('div', { style: 'margin:.25rem 0 .75rem' }, seg('theme', [['system', 'System'], ['light', 'Light'], ['dark', 'Dark']])),
        h('div', { class: 'faint' }, 'Text size. Chrome has no zoom for side panels, so the panel scales itself. Cmd or Ctrl with + , - or 0 also works while it has focus.'),
        h('div', { class: 'row', style: 'align-items:center;margin-top:.5rem' }, h('button', { class: 'btn small', 'aria-label': 'Smaller text', on: { click: () => bumpScale(-1) } }, 'A-'),
          h('div', { style: 'text-align:center;flex:1 1 auto', 'aria-live': 'polite' }, SCALE_LABELS[s.textScale] || 'Default', h('span', { class: 'faint' }, ` (${Math.round((s.textScale || 1) * 100)}%)`)),
          h('button', { class: 'btn small', 'aria-label': 'Larger text', on: { click: () => bumpScale(1) } }, 'A+'), h('button', { class: 'btn small', on: { click: () => bumpScale(0) } }, 'Reset')),
        h('div', { style: 'margin-top:.5rem' }, h('button', { class: 'btn small', on: { click: () => A.openPanelTab() } }, 'Open in a full tab', ic('ext')))),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Reading page'),
        h('div', { class: 'faint' }, 'By default the panel reads a page only when you click the JD Lens icon on it. You can allow it to re-read automatically as you switch tabs while the panel is open. Any http or https page works; browser pages such as chrome:// cannot be read. The pin keeps one JD in place.'),
        h('div', { style: 'margin-top:.5rem' }, state.autoScan ? h('span', { class: 'pill ok' }, 'Automatic reading is on') : h('button', { class: 'btn small', on: { click: async () => { state.autoScan = await A.requestAutoScan(); render(); } } }, 'Allow reading job pages automatically'))),
      dataFolderCard(),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Local helper'),
        state.helper && state.helper.ok ? h('dl', { class: 'kv' }, h('dt', null, 'Status'), h('dd', null, h('span', { class: 'pill ok' }, 'connected')), h('dt', null, separate() ? 'Data folder' : 'Repo'), h('dd', null, pathWithOpen(state.helper.data || state.helper.repo, 'data', 'Open the data folder')),
          separate() ? [h('dt', null, 'Engine'), h('dd', null, pathWithOpen(engineDir(), 'engine', 'Open the engine folder'))] : null,
          h('dt', null, 'Resume file'), h('dd', null, (state.helper.data || state.helper.repo) + '/master/master-resume.md'), h('dt', null, 'Skill profile'), h('dd', null, (engineDir() || state.helper.repo) + '/tools/jd-capture-extension/data/profile.json'),
          h('dt', null, 'Claude'), h('dd', null, state.helper.claude || 'not found'), h('dt', null, 'Version'), h('dd', null, state.helper.version))
          : h('div', null, h('span', { class: 'pill warn' }, 'not connected'), state.helper && state.helper.error ? h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Chrome says: ' + state.helper.error) : null, cmdRow(cmd('python3 tools/jobd/install.py'), 'Install once:'))),
      h('div', { class: 'card' }, h('div', { class: 'card-title' }, 'Skill profile'),
        p ? h('dl', { class: 'kv' }, h('dt', null, 'Generated'), h('dd', null, fmtDate(p.generated_at)), h('dt', null, 'Skills'), h('dd', null, `${(p.stats && p.stats.skill_rows) || p.rows.length} skill rows`),
          h('dt', null, 'Evidence'), h('dd', null, `${(p.stats && p.stats.evidence_entries) || 0} evidence entries`), h('dt', null, 'Career start'), h('dd', null, p.career_start)) : h('div', { class: 'faint' }, 'None'),
        h('div', { class: 'row', style: 'margin-top:.75rem' }, h('button', { class: 'btn small', on: { click: () => { state.showProfileJson = !state.showProfileJson; render(); } } }, 'Show what the extension holds'), h('button', { class: 'btn small', on: { click: rebuildProfile } }, 'Rebuild skill profile')),
        state.showProfileJson ? h('pre', { class: 'json' }, JSON.stringify(p, null, 2)) : null,
        h('div', { class: 'faint', style: 'margin-top:.5rem' }, 'Skills, levels and evidence IDs. The readable resume (no contact details, no compensation) is stored beside it for the Resume tab.'))];
  }

  // ---- render --------------------------------------------------------------------------------------
  function render() {
    const root = document.getElementById('app');
    const scroll = window.scrollY;
    root.replaceChildren();
    let body;
    if (state.view === 'settings') body = settingsView();
    else if (state.view === 'resume') body = resumeView();
    else body = state.loading ? [loader('Reading this job...')] : jdView();
    body = body.filter(Boolean);
    const jobhead = body[0] && body[0].classList && body[0].classList.contains('jobhead') ? body.shift() : null;
    root.append(header(), h('div', { class: 'hero' }, tabbar(), jobhead || null), ...banners(), ...body);
    if (state.toast) root.append(h('div', { class: 'toast', role: 'status' }, state.toast));
    window.scrollTo(0, scroll);
    document.body.dataset.overflow = String(document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 || root.scrollWidth > root.clientWidth + 1);
    if (document.body.dataset.overflow === 'true') {
      const edge = root.getBoundingClientRect().right + 1;
      document.body.dataset.overflowEls = [...root.querySelectorAll('*')].filter((e) => e.getBoundingClientRect().right > edge)
        .slice(0, 6).map((e) => e.tagName.toLowerCase() + '.' + (typeof e.className === 'string' ? e.className : '') + ':' + (e.textContent || '').trim().slice(0, 24)).join(' | ');
    }
    const clipped = [...root.querySelectorAll('.next-cta, .step-title, .step-sub, .jh-pill')].filter((e) => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible');
    document.body.dataset.clipped = clipped.map((e) => e.className + ':' + (e.textContent || '').trim().slice(0, 24)).join(' | ');
    document.body.dataset.ready = '1';
  }
  boot();
})();
