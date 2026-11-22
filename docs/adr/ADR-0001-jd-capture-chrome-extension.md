# ADR-0001: Chrome side panel to score a JD on the page and hand it to the /job skill

- Status: Proposed. Partly superseded by ADR-0002 (2026-11-21): the handoff is a native messaging host, not a Downloads inbox, and the extension is meant to be the main UI. Scoring, the skill profile, the panel design and the test plan here still stand.
- Date: 2026-11-21 (revised the same day: added on-page scoring and copyable commands)
- Deciders: Alex Morgan

## Context

The `/job` skill (`.claude/skills/job/SKILL.md`) turns a JD into a saved application file, a fit score, a tailored resume and a tracked status. Today a JD enters the pipeline by the user pasting a link or text into a Claude session.

the user wants two things from a Chrome extension:

1. **Score on the page.** Open any JD, see a fit score against his master resume data (`master/master-resume.md`) before deciding whether to click "Apply". Every JD is scored. He decides what score is acceptable: 50% may be fine for one role, 90% may be a pass for another. The tool shows the number and the evidence and does not decide for him.
2. **Commands in the side panel.** Under the score, show the exact terminal commands, with full paths, that continue the work with his skills (`/job add`, `tailor`, `build`, and a skip command). He copies a command from the panel and pastes it into a terminal.

Later phases (crawling the 59 careers pages in `prep/remote-hiring-links-arijit-ghosh.md`) will also need a reliable way to get a JD's text and score it.

Constraints, from the user's standing rules:
- Local only. No cloud documents, uploads, hosted database or remote API calls with his data.
- He applies himself. Nothing here submits forms or sends messages for him.
- Never commit unless asked.
- Confidential project names must not enter any file (the rule in `CLAUDE.md`).

### What changed from the first draft

The first draft said "no resume data in the browser". On-page scoring needs some of it. The risk that rule guarded against is data leaving his machine, not data existing in his own browser profile on his own machine. So the rule becomes: **only a derived skill profile goes into the extension, stored in `chrome.storage.local` (never `sync`, which uploads to Google)**. Contact details, compensation, notes, stories, the open-confirmations list and everything else stay in the repo.

## Decision drivers

1. Instant answer on the page, no Claude session needed for the first look.
2. The on-page score and the `/job` score must not contradict each other.
3. Verbatim JD text (a plain fetch returned paraphrases earlier).
4. Works on any careers site and on LinkedIn job pages.
5. Smallest permissions, no server, no open port.
6. The only data the browser holds is a minimal skill profile.

## Options considered

### Where scoring runs

| Option | For | Against |
|--------|-----|---------|
| S1. In the extension, deterministic, from a derived skill profile | Instant, offline, no setup beyond loading the extension. | Keyword and structure based, so it is less nuanced than Claude. Profile must be rebuilt when the master file changes. |
| S2. In Claude only (`/job add`) | Best judgement, full master data. | Needs a terminal session before he sees any number. Defeats "quickly check". |
| S3. Native messaging host that scores using the full master file | One scoring engine, full data, still local. | A host to install and debug. Slower to get working. |

### One scoring engine or two

| Option | For | Against |
|--------|-----|---------|
| E1. One JavaScript scorer (`tools/jd-scorer/score.js`) used by the extension and by a Node command the `/job` skill runs | Same rules everywhere, so the numbers agree. Tested once. | Scoring logic has to be written in JS (fine, the extension is JS). |
| E2. A scorer in the extension and a separate judgement in the skill | Skill is free to reason. | Two answers for the same JD. Drift over time. |

### How the JD gets to the repo

| Option | For | Against |
|--------|-----|---------|
| A. Download a JSON file into a fixed inbox, `/job add --inbox` imports it | No server, no native host. Easy to inspect and delete. | Two steps. |
| B. Local HTTP server on 127.0.0.1 | One click. | Always-on process and an open port that any web page can try to reach. |
| C. Native messaging host writing into the repo | One click, no open port. | Install and debug effort. |
| D. Extension-only storage with export | Simplest. | Data stays in the browser profile. |

### How the extension reads the page

| Option | For | Against |
|--------|-----|---------|
| 1. schema.org `JobPosting` JSON-LD when present, else main-content text | Clean fields on many sites, fallback covers the rest. | Sites vary. Needs fixtures. |
| 2. Send whole page HTML to be parsed elsewhere | Least extension code. | Noisy, and leaks unrelated page content such as a logged-in feed. |

## Decision

Build a **Manifest V3 extension with a side panel**.

### Scoring (S1 + E1)

- **One shared scorer** in `tools/jd-scorer/score.js`. The extension bundles it. A Node wrapper, `tools/score_jd.mjs <jd.json|text file>`, runs the same code so `/job score` uses it as its first pass and adds Claude's judgement on top (partials, wording, domain fit). If the two numbers differ by more than 15 points, the skill says so and explains why.
- **Same formula as the skill:** `fit_score = round(70 * must_score + 30 * nice_score)`. Each requirement is met (1), partial (0.5) or gap (0).
- **How the scorer reads a JD:**
  1. Split into sections by headings (requirements, qualifications, "you have", responsibilities, nice to have, bonus, plus, preferred). Text under nice-to-have headings is nice-to-have, requirements text is must-have; bullets in responsibilities count as must-have only for named technologies.
  2. For each bullet, extract concrete terms: technologies and practices from a vocabulary (`data/vocab.json`, plus `data/aliases.json` for Postgres = PostgreSQL, k8s = Kubernetes, RTL = React Testing Library, and so on) and years of experience (`8+ years`).
  3. A requirement is **met** when all its terms are in the profile at level `listed` or `user-confirmed`, **partial** when only some are, **gap** when none or the term is unknown to the profile. A years requirement is met if career years is at or above it.
  4. Terms the profile marks `earlier` or `confirm` are shown as **unconfirmed**. They do not count (same rule as the skill: an unconfirmed skill is a gap) but are listed, so he can see what confirming would change.
- **Output:** the score, must-have and nice-to-have counts, matched terms, missing terms, unconfirmed terms, and flags (India or remote wording found or not, posting age from `datePosted`, salary text if present).
- **No verdict.** The panel shows the number and, next to it, whether it is above or below a threshold **he sets** (stored with the extension, no default recommendation). Nothing is hidden or highlighted as "apply" or "skip". A 90% and a 50% show the same commands.

### Skill profile (what the browser holds)

- Generated by `tools/build_profile.py`, which reads `master/master-resume.md` and writes `tools/jd-capture-extension/data/profile.json`:
  - `career_years`, `generated_at`, `repo_path`
  - `skills`: name, aliases, level (`listed`, `user-confirmed`, `earlier`, `none`), years if filled, evidence fact IDs
  - nothing else: no phone, email, comp, notes, stories, answers, summaries or project descriptions.
- The extension loads it into `chrome.storage.local`. Rebuilding it is one command, shown in the panel when the profile is older than the master file.
- Because it comes from the master file, it cannot contain a confidential project name that is not in that file.

### Side panel commands (full paths)

Shown below the score, each with a Copy button. The repo path comes from `profile.json`; the inbox file path comes from the browser's download record (absolute path). Example for the Northwind page:

```
Step 1  Save this JD and get the full score
cd "/Users/example/jd-lens" && claude "/job add --inbox"

Step 2  If you want to apply: propose resume edits (you approve them)
cd "/Users/example/jd-lens" && claude "/job tailor northwind-2026-11"

Step 3  After approving: build the PDF and run the ATS check
cd "/Users/example/jd-lens" && claude "/job build northwind-2026-11"

Not for me: mark it skipped
cd "/Users/example/jd-lens" && claude "/job status northwind-2026-11 withdrawn"

Profile out of date? Rebuild it
cd "/Users/example/jd-lens" && python3 tools/build_profile.py
```

The slug (`northwind-2026-11`) is built from the captured company and month, the same way `/job add` names application files. After the application, the panel also shows `/interview add` for form questions. The exact CLI form (`claude "<slash command>"` as the starting prompt) must be checked on his install when this is built; if it differs, the panel uses the working form.

### Master resume view and applications list (added 2026-11-21)

- **Gear menu** items: Profile and applications, Master resume (HTML), Master resume (PDF), Settings, Rebuild skill profile (copies the command).
- **Master resume** opens as a local file in a new tab: `views/master-resume.html` and `views/master-resume.pdf`, generated by `tools/build_views.py` (already built and tested). The extension only links to them (file URL). The full master file is not copied into the extension. To verify at build: Chrome lets the extension open a file URL in a new tab; if it blocks it, the panel shows the path with a Copy button instead.
- **Applications list** in the panel: company, role, status, fit score, applied date, filter by status, sorted by score. A row opens a detail view: the resume sent, the posting, `views/applications.html#<slug>` for everything else, and copyable `/job status` and `/interview prep` commands. The panel never edits files.
- **Data:** `tools/build_profile.py` also writes `applications.json` (company, role, status, score, applied, resume path, posting URL, slug) from `applications/*.md`. Gaps, JD text and rounds are not copied into the browser; they are read from the HTML view.
- **Already applied:** when the open page matches an application's posting URL (query string ignored) or company, the panel shows a banner with the date and the resume sent. This avoids applying twice.
- **Freshness:** `/job status`, `/job add` and `/job build` end by running `tools/build_views.py` and `tools/build_profile.py`, so the lists stay current. The stale banner covers the case where they did not run.

### Panel layout (sketch)

```
 JD fit                              profile built 2026-11-21
 Northwind: Senior Full Stack Engineer - EMEA
 Quick score  86      your threshold: 70   (above)
 Must-haves 10 of 11     Nice-to-haves 3 of 4
 Matched     TypeScript, React, Express, NestJS, PostgreSQL, Jest ...
 Missing     Vite, Cypress
 Unconfirmed Kubernetes
 Flags       India listed, "India remote" not stated.  Posted 171 days ago.
 -----------------------------------------------------------------
 Next steps (copy, paste in a terminal)
  1 Save and fully score        [Copy]
  2 Tailor the resume           [Copy]
  3 Build the PDF               [Copy]
  Not for me: mark skipped      [Copy]
```

### Handoff (A) and page reading (1)

- **Trigger:** the user opens the side panel from the extension button on the JD page. Nothing runs in the background and nothing scrapes automatically. Scoring runs when the panel opens or he presses Refresh.
- **Permissions:** `activeTab`, `scripting`, `downloads`, `sidePanel`, `storage`. No broad host permissions, no network calls.
- **Capture:** a "Save JD" button writes `jd-<company>-<slug>.json` (record below, including the quick score) to `Downloads/job-inbox/`. Chrome extensions can only write under Downloads, so that path is a **symlink to `job-inbox/` inside the repo** (decided by the user, 2026-11-21): the file lands in the repo directly, with no copying or syncing. Setup is one command, `ln -s "/Users/example/jd-lens/job-inbox" ~/Downloads/job-inbox`, done at build time. To verify then: Chrome writes through the symlink, and the file appears in the repo. `/job add --inbox` reads each file, creates the application file as `add` does, runs the shared scorer, then Claude's judgement, and moves the file to `job-inbox/done/`.
- **Salary:** the panel highlights the offered salary exactly as the page states it (JSON-LD `baseSalary` or text, with currency and period). It stores no salary target and gives no verdict: the user reads the band and decides. "Not stated on this page" when absent.
- **Phase 2 (only if the two steps annoy him):** native messaging (option C) writing straight into the repo. Option B (localhost server) stays rejected.
- **Out of scope here:** form filling, auto-apply, sending messages.

### Captured record

```json
{
  "schema": 1,
  "captured_at": "2026-11-21T20:14:00+05:30",
  "url": "https://example.com/careers/job/123",
  "source_title": "page title",
  "company": "string or null",
  "role": "string or null",
  "location_text": "string or null",
  "salary_text": "string or null",
  "posted": "yyyy-mm-dd or null",
  "extraction": "jsonld | main-text",
  "jd_text": "full visible JD text, verbatim",
  "quick_score": {
    "score": 86, "must": "10/11", "nice": "3/4",
    "matched": ["TypeScript"], "missing": ["Vite"], "unconfirmed": ["Kubernetes"],
    "profile_generated_at": "2026-11-21"
  }
}
```

## Consequences

- Good: he sees a number and the evidence in seconds, on the page, before applying, and chooses his own bar.
- Good: one scorer means the panel and `/job score` agree. If they differ, the skill explains why.
- Good: the browser holds only skill names, levels and years. Contact details, comp, stories and notes never enter it, and nothing leaves his machine.
- Cost: the profile must be rebuilt when the master file changes. The panel warns when it is stale and shows the command.
- Cost: a keyword scorer misses nuance (for example "owned a payments platform" is not a technology term). Accepted: the quick score is for triage, and `/job` adds judgement before he spends effort on tailoring.
- Cost: extraction and section detection need upkeep as sites change. Mitigated by fixtures.
- Risk: LinkedIn and some sites restrict automated reading or change markup often. The panel reads only what is on screen in his own session, on his click, and falls back to "paste the text".
- Risk: the pasted `claude "/job ..."` form may differ by CLI version. Verified at build time.

## Test plan

- **Scoring fixtures:** the Northwind JD (verbatim text in `applications/northwind-2026-11.md`, expected about 86), the Globex and Initech JDs already in `applications/` (their "Gaps vs JD" sections are the manual reference), and 3 new real postings. Pass: the quick score is within 10 points of a manual score, and every gap in the manual notes appears under missing or unconfirmed.
- **Unconfirmed rule:** a skill at level `earlier` or `confirm` never raises the score, and always appears under unconfirmed.
- **Extraction fixtures:** the Northwind page, one LinkedIn job page, one Greenhouse or Lever page, one plain careers page. Pass: `jd_text` matches the page, no nav, feed or cookie text, right company, role, location and salary where present.
- **Privacy:** `profile.json` contains no phone, email, compensation, stories, answers or project descriptions. Permissions match the list above. No network request leaves the extension (check the network tab).
- **Handoff:** `/job add --inbox` produces the same application file shape as `/job add <url>`, and the stored score matches the panel within the 15-point rule.
- **Commands:** each command in the panel runs unchanged in a fresh terminal.

## Build plan (right after this ADR is accepted)

1. `tools/build_profile.py` and its test (no personal data in the output).
2. `tools/jd-scorer/score.js`, vocab and aliases, tested on the fixtures, with the `tools/score_jd.mjs` command.
3. Extension scaffold in `tools/jd-capture-extension/`: manifest, side panel, content script, options (threshold, repo path).
4. Page extraction, scoring in the panel, the copyable commands, Save JD to the inbox.
5. `/job add --inbox` and `/job score` updated to run the shared scorer first.
6. Try on the Northwind page, then three other real JD pages. Short README: load unpacked, where the inbox is, how to remove it.

## Out of scope (separate decisions)

- Crawling careers pages and their filters across the 59 companies. Needs its own ADR and the user's approval for each company.
- Any hosted database or sync across machines.
- Packaging for the Chrome Web Store. The extension is loaded unpacked for personal use only.

## Open questions

- Decided 2026-11-21: sharing the skill profile with the extension is fine; the inbox is a symlink from Downloads into the repo; no salary target is stored (the offered band is highlighted instead); the threshold starts unset and is tuned together while real JDs are scored.
- UI: wireframes in `docs/design/jd-panel/` (`01-wireframe-boxes.html`, `02-wireframe-detailed.html`). The final visual design (design language, light and dark themes) follows once the wireframes are confirmed.
- Should the panel open automatically on pages that look like job postings, or only when he clicks? Default: only on click.
