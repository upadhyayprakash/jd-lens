# Information architecture check: what we built against the IA document

Source: `docs/design/jd-panel/ui-info-architecture-resume-vs-jd.md`. Two passes: the first check (2026-11-22, before the fixes) is kept below. This top section is the result after the fixes.

**After the fixes: 73 checks. 67 met, 6 partial, 0 not met, 0 needing a decision.** (Before: 25 met, 25 partial, 22 not met, 1 decision.)

## Still open

| # | Requirement | Now | Why |
|---|-------------|-----|-----|
| A3 | Header: brand, pin/unpin, close | **Partial** | Close and Pin are built but cannot be tested without a real side panel. Try both once. |
| D7 | Do not duplicate the analysis in Details | **Partial** | Match percentage now appears three times (Overview score, Analysis ring, Details bar), down from five. |
| E7 | Edit profile, add or remove skills, update experience | **Partial** | Read-only by your decision. The Resume tab explains how to change the master file or ask Claude, with copyable commands. Edits from the panel come later. |
| H3 | Do not repeat the same information across Overview, Analysis, Details | **Partial** | Same as D7. |
| H4 | Secondary information in expandable sections | **Partial** | Read more, terminal commands and chip lists collapse. Flags and the requirement list do not. |
| H9 | Every interactive element works, no decorative buttons | **Partial** | Every button now does something (Review before applying has a real action). Close and Pin still need a real-panel check. |

## What changed

| # | Requirement | Before | Now | How it is met |
|---|-------------|--------|-----|---------------|
| A2 | Product name in the header: JD Fit | Decision | **Met** | Renamed to JD Lens by the user on 2026-11-22 (the doc's JD Fit is superseded). |
| A1 | Three functional areas: JD, Resume, Applications | Partial | **Met** | Applications is its own area: a full-page view opened from the shell (people icon), with its own dashboard and details. |
| A5 | Global navigation stays persistent | Not met | **Met** | The shell (header, JD | Resume, refresh, Applications, Settings) shows on every screen. |
| A6 | JD contextual tabs: Overview, Analysis, Details | Not met | **Met** | JD has three tabs in the document's order: Overview, Analysis, Details. |
| A7 | Resume contextual tabs: Profile, Skills, Experience | Not met | **Met** | Resume has three tabs: Profile, Skills, Experience. |
| A8 | Keep navigation state when switching JD and Resume | Not met | **Met** | The selected JD tab and Resume tab are remembered when you switch between JD and Resume. |
| B2 | Job summary: title, company, location, URL, posting date | Partial | **Met** | Posting date shows as a date with the age beside it. |
| B5 | Threshold control (user-defined minimum) | Partial | **Met** | Inline control on Overview: Set threshold, slider, Clear. |
| B6 | Flags: missing or ambiguous requirements, remote/location, experience mismatches, other | Partial | **Met** | Flags now include must-have requirements not met and experience mismatch. Ambiguity flags are in Analysis, Potential concerns. |
| B7 | Evidence summary: matched, missing, unconfirmed | Not met | **Met** | Three counts on Overview: Matched, Missing, Unconfirmed. Each opens the matching Analysis tab. |
| B8 | CTA: View full analysis | Partial | **Met** | Button reads View full analysis and opens Analysis. |
| C4 | Additional skills | Partial | **Met** | Additional skills is a fourth tab in Key skills match, with a list. |
| C5 | Skill overlap tags | Partial | **Met** | Skills overlap lives in Details only, as the document's hierarchy has it. |
| C6 | Evidence-based comparison of JD requirements against the master resume | Not met | **Met** | Requirement comparison: each requirement, met / partial / gap, with tappable evidence IDs that show the fact. |
| C7 | Experience and seniority alignment | Not met | **Met** | Experience alignment card: years asked vs yours, level in the JD vs your titles. |
| C8 | Potential concerns or ambiguities | Partial | **Met** | Potential concerns card: unmet must-haves, requirements that need your judgement, unstructured JD, no salary, seniority gap. |
| C10 | Mark an action as completed | Not met | **Met** | Mark done / Undo done on steps 3, 4 and 5, remembered per job. |
| D1 | Title, company, location, posting date | Partial | **Met** | Same as B2. |
| D3 | Required skills and qualifications | Not met | **Met** | Required skills and qualifications card, with Required and Preferred lists. |
| D6 | Link to the original job posting | Not met | **Met** | Details has an Open the original posting button. |
| E1 | Last updated timestamp of the master resume | Partial | **Met** | Shows when the master file was last updated, and when the skill profile was built. |
| E3 | Short profile summary | Not met | **Met** | Profile summary text from the master file, with the other variant expandable. |
| E4 | Skills, experience, projects, education, certifications, affiliations shown | Not met | **Met** | Education, certifications, awards, open work (Profile), skills by group (Skills), experience and projects (Experience). The master file has no affiliations, so none are shown. |
| E5 | Independently manageable sections | Not met | **Met** | Profile | Skills | Experience tabs. |
| E6 | Skills linked to the experience or project that proves them | Not met | **Met** | Evidence IDs show on every skill and requirement; tap one to read the fact and where it comes from. |
| E8 | Rebuild skill profile | Partial | **Met** | Rebuild skill profile is in Profile management as well as Settings. |
| E9 | Recalculate job matches when master data changes | Not met | **Met** | Rescore saved JDs button recalculates the keyword score of every saved JD. |
| F1 | Dedicated full-page view, not the narrow sidebar | Not met | **Met** | applications.html: a full-page view with a list and a detail pane (stacked on narrow windows). |
| F2 | Dashboard counts: saved, applied, interviewing, offers, rejections, withdrawn | Not met | **Met** | Dashboard counts: Total saved, Considering, Applied, Screening, Interviewing, Offers, Rejected, Withdrawn. Each filters the list. |
| F4 | Card: company, title, match score, status, date added, date applied | Partial | **Met** | Cards show company, title, match (full or keyword), status, date added, date applied, location. |
| F5 | Default sort: recent activity or best match | Partial | **Met** | Sort: Most recent activity (default), Best match, Date added. |
| F6 | Detail: company, role, location, posting date, match, status | Partial | **Met** | Location shown in the card and in Job information. |
| F9 | Interview rounds: history, date, type, notes, outcome, add round | Partial | **Met** | The round form has type, date, interviewer, outcome and notes; the table shows all of them. |
| F11 | Status changes preserve history, no overwriting | Not met | **Met** | Every status change appends a row to a Status history section in the application file (with an optional note), shown as a timeline. Old rows are never rewritten. |
| G1 | Scoring: minimum threshold and scoring preferences | Partial | **Met** | Scoring section: threshold, plus a real preference (partial skills: half, no or full credit) and how the score is calculated. |
| G2 | Appearance: theme and text size together | Partial | **Met** | Theme and text size are one Appearance section. |
| G4 | Local helper: status, resume file location, skill profile location, version | Partial | **Met** | Local helper shows the resume file and skill profile paths. |
| G5 | Skill profile: generated time, skills and evidence counts, show, rebuild | Partial | **Met** | Skill profile shows generated date, skill rows and evidence entries. |
| H6 | Skeleton or loading state while analysing | Not met | **Met** | Skeleton cards while a page is being read. |
| H8 | Keep the current job context while moving between sections | Partial | **Met** | A Current job strip on the Resume tab and Settings returns you to the job. |
| H10 | Shared JobContext and ResumeContext, no duplicated state per view | Partial | **Met** | JobContext and ResumeContext are built once per render and every tab reads them, so tabs cannot disagree. |
| I1 | Brand gradient #f5a8a0 to #f4c686 | Not met | **Met** | Brand gradient is now #f5a8a0 to #f4c686 in both themes. |
| I2 | Use the gradient selectively, never on large surfaces or every card | Partial | **Met** | The saved banner and salary card use a gradient border, not a fill; Pro Tip uses a faint fill. Gradient stays on tabs, bars, ring and primary buttons. |

---

## Original check (before the fixes)


Source: `docs/design/jd-panel/ui-info-architecture-resume-vs-jd.md` (your Downloads file, copied here). Checked against the extension as built on 2026-11-22 (design v2). Statuses: **Met**, **Partial** (there but incomplete or in the wrong place), **Not met**, **Decision** (needs you).

**Result: 73 checks. 25 met, 25 partial, 22 not met, 1 needs your decision.**

Priority: P1 = structure or small fix that should be done first, P2 = real feature work, P3 = polish.


### Structure

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| A1 | Three functional areas: JD, Resume, Applications | **Partial** | Two primary areas (JD, Resume). Applications is a list inside the Resume tab. | Make Applications its own area (see F1). | P2 |
| A2 | Product name in the header: JD Fit | **Decision** | We use "JD vs Resume", as you told me when you sent the new designs. The IA doc still says JD Fit. | You decide which name wins. | Decision |

### Shell

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| A3 | Header: brand, pin/unpin, close | **Met** | Done, plus A- and A+ (not in the doc). The Close button is untested in a real side panel. | Verify Close and Pin in Chrome. | P3 |
| A4 | Primary navigation: JD | Resume, gradient on the active one | **Met** | Done. |  |  |
| A5 | Global navigation stays persistent | **Not met** | The JD/Resume bar disappears on Details, Analysis, application and settings screens (replaced by a back button). | Keep the shell on every screen. | P1 |
| A6 | JD contextual tabs: Overview, Analysis, Details | **Not met** | Overview is the JD tab itself. Details and Analysis sit behind a "View full details" button, in the order Details then Analysis. | Make Overview | Analysis | Details three tabs inside JD, in that order. | P1 |
| A7 | Resume contextual tabs: Profile, Skills, Experience | **Not met** | None. The Resume tab is one scrolling page. | Add contextual tabs (see E). | P2 |
| A8 | Keep navigation state when switching JD and Resume | **Not met** | Analysis is a separate screen, so switching to Resume and back drops you at Overview. | Remember the selected sub-tab per section. | P1 |

### JD Overview

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| B1 | Saved/applied indicator with a link to application details | **Met** | Done (gradient banner, Details link). |  |  |
| B2 | Job summary: title, company, location, URL, posting date | **Partial** | All present, but the posting date shows as "Posted 171 days ago", not the date. | Show the date, keep the age as a hint. | P3 |
| B3 | Match score with change since last evaluation | **Met** | Done (the +7 indicator). |  |  |
| B4 | Salary range, "not stated", manual update | **Met** | Done. |  |  |
| B5 | Threshold control (user-defined minimum) | **Partial** | Shows the bar and a marker, but you set it in Settings through a "set one" link. | Add an inline control on Overview. | P2 |
| B6 | Flags: missing or ambiguous requirements, remote/location, experience mismatches, other | **Partial** | Remote, India, age, scam and years mismatch. No flag for missing or ambiguous requirements. | Add "missing N required skills" and ambiguity flags. | P2 |
| B7 | Evidence summary: matched, missing, unconfirmed | **Not met** | A sentence ("JD mentions 21 skills, you have 19") and a Match pill. No three-way split. | Show matched / missing / unconfirmed counts. | P1 |
| B8 | CTA: View full analysis | **Partial** | The button says "View full details" and opens Details, not Analysis. | Rename and point it to Analysis. | P1 |

### Analysis

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| C1 | Overall match score with a visual indicator | **Met** | Done (ring). |  |  |
| C2 | Matched skills | **Met** | Done (Key skills match, Matched tab). |  |  |
| C3 | Missing skills | **Met** | Done. |  |  |
| C4 | Additional skills | **Partial** | Only a count ("Extra skills 13"). No list. | List them, with a +more chip. | P1 |
| C5 | Skill overlap tags | **Partial** | They are in Details, not Analysis. | Keep one copy, in Analysis (see H3). | P2 |
| C6 | Evidence-based comparison of JD requirements against the master resume | **Not met** | Not shown. The scorer already computes each requirement with its marks, but the UI only shows chips. | Add a requirement list: requirement, met/partial/gap, evidence fact IDs. | P1 |
| C7 | Experience and seniority alignment | **Not met** | Only one years-mismatch flag on Overview. | Add a section: years asked vs yours, seniority words. | P1 |
| C8 | Potential concerns or ambiguities | **Partial** | Spread across Flags on Overview. | Collect them in Analysis. | P2 |
| C9 | Actionable next steps | **Met** | Done, a superset: save, full score, tailor, missing skills, review, skip. |  |  |
| C10 | Mark an action as completed | **Not met** | "Done" shows only when something is detected (saved, resume built). You cannot tick a step yourself. | Add a tick with remembered state. | P2 |
| C11 | Pro Tip card | **Met** | Done. |  |  |

### Details

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| D1 | Title, company, location, posting date | **Partial** | Present, date shown as age. | Same as B2. | P3 |
| D2 | Job highlights | **Met** | Done. |  |  |
| D3 | Required skills and qualifications | **Not met** | Not shown. Only highlights and the description. | List required and preferred items from the JD. | P1 |
| D4 | Job description with expandable content | **Met** | Done (Read more). |  |  |
| D5 | Your match percentage and skills overlap | **Met** | Done. |  |  |
| D6 | Link to the original job posting | **Not met** | The link is on Overview only. Details says "Source: Page text". | Add the link here. | P1 |
| D7 | Do not duplicate the analysis in Details | **Partial** | Your match and overlap sit in Details and Analysis both (see H3). | Decide one home for each. | P2 |

### Resume

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| E1 | Last updated timestamp of the master resume | **Partial** | Shows when the skill profile was built, not when the master file last changed. | Show the master file's modified time. | P2 |
| E2 | Open master as HTML or PDF | **Met** | Done. |  |  |
| E3 | Short profile summary | **Not met** | Only counts ("25 skill rows, 12 years"). | Show the summary text from the master file. | P2 |
| E4 | Skills, experience, projects, education, certifications, affiliations shown | **Not met** | None of these are shown. The tab links out to the HTML. | Render each section in the panel (read-only first). | P2 |
| E5 | Independently manageable sections | **Not met** | One block. | Contextual tabs: Profile, Skills, Experience. | P2 |
| E6 | Skills linked to the experience or project that proves them | **Not met** | The data has evidence IDs, but the UI never shows them. | Show IDs and open the fact in the master view. | P2 |
| E7 | Edit profile, add or remove skills, update experience | **Not met** | Not possible from the panel. Today you edit the master file by hand or confirm skills in chat. | Needs a design: edit through the helper with the same confirmed/earlier rules. | P2 |
| E8 | Rebuild skill profile | **Partial** | Works, but only in Settings and the stale banner. | Add it to the Resume section. | P3 |
| E9 | Recalculate job matches when master data changes | **Not met** | Scores are recalculated when you open a page. Saved applications keep their old score. | Add "Rescore saved JDs". | P3 |
| E10 | Master is the source of truth; job-specific variants never overwrite it | **Met** | Done. Tailored resumes are built in tailored/, the master file is only changed by you. |  |  |

### Applications

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| F1 | Dedicated full-page view, not the narrow sidebar | **Not met** | List and detail live in the sidebar. "Open all details" opens a static HTML page. | Build a full-page extension view for the dashboard and details. | P2 |
| F2 | Dashboard counts: saved, applied, interviewing, offers, rejections, withdrawn | **Not met** | Only a total count. | Add the counts. | P2 |
| F3 | Filters: All, Applied, Interviewing, Considering | **Met** | Done. |  |  |
| F4 | Card: company, title, match score, status, date added, date applied | **Partial** | No "date added". Score is blank for applications never scored. | Expose the captured date. | P2 |
| F5 | Default sort: recent activity or best match | **Partial** | Best score only, no recent-activity option or toggle. | Add the toggle. | P2 |
| F6 | Detail: company, role, location, posting date, match, status | **Partial** | Location is missing. | Add it. | P3 |
| F7 | Files: resume PDF, posting, full details, copy path | **Met** | Done. |  |  |
| F8 | Gaps noted | **Met** | Done. |  |  |
| F9 | Interview rounds: history, date, type, notes, outcome, add round | **Partial** | The form has round, date, interviewer, result. Notes are stored but there is no field, and the list does not show them. | Add notes to the form and list. | P2 |
| F10 | Update status | **Met** | Done, all 7 statuses. |  |  |
| F11 | Status changes preserve history, no overwriting | **Not met** | The status field is overwritten. Backups exist in applications/.history but no event list is kept or shown. | Add a status history log per application and a Status History view. | P1 |

### Settings

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| G1 | Scoring: minimum threshold and scoring preferences | **Partial** | Threshold only, no preferences. | Name the section Scoring; add preferences if you want some. | P3 |
| G2 | Appearance: theme and text size together | **Partial** | Two separate cards. | Merge into one Appearance section. | P3 |
| G3 | Reading page: automatic reading and supported-page behaviour | **Met** | Done (no list of supported pages). |  |  |
| G4 | Local helper: status, resume file location, skill profile location, version | **Partial** | Status, repo, Claude path and version. No resume file or skill profile paths. | Add both paths. | P3 |
| G5 | Skill profile: generated time, skills and evidence counts, show, rebuild | **Partial** | Time, skill-row count, show, rebuild. No evidence count. | Add it. | P3 |

### UX

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| H1 | Optimised for a 350 to 400px viewport | **Met** | Done, tested down to 320px at 200% text. |  |  |
| H2 | Tabs for related views only | **Met** | Done. |  |  |
| H3 | Do not repeat the same information across Overview, Analysis, Details | **Not met** | The match percentage appears five times: Score box, Match pill, a Skills match flag, the Analysis ring, and Your match in Details. | Show it in a few deliberate places only. | P1 |
| H4 | Secondary information in expandable sections | **Partial** | Read more, terminal commands and tabs are expandable. Evidence chips and flags are not. | Collapse flags and long lists. | P3 |
| H5 | Match score visible and prominent | **Met** | Done. |  |  |
| H6 | Skeleton or loading state while analysing | **Not met** | None. The panel is blank until the scan arrives. | Add skeletons. | P1 |
| H7 | Empty, error and disconnected states | **Met** | Done: no JD, error, helper missing, stale profile. |  |  |
| H8 | Keep the current job context while moving between sections | **Partial** | The job stays in memory, but the Resume tab and application screens show no "current job" reminder. | Add a compact current-job strip. | P3 |
| H9 | Every interactive element works, no decorative buttons | **Partial** | Close and Pin are unverified in a real side panel. "Review before applying" has no button. | Verify both in Chrome; give that step a real action or fold it into the tick (C10). | P2 |
| H10 | Shared JobContext and ResumeContext, no duplicated state per view | **Partial** | All views read one shared state, so they cannot disagree. But it is one large file, not separate JobContext and ResumeContext modules. | Split into two context modules. | P3 |

### Visual

| # | Requirement (from the doc) | Status | What we have now | Fix | Pri |
|---|----------------------------|--------|------------------|-----|-----|
| I1 | Brand gradient #f5a8a0 to #f4c686 | **Not met** | We use #fb8b83 to #ffc376 (light) and #f28e84 to #f6be7d (dark), sampled from your images. These are your two colours. | Replace both pairs with the doc's pair. One-line change. | P1 |
| I2 | Use the gradient selectively, never on large surfaces or every card | **Partial** | Used on tabs, bars, ring, Pro Tip (as the doc suggests), but also as a fill on the saved banner and the salary card. | Reduce those two to a border or small accent. | P2 |
| I3 | Dark and light themes | **Met** | Done. |  |  |

### The five structural gaps that matter most

1. **The sidebar and the Applications area are mixed up.** The doc wants the sidebar to evaluate the current job and open the master resume, and Applications to be a separate full-page view with a dashboard. We put the application list and detail in the sidebar (A1, F1, F2).
2. **JD navigation is wrong.** The doc has Overview, Analysis and Details as three persistent tabs. We have Overview as the root and Details and Analysis behind a button, with the global shell hidden (A5, A6, A8).
3. **The Resume section is a link, not a section.** It opens the HTML and lists applications. It does not show the profile, skills, experience, projects or education, and cannot manage them (E3 to E7).
4. **Analysis does not explain the score.** It has chips and a count, but no requirement-by-requirement comparison with evidence, no experience alignment and no list of extra skills (C4, C6, C7).
5. **No status history.** Status changes overwrite the field (F11).

### Decisions needed from you

1. **Name:** "JD vs Resume" (what you told me) or "JD Fit" (what the doc says)?
2. **Brand gradient:** adopt the doc's #f5a8a0 to #f4c686 (recommended, it is your pair).
3. **Applications:** build the dedicated full-page extension view, as the doc recommends?
4. **Resume editing (E7):** the doc wants add/remove skills and edit experience from the panel. That means the panel writing to your master file. Options: (a) read-only Resume section now, edits stay in chat; (b) edits through the helper with the same rules as today (a skill is only counted after you confirm it, every write keeps a backup). I recommend (a) first, then (b).

