/* JD quick scorer. One engine, used by the Chrome extension panel and by `tools/score_jd.mjs`.
 *
 * score(jdText, profile, meta?) -> result
 *   profile: tools/jd-capture-extension/data/profile.json (skill rows with levels, career_start, domains)
 *   meta:    { salary_text, posted (yyyy-mm-dd), location_text, now (Date, for tests) }
 *
 * fit_score = round(70 * must_score + 30 * nice_score). Each requirement is met (1), partial (0.5) or gap (0).
 * A skill the master file marks `earlier` (older resume only) gives no credit and is reported as unconfirmed.
 * This is a keyword and structure check: requirements with no recognisable term are counted as "unscored".
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./vocab.js'));
  else root.JDScorer = factory(root.JDVocab);
})(typeof self !== 'undefined' ? self : this, function (VOCAB) {
  const CREDIT = { listed: 1, 'user-confirmed': 1, partial: 0.5, earlier: 0, none: 0 };
  const RANK = { listed: 3, 'user-confirmed': 3, partial: 2, earlier: 1, none: 0 };

  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&');
  const edge = (src) => '(?<![A-Za-z0-9])(?:' + src + ')(?![A-Za-z0-9])';

  // Build one list of {term, re} patterns, longest alias first.
  const PATTERNS = (() => {
    const out = [];
    for (const v of VOCAB) {
      (v.a || []).forEach((a) => out.push({ term: v.t, re: new RegExp(edge(esc(a)), 'gi'), len: a.length }));
      (v.cs || []).forEach((a) => out.push({ term: v.t, re: new RegExp(edge(esc(a)), 'g'), len: a.length }));
      (v.rx || []).forEach((r) => out.push({ term: v.t, re: new RegExp(r, 'g'), len: r.length }));
    }
    return out;
  })();
  const KIND = Object.fromEntries(VOCAB.map((v) => [v.t, v]));

  // Terms found in a text, longest match first, no overlaps (so "React" is not read inside "React Native").
  function extractTerms(text, extra) {
    const hits = [];
    for (const p of extra && extra.length ? PATTERNS.concat(extra) : PATTERNS) {
      p.re.lastIndex = 0;
      let m;
      while ((m = p.re.exec(text))) {
        hits.push({ term: p.term, start: m.index, end: m.index + m[0].length });
        if (m[0].length === 0) p.re.lastIndex++;
      }
    }
    hits.sort((a, b) => (b.end - b.start) - (a.end - a.start) || a.start - b.start);
    const taken = [];
    for (const h of hits) {
      if (taken.some((t) => h.start < t.end && h.end > t.start)) continue;
      taken.push(h);
    }
    taken.sort((a, b) => a.start - b.start);
    const seen = [];
    for (const h of taken) if (!seen.includes(h.term)) seen.push(h.term);
    return seen;
  }

  // Any skill you list in your master file becomes a term the scorer looks for in a JD, even if the built-in vocabulary
  // does not know it (a niche tool, a new framework). Terms the vocabulary already knows are left to the vocabulary.
  const CUSTOM_CACHE = new WeakMap();
  function splitNames(text) {
    const out = []; let depth = 0, cur = '';
    for (const ch of text || '') {
      if (ch === '(') depth++; else if (ch === ')') depth = Math.max(0, depth - 1);
      if (ch === ',' && depth === 0) { out.push(cur); cur = ''; } else cur += ch;
    }
    out.push(cur);
    return out;
  }
  function customPatterns(profile) {
    if (CUSTOM_CACHE.has(profile)) return CUSTOM_CACHE.get(profile);
    const out = [], seen = new Set();
    for (const row of profile.rows || []) {
      for (let name of splitNames(row.skills)) {
        name = name.replace(/\([^)]*\)/g, '').replace(/\s+/g, ' ').trim();
        if (name.length < 2 || name.length > 40 || seen.has(name.toLowerCase())) continue;
        seen.add(name.toLowerCase());
        if (extractTerms(name).length) continue;
        out.push({ term: name, re: new RegExp(edge(esc(name)), 'gi'), len: name.length });
      }
    }
    CUSTOM_CACHE.set(profile, out);
    return out;
  }

  function careerYears(profile, now) {
    const [y, m] = (profile.career_start || '').split('-').map(Number);
    if (!y) return 0;
    const d = now || new Date();
    return Math.floor(((d.getFullYear() - y) * 12 + (d.getMonth() + 1 - (m || 1))) / 12);
  }

  // term -> { level, credit } from the profile's skill rows
  function skillMap(profile) {
    const map = {};
    const extra = customPatterns(profile);
    for (const row of profile.rows || []) {
      for (const t of extractTerms(row.skills, extra)) {
        if (!map[t] || RANK[row.level] > RANK[map[t].level]) map[t] = { level: row.level, evidence: row.evidence || [] };
      }
    }
    return map;
  }

  const creditOf = (level, cfg) => (level === 'partial' ? cfg.partial : CREDIT[level] || 0);

  function termInfo(term, map, profile, cfg) {
    const v = KIND[term] || {};
    if (v.kind === 'domain') {
      const has = (profile.domains || []).some((d) => d.toLowerCase() === term.toLowerCase());
      return { level: has ? 'listed' : 'none', credit: has ? 1 : 0, evidence: [] };
    }
    if (v.kind === 'concept') {
      let best = 'none', ev = [];
      for (const s of v.by || []) if (map[s] && RANK[map[s].level] > RANK[best]) { best = map[s].level; ev = map[s].evidence || []; }
      return { level: best, credit: creditOf(best, cfg), evidence: ev };
    }
    const e = map[term];
    return e ? { level: e.level, credit: creditOf(e.level, cfg), evidence: e.evidence || [] } : { level: 'absent', credit: 0, evidence: [] };
  }

  // ---- structure -------------------------------------------------------------------------------
  const H_STOP = /^(about (us|the company|[A-Z][\w.&-]*)|who we are|benefits|perks|total rewards|compensation|salary|equal opportunity|why (join|should|you)|our (mission|values|story)|how to apply|some things you|what we offer|why .* ?\?$)/i;
  const H_NICE = /(nice[- ]to[- ]have|bonus|\bplus(es)?\b|preferred|brownie|good to have|desirable|even better|would be great)/i;
  const H_MUST = /(requirements?|qualifications?|what you('|’)ll need|what we('|’)re looking for|you have|you('|’)ve got|must[- ]have|who you are|about you|skills and experience|what you bring|looking for|your background)/i;
  const H_RESP = /(responsibilit|what you('|’)ll do|what you will do|the role|your role|duties|in this role|day[- ]to[- ]day|what you.ll own)/i;
  const NICE_LINE = /(\b(is|are|would be)\s+(a\s+)?(plus|bonus|nice|preferred|desirable)\b|\bnice to have\b|\ba plus\b|\bbonus\b|\bpreferred\b|\bideally\b|\bbrownie\b)/i;

  const PLUS_SENTENCE = /\b(is|are|would be)\s+(a\s+)?(plus|bonus|nice|preferred|desirable)\b/i;

  function headingKind(line, isBullet) {
    const l = line.trim();
    if (!l || l.length > 90 || isBullet) return null;
    if (l.split(/\s+/).length > 8) return null;                       // headings are short
    const lc = l.replace(/[*_\s]+$/, '');                              // tolerate markdown bold around a heading
    if (!/:$/.test(lc) && PLUS_SENTENCE.test(l)) return null;         // "Docker is a plus" is a requirement, not a heading
    const looksHeading = /:$/.test(lc) || !/[.!?]$/.test(lc);
    if (!looksHeading) return null;
    if (H_STOP.test(l)) return 'stop';
    if (H_NICE.test(l)) return 'nice';
    if (H_MUST.test(l)) return 'must';
    if (H_RESP.test(l)) return 'resp';
    if (/^(summary|overview|description|job description|the opportunity|application)$/i.test(l.replace(/:$/, ''))) return 'other';
    return null;
  }

  function splitUnits(text) {
    const units = [];
    let section = null; // null until a heading is seen
    let sawHeading = false;
    for (const raw of text.split(/\n+/)) {
      const isBullet = /^\s*[-*•●▪‣]+\s+/.test(raw);
      const line = raw.replace(/^\s*[-*•●▪‣]+\s*/, '').trim();
      if (!line) continue;
      const hk = headingKind(line, isBullet);
      if (hk) { section = hk; sawHeading = true; continue; }
      if (section === 'stop' || section === 'other') continue;
      for (const s of line.split(/(?<=[.!?])\s+(?=[A-Z])/)) {
        const t = s.trim();
        if (t.length < 4) continue;
        let kind = section === 'nice' ? 'nice' : 'must';
        if (NICE_LINE.test(t)) kind = 'nice';
        units.push({ text: t, kind, section: section || 'none' });
      }
    }
    return { units, sawHeading };
  }

  function yearsIn(text) {
    const m = text.match(/(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years?|yrs?)\b/i);
    return m ? parseInt(m[1], 10) : 0;
  }

  // ---- salary, flags ---------------------------------------------------------------------------
  const CUR = '(?:[$€£₹]|USD|EUR|GBP|INR|CAD|AUD|Rs\\.?)';
  const NUM = '\\d[\\d,]*(?:\\.\\d+)?\\s?(?:[kKmM]\\b|lakhs?|LPA|lpa|crores?)?';
  const SAL_RX = new RegExp(
    '(?:' + CUR + '\\s?' + NUM + '(?:\\s?(?:-|–|to)\\s?' + CUR + '?\\s?' + NUM + ')?(?:\\s?(?:USD|EUR|GBP|INR|CAD|AUD))?' +
    '|\\d[\\d.]*\\s?(?:-|–|to)\\s?\\d[\\d.]*\\s?(?:LPA|lpa|lakhs?))' +
    '(?:\\s?(?:per|/|a)\\s?(?:year|yr|annum|month|hour|hr))?', 'g');

  function findSalary(text, metaText) {
    if (metaText && metaText.trim()) return { text: metaText.trim(), source: 'structured data' };
    let best = null;
    SAL_RX.lastIndex = 0;
    let m;
    while ((m = SAL_RX.exec(text))) {
      const after = text.slice(m.index + m[0].length, m.index + m[0].length + 16).toLowerCase();
      if (/^\s*(billion|million|trillion|bn\b|arr|valuation)/.test(after)) continue;
      if (/^\s?[mMbB]\b/.test(after) && !/[kK]/.test(m[0])) continue;
      const before = text.slice(Math.max(0, m.index - 70), m.index).toLowerCase();
      let score = 0;
      if (/(salary|compensation|pay range|base pay|ote|range|per year|annual)/.test(before)) score += 3;
      if (/(-|–|\bto\b)/.test(m[0])) score += 2;
      if (/\b(usd|inr|eur|gbp)\b/i.test(m[0])) score += 1;
      if (!best || score > best.score) best = { score, text: m[0].trim() };
    }
    return best && best.score >= 2 ? { text: best.text, source: 'page text' } : null;
  }

  function flagsFor(text, meta, now) {
    const loc = (meta && meta.location_text) || '';
    const all = loc + '\n' + text;
    let india = 'absent';
    if (/\bindia\b/i.test(all)) india = 'listed';
    if (/india[^.\n]{0,50}\bremote\b|\bremote\b[^.\n]{0,50}\bindia\b/i.test(all)) india = 'stated';
    let remote = 'unknown';
    if (/remote[- ]first|fully remote|100% remote|work from anywhere|\bremote\b/i.test(all)) remote = 'remote';
    else if (/\bhybrid\b/i.test(all)) remote = 'hybrid';
    else if (/\bon-?site\b|in[- ]office/i.test(all)) remote = 'onsite';
    const scam = [];
    if (/(registration|training|security|processing|application)\s+fee|pay\s+(a\s+)?(deposit|fee)|send\s+money|western union|gift card/i.test(text)) scam.push('asks for a fee or payment');
    if (/[\w.+-]+@(gmail|yahoo|outlook|hotmail|proton(mail)?)\.\w+/i.test(text)) scam.push('contact is a free email address');
    if (/(apply|contact|message).{0,40}(whatsapp|telegram)|(whatsapp|telegram).{0,40}(apply|contact)/i.test(text)) scam.push('asks you to apply via WhatsApp or Telegram');
    let posted_days = null;
    if (meta && meta.posted) {
      const d = new Date(meta.posted);
      if (!isNaN(d)) posted_days = Math.floor(((now || new Date()) - d) / 86400000);
    } else {
      const m = text.match(/Posted(?: on)?:?\s*([A-Z][a-z]+ \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})/);
      if (m) { const d = new Date(m[1]); if (!isNaN(d)) posted_days = Math.floor(((now || new Date()) - d) / 86400000); }
    }
    return { india, remote, scam, posted_days };
  }

  // ---- main ------------------------------------------------------------------------------------
  function score(jdText, profile, meta) {
    meta = meta || {};
    const now = meta.now || new Date();
    const map = skillMap(profile);
    const extra = customPatterns(profile);
    const have = careerYears(profile, now);
    const { units, sawHeading } = splitUnits(jdText);
    const cfg = { partial: typeof meta.partialCredit === 'number' ? meta.partialCredit : 0.5 };

    const scored = [];
    let unscored = 0;
    for (const u of units) {
      const terms = extractTerms(u.text, extra);
      const yrs = yearsIn(u.text);
      if (!terms.length && !yrs) { if (u.section !== 'resp') unscored++; continue; }
      // In plain responsibility text only named technologies count as requirements.
      const infos = terms.map((t) => Object.assign({ t }, termInfo(t, map, profile, cfg)));
      let mark = null;
      if (infos.length) {
        const frac = infos.reduce((a, i) => a + i.credit, 0) / infos.length;
        mark = frac >= 0.75 ? 1 : frac > 0 ? 0.5 : 0;
      }
      if (yrs) {
        const ym = have >= yrs ? 1 : have >= yrs - 3 ? 0.5 : 0;
        mark = mark === null ? ym : Math.min(mark, ym);
      }
      scored.push({ text: u.text.length > 300 ? u.text.slice(0, 297) + '...' : u.text, kind: u.kind, terms: infos, years: yrs || null, mark });
    }

    const agg = (kind) => {
      const us = scored.filter((s) => s.kind === kind);
      const met = us.filter((s) => s.mark === 1).length;
      const partial = us.filter((s) => s.mark === 0.5).length;
      const gap = us.filter((s) => s.mark === 0).length;
      const n = us.length;
      return { n, met, partial, gap, score: n ? (met + 0.5 * partial) / n : null };
    };
    const must = agg('must');
    const nice = agg('nice');
    let fit;
    if (must.n && nice.n) fit = Math.round(70 * must.score + 30 * nice.score);
    else if (must.n) fit = Math.round(100 * must.score);
    else if (nice.n) fit = Math.round(100 * nice.score);
    else fit = null;

    const matched = [], missing = [], unconfirmed = [], partialTerms = [];
    const seen = new Set();
    for (const s of scored) for (const i of s.terms) {
      if (seen.has(i.t)) continue;
      seen.add(i.t);
      if (i.level === 'earlier') unconfirmed.push(i.t);
      else if (i.level === 'partial') partialTerms.push(i.t);
      else if (i.credit > 0) matched.push(i.t);
      else missing.push(i.t);
    }
    const reqYears = Math.max(0, ...scored.map((s) => s.years || 0));
    const salary = findSalary(jdText, meta.salary_text);
    const flags = flagsFor(jdText, meta, now);

    // every requirement-like line (also the ones with no recognisable skill), for the Details view
    const requirements = units.filter((u) => u.section !== 'resp').slice(0, 40)
      .map((u) => ({ text: u.text.length > 300 ? u.text.slice(0, 297) + '...' : u.text, kind: u.kind }));

    return {
      score: fit, must, nice, matched, partial: partialTerms, missing, unconfirmed, unscored, requirements,
      years: { required: reqYears || null, have }, salary, flags, structured: sawHeading,
      units: scored, generated_at: now.toISOString(),
    };
  }

  return { score, extractTerms, customPatterns, skillMap, careerYears, findSalary, splitUnits };
});
