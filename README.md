# JD Lens

[![JD Lens: score any job against your resume. Click to watch the 2 minute demo](docs/images/jd-lens-overview.png)](https://youtu.be/LMyvg42zjc8)

[Watch the 2 minute demo](https://youtu.be/LMyvg42zjc8)

A Chrome side panel that scores a job description against **your own resume data**, then helps you tailor a resume and prepare for the interview. Everything runs on your computer: no account, no server, no analytics.

- **Instant score** for the page you are on: keyword match, offered salary, red flags (location, a stale posting, scam signals), no AI needed.
- **Your match** against a threshold you choose, with a verdict.
- **Analysis**: matched, missing and unconfirmed skills, each tied to the fact in your resume that backs it.
- **With Claude Code** (optional, your own sign-in): a judged full score, a tailored resume proposal you approve before anything is built, a PDF, and a Brag Sheet to read before the interview.
- **Applications page**: every saved JD with status, rounds and history.

Nothing is applied or sent for you, and resume claims only come from facts in your own master file.

## Get started
Read **[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)** (about 10 minutes). In short:

1. Copy `master/master-resume.template.md` to `master/master-resume.md` and replace the sample data with your own facts.
2. `python3 tools/setup.py`, then `python3 tools/doctor.py` to check your machine.
3. Load `tools/jd-capture-extension/` in Chrome (`chrome://extensions`, Developer mode, Load unpacked).
4. Install the local helper once: `python3 tools/jobd/install.py`.

By default your data lives in this folder. To keep it somewhere else (for example your own private repo), choose a data folder in Settings or run `python3 tools/setup.py --data-dir "/full/path"`; see [the guide](docs/GETTING-STARTED.md#keeping-your-data-in-its-own-folder).

## What is in this repo
| Path | What |
|------|------|
| `tools/jd-capture-extension/` | The Chrome extension (side panel, Applications page) |
| `tools/jobd/` | The local helper (native messaging host) that saves files and runs Claude on your machine |
| `tools/jd-scorer/`, `tools/score_*.{py,mjs}` | The scorer |
| `tools/*.py` | Profile builder, application tracking, checks, packaging |
| `.claude/skills/job/` | The `/job` skill for Claude Code |
| `master/master-resume.template.md` | A sample master resume (made-up data) |
| `tailored/_base/layouts/` | Three sample resume layouts (basic, two-column, with photo), with made-up content |
| `docs/` | Getting started, architecture decisions (ADRs), design notes, store listing and release notes |

Your own data (`master/master-resume.md`, `applications/`, `tailored/`, `stories/`, `answers/`, built profile files) is git-ignored: it stays in your clone.

## Tests
`python3 -m unittest discover -s tools/tests` (unit tests, no personal data needed). `python3 tools/tests/render_panel.py [--only=01,02] [--shots]` renders every panel screen in headless Chrome with mock data and checks them.

## Status
Pre-release. Privacy policy and store listing drafts are in `docs/publishing/`.

## Licence
JD Lens is free software under the **GNU Affero General Public License v3.0** (see [LICENSE](LICENSE)). You can use, study, change and share it. If you distribute a modified version, or let others use it over a network, you must make your source available under the same licence. The AGPL covers the code, not the JD Lens name or logo.
