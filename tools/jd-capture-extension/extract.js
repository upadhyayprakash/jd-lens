/* Injected into the active tab (chrome.scripting.executeScript, func: extractPage). Must be self-contained:
 * it is serialised and run in the page, so it cannot use anything defined outside it.
 * Reads only what is already on screen in the user's own session. Returns plain data; sends nothing anywhere.
 */
function extractPage() {
  const MAX = 120000;
  const clean = (s) => (s || '').replace(/ /g, ' ').replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  const out = { ok: true, url: location.href, source_title: document.title, extraction: 'main-text',
                company: null, role: null, location_text: null, salary_text: null, posted: null, jd_text: '' };

  const htmlToText = (html) => {
    const doc = new DOMParser().parseFromString(html || '', 'text/html');
    doc.querySelectorAll('li').forEach((li) => li.prepend('- '));
    doc.querySelectorAll('br, p, div, h1, h2, h3, h4, h5, ul, ol, li, tr').forEach((e) => e.after('\n'));
    return clean(doc.body.textContent);
  };

  // 1. schema.org JobPosting JSON-LD, when the page has it
  const nodes = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach((s) => {
    try {
      const j = JSON.parse(s.textContent);
      (Array.isArray(j) ? j : j['@graph'] || [j]).forEach((n) => nodes.push(n));
    } catch (e) { /* ignore malformed blocks */ }
  });
  const jp = nodes.find((n) => n && [].concat(n['@type'] || []).includes('JobPosting'));
  if (jp) {
    out.extraction = 'jsonld';
    out.role = jp.title || null;
    out.company = (jp.hiringOrganization && (jp.hiringOrganization.name || jp.hiringOrganization)) || null;
    if (typeof out.company !== 'string') out.company = null;
    const org = jp.hiringOrganization;
    const orgUrl = org && typeof org === 'object' ? (org.sameAs || org.url) : null;
    const u0 = [].concat(orgUrl || []).find((x) => typeof x === 'string' && /^https?:\/\//i.test(x));
    if (u0) { try { out.company_url = new URL(u0).origin; } catch (e) { /* ignore */ } }
    out.posted = jp.datePosted ? String(jp.datePosted).slice(0, 10) : null;
    const locs = [].concat(jp.jobLocation || []).map((l) => {
      const a = l && l.address ? l.address : {};
      return [a.addressLocality, a.addressRegion, typeof a.addressCountry === 'object' ? a.addressCountry.name : a.addressCountry].filter(Boolean).join(', ');
    }).filter(Boolean);
    const apl = [].concat(jp.applicantLocationRequirements || []).map((x) => x && x.name).filter(Boolean);
    const remote = jp.jobLocationType === 'TELECOMMUTE' ? ['Remote'] : [];
    out.location_text = [...remote, ...locs, ...apl].join(' | ') || null;
    const bs = jp.baseSalary;
    if (bs) {
      const v = bs.value || {};
      const cur = bs.currency || v.currency || '';
      const unit = (v.unitText || '').toLowerCase();
      const fmt = (n) => (typeof n === 'number' ? n.toLocaleString('en-US') : n);
      if (v.minValue != null && v.maxValue != null) out.salary_text = `${cur} ${fmt(v.minValue)} - ${fmt(v.maxValue)}${unit ? ' per ' + unit : ''}`.trim();
      else if (v.value != null) out.salary_text = `${cur} ${fmt(v.value)}${unit ? ' per ' + unit : ''}`.trim();
    }
    const d = htmlToText(jp.description || '');
    if (d.length > 300) out.jd_text = d;
  }

  // 2. fallback: the visible text of the main content
  if (!out.jd_text) {
    const cands = ['main', '[role="main"]', 'article'];
    let el = null;
    for (const sel of cands) {
      const e = document.querySelector(sel);
      if (e && (e.innerText || '').length > 400) { el = e; break; }
    }
    out.jd_text = clean((el || document.body).innerText || '');
    // when JSON-LD gave the structured fields but a short description, keep the page text too
  }
  if (jp && out.jd_text && !out.location_text) {
    const m = out.jd_text.match(/Locations?:\s*([^\n]+)/i);
    if (m) out.location_text = m[1].trim();
  }
  if (!out.role) {
    const h1 = document.querySelector('h1');
    out.role = (h1 && h1.innerText.trim()) || (document.title || '').split(/[|–-]/)[0].trim() || null;
  }
  if (!out.company) {
    const og = document.querySelector('meta[property="og:site_name"]');
    out.company = (og && og.content) || location.hostname.replace(/^(www|careers|jobs)\./, '').split('.')[0];
  }
  if (!out.company_url) {
    // The company's own site, when the job is on it. Job boards and applicant-tracking hosts are not the company.
    const host = location.hostname.toLowerCase().replace(/^www\./, '');
    const board = /(^|\.)(greenhouse\.io|lever\.co|myworkdayjobs\.com|workday\.com|ashbyhq\.com|smartrecruiters\.com|linkedin\.com|indeed\.com|glassdoor\.[a-z.]+|naukri\.com|wellfound\.com|angel\.co|icims\.com|jobvite\.com|bamboohr\.com|workable\.com|taleo\.net|successfactors\.[a-z]+|breezy\.hr|recruitee\.com|teamtailor\.com|rippling\.com|dover\.com|paylocity\.com|ultipro\.com|oraclecloud\.com|eightfold\.ai|google\.com|monster\.com|ziprecruiter\.com|instahyre\.com|foundit\.in|cutshort\.io|hirist\.[a-z]+)$/.test(host);
    const parts = host.split('.');
    const two = /^(co|com|org|net|gov|ac)$/.test(parts[parts.length - 2] || '') && parts.length > 2;
    const reg = parts.slice(two ? -3 : -2).join('.');
    if (!board && parts.length >= 2 && location.protocol.startsWith('http')) out.company_url = 'https://' + reg;
  }
  if (out.jd_text.length > MAX) out.jd_text = out.jd_text.slice(0, MAX);
  out.chars = out.jd_text.length;
  return out;
}
