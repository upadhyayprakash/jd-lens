# JD Lens: get started in 10 minutes

JD Lens is a Chrome extension that scores any job posting against **your own resume data** while you read it. It shows the score, the salary the page offers, red flags, and exactly which requirements you do and do not meet. It also tracks your applications and, optionally, uses Claude to tailor your resume.

Everything runs on your computer. There is no account, no server and no API key.

**Jump to:** [What you need](#1-what-you-need) | [Privacy and permissions](#2-what-it-touches-permissions-storage-network) | [Quick start](#3-quick-start) | [How-tos](#8-how-tos) | [FAQ](#9-faq) | [Troubleshooting](#11-troubleshooting)

---

## 1. What you need

| You need | For | Check it with | Required? |
|----------|-----|---------------|-----------|
| **Google Chrome 116 or newer** | The extension (side panel) | `chrome://version` | Yes |
| **Python 3.9 or newer** | Setup, the local helper, the scripts | `python3 --version` | Yes |
| **macOS** | The helper installer is tested here | - | Recommended (see section 13) |
| **Node.js 18 or newer** | Rescoring saved JDs, Claude's full score | `node --version` | Recommended |
| **Claude Code + a sign-in** | The "Use Claude" steps and the `/job` and `/interview` skills | `claude --version` | Optional |
| **poppler** (`brew install poppler`) | Checking tailored resume PDFs | `pdfinfo -v` | Optional |

**You do not need:** an Anthropic API key, any other account, a database, a server, or internet access to score a page.

Not sure what you have? After step 2 below, run `python3 tools/doctor.py`: it checks everything on this list and tells you the exact command to fix each gap.

---

## 2. What it touches: permissions, storage, network

### Chrome permissions

| Permission | Why |
|------------|-----|
| `activeTab`, `scripting` | Read the text of the job page **only when you click the JD Lens icon** on it |
| `sidePanel` | Show the panel beside the page |
| `storage` | Remember your settings (see below) |
| `nativeMessaging` | Talk to the small local helper that reads and writes your files |
| Optional: all `http(s)` pages | Off by default. A button in Settings turns on automatic re-reading as you switch tabs |

### Where your data lives

| Where | What | Leaves your computer? |
|-------|------|-----------------------|
| **Chrome storage** (`chrome.storage.local`) | Threshold, theme, text size, score history, salary notes you typed, step ticks | No. Never synced to your Google account |
| **Your data folder** (the project folder unless you choose another, see section 10) | `master/` your resume facts, `applications/` your saved JDs and history, `tailored/` resumes built for a job, `job-inbox/` copies of saved JDs, `views/` readable pages | No |
| **`tools/jd-capture-extension/data/`** | Generated copies the extension reads: your skills, your readable resume (no phone or email), a short list of your applications | No |

### Network

- **The extension makes no network requests.** Scoring happens in the browser.
- **Claude steps are the only exception.** When you press "Use Claude" (or run `/job` in a terminal), Claude Code reads the JD text and your master resume facts and sends them to Anthropic, under your own sign-in and Anthropic's terms. If that is not acceptable, simply never press those buttons: everything else works without Claude.
- Building a resume PDF loads one web font from Google Fonts. It still works offline with a fallback font.

### The helper and the Claude runs are fenced in

- The helper starts only when the extension calls it, has a **fixed list of operations** (it cannot run arbitrary commands) and answers **only this extension's ID**.
- Every write keeps a backup of the previous file in `applications/.history/`.
- Each Claude run uses an allowlist of tools (no network tools, no git), can only write in the folders it needs, and has a **spend cap**. Text inside a JD is treated as untrusted data.
- Every helper action is logged (without contents) in `tools/jobd/jobd.log`.

---

## 3. Quick start

### Step 1. Get the project (1 minute)

Download it (green **Code** button, then **Download ZIP**, or `git clone`) and open Terminal **inside the project folder**. Keep the folder where it is: if you move it later, rerun step 2.

### Step 2. Run setup (1 minute)

```bash
python3 tools/setup.py
```

It creates the folders, makes your starter resume file from a template, builds the data the extension reads, installs the local helper, and runs the health check. It never overwrites your resume, so it is safe to run again.

### Step 3. Put your own details in the resume file (5 to 15 minutes, once)

Open `master/master-resume.md`. It starts as **made-up sample data** so you can see how it works. Replace it with yours. The file explains the layout; the rules that matter:

1. **Keep the headings and tables exactly as they are.** Add or remove rows, not columns.
2. **Section 3:** your experience as short facts, each with an ID like `F-AB-01`.
3. **Section 5:** your skills. Give each a **level** and the **fact IDs that prove it**.

| Level | Meaning | Counts toward the score? |
|-------|---------|--------------------------|
| `listed` | It is on your resume | Yes |
| `user-confirmed` | You wrote it here yourself | Yes |
| `partial` | Real but limited (a course, a certificate) | Half |
| `earlier` | Only on an older resume | No, until you confirm it |
| `none` | No evidence | No |

Only claim what you can back up. The score is only as honest as this file.

Then rebuild what the extension reads:

```bash
python3 tools/build_profile.py
```

### Step 4. Load the extension in Chrome (1 minute)

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and choose the folder `tools/jd-capture-extension`.
4. Check that the **ID** shown is `lccgfiimocbpmoiknggdcbhiijbodpcf` (it matches the file `EXTENSION_ID`).
5. Click the puzzle icon and **pin** JD Lens.

### Step 5. Check everything (30 seconds)

```bash
python3 tools/doctor.py
```

Every line should say `OK`. A `WARN` is optional or cosmetic; a `FAIL` has a "fix:" line with the command.

### Step 6. Try it

Open any job posting and click the JD Lens icon. The panel opens and scores the page.

---

## 4. Your first job, step by step

| | Where | What to do |
|--|-------|------------|
| 1 | **JD, Overview** | Read the score, the salary the page offers and the flags. Press **Set threshold** to choose the score you consider worth a look |
| 2 | **JD, Analysis** | See why: matched, missing and unconfirmed skills, each requirement with the fact that backs it, and what needs your own judgement |
| 3 | **Save JD** | Stores the posting text with status "considering". Nothing is applied or sent |
| 4 | **Get the full score** (Claude) | Adds judgement on soft requirements. Optional |
| 5 | **Tailor your resume** (Claude) | Proposes resume edits **using only facts from your master file**. You read the proposal and approve before anything is built |
| 6 | **Approve and build PDF** (Claude) | Builds a tailored 2-page resume and checks its keywords |
| 7 | **Applications** (people icon) | A full page: dashboard, status, interview rounds, status history. After you apply, set the status to **applied** |

The score is a **keyword check, not a verdict**. It cannot judge soft requirements like communication. Use it to decide where to spend your time.

---

## 5. What needs Claude and what does not

| Feature | Needs Claude? | Spend cap per run |
|---------|---------------|-------------------|
| Score a page, flags, salary, evidence, requirement comparison | **No** | - |
| Save a JD, status changes, interview rounds, status history, the Applications page | **No** (local helper) | - |
| Resume tab: summary, skills, experience, evidence | **No** | - |
| Rescore all saved JDs | **No** (needs Node) | - |
| Get the full score | Yes | $1.00 |
| Tailor your resume (proposal) | Yes | $1.50 |
| Approve and build PDF | Yes | $2.00 |
| `/interview add` (answer drafts) and `/interview prep` | Yes | $1.50 and $1.00 |

Claude steps use **your Claude Code sign-in** (your plan's usage), not an API key. A typical run costs roughly 10 to 30 cents of usage and takes under a minute. Every "Use Claude" button has a matching "Run in a terminal instead" command if you prefer to watch it work.

If a step reports **"N commands were blocked"**, Claude was not allowed to run something and the result may be incomplete. Press the step again; if it repeats, see Troubleshooting.

---

## 6. The Claude skills

Two skills live in `.claude/skills/` inside the project:

| Skill | What it does |
|-------|--------------|
| `/job` | `add`, `score`, `tailor`, `build`, `status`, `list`: the whole pipeline from a job description to a tracked, tailored application. The extension uses the same scripts |
| `/interview` | Drafts answers to application questions from your stories, builds a recall sheet before an interview, records a debrief |

**To use them:** open Terminal in the project folder and run `claude`. Claude Code finds the skills automatically; no install is needed. Then type, for example, `/job add <paste a job URL>`.

The skills are optional. The extension works without them, and they need Claude Code.

---

## 7. Day to day

| I want to | Do this |
|-----------|---------|
| Check a job | Open it, click the JD Lens icon |
| Keep one JD while I browse other tabs | Press the pin in the panel header |
| Make the text bigger | **A+** in the header, or Cmd and + while the panel is focused |
| See all my applications | The people icon, or **Resume > Profile > Open Applications** |
| Add a skill I really have | Edit `master/master-resume.md`, run `python3 tools/build_profile.py`, then **Resume > Profile > Rescore saved JDs** |
| Open my master resume | **Resume > Profile > Open as HTML** or PDF |
| Change a status | Applications page, **Update status** (the old status stays in the history) |

---

## 8. How-tos

### Add a skill I have (for example Python)

A skill only counts when it is in your master resume with **a level and the evidence behind it**. The quickest way:

```bash
python3 tools/add_skill.py "Python" --group Backend \
  --fact "Used Python for ETL scripts and data analysis at Example Corp (2019 to 2020)" --years "2019 to 2020"
```

- `--fact` is required and must say **where and how** you used it. A skill with no evidence is refused, on purpose.
- `--group` is one of the headings in section 5 of your file (Frontend, Backend, Data, Infra and delivery, ...). Leave it out if the skill is already listed; the command then raises its level and adds the new evidence.
- It writes the fact into section 3, adds the row to your skills table, keeps a backup in `master/.history/`, and rebuilds what the extension reads.
- Add `--dry-run` first to see exactly what it would write.

**Then, so the new skill shows up in your scores:**
1. In the panel: **Resume > Profile > Rescore saved JDs** (updates every saved JD's keyword score).
2. On a JD that matters: **Analysis > Get the full score** (Claude re-judges with your new evidence).

Prefer to edit by hand? Add a line under section 3 (`- **F-USR-06** Used Python for ...`) and a row in section 5 (`| Python | user-confirmed | F-USR-06 | | |`), then run `python3 tools/build_profile.py`.

Levels: `user-confirmed` or `listed` count in full, `partial` counts half, `earlier` and `none` do not count.

### Why is a skill I have not counted?

Check in this order:
1. **Is it in `master/master-resume.md` (section 5)?** The scorer only knows what is in that file. Use the command above.
2. **What level is it?** `earlier` and `none` never count. The same command raises a level.
3. **Is the name recognisable?** The scorer matches the skill's name in the JD text, ignoring case. It knows common synonyms (Postgres and PostgreSQL, K8s and Kubernetes). For anything else it matches the exact name you wrote, so use the name the industry uses.
4. **Did you rebuild?** The panel shows "Skill profile is older than your master file" until you press **Rebuild now** (or `python3 tools/build_profile.py`; `add_skill.py` does this for you).
5. **Is a saved JD still showing an old score?** Press **Rescore saved JDs**, then **Get the full score** again.
6. **Does the JD use a different word?** Add the other spelling as its own row, for example both "Node.js" and "NodeJS".

### Upgrade a skill from partial or older-resume-only to confirmed

Run the same command with a fact that proves it, for example `python3 tools/add_skill.py "Kubernetes" --fact "Ran the production Kubernetes cluster for the billing service at Example Corp for 18 months"`. It raises the level and adds the evidence.

### Add a new job or project to my experience

Open `master/master-resume.md` and add a heading in section 3 in this form, then facts under it:

```
### Company Name, Your Title (Mon YYYY to Mon YYYY, City)

- **F-CN-01** (verified) What you did, with the number if you have one.
```

Use a short unique ID prefix per company. Reference those IDs in section 5, then run `python3 tools/build_profile.py`.

### Choose a resume layout, contact details and a photo

- **Layout:** Settings, **Tailored resume layout**: *Basic* (one column), *Two column* (sidebar and main) or *With photo*. A tailored resume starts from that layout. To use a layout of your own, put a file with the same name in `tailored/_base/layouts/` inside your data folder (for example `two-column.html`); it replaces the shipped one. Keep its structure and its `@page` print rules.
- **Contact details:** they come from the table in section 1 of your master resume (Name, Location, Email, Phone, Portfolio, LinkedIn, GitHub, Headline). The layouts ship with made-up sample values, and the build replaces every one of them with yours and leaves out a line whose row is empty. The file name uses your name too (Priya Rao gives `priya_rao_resume_<company>.pdf`).
- **Photo (With photo layout only):** Settings, **Profile photo**, **Choose photo...** (macOS file picker; the picture is resized and saved as `master/photo.jpg` in your data folder). You can also copy a JPEG there yourself. It stays on your computer (it is git-ignored together with the rest of your data). Without one, the layout keeps a plain avatar. Many employers, especially in the US and UK, prefer resumes without a photo; use it where it is the norm.

### Understand why a JD got its score

Open **JD > Analysis**. **Requirement comparison** lists each requirement as met, partial or a gap, with the fact IDs that back it (tap an ID to read the fact). **Key skills match** shows matched, missing, unconfirmed and additional skills. **Potential concerns** lists what needs your own judgement. After a full score, **Claude's assessment** shows the written reasoning.

### Change how partial skills count

**Settings > Scoring > Scoring preferences**: half credit (default), no credit or full credit. Skills marked `earlier` never count, whatever you choose.

### Keep one job open while I look at others

Press the **pin** in the panel header. Press it again to release.

### Score a page the panel cannot read

Open the panel, paste the job description text into the box on the empty screen, add a company and role, and press **Score pasted text**.

### Record that I applied, and what happened next

Open **Applications** (people icon). Select the job, set the status (for example **applied**), add a note if you like, and log interview rounds with **Add round**. Every change is added to the **Status history**; nothing is overwritten.

### Undo a mistake in my files

- Your resume file: the last copies are in `master/.history/` (made by `add_skill.py`).
- An application: every change keeps the previous version in `applications/.history/`.
Copy the file you want back over the current one, then run `python3 tools/build_profile.py`.

---

## 9. FAQ

**Is my data sent anywhere?** Not by the extension. Only when you press a "Use Claude" button (or run a skill in a terminal) does Claude Code send the JD text and your resume facts to Anthropic, under your own sign-in. See section 2.

**Does it cost anything?** The extension and scripts are free. Claude steps use your Claude plan's usage (roughly 10 to 30 cents per run, with a hard cap of $1 to $2).

**Why do I see two scores?** The **keyword score** is instant and free: it counts the skills the JD names that your resume backs up. The **full score** is Claude's judgement, and it also weighs things keywords cannot see, like ownership, communication and seniority. Once a full score exists it becomes the main number everywhere, with the keyword score beside it. They often differ, and the full score is usually the lower and more honest one.

**Which one should I trust?** Use the keyword score to decide quickly whether to look closer, and the full score to decide whether to apply.

**What does "unconfirmed" mean?** Skills that are only partial, or only on an older resume. They never raise the score until you confirm them with evidence.

**What does "needs your own judgement" mean?** Soft requirements ("communicates well", "owns projects") cannot be checked against a skills list. The panel lists them so you can decide for yourself.

**Can I use it without Claude?** Yes. Scoring, flags, salary, evidence, saving JDs, the Applications page and your Resume tab all work without it. Only the "Use Claude" steps and the two skills need it.

**Does it apply to jobs for me?** Never. It does not fill in forms, send messages or submit anything.

**Why does it say "Local helper not connected"?** The small helper that reads and writes your files is not installed, or the project folder moved. Run `python3 tools/jobd/install.py`. Scoring still works without it.

**A Claude step says "N commands were blocked". What now?** Claude tried a command outside what it is allowed to run, so the result may be incomplete. Press the step again, or run the "Run in a terminal instead" command shown under it.

**Will it work in Edge, Brave or Arc?** They are Chromium browsers and can load the extension, but only Google Chrome is tested, and the helper installer writes to Chrome's folder.

**What is the difference between my master resume and a tailored resume?** The master file is your single source of facts and is only changed by you. A tailored resume is built for one job from those facts, saved in `tailored/`, and never overwrites the master.

**How do I start over?** Delete `tools/jd-capture-extension/data/` and run `python3 tools/build_profile.py`. To clear your applications, move the files out of `applications/`. Your master resume is never touched by either.

---

## 10. Where things are

| Path | What it is | Yours or generated? |
|------|------------|---------------------|
| `master/master-resume.md` | Your resume facts. The one file that matters | **Yours** |
| `applications/` | One file per saved JD, with rounds and status history | **Yours** |
| `tailored/` | Resumes built for a specific job | Yours (built) |
| `tools/jd-capture-extension/` | The extension (load this folder in Chrome) | Code |
| `tools/jd-capture-extension/data/` | What the extension reads | Generated by `build_profile.py` |
| `tools/jobd/` | The local helper | Code |
| `tools/` (the rest) | Scripts: setup, doctor, scoring, tests | Code |
| `.claude/skills/` | The `/job` and `/interview` skills | Code |
| `views/` | Readable HTML and PDF copies of your data | Generated |
| `docs/` | This guide, design notes, decisions | Docs |

Back up `master/`, `applications/` and `tailored/`. Everything else can be rebuilt.

### Keeping your data in its own folder

By default your data lives in the project folder. You can keep it somewhere else instead, for example a private repo of your own, so the project folder holds only code and you can update or replace it freely:

- **In the panel:** Settings, **Your data folder**, **Choose folder...**. Pick the folder. If it has no master resume, JD Lens can add the sample one.
- **From a terminal** (in the project folder, the one that contains `tools/`): `python3 tools/setup.py --data-dir "/full/path/to/folder"` (first install), or later `python3 tools/paths.py set "/full/path/to/folder"`. `python3 tools/paths.py show` says where things are, and `python3 tools/paths.py clear` goes back to the project folder.
- **To start a new folder by hand:** `python3 tools/paths.py init "/full/path/to/folder"` creates `master/`, `applications/`, `tailored/` and `views/` and copies the sample master resume into it. An existing master resume is never replaced.

The folder only needs those subfolders (`job-inbox/` appears when you save a JD). The extension and the scripts then read and write it there. Claude runs start in that folder, with the project folder added so the `/job` skill is found. The generated files in `tools/jd-capture-extension/data/` stay with the extension. The setting is stored in `jdlens.config.json` next to `tools/` (git-ignored); the `JD_LENS_DATA` environment variable overrides it.

---

## 11. Troubleshooting

| You see | Likely cause | Fix |
|---------|--------------|-----|
| "Local helper not connected" | The helper is not installed, or the folder was moved | `python3 tools/jobd/install.py`, then reload the extension |
| `doctor` says the helper "allows a different extension ID" | The extension was loaded from a different folder or copy | Load `tools/jd-capture-extension` from this project, or rerun `install.py` |
| "No skill profile yet" | `build_profile.py` has not run | `python3 tools/build_profile.py`, then press Refresh |
| "Skill profile is older than your master file" | You edited the resume file | Press **Rebuild now** in the panel, or run `build_profile.py` |
| The icon does nothing / "could not read this page" | Chrome pages (`chrome://`) and the Web Store cannot be read | Open a normal job page and click the icon on it |
| Score is `--` or "No recognisable requirements" | The page text was not found | Press Refresh, or paste the JD text into the box |
| A score looks wrong | A skill is missing or at the wrong level in your resume file | Check **Resume > Skills**, fix the file, rebuild |
| "N commands were blocked" after a Claude step | Claude tried a command outside its allowlist | Run the step again. If it repeats, run the "in a terminal" command, and keep `tools/jobd/jobs/*.out` to show when asking for help |
| Claude steps do nothing / "claude not found" | Claude Code is missing or not signed in | Run `claude` once in Terminal and sign in, then `python3 tools/jobd/install.py` |
| Anything else | | `python3 tools/doctor.py`, then look at `tools/jobd/jobd.log` |

---

## 12. Update, backup and remove

- **Update:** replace the code files with the new version (keep `master/`, `applications/`, `tailored/`), then run `python3 tools/setup.py` and press the reload arrow on the extension in `chrome://extensions`.
- **Back up:** copy `master/`, `applications/` and `tailored/`.
- **Remove:** `python3 tools/jobd/install.py --uninstall`, then remove the extension in `chrome://extensions`. Your files stay where they are.
- **Check it still works:** `python3 tools/doctor.py`, and for developers `python3 -m unittest discover -s tools/tests` and `node --test tools/jd-scorer/`.

---

## 13. Other systems (Linux, Windows)

- **The panel and scoring work on any system** that runs Chrome 116+: open a job page and read the score, flags, salary and evidence. You will see "Local helper not connected" and cannot save JDs or change statuses.
- **The helper installer is tested only on macOS** (Chrome). On Linux, the helper's manifest goes in `~/.config/google-chrome/NativeMessagingHosts/` and the file is written by `install.py --manifest-dir <that folder>`; this is untested. Windows needs a registry entry and is not supported yet.
- Resume PDF building expects Google Chrome at its macOS path.

---

## 14. Sharing JD Lens, and Claude marketplace plugins

Right now JD Lens ships as a project folder: the extension, the helper and the two skills together, set up by `python3 tools/setup.py`.

The skills can later be published as a **Claude Code plugin** so people install them with `/plugin install`. That needs one change first: the skills call scripts by a path relative to the project (`tools/...`). In plugin form the scripts live in the plugin, so the skills must find them through the plugin root and read your data from a configurable folder. The extension and helper stay a downloadable folder, because Chrome loads extensions from disk.

Recommended order: share the project folder with this guide first, then split out a plugin for `/job` and `/interview` once the folder structure is stable.
