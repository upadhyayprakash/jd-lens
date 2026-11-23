/* Design and test harness only. Active ONLY when the page URL has ?mock (never in normal use).
 * Feeds the panel and the Applications page sample data so screens can be rendered and checked without Chrome's extension APIs.
 * Options: ?mock&screen=jd|resume|settings&tab=overview|analysis|details|profile|skills|experience&theme=light|dark
 *          &state=empty|loading|stale|nohelper|saved|applied|running|proposal|pinned&delta=7&threshold=70&scale=1.5&mockwidth=320
 * Applications page: applications.html?mock&state=nohelper|empty#globex-2026-10 */
(function () {
  const params = new URLSearchParams(location.search);
  if (!params.has('mock')) return;
  const st = params.get('state') || '';

  const JD = `Senior Full Stack Engineer - EMEA
Overview
Application
Who we are is what we do.
Northwind is the all-in-one payroll and HR platform for global teams. Among the largest globally distributed companies in the world, our team of 7,000 spans more than 100 countries.
Summary
The Senior Full Stack Engineer is responsible for designing, developing, and maintaining both the front-end and back-end components of Northwind's platform. You will be part of a cross-functional team that collaborates closely with Product, Design, and DevOps teams to deliver high-quality, scalable, and secure solutions.
Responsibilities
You will develop high-quality, responsive web applications using TypeScript, Javascript, React, Express. Experience with NestJS, Vite, and Next.js is a plus.
You will design and implement server-side APIs, data models, and business logic using mainly Express framework
You will create client-side function-based React components, hooks, stories, and tests to interact with your server-side work
You will create and optimize database schemas, queries, and interactions with Postgres.
You will build reusable and modular components on both the front and back end that promote code reusability, maintainability, and scalability.
You will participate in code reviews and provide constructive feedback to team members to maintain code quality standards.
Qualifications
At least 8 years of Full-Stack experience, with a focus on TypeScript development.
Expert in the art of designing, coding, testing, and maintaining applications using the tech listed above.
Thrive in a collaborative, remote-first work culture where teamwork and camaraderie are key.
Embrace independence and take ownership of your projects, yet also excel in a team setting and love to contribute.
Communicate complex ideas with ease and enjoy collaborating with diverse teams of technical and non-technical stakeholders.
Extra brownie points if you:
Have experience with SaaS products running 24/7 on a major cloud vendor.
Solid understanding of RESTful APIs, microservices architecture, and asynchronous programming.
Experience with testing frameworks (Jest, Mocha, Chai, Storybook, React Testing Library) and automated testing methodologies (Cypress).
Knowledge of containerization technologies (Docker, Kubernetes)
Total Rewards
Salary ranges are quoted in USD as a consistent global reference. Your offer will be localized to your country's currency using a market-aligned conversion.
Full-Stack Engineering
Full-time
Locations:
India, Pakistan, Philippines, Indonesia, Belgium, Czech Republic, Estonia, Croatia, Armenia, Egypt, Albania, Georgia, Greece, Spain, Slovakia
Salary range:
$60,000 - $100,000 USD
Posted on
June 03, 2026`;

  const SCAN = { ok: true, tabId: 1, url: 'https://www.northwind.example/careers/job/1946e291-2f42-4d70-9306-6582f6506b61/?source=linkedin',
                 source_title: 'Senior Full Stack Engineer - EMEA - Careers at Northwind', extraction: 'main-text', company: 'Northwind', company_url: 'https://www.northwind.example',
                 role: params.has('longtitle') ? 'Senior Staff Software Engineer, Distributed Identity Platform and Developer Experience (Remote, EMEA and India)' : 'Senior Full Stack Engineer - EMEA', location_text: 'India, Pakistan, Philippines +20 more', salary_text: null, posted: '2026-06-03', jd_text: JD };

  const PHOTO_PREVIEW = 'data:image/svg+xml;utf8,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Crect width=%27100%27 height=%27100%27 fill=%27%23C9C2B6%27/%3E%3Ccircle cx=%2750%27 cy=%2738%27 r=%2717%27 fill=%27%23F3EFE8%27/%3E%3Cpath d=%27M16 100c2-24 17-36 34-36s32 12 34 36z%27 fill=%27%23F3EFE8%27/%3E%3C/svg%3E';
  const profile = {
    schema: 1, generated_at: '2026-11-21T20:14:00+05:30', master_modified: '2026-11-22T00:20:00+05:30', master_sha256: 'mock', repo_path: '/Users/example/jd-lens', career_start: '2014-07',
    domains: ['SaaS', 'payments', 'fintech', 'real-time'], stats: { skill_rows: 25, evidence_entries: 14 },
    rows: [
      ['React (function components, hooks)', 'listed', ['F-LM-01', 'F-PY-01', 'F-EV-02']], ['TypeScript', 'listed', ['F-LM-01']], ['JavaScript', 'user-confirmed', ['F-BR-02']], ['Next.js', 'listed', ['F-SP-06']],
      ['React Testing Library', 'user-confirmed', ['F-USR-02']], ['Jest', 'listed', ['F-LM-05']], ['Playwright', 'listed', ['F-SP-03']], ['Storybook', 'user-confirmed', ['F-USR-03']],
      ['Mocha, Chai', 'user-confirmed', ['F-USR-03']], ['Node.js', 'listed', ['F-LM-04']], ['NestJS', 'listed', ['F-LM-04']], ['Express.js', 'user-confirmed', ['F-USR-01']],
      ['REST APIs', 'listed', ['F-LM-02']], ['Microservices', 'user-confirmed', ['F-LM-04']], ['Kafka', 'user-confirmed', ['F-USR-04']], ['Redis', 'listed', ['F-LM-02']], ['BullMQ', 'listed', ['F-LM-04']],
      ['Event-driven design', 'listed', ['F-SP-01']], ['PostgreSQL', 'user-confirmed', ['F-BR-04']], ['MySQL', 'user-confirmed', ['F-BR-04']], ['AWS (S3, CloudFront, EC2)', 'listed', ['F-PY-03']],
      ['Docker', 'listed', ['F-SAP-02']], ['Kubernetes', 'partial', ['F-CE-01']], ['GitHub Actions, GitLab CI', 'listed', ['F-PY-03']], ['Java, Go, Spring Boot', 'earlier', ['F-SAP-03']],
    ].map(([skills, level, evidence]) => ({ skills, level, evidence })),
  };
  if (params.get('datafolder') === 'separate') profile.repo_path = '/Users/example/My Resume Data';     // your data folder is apart from the engine

  const F = (id, status, text, needs) => ({ id, status, text, needs_confirm: !!needs });
  const resume = {
    schema: 1, generated_at: profile.generated_at, master_modified: profile.master_modified, headline: 'Senior Full-Stack Engineer · AI Product Engineering',
    education: 'B.E. Computer Science, Example University, 2010 to 2014', career_start: '2014-07',
    summaries: [
      { id: 'S-AI', note: 'current resume', text: 'Full-stack engineer with 10+ years across fintech (Payly, EventHub) and AI products (Lumenly, Brightlabs). Ships LLM features in production, from real-time AI writing suggestions at ~9K req/s to streaming PDF-Chat. USPTO patent holder.', facts: [] },
      { id: 'S-FS', note: 'proposed, product full-stack', text: 'Senior full-stack engineer with 10+ years building TypeScript, React and Node.js SaaS systems at scale: PayPlus payments (2.4M transactions/day, latency cut 80%), Lumenly real-time pipelines (~9K req/s peak).', facts: [] },
    ],
    companies: [
      { company: 'Lumenly', title: 'Senior Fullstack Developer, Core Tools & Growth', period: 'Feb 2025 to now', location: 'Remote', facts: [
        F('F-LM-01', 'verified', 'Led the Grammar Checker migration to TipTap v3 with LLM-powered real-time recommendation pipelines, streamed check-as-you-type over WebSockets.'),
        F('F-LM-02', 'verified', 'Designed and scaled rate-limited recommendation APIs for freemium access with Redis-backed usage limits at ~9K req/s peak.'),
        F('F-LM-04', 'verified', 'Extended the NestJS job service (PDF suite) with a handler registry and strategy-based provider abstraction.'),
        F('F-LM-05', 'verified', 'Ships through an Nx monorepo (30+ packages) with canary rollouts, AI code review, UAT, integration suites and A/B releases.') ] },
      { company: 'Own products', title: 'Founder & Engineer', period: '2025 to now', location: 'Bengaluru', facts: [
        F('F-SP-01', 'verified', 'Agentic PR Platform: event-driven multi-agent system turning GitHub issues, Slack requests and PRDs into reviewed pull requests.'),
        F('F-SP-06', 'verified', 'Contoso, "the trust layer for modern discovery". Next.js, Nx.') ] },
      { company: 'Payly Financial', title: 'Senior Fullstack Developer (Lead)', period: 'May 2022 to Aug 2024', location: 'Bengaluru', facts: [
        F('F-PY-01', 'verified', 'Led the frontend revamp of the PayPlus payments app (2.4M transactions/day), cutting latency by 80% (300ms to 63ms).'),
        F('F-PY-03', 'verified', 'Led scoping, risk assessment and estimation; built CI/CD on AWS S3/CloudFront with New Relic monitoring.'),
        F('F-PY-04', 'earlier', 'Stack on that team: Java, ReactJS, AWS, GitLab CI/CD, Istio.', true) ] },
      { company: 'Brightlabs', title: 'Fullstack Developer', period: 'Apr 2019 to Jul 2020', location: 'Bengaluru', facts: [
        F('F-BR-02', 'verified', 'Built admin dashboards with RBAC; materialised OLAP queries and client caching cut page load by 40%.'),
        F('F-BR-04', 'user-confirmed', 'Production-level schema design on Postgres and MySQL: denormalised tables and role-based views for real-time dashboards.') ] },
    ],
    awards: [F('F-AW-01', 'verified', 'US 10,936,288, Voice-enabled User Interface Framework, USPTO, granted Mar 2021 (SAP Labs).'), F('F-AW-02', 'verified', 'Winner, Lumenly DevJam, May 2025.')],
    certifications: [F('F-CE-01', 'verified', 'Software Architecture: From Developer to Architect; Learning Kubernetes; Deep learning foundations (TSAI EVA).')],
    open_work: [F('F-OW-01', 'verified', 'HDR brightness preference: proposed a CSS user preference for sudden HDR brightness spikes (w3c/csswg-drafts#14616).')],
    other: [],
    skills: [
      { group: 'Frontend', rows: [
        { skills: 'React (function components, hooks)', level: 'listed', evidence: ['F-LM-01', 'F-PY-01'], years: '', notes: '' },
        { skills: 'TypeScript', level: 'listed', evidence: ['F-LM-01'], years: '', notes: '' },
        { skills: 'Storybook', level: 'user-confirmed', evidence: [], years: '', notes: '' },
        { skills: 'Cypress', level: 'none', evidence: [], years: '', notes: 'Not confirmed.' }] },
      { group: 'Backend', rows: [
        { skills: 'Node.js', level: 'listed', evidence: ['F-LM-04'], years: '', notes: '' },
        { skills: 'Express.js', level: 'user-confirmed', evidence: ['F-BR-04'], years: 'since Apr 2019', notes: '' },
        { skills: 'Kafka', level: 'user-confirmed', evidence: [], years: '', notes: '' }] },
      { group: 'Infra and delivery', rows: [
        { skills: 'Kubernetes', level: 'partial', evidence: ['F-CE-01'], years: '', notes: 'Certificate and learning only.' },
        { skills: 'Java, Go, Spring Boot', level: 'earlier', evidence: [], years: '', notes: '' }] },
    ],
    facts: {},
  };
  resume.companies.forEach((c) => c.facts.forEach((f) => { resume.facts[f.id] = Object.assign({ where: c.company }, f); }));
  [...resume.awards, ...resume.certifications, ...resume.open_work].forEach((f) => { resume.facts[f.id] = Object.assign({ where: 'Awards and more' }, f); });

  const apps = [
    { slug: 'northwind-2026-11', company: 'Northwind', role: 'Senior Full Stack Engineer - EMEA', status: 'applied', applied: '2026-11-21', added: '2026-11-21', location: 'India, Pakistan, Philippines, Indonesia', last_activity: '2026-11-21', fit_score: 86, fit_scored: '2026-11-21', quick_score: 97, posted: '2026-06-03', source: SCAN.url, resume: 'tailored/northwind-2026-11/alex_morgan_resume_northwind.pdf', resume_exists: true },
    { slug: 'umbrella-2026-11', company: 'Umbrella', role: 'Full Stack Software Engineer, Staff (CAD Infrastructure)', status: 'considering', applied: '', added: '2026-11-21', location: 'Bengaluru, India', last_activity: '2026-11-21', fit_score: 78, quick_score: 71, posted: '', source: 'https://careers.umbrella.com/careers/job/446720103301', resume: '', resume_exists: false },
    { slug: 'globex-2026-10', company: 'Globex', role: 'Principal Software Engineer, Agent & App Platform', status: 'interviewing', applied: '2026-10-17', added: '2026-10-17', location: 'Remote', last_activity: '2026-10-25', fit_score: null, quick_score: 50, posted: '', source: 'LinkedIn', resume: '', resume_exists: false },
    { slug: 'initech-2026-10', company: 'Initech', role: 'Applied AI Architect (Technical Success)', status: 'applied', applied: '2026-10-19', added: '2026-10-19', location: 'Bengaluru, Mumbai or Delhi (hybrid)', last_activity: '2026-10-19', fit_score: null, quick_score: 60, posted: '', source: 'Ashby', resume: '', resume_exists: false },
    { slug: 'contoso-2026-10', company: 'Contoso', role: 'Staff Engineer - Platform', status: 'offer', applied: '2026-10-02', added: '2026-10-01', location: 'Remote', last_activity: '2026-11-18', fit_score: 91, quick_score: 88, posted: '', source: 'https://example.com/jobs/1', resume: '', resume_exists: false },
    { slug: 'fabrikam-2026-09', company: 'Fabrikam', role: 'Software Engineer', status: 'rejected', applied: '2026-09-18', added: '2026-09-17', location: 'Pune, India', last_activity: '2026-10-03', fit_score: 64, quick_score: 66, posted: '', source: 'https://example.com/jobs/2', resume: '', resume_exists: false },
    { slug: 'wingtip-2026-09', company: 'Wingtip', role: 'Backend Engineer', status: 'withdrawn', applied: '', added: '2026-09-05', location: '', last_activity: '2026-09-09', fit_score: null, quick_score: 40, posted: '', source: 'https://example.com/jobs/3', resume: '', resume_exists: false },
  ];
  if (params.has('fit')) apps[0].fit_score = Number(params.get('fit'));         // test: Claude's score can be lower than the keyword score
  let saved = apps.filter((a) => a.slug !== 'northwind-2026-11');
  if (st === 'applied' || st === 'nofit' || st === 'running' || st === 'denied') saved = apps.slice();
  if (params.get('nofitscore')) saved = saved.map((a) => (a.slug === 'northwind-2026-11' ? Object.assign({}, a, { fit_score: null, fit_scored: '' }) : a));   // no full score yet
  if (st === 'proposal') saved = apps.map((a) => (a.slug === 'northwind-2026-11' ? Object.assign({}, a, { resume: '', resume_exists: false }) : a));   // proposal waiting for approval: no PDF yet
  if (st === 'saved') saved = apps.map((a) => (a.slug === 'northwind-2026-11' ? Object.assign({}, a, { status: 'considering', applied: '', resume: '', resume_exists: false }) : a));
  if (st === 'empty-apps') saved = [];
  let jobStart = 0;

  const HIST = {
    'globex-2026-10': [['2026-10-17', '-', 'applied', 'Added'], ['2026-10-22', 'applied', 'screening', 'Recruiter replied'], ['2026-10-25', 'screening', 'interviewing', 'Technical round booked']],
    'northwind-2026-11': [['2026-11-21', '-', 'applied', 'Added']],
  };
  const ROUNDS = { 'globex-2026-10': [['2026-10-25', 'Recruiter call', 'Talent partner', 'Walked through the platform team scope. Asked about Temporal.', 'advanced'], ['2026-11-02', 'Technical interview', 'Staff engineer', 'System design: agent registry.', 'pending']] };

  window.MockApi = {
    settings: { get: async () => ({ threshold: params.has('threshold') ? Number(params.get('threshold')) : null, theme: 'system', textScale: params.has('scale') ? Number(params.get('scale')) : 1,
      permNudgeAt: params.has('nudge') ? 1 : Date.now(), scoreHistory: params.has('delta') ? { 'https://www.northwind.example/careers/job/1946e291-2f42-4d70-9306-6582f6506b61': { score: 97 - Number(params.get('delta')), at: 0 } } : {}, salaryNotes: {}, stepsDone: params.has('done') ? { 'northwind-2026-11': { 4: true } } : {} }), set: async () => {} },
    activeTab: async () => (params.has('othertab') ? 98765 : null), tabScan: async () => null, onTab: () => {},
    host: async (op, a) => {
      a = a || {};
      if (st === 'nohelper') return { ok: false, helper_missing: true, error: 'Specified native messaging host not found.' };
      switch (op) {
        case 'resume_info': return { ok: true, found: true, pages: params.get('pdfpages') ? Number(params.get('pdfpages')) : 2, bytes: 86000 };
        case 'get_prefs': return { ok: true, prefs: { resume_pages: params.get('pages') === 'any' ? 'any' : Number(params.get('pages')) || 2, resume_layout: params.get('layout') || 'two-column' } };
        case 'set_pref': return { ok: true, prefs: a.key === 'resume_layout' ? { resume_pages: 2, resume_layout: a.value } : { resume_pages: a.value === 'any' ? 'any' : Number(a.value), resume_layout: 'two-column' } };
        case 'ping': {
          const sep = params.get('datafolder') === 'separate', data = sep ? '/Users/example/My Resume Data' : profile.repo_path;
          return { ok: true, version: '1.0.0', repo: data, engine: '/Users/example/jd-lens', data, data_source: sep ? 'config' : 'engine', has_master: params.get('nomaster') ? false : true,
                   claude: '/Users/example/.local/bin/claude', node: '/usr/local/bin/node' };
        }
        case 'photo_info': return { ok: true, has_photo: params.has('photo'), path: '/Users/example/My Resume Data/master/photo.jpg', preview: params.has('photo') ? PHOTO_PREVIEW : undefined };
        case 'choose_photo': return { ok: true, path: '/Users/example/Pictures/me.jpg' };
        case 'set_photo': return { ok: true, has_photo: true, path: '/Users/example/My Resume Data/master/photo.jpg', preview: PHOTO_PREVIEW };
        case 'remove_photo': return { ok: true, has_photo: false };
        case 'open_folder': return a.which === 'data' || a.which === 'engine' ? { ok: true, opened: '/Users/example/My Resume Data' } : { ok: false, error: "which must be 'data' or 'engine'" };
        case 'data_dir': return { ok: true, engine: '/Users/example/jd-lens', data: '/Users/example/My Resume Data', source: 'config', separate: true, has_master: true };
        case 'choose_data_dir': return { ok: true, path: '/Users/example/My Resume Data', has_master: !params.has('emptychoice') };
        case 'set_data_dir': return { ok: true, engine: '/Users/example/jd-lens', data: a.path, source: 'config', separate: true, has_master: true, sample_added: !!a.sample, profile_rebuilt: true };
        case 'clear_data_dir': return { ok: true, engine: '/Users/example/jd-lens', data: '/Users/example/jd-lens', source: 'engine', separate: false, has_master: true, profile_rebuilt: false };
        case 'profile_status': return params.has('noprofile') ? (params.get('nomaster') ? { ok: true, current: null, reason: 'no master resume' } : { ok: true, current: false, missing: true }) : { ok: true, current: st !== 'stale' };
        case 'list': return { ok: true, applications: saved };
        case 'show': { const x = saved.find((s) => s.slug === a.slug) || saved[0]; return { ok: true, application: Object.assign({}, x, { rounds: ROUNDS[x.slug] || [], history: HIST[x.slug] || [['' + x.added, '-', x.status, 'Added']],
          files: { application: profile.repo_path + '/applications/' + x.slug + '.md', resume: x.resume ? profile.repo_path + '/' + x.resume : '', details_html: profile.repo_path + '/views/applications.html#' + x.slug } }) }; }
        case 'delete_preview': return { ok: true, dry_run: true, slug: a.slug, items: [
          { label: 'Application file (JD, scores, proposal, Brag Sheet)', paths: ['applications/' + a.slug + '.md'], bytes: 18400 },
          { label: '4 automatic backups of the application file', paths: ['applications/.history/' + a.slug + '-20261122-024204-712078.md', 'applications/.history/' + a.slug + '-20261122-024219-303345.md', 'applications/.history/' + a.slug + '-20261122-031914-045546.md'], bytes: 71200 },
          { label: 'Tailored resume folder (HTML, PDF, questions and answers)', paths: ['tailored/' + a.slug], bytes: 238000 },
          { label: 'Brag Sheet page', paths: ['views/brag/' + a.slug + '.html'], bytes: 9100 }] };
        case 'delete_app': saved = saved.filter((x) => x.slug !== a.slug); return { ok: true, slug: a.slug, trash: '.trash/20261122-120000-' + a.slug };
        case 'brag_view': return { ok: true, found: true, html: profile.repo_path + '/views/brag/' + a.slug + '.html' };
        case 'read_section': return a.section === 'Brag Sheet' ? { ok: true, found: !params.has('nobrag'), text: '### JD pillars\n1. TypeScript and React at scale\n2. Node.js services on AWS\n\n### Matched wins\n- **TypeScript and React at scale** [F-LM-02]: led the Grammar Checker migration to TipTap v3. So what: shows you can move a large front end without downtime.\n- **Node.js services on AWS** [F-PY-03]: built CI/CD on S3/CloudFront with monitoring. So what: matches their deploy-and-observe ownership.\n\n### Gap bridges\n- **Cypress**: not in your master file. Closest: integration and UAT tests [F-LM-04].\n\n### Revision view\n| Pillar | Best win | One number | One sentence |\n|---|---|---|---|\n| TypeScript and React | TipTap v3 migration | 30+ packages | Moved a large monorepo front end without a freeze. |' }
          : a.section === 'Tailoring proposal'
          ? { ok: true, found: true, text: '1. Headline: "Senior Full-Stack Engineer · TypeScript, React, Node.js".\n2. Summary: S-FS variant (facts F-PY-01, F-LM-02, F-EV-01).\n3. Skills: add Express, JavaScript, Storybook, Mocha, Chai, React Testing Library.\n4. Brightlabs bullet: add schema design and role-based views (F-BR-04).\nNot added: Cypress, Vite.' }
          : a.section === 'Fit' ? { ok: true, found: st !== 'nofit', text: 'Strong match on TypeScript, React, Express and Postgres (F-PY-01, F-LM-04, F-BR-04). All 5 must-haves met.\nGaps: Vite and Cypress are not claimed. Kubernetes is a certificate only.\nSoft requirements (code reviews, stakeholder communication) rest on lead-role evidence, so the judged score sits below the keyword score. India hiring is listed but not stated in words: confirm with recruiting.\nAssessment: apply, lead with the PayPlus and Lumenly facts.' }
          : { ok: true, found: a.section === 'Gaps vs JD', text: 'Vite and Cypress not claimed. Kubernetes is a certificate only.' };
        case 'claude_start': jobStart = Date.now(); return { ok: true, job: '20261121-210000-abc123' };
        case 'claude_status': return st === 'running' || Date.now() - jobStart < 4000 ? { ok: true, state: 'running', seconds: Math.round((Date.now() - jobStart) / 1000) } : { ok: true, state: 'done', result: 'Proposal written to the application file.', cost_usd: 0.31 };
        case 'master_view': return { ok: true, html: profile.repo_path + '/views/master-resume.html', pdf: profile.repo_path + '/views/master-resume.pdf', applications_html: profile.repo_path + '/views/applications.html' };
        case 'rescore_saved': return { ok: true, results: saved.map((x) => ({ slug: x.slug, old: x.quick_score, new: x.quick_score })) };
        case 'status': return { ok: true, status: { from: 'applied', to: a.status } };
        default: return { ok: true };
      }
    },
    rescan: async () => (st === 'empty' ? { ok: false, error: 'Chrome did not allow reading this page.' } : SCAN),
    lastScan: async () => (st === 'empty' || st === 'loading' ? null : SCAN),
    onScan: () => {},
    openUrl: async (u) => { console.log('open', u); },
    openPanelTab: async () => { console.log('open panel in a tab'); },
    openApps: async (slug) => { console.log('open applications', slug); },
    loadJSON: async (p) => (p.endsWith('profile.json') ? (params.has('noprofile') ? null : profile) : p.endsWith('resume.json') ? (st === 'noresume' || params.has('noprofile') ? null : resume) : { applications: saved }),
    connect: () => {},
    requestAutoScan: async () => true,
    hasAutoScan: async () => false,
    afterBoot: async (state) => {
      if (st === 'pinned') state.pinned = SCAN.url;
      if (st === 'running') { state.job = { job: '20261121-210000-abc123', kind: params.get('jobkind') || 'tailor', slug: 'northwind-2026-11', state: 'running', seconds: 12 }; }
      if (st === 'denied') { state.job = { job: 'x', kind: 'full_score', slug: 'northwind-2026-11', state: 'done', cost_usd: 0.13, blocked: 2,
        denied: ['cd "/Users/example/jd-lens" && cat applications/soylent-2026-11.md; ls tailored/soylent-2026-11', 'python3 tools/build_profile.py && node tools/score_jd.mjs applications/soylent-2026-11.md'],
        result: "I couldn't score soylent-2026-11. Bash was denied in this non-interactive session. I didn't score by hand." }; }
      if (st === 'proposal') { state.proposal = (await window.MockApi.host('read_section', { slug: 'northwind-2026-11', section: 'Tailoring proposal' })).text;
        state.job = { job: 'x', kind: 'tailor', slug: 'northwind-2026-11', state: 'done', result: 'Proposal written to the application file.', cost_usd: 0.31 }; }
      if (params.has('open')) params.get('open').split(',').forEach((id) => { state.factOpen[id] = true; });
      if (params.has('choosing')) state.dataChoice = { path: '/Users/example/My Resume Data', sample: true, has_master: params.get('choosing') !== 'empty' };     // the confirm card, as if a folder was just picked
    },
  };
  // test hook: click the first button whose label starts with this text, once the panel has drawn (the render checks only read the page, they cannot click)
  if (params.has('click')) setTimeout(() => { const b = [...document.querySelectorAll('button')].find((x) => x.textContent.trim().startsWith(params.get('click'))); if (b) b.click(); }, 1500);
  if (params.has('mockwidth')) { const st2 = document.createElement('style'); st2.textContent = '#app{max-width:' + Number(params.get('mockwidth')) + 'px;margin:0}'; document.head.append(st2); }
})();
