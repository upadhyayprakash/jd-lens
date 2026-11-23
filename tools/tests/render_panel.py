#!/usr/bin/env python3
"""Render every panel screen (mock data) in light and dark with headless Chrome, and assert on the content.

Usage: python3 tools/tests/render_panel.py [--shots] [--only=01,02c] [--width 380]
  --shots writes screenshots (off by default: the checks read the DOM, they do not need pictures). --only runs the screens whose names start with one of the prefixes.
Screenshots go to docs/design/jd-panel/screens/. Exit code 1 if an assertion fails or the page reports a JS error.
Each screen is rendered inside a fixed-width iframe, because headless Chrome will not make a window narrower than ~500px
and the real side panel is about 360 to 480px wide.
"""
import pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXT = ROOT / "tools" / "jd-capture-extension"
OUT = ROOT / "docs" / "design" / "jd-panel" / "screens"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH = int(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else 380

# name -> (query, height, strings that must appear)
SCREENS = {
    "01-overview":          ("screen=jd&tab=overview", 1900, ["JD Lens", "Overview", "Analysis", "Details", "@aria-label=\"Applications (full page, opens in a new tab)", "Senior Full Stack Engineer - EMEA", "Northwind", "Posted 3 Jun 2026", "Next action", "Save JD", "!Not saved yet", "Keyword score", "Save the JD to get a full score", "97", "$60,000 - $100,000 USD", "!Salary offered", "!Evidence", "Your match", "@Click to change it in Settings", "!Set threshold", "Flags", "No scam signals found", "Skills", "matched", "missing", "unconfirmed", "View full analysis"]),
    "02-overview-applied":  ("screen=jd&state=applied", 1900, ["Details", "applied", "!You applied on", "!This JD is saved", "Full score", "86", "Judged by Claude on 21 Nov 2026", "Keyword score: 97", "Your match", "@default threshold"]),
    "02b-overview-full-lower-than-keyword": ("screen=jd&state=applied&fit=77&threshold=80", 1900, ["Full score", "77", "Judged by Claude on 21 Nov 2026", "Keyword score: 97", "@Below your threshold of 80", "@Compared with the full score", "!Edit threshold"]),
    "03-overview-threshold": ("screen=jd&state=saved&threshold=80", 1900, ["Details", "!This JD is saved", "@At or above your threshold of 80", "@Compared with the full score", "Worth a look", "!Edit threshold", "!Set threshold"]),
    "03b-overview-below-threshold": ("screen=jd&state=saved&threshold=90", 1900, ["@Below your threshold of 90", "Below your bar"]),
    "03d-permission-nudge": ("screen=jd&state=saved&nudge=1", 1900, ["Tip: let the panel follow your tabs.", "Not now"]),
    "03c-different-tab-banner": ("screen=jd&state=saved&othertab=1", 1900, ["This is a different tab.", "Click the JD Lens icon in the toolbar to score this page."]),
    "04-overview-delta":    ("screen=jd&state=saved&delta=7", 1900, ["+7", "Full score", "Keyword score"]),
    "05-overview-pinned":   ("screen=jd&state=pinned", 1900, ["JD Lens", "Northwind"]),
    "06-loading":           ("screen=jd&state=loading", 900, ["JD Lens", "Reading this job...", "@lens-anim"]),
    "07-analysis":          ("screen=jd&tab=analysis&state=applied", 4600, ["Profile overview", "Full score", "Keyword match", "Keyword breakdown", "Claude's assessment", "Strong match on TypeScript", "Missing skills", "Extra skills", "Experience alignment", "Years of experience", "Level in the JD", "Key skills match", "Additional", "Requirement comparison", "Required", "Potential concerns", "Pro Tip", "!Next steps", "!JD pillars"]),
    "07b-analysis-unjudged": ("screen=jd&tab=analysis", 4400, ["Keyword match", "Keyword breakdown"]),
    "07d-overview-brag-sheet": ("screen=jd&state=applied", 4400, ["Next steps", "Brag Sheet", "JD pillars", "Open full page", "Matched wins", "@aria-label=\"Run again: Brag Sheet"]),
    "07e-overview-no-brag-sheet": ("screen=jd&state=applied&nobrag=1", 4400, ["Brag Sheet", "Not made yet", "Make Brag Sheet"]),
    "07c-analysis-no-assessment": ("screen=jd&tab=analysis&state=nofit&threshold=80", 4400, ["Claude's assessment", "No written assessment in the application file yet"]),
    "08-analysis-evidence": ("screen=jd&tab=analysis&state=applied&open=F-BR-04,F-LM-04", 4800, ["Requirement comparison", "F-BR-04"]),
    "09-analysis-save-card": ("screen=jd", 4600, ["Save this JD", "Save JD", "Next steps"]),
    "10-running-tailor":  ("screen=jd&state=running", 4600, ["Next action", "Proposal running (12s)", "Running (12s)", "Cancel", "!Claude is working in your repo"]),
    "10f-running-narrow": ("screen=jd&state=running&jobkind=tailor&mockwidth=320&scale=1.3", 4600, ["Proposal running (12s)", "Running (12s)", "Cancel"]),
    "10g-running-full-score-narrow": ("screen=jd&state=running&jobkind=full_score&nofitscore=1&mockwidth=320&scale=1.3", 4600, ["Full score running (12s)", "Running (12s)", "Cancel"]),
    "10c-running-full-score": ("screen=jd&state=running&jobkind=full_score&nofitscore=1", 4600, ["Full score running (12s)", "Running (12s)", "Cancel", "Get the full score"]),
    "10d-running-brag": ("screen=jd&state=running&jobkind=brag&nobrag=1", 4600, ["Brag Sheet running (12s)", "Running (12s)", "Cancel"]),
    "10e-running-build": ("screen=jd&state=running&jobkind=build&nofitscore=1", 4600, ["Build running (12s)", "Running (12s)", "Cancel"]),
    "10b-analysis-blocked": ("screen=jd&state=denied", 5000, ["Full score finished, but 2 commands were blocked", "Claude was not allowed to run", "score_jd.mjs", "may be incomplete"]),
    "11-analysis-proposal": ("screen=jd&state=proposal", 5000, ["Proposal (you approve before anything is built)", "Approve and build PDF", "Request changes", "Proposed", "Scored", "@aria-label=\"Run again: resume proposal", "!Resume proposal finished", "!of usage", "!Proposal written to the application file"]),
    "02d-next-action-no-full-score": ("screen=jd&state=applied&nofitscore=1", 1900, ["Next action", "Get full score", "!Not saved yet"]),
    "02e-next-action-build": ("screen=jd&state=saved", 1900, ["Next action", "Approve and build PDF", "Tailor your resume", "!Tailor your experience"]),
    "02f-next-action-slides": ("screen=jd&state=applied&autoslide=1", 1900, ["Next action", "Add missing skills", "@aria-label=\"Show action 1 of 2"]),
    "03e-match-strong": ("screen=jd&state=applied&threshold=40", 1900, ["Strong match", "@Well above your threshold of 40", "@bar thick strong", "!Well above your threshold of 40."]),
    "03f-threshold-explicit-50": ("screen=jd&state=applied&threshold=50", 1900, ["@Well above your threshold of 50", "@Click to change it in Settings"]),
    "03g-threshold-default-50": ("screen=jd&state=applied", 1900, ["@Well above the default threshold of 50", "@until you choose your own in Settings"]),
    "20c-settings-default-threshold": ("screen=settings&state=applied", 3200, ["Using the default (50)", "It starts at 50", "!Reset to default"]),
    "20d-settings-explicit-threshold": ("screen=settings&state=applied&threshold=50", 3200, ["Saved: 50", "Reset to default (50)"]),
    "02c-overview-compact-skills": ("screen=jd&state=applied", 2600, ["Next action", "Review your resume", "Add missing skills", "Skills", "Key skills match", "matched", "missing", "unconfirmed", "The JD mentions", "View full analysis", "Next steps", "Brag Sheet", "Save this JD", "Scored", "!Evidence", "!Salary offered"]),
    "12b-resources-built":  ("screen=jd&tab=resources&state=applied", 1800, ["Resources", "Tailored resume", "alex_morgan_resume_northwind.pdf", "Open PDF", "Copy file path", "2 pages", "KB", "Brag Sheet", "Open Brag Sheet", "Copy as text"]),
    "12c-resources-empty":  ("screen=jd&tab=resources&state=saved&nobrag=1", 1500, ["Tailored resume", "Not built yet", "Go to Next steps", "Not made yet"]),
    "12d-resources-unsaved": ("screen=jd&tab=resources", 1200, ["Save the JD first", "Tailored resume", "Brag Sheet"]),
    "12-details":           ("screen=jd&tab=details&state=saved", 3000, ["Job details", "Open the original posting", "JD highlights", "Required skills and qualifications", "Required", "Preferred", "Job description", "Read more", "Your match", "Full score, judged by Claude", "Skills overlap"]),
    "13-no-jd":             ("screen=jd&state=empty", 1000, ["No job description found", "Score pasted text", "Refresh"]),
    "14-helper-missing":    ("screen=jd&state=nohelper", 2100, ["Local helper not connected", "tools/jobd/install.py"]),
    "15-stale-profile":     ("screen=jd&state=stale", 2100, ["Skill profile is older than your master file", "Rebuild now"]),
    "16-resume-profile":    ("screen=resume&tab=profile&state=applied", 2400, ["Profile", "Skills", "Experience", "Master resume", "Last updated 22 Nov 2026", "Open as HTML", "Open as PDF", "Education and certifications", "Applications", "Open Applications", "Profile management", "Rebuild skill profile", "Rescore saved JDs", "How to change your profile", "Add a skill with its evidence", "add_skill.py", "Current job"]),
    "17-resume-skills":     ("screen=resume&tab=skills&state=applied", 3000, ["Frontend", "Backend", "Infra and delivery", "React", "on resume", "confirmed", "partial", "older resume only", "F-LM-01"]),
    "18-resume-skills-evidence": ("screen=resume&tab=skills&open=F-LM-01&state=applied", 3200, ["F-LM-01", "Led the Grammar Checker migration"]),
    "19-resume-experience": ("screen=resume&tab=experience&state=applied", 2600, ["Professional experience", "Lumenly", "Payly Financial", "Projects and achievements", "Awards"]),
    "20b-settings-any-length": ("screen=settings&state=applied&pages=any", 3200, ["Tailored resume length", "Any length"]),
    "20e-settings-photo-layout": ("screen=settings&state=applied&layout=photo", 3200, ["Tailored resume layout", "Basic", "Two column", "With photo", "Sidebar with a photo"]),
    "20f-settings-data-folder": ("screen=settings&state=applied", 3200, ["Your data folder", "Choose folder...", "the default: the engine folder", "Master resume", "found", "!Use the engine folder", '@aria-label="Open the data folder"']),
    "20g-settings-separate-data": ("screen=settings&state=applied&datafolder=separate", 3200, ["Your data folder", "this setting", "Use the engine folder", "Engine", "/Users/example/My Resume Data", "/Users/example/jd-lens", '@aria-label="Open the data folder"', '@aria-label="Open the engine folder"']),
    "20h-first-run-no-master": ("screen=jd&state=saved&nomaster=1", 3600, ["No master resume in your data folder yet", "Choose data folder"]),
    "20i-terminal-with-separate-data": ("screen=jd&state=saved&datafolder=separate", 3600, ["cd \"/Users/example/My Resume Data\"", "claude --add-dir \"/Users/example/jd-lens\" \"/job"]),
    "20j-settings-photo-card": ("screen=settings&state=applied", 3400, ["Profile photo", "Choose photo...", "No photo yet", "!Remove photo"]),
    "20k-settings-photo-set": ("screen=settings&state=applied&photo=1", 3400, ["Profile photo", "Change photo...", "Remove photo", "Photo in use"]),
    "20l-no-profile-helper-ok": ("screen=jd&state=saved&noprofile=1", 1400, ["No skill profile yet", "Build it now", "!python3 tools/build_profile.py", "!/path/to/jd-lens"]),
    "20m-no-profile-no-master": ("screen=jd&state=saved&nomaster=1&noprofile=1", 1400, ["No master resume in your data folder yet", "Choose data folder", "Scoring starts once your data folder has a master resume", "!No skill profile yet", "!Build it now"]),
    "20n-no-profile-no-helper": ("screen=jd&state=nohelper&noprofile=1", 1400, ["Finish setup", "python3 tools/setup.py", "Then reload this extension", "!Local helper not connected", "!/path/to/jd-lens"]),
    "20o-no-resume-tab-helper-ok": ("screen=resume&state=applied&noprofile=1", 1400, ["No skill profile yet", "Build it now"]),
    "20p-no-readable-resume": ("screen=resume&tab=experience&state=noresume", 1400, ["No readable resume yet", "Build it now", "!python3 tools/build_profile.py"]),
    "20-settings":          ("screen=settings&state=applied", 3200, ["Settings", "Scoring", "Scoring preferences", "Half credit", "How the score is calculated", "Tailored resume length", "1 page", "2 pages", "3 pages", "Any length", "Tailored resume layout", "Basic", "Two column", "With photo", "Your data folder", "Appearance", "Text size", "Open in a full tab", "Reading page", "Local helper", "connected", "Resume file", "Skill profile", "evidence entries", "Show what the extension holds"]),
    "21-large-text":        ("screen=jd&state=saved&scale=1.5", 3600, ["Northwind", "$60,000 - $100,000 USD", "A-", "A+"]),
    "22-max-text":          ("screen=jd&state=saved&scale=2", 4800, ["Northwind", "$60,000 - $100,000 USD"]),
    "23-narrow-overview":   ("screen=jd&state=applied&scale=2&mockwidth=320", 6600, ["Northwind", "$60,000 - $100,000 USD", "Details"]),
    "24-narrow-analysis":   ("screen=jd&tab=analysis&state=saved&scale=1.5&mockwidth=320", 9000, ["Profile overview", "Pro Tip", "!Next steps"]),
    "25-narrow-resume":     ("screen=resume&tab=skills&state=applied&scale=1.5&mockwidth=320", 5200, ["Frontend", "Backend"]),
}


# full-page Applications view: name -> (query, hash, window width, height, strings)
APP_SCREENS = {
    "30-apps-dashboard":  ("state=applied", "", 1200, 1500, ["Applications", "Total saved", "Considering", "Applied", "Screening", "Interviewing", "Offers", "Rejected", "Withdrawn", "Most recent activity", "Best match", "Date added", "Northwind", "Umbrella", "Globex", "Contoso", "Added 21 Nov 2026", "Applied 17 Oct 2026", "Keyword 50", "Match 86", "Select an application"]),
    "31-apps-detail":     ("state=applied", "globex-2026-10", 1200, 2300, ["Job information", "Posting date", "Files", "Resume submitted (PDF)", "Original job posting", "Full job details (HTML)", "Copy file path", "Gaps noted", "Interview rounds", "Recruiter call", "Technical interview", "Notes", "Add round", "Update status", "Status history", "Technical round booked", "Recruiter replied"]),
    "31b-apps-terminal-with-separate-data": ("state=applied&datafolder=separate", "globex-2026-10", 1200, 2300, ["cd \"/Users/example/My Resume Data\"", "claude --add-dir \"/Users/example/jd-lens\" \"/job status"]),
    "32-apps-interviewing": ("state=applied&filter=interviewing&sort=best", "", 1200, 1200, ["Globex", "Interviewing"]),
    "33-apps-narrow-list": ("state=applied", "", 700, 1700, ["Total saved", "Northwind", "Globex"]),
    "34-apps-narrow-detail": ("state=applied", "globex-2026-10", 700, 2900, ["All applications", "Job information", "Status history"]),
    "35-apps-no-helper":  ("state=nohelper", "", 1200, 1300, ["Local helper not connected", "read only", "tools/jobd/install.py", "Globex"]),
    "38-apps-danger-zone": ("state=applied", "globex-2026-10", 1200, 3400, ["Danger zone", "Delete this JD and all its data", "Delete JD and data"]),
    "39-apps-delete-confirm": ("state=applied&opendel=1", "globex-2026-10", 1200, 1400, ["Delete Globex", "and all its data?", "Application file (JD, scores, proposal, Brag Sheet)", "Tailored resume folder", "Brag Sheet page", "Nothing is erased", "Cancel", "Delete everything"]),
    "36-apps-empty":      ("state=empty-apps", "", 1200, 900, ["No applications yet"]),
    "37-apps-large-text": ("state=applied&scale=1.5", "globex-2026-10", 1200, 3600, ["Job information", "Status history"]),
}


def chrome(*args, timeout=90):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", *args], capture_output=True, text=True, timeout=timeout)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shots = "--shots" in sys.argv                                      # screenshots are for people (design review), not for the pass/fail checks
    only = [x for a in sys.argv if a.startswith("--only=") for x in a[7:].split(",") if x]          # --only=23,12b : just the screens whose name starts with one of these
    pick = lambda name: not only or any(name.startswith(o) for o in only)
    fails, ran = [], []
    for name, (q, height, must) in SCREENS.items():
        if not pick(name):
            continue
        ran.append(name)
        for theme in ("light", "dark"):
            url = f"file://{EXT}/panel.html?mock&theme={theme}&{q}"
            dom = chrome("--virtual-time-budget=6000", "--dump-dom", url).stdout
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", dom))
            err = re.findall(r'data-error="([^"]*)"', dom)
            if "data-ready" not in dom:
                fails.append(f"{name}/{theme}: page never rendered")
            if err:
                fails.append(f"{name}/{theme}: JS error: {err[0]}")
            for el in re.findall(r'data-clipped="([^"]+)"', dom):
                fails.append(f"{name}/{theme}: text is cut off: {el}")
            if 'data-overflow="true"' in dom:
                fails.append(f"{name}/{theme}: content overflows sideways")
            for s in must:
                if s.startswith("@"):
                    if s[1:] not in dom:
                        fails.append(f"{name}/{theme}: missing markup {s[1:]!r}")
                elif s.startswith("!"):
                    if s[1:] in text:
                        fails.append(f"{name}/{theme}: unexpected text {s[1:]!r}")
                elif s not in text:
                    fails.append(f"{name}/{theme}: missing text {s!r}")
            if shots:
                wrap = pathlib.Path(tempfile.mkdtemp()) / "frame.html"
                bg = "#141517" if theme == "dark" else "#f6f6f4"
                wrap.write_text(f'<!doctype html><body style="margin:0;background:{bg}"><iframe src="{url}" style="border:0;width:{WIDTH}px;height:{height}px"></iframe>')
                chrome("--virtual-time-budget=6000", f"--window-size={WIDTH + 120},{height}", f"--screenshot={OUT / (name + '-' + theme + '.png')}", f"file://{wrap}")
        print("ok  ", name)
    for name, (q, frag, width, height, must) in APP_SCREENS.items():
        if not pick(name):
            continue
        ran.append(name)
        for theme in ("light", "dark"):
            url = f"file://{EXT}/applications.html?mock&theme={theme}&{q}" + (f"#{frag}" if frag else "")
            dom = chrome("--virtual-time-budget=6000", f"--window-size={width},{height}", "--dump-dom", url).stdout
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", dom))
            if "data-ready" not in dom:
                fails.append(f"{name}/{theme}: page never rendered")
            for e in re.findall(r'data-error="([^"]*)"', dom):
                fails.append(f"{name}/{theme}: JS error: {e}")
            for el in re.findall(r'data-clipped="([^"]+)"', dom):
                fails.append(f"{name}/{theme}: text is cut off: {el}")
            if 'data-overflow="true"' in dom:
                fails.append(f"{name}/{theme}: content overflows sideways")
            for m in must:
                if m not in text:
                    fails.append(f"{name}/{theme}: missing text {m!r}")
            if shots:
                chrome("--virtual-time-budget=6000", f"--window-size={width},{height}", f"--screenshot={OUT / (name + '-' + theme + '.png')}", url)
        print("ok  ", name)
    if fails:
        print("\nFAILURES:"); [print(" -", f) for f in fails]; sys.exit(1)
    if not ran:
        print("no screen matched --only"); sys.exit(1)
    print(f"\nall {len(ran) * 2} renders passed" + (f"; screenshots in {OUT}" if shots else ""))


if __name__ == "__main__":
    main()
