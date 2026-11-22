# Chrome Web Store listing: draft copy

Status: draft for review, 22 Nov 2026. Replace the screenshot and video placeholders once the real recordings exist.
Character limits are the store's (CHECK them in the dashboard when you paste).

## Name
JD Lens

## Summary (max 132 characters)
Score any job description against your own resume data. Tailor your resume and prepare your pitch. Runs on your machine.
(120 characters)

## Category and language
Productivity. English.

## Description

JD Lens reads the job page you are on and tells you, in seconds, how well it fits your own resume.

**What you get**
- An instant keyword score, the offered salary and red flags (location, a stale posting, scam signals), with no AI needed.
- Your match: the score against a threshold you choose, with a verdict you can trust at a glance.
- Analysis: matched, missing and unconfirmed skills, each tied to the fact in your resume that backs it.
- A full score with a written assessment from Claude, when you ask for it.
- A tailored resume proposal you approve before anything is built, then a PDF you can send.
- A Brag Sheet: your pitch for that job, to read before the interview.
- Every application in one place, with status, rounds and history.

**Honest by design**
Nothing is applied or sent for you. Resume claims come only from facts in your own master resume, and every point shows its source.

**Before you install: what it needs**
JD Lens works with a local helper and your own resume file, both on your computer. The helper is a small program you install once (instructions on the project page); it saves applications and runs Claude on your machine. The AI steps use your own Claude Code installation and account. Without them the extension still shows the instant keyword score for a profile you have built.

**Your data**
Everything stays on your computer. There is no account, no analytics and no server of ours. See the privacy policy.

## Single purpose (the store asks for one sentence)
Score a job description against the user's own resume data and help them track and act on applications for it.

## Permission justifications
- **activeTab:** read the job page the user clicks the toolbar icon on, to score it. Nothing is read from other tabs.
- **scripting:** run the page reader on that tab, after the user's click.
- **sidePanel:** show the scores, analysis and next steps beside the job page.
- **storage:** keep the user's settings (theme, threshold, page length) and the last page read for this browser session.
- **nativeMessaging:** talk to the JD Lens helper the user installs on their own computer. It saves applications, builds the skill profile and runs the user's own Claude Code on their machine. No data goes to any server of ours.
- **Optional host access (http and https pages):** off by default. If the user chooses "Allow reading job pages automatically", the panel re-reads the page when they switch tabs. It can be revoked any time from Settings or the browser.

## Data-use disclosures (privacy practices tab)
- Collects: website content of the job page the user chooses to score. Used only inside the extension, on the user's computer.
- Does not sell data, does not use it for unrelated purposes, does not transfer it to us or third parties by the extension. (The user's own Claude Code, which the user runs, sends prompts to Anthropic under the user's own account.)
- No remote code. All code ships in the package.
- One outgoing request: the company's own website icon (`/favicon.ico`) when the page names a company website, to show its logo.

## Screenshots (1280 x 800, up to 5) and video
Plan, in this order (to be captured from the real app after the recordings):
1. Overview: header, Next action, Your match.
2. Analysis: Key skills match and requirement comparison.
3. Next steps with a finished step and the tailored resume proposal.
4. Brag Sheet.
5. Applications page.
Video: the 90-second cut (YouTube link in the video field). Not ready yet.

## Links needed
- Homepage and support: the new repo or landing page (after the repo split).
- Privacy policy URL: host `privacy-policy.md` (landing site or the repo's Pages).
