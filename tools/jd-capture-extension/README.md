# JD Lens: Chrome side panel for your job search

**New here? Start with [`docs/GETTING-STARTED.md`](../../docs/GETTING-STARTED.md)** (prerequisites, permissions, setup in minutes). This file is the technical reference.

Scores the job page you have open against your master resume data, shows the salary the page offers, and lets you save, score, tailor, build and track applications without leaving the browser. Everything runs on this machine. Decisions: `docs/adr/ADR-0001-jd-capture-chrome-extension.md` and `docs/adr/ADR-0002-native-host-backend.md`.

## One-time setup (about two minutes)

1. Build the data the panel reads: `python3 tools/build_profile.py` (and `python3 tools/sync_extension.py` if you changed the scorer).
2. Install the local helper (a small program Chrome starts on demand; no server, no open port):
   `python3 tools/jobd/install.py`
   It writes one manifest into Chrome's NativeMessagingHosts folder, allowing only this extension's ID (`EXTENSION_ID`).
3. In Chrome open `chrome://extensions`, switch on **Developer mode**, press **Load unpacked** and choose `tools/jd-capture-extension/`. The ID shown must match `EXTENSION_ID` (`lccgfiimocbpmoiknggdcbhiijbodpcf`).
4. Pin the extension. Open a job page and click the JD Lens icon: the side panel opens and scores the page.

To remove it: `python3 tools/jobd/install.py --uninstall`, then remove the extension in `chrome://extensions`.

## What it does (design v3, follows the information architecture doc)

**Shell, always visible:** header (A-, A+, Pin, Close), JD | Resume, Refresh, Applications (opens the full-page view), Settings.

| Where | What |
|-------|------|
| **JD > Overview** | Saved or applied banner, Job Summary (with the posting date), Score (with the change since you last scored this JD), Salary offered as written on the page (with "Update?"), Threshold with an inline slider, Flags, and Evidence counts (matched, missing, unconfirmed). "View full analysis" opens Analysis |
| **JD > Analysis** | Profile overview (match ring, missing and extra skills), Experience alignment, Key skills match (Matched, Missing, Unconfirmed, Additional), Requirement comparison with evidence IDs, Potential concerns, Next steps (with Mark done) and a Pro Tip |
| **JD > Details** | Job details with a link to the original posting, JD highlights, Required skills and qualifications, the description (Read more), Your match and Skills overlap |
| **Resume > Profile** | Master resume (last updated, open as HTML or PDF, summary), education and certifications, application counts, profile management (Rebuild skill profile, Rescore saved JDs, how to change the master file) |
| **Resume > Skills** | Every skill by group with its level (on resume, confirmed, partial, older resume only, no evidence) and evidence IDs you can tap to read the fact |
| **Resume > Experience** | Professional experience by company, projects and achievements, awards, each fact with its ID and status |
| **Applications (full page)** | Dashboard counts, status filters, sort (recent activity, best match, date added), search, application cards, and for one application: job information, files, gaps noted, interview rounds (with notes), update status (with a note) and the status history |
| **Settings** | Scoring (threshold, how partial skills count, how the score is calculated), Appearance (theme and text size), Reading page, Local helper (status and file locations), Skill profile (generated date, skills and evidence counts, show, rebuild) |

Next steps on Overview (with a "Next action" bar at the top that slides through what you can do next, and scrolls to the step): Save JD (asks first), Get the full score, Tailor your resume (proposal, then Approve and build PDF), Add missing skills, Review before applying, Not for me. Buttons marked "Use Claude" run a headless Claude in this repo on your plan. Each step has a "Run in a terminal instead" command with the full path.

Reads and status changes are one click. Anything that writes a JD or a resume asks first. The panel never edits your files itself: the helper does, through `tools/jobs.py`, which keeps a backup of the previous file in `applications/.history/` and appends every status change to a Status history section in the application file.

## The gradient

Two colours drive every gradient (active tabs, bars, the match ring, gradient borders, the Pro Tip card, the logo): `--grad-a` and `--grad-b` at the top of `panel.css`, set to the brand pair in the information architecture doc (`#f5a8a0` to `#f4c686`), plus `--grad-angle` for the tilt. Gradients are used selectively (navigation indicator, progress, call-to-action accents, thin card borders), not on large surfaces. The logo is `icons/logo.svg`; the PNG icons are rendered from it.

## Text size and zoom

Chrome has no zoom for side panels: Cmd + and Cmd - only zoom the web page in the tab. So the panel scales itself:
- **A- and A+** in the top bar, or **Cmd or Ctrl with + , - and 0** while the panel has focus (seven steps, 90% to 200%). The choice is remembered.
- **Settings, Text size** shows the current step and a Reset button.
- **Gear menu, Open in a tab** opens the same panel as a normal tab, where Chrome's own Cmd + zoom also works. In a tab, Refresh re-reads the job page you last scanned.
- You can also drag the side panel's left edge to make it wider.
- The layout reflows when text is large: cards stack, rows wrap, long URLs break. Tested down to a 320px panel at 200%.

After pulling changes, press the reload arrow on the extension in `chrome://extensions` to pick them up.

## What the extension holds

`data/profile.json` (skill names, levels, evidence IDs, career start, domain words, repo path, counts), `data/resume.json` (the readable resume for the Resume tab: summaries, experience facts, skills by group, awards, certifications, education, an index of facts by ID; no phone, email or other contact details) and `data/applications.json` (company, role, status, score, dates, resume path, posting URL). Settings, "Show what the extension holds" prints the profile. Stored locally by Chrome (`chrome.storage.local`, never synced). All three data files are generated by `python3 tools/build_profile.py` and are not committed.

## Permissions

`activeTab` and `scripting` (read the page when you click the icon), `sidePanel`, `storage`, `nativeMessaging` (talk to the helper). Optional, off until you press the button in Settings: reading `http(s)` pages automatically while the panel is open. No network access of its own.

## Adding a skill

`python3 tools/add_skill.py "Python" --group Backend --fact "Used Python for ETL scripts at Example Corp (2019 to 2020)"` adds the evidence and the skills row to your master resume, keeps a backup, and rebuilds the profile. Then press Rescore saved JDs in the panel. Details: `docs/GETTING-STARTED.md`, section How-tos.

## Keeping it current

- `python3 tools/build_profile.py` after you change `master/master-resume.md` (the panel shows a banner and a Rebuild button when it is stale).
- The `/job` skill refreshes the views and lists after each change.

## Tests

```
python3 -m unittest discover -s tools/tests -v     # jobs script, helper, page extraction (real Chrome)
node --test tools/jd-scorer/                       # the scorer
python3 tools/tests/render_panel.py                # every screen, light and dark, with content checks
python3 tools/tests/e2e_extension.py               # real Chrome loads the extension and reaches the helper
```
Write operations are only ever tested on a temporary copy of the repo.

## Files

`manifest.json`, `background.js` (icon click, page read), `extract.js` (runs in the page), `common.js` (API layer, DOM helper, icons, shared by both pages), `panel.html/js/css` (the side panel), `applications.html`, `apps.js`, `apps.css` (the full-page Applications view), `lib/` (copy of the shared scorer, kept in sync by `tools/sync_extension.py`), `data/` (generated), `mock.js` (design harness, active only with `?mock`), `icons/`.
