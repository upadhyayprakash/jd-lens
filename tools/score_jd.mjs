#!/usr/bin/env node
// Score a JD against the skill profile. Same engine as the Chrome extension.
// Usage: node tools/score_jd.mjs <jd.json | jd.txt | application.md> [--profile path] [--summary]
//   jd.json: a captured record ({ jd_text, salary_text, posted, location_text }); .txt: plain JD text;
//   application .md: the JD section of an application file.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const here = path.dirname(fileURLToPath(import.meta.url));
const { score } = require('./jd-scorer/score.js');

const args = process.argv.slice(2);
const pi = args.indexOf('--profile');
const skip = pi >= 0 ? new Set([pi, pi + 1]) : new Set();
const file = args.find((a, i) => !a.startsWith('--') && !skip.has(i));
if (!file) { console.error('usage: node tools/score_jd.mjs <jd.json|jd.txt|application.md> [--profile path] [--summary]'); process.exit(2); }
const profilePath = pi >= 0 ? args[pi + 1] : path.join(here, 'jd-capture-extension', 'data', 'profile.json');
const profile = JSON.parse(readFileSync(profilePath, 'utf8'));

let text = readFileSync(file, 'utf8');
let meta = {};
if (file.endsWith('.json')) { const r = JSON.parse(text); text = r.jd_text; meta = { salary_text: r.salary_text, posted: r.posted, location_text: r.location_text }; }
else if (file.endsWith('.md')) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  if (m) { const p = m[1].match(/^posted:\s*(\S+)/m); if (p) meta.posted = p[1]; }
  const body = text.replace(/^---[\s\S]*?\n---\n/, '');
  const sec = body.match(/^## JD[^\n]*\n([\s\S]*?)(?=^## (?!#)|(?![\s\S]))/m);
  text = sec ? sec[1] : body;
}
const r = score(text, profile, meta);
if (args.includes('--summary')) {
  console.log(`score ${r.score}  must ${r.must.met}/${r.must.n} (+${r.must.partial} partial)  nice ${r.nice.met}/${r.nice.n} (+${r.nice.partial} partial)  unscored ${r.unscored}`);
  console.log('matched:    ' + r.matched.join(', '));
  console.log('partial:    ' + r.partial.join(', '));
  console.log('missing:    ' + r.missing.join(', '));
  console.log('unconfirmed:' + r.unconfirmed.join(', '));
  console.log('salary:     ' + (r.salary ? r.salary.text : 'not stated'));
  console.log('flags:      ' + JSON.stringify(r.flags));
} else {
  // the requirements that are not fully met, for the judgement step
  r.gaps = r.units.filter((u) => u.mark < 1).map((u) => ({ text: u.text, kind: u.kind, mark: u.mark, terms: u.terms.map((t) => t.t + (t.level === 'partial' ? ' (partial)' : t.level === 'earlier' ? ' (older resume only)' : t.credit === 0 ? ' (not in master)' : '')) }));
  delete r.units;
  console.log(JSON.stringify(r, null, 2));
}
