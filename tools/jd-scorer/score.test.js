// Run: node --test tools/jd-scorer/
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { score, extractTerms, findSalary, careerYears } = require('./score.js');

const root = path.resolve(__dirname, '..', '..');
const profile = JSON.parse(fs.readFileSync(path.join(root, 'tools/jd-capture-extension/data/profile.json'), 'utf8'));
const NOW = new Date('2026-11-21T12:00:00Z');

function jdFrom(app) {
  const t = fs.readFileSync(path.join(root, 'tools/tests/fixtures/applications', app + '.md'), 'utf8').replace(/^---[\s\S]*?\n---\n/, '');
  const m = t.match(/^## JD[^\n]*\n([\s\S]*?)(?=^## (?!#)|(?![\s\S]))/m);
  return m[1];
}

test('longest match wins: React Native is not also read as React', () => {
  assert.deepStrictEqual(extractTerms('We use React Native and React Testing Library.'), ['React Native', 'React Testing Library']);
  assert.deepStrictEqual(extractTerms('React, Express and Node.js'), ['React', 'Express', 'Node.js']);
});

test('case rules: lowercase "express", "rest", "go" are ordinary words', () => {
  assert.deepStrictEqual(extractTerms('You express ideas, take a rest, and go far.'), []);
  assert.deepStrictEqual(extractTerms('We build with Go, Python and REST APIs.'), ['Go', 'Python', 'REST']);
  assert.deepStrictEqual(extractTerms('Java and JavaScript'), ['Java', 'JavaScript']);
});

test('profile holds no personal data', () => {
  const raw = fs.readFileSync(path.join(root, 'tools/jd-capture-extension/data/profile.json'), 'utf8');
  const withoutPath = raw.replace(profile.repo_path, '');
  for (const bad of ['+91', '@yahoo', '88610', 'example.morgan', 'Payly', 'Lumenly']) assert.ok(!withoutPath.includes(bad), bad);
  assert.deepStrictEqual(Object.keys(profile).sort(), ['career_start', 'domains', 'generated_at', 'master_modified', 'master_sha256', 'repo_path', 'rows', 'schema', 'stats']);
});

test('career years from the master start date', () => {
  assert.strictEqual(careerYears(profile, NOW), 12);
});

test('Northwind: strong, with Vite and Cypress missing and Kubernetes partial', () => {
  const r = score(jdFrom('northwind-2026-11'), profile, { now: NOW, posted: '2026-06-03' });
  assert.ok(r.score >= 85 && r.score <= 100, 'score ' + r.score);
  for (const t of ['TypeScript', 'Express', 'React', 'NestJS', 'PostgreSQL', 'Storybook', 'Mocha', 'Chai', 'microservices']) assert.ok(r.matched.includes(t), t);
  assert.ok(r.missing.includes('Vite') && r.missing.includes('Cypress'));
  assert.ok(r.partial.includes('Kubernetes'));
  assert.strictEqual(r.flags.posted_days, 171);
  assert.ok(r.unscored > 0, 'soft requirements are reported, not scored');
});

test('Globex: clearly lower, years short of 14, Go and Prometheus unconfirmed', () => {
  const r = score(jdFrom('globex-2026-10'), profile, { now: NOW });
  const northwind = score(jdFrom('northwind-2026-11'), profile, { now: NOW });
  assert.ok(r.score < northwind.score - 25, `globex ${r.score} vs northwind ${northwind.score}`);
  assert.strictEqual(r.years.required, 14);
  for (const t of ['Terraform', 'Temporal', 'Helm', 'MCP']) assert.ok(r.missing.includes(t), t);
  assert.ok(r.unconfirmed.includes('Go') && r.unconfirmed.includes('Prometheus'));
});

test('unconfirmed skills never raise the score', () => {
  const jd = 'Requirements\nExperience with Go and Prometheus.\n';
  const r = score(jd, profile, { now: NOW });
  assert.strictEqual(r.score, 0);
  assert.deepStrictEqual(r.unconfirmed.sort(), ['Go', 'Prometheus']);
  // the same JD with the skills confirmed scores higher
  const confirmed = JSON.parse(JSON.stringify(profile));
  confirmed.rows.forEach((x) => { if (/Go|Prometheus/.test(x.skills)) x.level = 'user-confirmed'; });
  assert.ok(score(jd, confirmed, { now: NOW }).score > 0);
});

test('years requirement: met, near miss (half), far miss (zero)', () => {
  const s = (n) => score(`Requirements\n${n}+ years of TypeScript experience.\n`, profile, { now: NOW }).score;
  assert.strictEqual(s(8), 100);
  assert.strictEqual(s(14), 50);
  assert.strictEqual(s(20), 0);
});

test('nice-to-have sections and "is a plus" lines count as nice', () => {
  const r = score('Requirements\nStrong TypeScript.\nNice to have\nExperience with Terraform.\nKnowledge of Docker is a plus.\n', profile, { now: NOW });
  assert.strictEqual(r.must.n, 1);
  assert.strictEqual(r.nice.n, 2);
  assert.strictEqual(r.score, Math.round(70 * 1 + 30 * 0.5));
});

test('salary: picks the pay range, ignores valuation noise, prefers structured data', () => {
  const text = 'We raised at a $17.3 billion valuation with $1 B ARR.\nSalary range:\n$60,000 - $100,000 USD\nPosted on June 03, 2026';
  assert.strictEqual(findSalary(text, '').text, '$60,000 - $100,000 USD');
  assert.strictEqual(findSalary('No pay info here, $17.3 billion valuation.', ''), null);
  assert.strictEqual(findSalary(text, 'INR 30-40 LPA').text, 'INR 30-40 LPA');
  assert.ok(/12-18 LPA/.test(findSalary('Compensation: 12-18 LPA depending on experience', '').text));
});

test('flags: India stated vs only listed, remote wording, scam signals', () => {
  assert.strictEqual(score('Requirements\nTypeScript.\nLocations: India, Spain', profile, { now: NOW }).flags.india, 'listed');
  assert.strictEqual(score('Requirements\nTypeScript.\nRemote in India.', profile, { now: NOW }).flags.india, 'stated');
  assert.strictEqual(score('Requirements\nTypeScript.', profile, { now: NOW }).flags.india, 'absent');
  const scam = score('Requirements\nTypeScript. Pay a registration fee. Apply on WhatsApp. mail jobs@gmail.com', profile, { now: NOW }).flags.scam;
  assert.strictEqual(scam.length, 3);
});

test('a JD with no recognisable requirements gives a null score, not a fake number', () => {
  assert.strictEqual(score('We are a friendly company that loves people.', profile, { now: NOW }).score, null);
});

test('regression: a bullet without a trailing period is a requirement, not a heading', () => {
  const jd = 'Requirements\n- Strong TypeScript\nNice to have\n- Experience with Kafka\n- Terraform is a plus\n';
  const r = score(jd, profile, { now: NOW });
  assert.strictEqual(r.nice.n, 2);
  assert.ok(r.missing.includes('Terraform'));
  // the same lines without bullet markers (plain page text) behave the same way
  const r2 = score('Requirements\nStrong TypeScript\nNice to have\nExperience with Kafka\nTerraform is a plus\n', profile, { now: NOW });
  assert.strictEqual(r2.nice.n, 2);
  assert.ok(r2.missing.includes('Terraform'));
});

test('requirement units carry evidence IDs from the profile', () => {
  const r = score('Requirements\n- Strong PostgreSQL and Express\n', profile, { now: NOW });
  const terms = Object.fromEntries(r.units[0].terms.map((t) => [t.t, t]));
  assert.ok(terms.PostgreSQL.evidence.includes('F-BR-04'), JSON.stringify(terms.PostgreSQL));
  assert.ok(terms.Express.evidence.includes('F-USR-01'));
});

test('requirements list keeps lines with no recognisable skill and drops responsibilities', () => {
  const jd = 'Responsibilities\nYou will build things with TypeScript.\nRequirements\nStrong communication skills.\n- 5+ years of React\nNice to have\nKafka\n';
  const r = score(jd, profile, { now: NOW });
  const texts = r.requirements.map((q) => q.kind + ':' + q.text);
  assert.deepStrictEqual(texts, ['must:Strong communication skills.', 'must:5+ years of React', 'nice:Kafka']);
});

test('partial credit is configurable', () => {
  const jd = 'Requirements\n- Experience with Kubernetes\n';
  assert.strictEqual(score(jd, profile, { now: NOW }).score, 50);                       // Kubernetes is partial: half credit
  assert.strictEqual(score(jd, profile, { now: NOW, partialCredit: 0 }).score, 0);
  assert.strictEqual(score(jd, profile, { now: NOW, partialCredit: 1 }).score, 100);
});

test('resume.json: readable resume data without contact details', () => {
  const raw = fs.readFileSync(path.join(root, 'tools/jd-capture-extension/data/resume.json'), 'utf8');
  const rd = JSON.parse(raw);
  for (const bad of ['+91', '@yahoo', '88610', 'example.morgan']) assert.ok(!raw.includes(bad), bad);
  assert.ok(rd.companies.some((c) => c.company === 'Lumenly' && c.facts.length > 3));
  assert.ok(rd.summaries.length >= 2 && rd.education && rd.master_modified);
  assert.ok(rd.facts['F-LM-02'].text.includes('14K'));
  assert.ok(rd.skills.some((g) => g.group === 'Backend' && g.rows.some((r) => /Express/.test(r.skills))));
});

test('a skill you list that the vocabulary does not know is still recognised in a JD', () => {
  const custom = JSON.parse(JSON.stringify(profile));
  custom.rows.push({ skills: 'Obscure Tool (internal)', level: 'user-confirmed', evidence: ['F-X-1'] }, { skills: 'Older Thing', level: 'earlier', evidence: [] });
  const r = score('Requirements\n- Experience with Obscure Tool and Older Thing\n- Strong TypeScript\n', custom, { now: NOW });
  const terms = Object.fromEntries(r.units.flatMap((u) => u.terms.map((t) => [t.t, t])));
  assert.strictEqual(terms['Obscure Tool'].level, 'user-confirmed');
  assert.ok(r.matched.includes('Obscure Tool'));
  assert.ok(r.unconfirmed.includes('Older Thing'));                  // still never counts until confirmed
  // without the rows, the same JD ignores those words
  const plain = score('Requirements\n- Experience with Obscure Tool and Older Thing\n', profile, { now: NOW });
  assert.deepStrictEqual(plain.units, []);
});

test('data, cloud and identity terms are known, so a missing one shows as a gap', () => {
  assert.deepStrictEqual(extractTerms('Python, Pandas, Boto3, ETL and AWS Bedrock'), ['Python', 'Pandas', 'Boto3', 'ETL', 'Bedrock']);
  assert.deepStrictEqual(extractTerms('SSO with OIDC and SAML'), ['SSO', 'OAuth', 'SAML']);
  const r = score('Requirements\n- Python, Pandas and Boto3\n', profile, { now: NOW });
  for (const t of ['Pandas', 'Boto3']) assert.ok(r.missing.includes(t), t);
});

test('adding Python with evidence turns a gap into a match', () => {
  const jd = 'Requirements\n- Strong Python\n';
  assert.ok(score(jd, profile, { now: NOW }).missing.includes('Python'));
  const withPython = JSON.parse(JSON.stringify(profile));
  withPython.rows.push({ skills: 'Python', level: 'user-confirmed', evidence: ['F-USR-06'] });
  const r = score(jd, withPython, { now: NOW });
  assert.ok(r.matched.includes('Python'));
  assert.strictEqual(r.score, 100);
});
