# ADR-0004: Gradual onboarding and feature preferences

- Status: Proposed (2026-11-22). Experimental. To be discussed with the user before any build.
- Idea owner: Alex Morgan.
- Related: ADR-0003 (information architecture), the weekly permission reminder already in the panel.

## Problem

JD Lens already has many areas: JD (Overview, Analysis, Details), Resume (Profile, Skills, Experience), Applications, Settings,
Brag Sheet, Claude actions, an optional permission and a local helper. A new user who clicks the icon sees all of it at once.
They may not know what to do first, and the features that need setup (the helper, the Claude skills, a master resume) look broken
before they are set up.

## Idea

Introduce the capabilities in stages, by hints, and let the user choose the pace. Features are switched on by a preferences panel
in Settings; a few are on by default at install. The user is asked once, at the start, whether to start quick and complete or
gradually.

## Proposed decision (to be confirmed)

1. **First run asks one question:** "Show me everything now" (quick and complete) or "Show me step by step" (gradual, the default
   highlight). The answer is stored and can be changed in Settings.
2. **A Features panel in Settings** with one checkbox per feature group. Turning one off hides its tabs, cards and hints. Nothing is
   deleted; saved data stays.
3. **Default ON at first install (core loop):** instant keyword score, Your match with threshold, JD Overview, Details.
4. **Default OFF until introduced (needs setup or more thought):** Analysis (needs the helper and Claude), Brag Sheet and tailoring,
   Applications dashboard, Resume management, automatic tab reading.
5. **Introduction by hints, one at a time, never blocking:** a hint appears after the user has finished the step before it
   (for example, after the first score: "Want Claude's judgement on this?"). Each hint can be dismissed, snoozed, or turned into a
   permanent preference. A hint never appears twice after "Don't show again".
6. **Gradual path (draft order):** (1) score a JD, (2) set a threshold, (3) save a JD, (4) full score and Analysis,
   (5) Brag Sheet, (6) Applications and status, (7) optional: follow tabs automatically.
7. **Prompt types:** inline card in the panel for the next step; tooltip on a new control (the own tooltip component); toast for
   confirmations; the weekly reminder only for the optional permission. No modal dialogs, no tours that cover the UI.

## Open questions

- Which features are truly default ON? The list above is a first guess.
- What does "quick and complete" turn on, and does it also run a setup check (helper, skills, master file)?
- How is progress detected without reading anything private? (Counts of saved JDs and settings flags only, kept in local storage.)
- Does the gradual flow need a way to skip ahead, and a "show me what I'm missing" list?
- How are existing users migrated (assume quick and complete, nothing hidden)?
- Which setup steps need the local helper, and how does the panel explain it before it is installed?
- How do we measure whether it works, with no analytics? (Manual testing with a few new users.)

## Consequences

- More state (preferences, hint progress) in `chrome.storage.local`, and every view must respect hidden features.
- Each feature needs a short intro hint and a clear "off" state.
- Test matrix grows: quick and gradual paths, each feature on and off.

## Follow-ups

- Write the article for the portfolio and LinkedIn: how to onboard new users to a feature-rich app without overwhelming them.
- Prototype the first-run question and two hints before building the full panel.
