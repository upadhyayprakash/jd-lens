# ADR-0003: Information architecture of the extension

- Status: Accepted (2026-11-22, the user)
- Source: `docs/design/jd-panel/ui-info-architecture-resume-vs-jd.md`; the check is in `docs/design/jd-panel/ia-validation.md`.

## Decision

1. **The sidebar evaluates the current job and opens the master resume.** Two primary areas in a persistent shell: **JD** (Overview, Analysis, Details) and **Resume** (Profile, Skills, Experience).
2. **Applications is a separate, full-page extension view** (`applications.html`), opened from the shell. It owns the dashboard, filters, sort and application details. The sidebar only shows application counts and a saved or applied banner for the current job.
3. **One shared context per area.** JobContext (scan, score, matched and missing skills, evidence, application record) and ResumeContext (skill profile and readable resume) are built once per render. Overview, Analysis and Details read the same context, so they cannot disagree.
4. **The master resume is the single source of truth.** The Resume section is read-only for now. Changes are made in the master file (or by asking Claude); a skill only counts after the user confirms it. Job-specific resumes are built under `tailored/` and never overwrite the master file.
5. **Status changes are events, not overwrites.** Every change appends a row to a Status history section in the application file.
6. **Gradient:** the brand pair `#f5a8a0` to `#f4c686`, used selectively (navigation indicator, progress, call-to-action accents, thin borders).
7. **Name:** JD Lens (chosen by the user on 2026-11-22). The IA doc says JD Fit; JD Lens supersedes it. Earlier names, JD Fit and JD vs Resume, appear only in historical docs.

## Consequences

- Reading and layout follow the doc. The cost is one more extension page and a larger data set in the extension (`resume.json`, no contact details).
- Editing the profile from the panel is not built. When it is, it must go through the helper with backups and the same confirmation rules.
- The match percentage still appears in three places (Overview, Analysis, Details), because the doc lists it in each.
