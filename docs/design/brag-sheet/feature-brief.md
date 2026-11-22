# Brag Sheet: feature brief

Status: draft, 22 Nov 2026. Owner: the user. Not built yet.

## What it is

A per-application "Pitch Doc" for the candidate (not for the employer). For one JD it
shows which of your past work matters most, why, and what to say about it. It is the
second output of the "Tailor your resume" step: the first output is the tailored
resume (what you send), the second is the Brag Sheet (what you read before a screener
or interview).

Name: **Brag Sheet**, subtitle "Pitch Doc".

## Why it makes JD Lens different

Most JD tools stop at a score. The Brag Sheet turns the score into evidence: it
remembers your work, picks what matters for this role, and gives you a quick revision
page just before the interview. It adds no permissions and nothing leaves the machine.

## Sections

1. **JD pillars.** Top 4 to 6 requirements in the JD's own wording.
2. **Matched wins.** 2 to 3 per pillar. Each shows: fact ID(s) from the master file,
   the metric, a rewrite in the JD's language (Action + Context + Result), and a one
   line "so what" for this employer.
3. **Gap bridges.** For requirements only partly met, the closest honest proof. A true
   gap is stated as a gap and is never turned into a claim.
4. **Story bank.** Per win: trade-offs, constraints, what went wrong, the context that
   does not fit on a resume line. Links to a story in `stories/` where one exists.
5. **Revision view.** One screen: pillar, best win, one number, one sentence. For the
   last 10 minutes before an interview.

## Where it appears

- **HTML page** (like the master resume): full sheet, printable.
- **Panel view** in the side panel, read from the JD page. Condensed (pillars, top wins,
  gaps) with a link to the HTML page. Shown automatically when the current tab's
  normalized URL matches a saved application.
- **Applications page:** a "Brag Sheet" tab in each application's tabbed view.

## Rules (inherited from the job skill)

- Claims come only from `master/master-resume.md`, cited by fact ID. Items marked
  `earlier` or `confirm` are not claims until the user confirms them.
- Never upgrade titles, numbers, scale or years.
- If a fact is needed that only the user has, use the existing `questions.json` /
  `answers.json` flow.
- No em dashes anywhere.

## Data and storage

- Source of truth: a `## Brag Sheet` section in `applications/<slug>.md`, same pattern
  as `## Fit` and `## Tailoring proposal`. Machine-readable twin:
  `tailored/<slug>/brag-sheet.json` (pillars, wins with fact IDs, gaps, stories) so the
  panel, HTML page and Applications tab render from one source.
- HTML output: `tailored/<slug>/brag-sheet.html`.
- Job queue: a new `brag` kind in `tools/jobd/claude_jobs.py`, may_write
  `applications/` and `tailored/`. "Tailor your resume" queues `tailor` then `brag`.

## Open questions

1. Link story bank to `stories/` (S1 to S8, reusable interview stories with facts,
   numbers and follow-up prep) or keep separate. Recommendation: link, so a story is
   written once and referenced from the answer bank and the Brag Sheet.
2. Revision view: also a print/PDF one-pager?
3. Does Vandelay (provisional, truncated JD) show a Brag Sheet, or only after a full JD?
   Recommendation: show with a "JD looks incomplete" notice.

## Sources

Gemini and Google search answers on "JD-customized brag sheet" (22 Nov 2026): used for
structure only (requirement mapping, impact bullets, gap bridge, story bank). Examples
in those answers are not facts about the user and are not used.
