# ADR-0002: A native messaging host as the extension's local backend

- Status: Accepted (2026-11-21, the user)
- Supersedes in part: ADR-0001 (the handoff via a Downloads inbox and symlink, and the "copy a command" flow as the main route)
- Deciders: Alex Morgan

## Context

ADR-0001 designed the Chrome side panel as a viewer: it reads generated JSON, writes one JSON file per saved JD, and every change goes through a command the user copies into a terminal. the user's goal is stronger: **the extension should eventually be the only UI** for his job search: see applications and their status, change them, log rounds, save and score JDs, tailor and build resumes, prepare for interviews.

That needs two-way communication with his local data, with no always-on server and nothing leaving the machine.

## Decision drivers

1. Two-way: the panel reads and changes local data.
2. No always-on process and no open port.
3. Only his own extension can use it. Web pages cannot.
4. The skills (`/job`, `/interview`) stay the single source of the logic. The UI does not re-implement them.
5. Cheap and instant for simple things, Claude only where judgement is needed.
6. Data safety: no test or bug may damage his real application files.

## Options considered

| Option | For | Against |
|--------|-----|---------|
| Files plus copied commands (ADR-0001) | Zero install, transparent. | One-way. Cannot be the only UI. |
| Local HTTP server | One click, easy to code. | Always-on process, open port reachable by any web page (needs tokens, origin checks). |
| **Chrome native messaging host** | Chrome starts it on demand over stdin/stdout. No port. Only the extension ID listed in the host manifest can call it. | One-time install of a manifest file. Message size limits. Harder to debug than a server. |
| Attach to an open terminal Claude session | Would reuse a running session. | Not possible. Each call must be a new headless run. |

## Decision

Use a **Chrome native messaging host**: a small Python program in this repo (`tools/jobd/host.py`) registered in Chrome's `NativeMessagingHosts` folder, callable only by this extension's ID.

```
Side panel (UI)
  -> service worker (message router)
     -> native host (started by Chrome per use, exits when done)
        -> deterministic operations: run tools/ scripts directly
        -> Claude operations: run headless `claude -p` in the repo
        -> read and write applications/, master/, tailored/, views/
```

### Two kinds of operation

**Deterministic** (instant, free, no Claude). The host calls `tools/jobs.py`, `tools/build_views.py`, `tools/build_profile.py`, `tools/jd-scorer`, `tools/render_pdf.sh`, `tools/check_resume.py`. The `/job` skill calls the same scripts, so there is one code path.

**Judgement** (uses Claude). The host runs `claude -p` (headless print mode) in the repo with the user's existing Claude login, so it uses his plan's usage and no API key. Each call is a new run (resumable), not an attach to an open terminal session. Results are written to the application files, which stay the source of truth, and the panel re-reads them. Buttons for these operations carry a "uses Claude" marker.

To verify at build: that `claude -p` can invoke the `/job` and `/interview` skills by name. If not, the host sends the skill's instructions as the prompt.

### Operations and approvals

Default approval policy (the user, 2026-11-21): one click for reads and status changes; an approval card for anything that writes a resume or a JD file.

| Operation | Kind | Approval |
|-----------|------|----------|
| list applications, show details, open master view, quick score, rebuild views and profile | Deterministic | One click |
| change status, log an interview round, set `resume` or `fit_score` | Deterministic write | One click. The previous file is kept in `applications/.history/` for recovery. |
| save a JD as a new application | Deterministic write | Approval card showing company, role and the file that will be created |
| full fit score with judgement | Claude | One click (writes only the Fit section and score of one application file) |
| tailoring proposal | Claude | Shown as a card. Nothing is built until he presses Approve. |
| build the tailored resume (HTML, PDF, ATS check) | Deterministic after approval | Approval card (the approved proposal) |
| draft answers to application questions, interview prep | Claude | Result shown as a draft. Saving it to `answers/` needs Approve. |

**Claude needs to ask a question** (for example "do you have a real Express example?"): the run writes the question to the application file and stops. The panel shows a question card, the user answers, and the next run continues with the answer. No question is guessed.

### Security

- **Fixed allowlist.** The host accepts only the operations above. It never runs an arbitrary command or path. Every argument is validated (slugs match `^[a-z0-9][a-z0-9-]*$`, statuses come from a fixed list, paths are built from the repo root and checked to stay inside it).
- **Only this extension.** The host manifest lists one allowed origin (this extension's ID). The extension exposes no external connections, so web pages and other extensions cannot reach the host.
- **No network from the host** except what `claude` itself does under his login.
- **Claude runs with limited tools.** Headless runs are launched with an allowlist of tools and the repo as working directory. No commits, no pushes (the standing rule: commit only when he asks).
- **Message limits.** Chrome limits host-to-browser messages to 1 MB, so large content (full JD text, master data) is returned as a file path, not inline.
- **Logging.** Every operation is appended to `tools/jobd/jobd.log` (time, operation, arguments, result code), never message contents like JD text.

### Data safety and testing

Per the user's standing rule on mutating calls: **no write operation is ever tested against the real data.** Tests build a temporary copy of the repo (`tools/`, `applications/`, `master/`) and run every script there, because scripts locate the repo from their own file path. Only read operations are checked against the real files.

## Consequences

- Good: the extension can become the only UI, with real two-way control and no server.
- Good: skills and UI share scripts, so behaviour cannot drift.
- Good: most actions are instant and free. Claude is used only where judgement helps.
- Cost: one-time install of the host manifest in `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`, and re-registering if the extension ID changes (an unpacked extension's ID is fixed by a `key` in the manifest, which we set).
- Cost: harder to debug than a server. Mitigated by the log and by making every operation runnable from the command line.
- Cost: headless Claude runs take time and use plan usage. The panel shows progress and a clear "uses Claude" marker.
- ADR-0001's Downloads inbox and symlink are no longer needed. The "copy a command" panel stays as a fallback and as a way to see exactly what runs.

## Build order

1. **Scripts (shared by host and skill):** `tools/jobs.py` with `list`, `show`, `status`, `round`, `set`, `save-jd`; backups in `applications/.history/`; tests on a scratch repo copy. **Done.**
2. `tools/build_profile.py` and `tools/jd-scorer/` (profile, `applications.json`, quick score, `tools/score_jd.mjs`). **Done.**
3. Native host (`tools/jobd/host.py`, `claude_jobs.py`), installer, operation allowlist, log, tests. **Done.**
4. Extension: side panel with all screens from the wireframes, light and dark themes. **Done** (`tools/jd-capture-extension/`).
5. Claude operations with approval and question cards. **Done** (verified with a fake `claude` in tests, and `claude -p` invoking the `/job` skill by name on a scratch repo).

Verified in real Chrome (throwaway profile): the extension loads with the fixed ID and reaches the host. Still to try by hand the first time: clicking the toolbar icon on a live job page (opening the side panel needs a real click) and a real headless Claude run from a panel button.

## Open items

- Verify `claude -p` with skills, tool allowlists, JSON output and resume of a session (build step 5).
- Extension ID: set a fixed `key` in the manifest so the allowed origin never changes.
- Python path for the host: use the interpreter found at install time, recorded in the manifest.
- Undo for status changes (restore from `.history`): later, only if wanted.
