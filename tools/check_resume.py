#!/usr/bin/env python3
"""Check a finished resume PDF: page count, JD keyword coverage, em dashes, forbidden terms.

Usage:
  tools/check_resume.py resume.pdf --keywords "TypeScript,React,Next.js" [--forbid "term1,term2"] [--pages N|any]

--pages defaults to the "resume_pages" setting (tools/prefs.py, default 2); "any" skips the page check.
Exit code 1 if the page count is wrong, an em dash is present, or a forbidden term is found.
Keyword matching is case-insensitive on whole tokens (so "rest" does not match "forest").
"""
import argparse, pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import prefs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--keywords", default="", help="comma-separated JD keywords")
    ap.add_argument("--forbid", default="", help="comma-separated terms that must not appear")
    ap.add_argument("--pages", default=None, help="expected page count, or 'any'; default: the resume_pages setting")
    a = ap.parse_args()

    info = subprocess.run(["pdfinfo", a.pdf], capture_output=True, text=True, check=True).stdout
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    text = subprocess.run(["pdftotext", "-layout", a.pdf, "-"], capture_output=True, text=True, check=True).stdout
    low = text.lower()
    ok = True

    want = prefs.pages_target() if a.pages is None else (None if str(a.pages).lower() == "any" else int(a.pages))
    print(f"pages: {pages} (target: {'any' if want is None else want})")
    if want is not None and pages != want:
        ok = False
        print("  FAIL: wrong page count")
    print(f"words extracted: {len(text.split())} (0 would mean an unreadable PDF)")
    if "\u2014" in text:
        ok = False
        print("em dash: FOUND (fail)")
    else:
        print("em dash: none")

    def has(term):
        t = term.strip().lower()
        return re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", low) is not None

    kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
    if kws:
        hit = [k for k in kws if has(k)]
        miss = [k for k in kws if not has(k)]
        pct = round(100 * len(hit) / len(kws))
        print(f"keywords: {len(hit)} of {len(kws)} ({pct}%)")
        print("  missing: " + (", ".join(miss) if miss else "none"))

    for f in [x.strip() for x in a.forbid.split(",") if x.strip()]:
        if has(f):
            ok = False
            print(f"forbidden term present: {f} (fail)")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
