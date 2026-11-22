#!/usr/bin/env python3
"""Extraction test with REAL Chrome (headless) on two fixture pages, then the full chain: extract -> score.
Skipped if Chrome or node is missing. Run: python3 -m unittest discover -s tools/tests -v
"""
import html, json, pathlib, re, shutil, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FIX = pathlib.Path(__file__).resolve().parent / "fixtures"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def extract(name):
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files", "--virtual-time-budget=3000", "--dump-dom", f"file://{FIX / name}"],
                       capture_output=True, text=True, timeout=90)
    m = re.search(r'data-out="([^"]*)"', r.stdout)
    assert m, "extractor did not run: " + r.stderr[-300:]
    return json.loads(html.unescape(m.group(1)))


@unittest.skipUnless(pathlib.Path(CHROME).exists() and shutil.which("node"), "needs Chrome and node")
class ExtractTest(unittest.TestCase):
    def test_jsonld_posting(self):
        d = extract("jsonld.html")
        self.assertEqual(d["extraction"], "jsonld")
        self.assertEqual((d["company"], d["role"], d["posted"]), ("Acme Corp", "Senior Backend Engineer", "2026-11-10"))
        self.assertIn("Remote", d["location_text"]); self.assertIn("India", d["location_text"]); self.assertIn("Bengaluru", d["location_text"])
        self.assertEqual(d["salary_text"], "INR 3,000,000 - 4,500,000 per year")
        self.assertIn("- Strong PostgreSQL and Redis", d["jd_text"])      # list items become bullet lines
        self.assertNotIn("Cookie", d["jd_text"])

    def test_plain_page_uses_main_text(self):
        d = extract("plain.html")
        self.assertEqual(d["extraction"], "main-text")
        self.assertEqual((d["company"], d["role"]), ("Globex", "Platform Engineer"))
        self.assertIn("6+ years", d["jd_text"])
        self.assertNotIn("Globex Careers | Menu", d["jd_text"])           # header outside <main> is left out
        self.assertNotIn("Cookie settings", d["jd_text"])

    def test_full_chain_extract_then_score(self):
        # build a profile from the sample master (made-up data) in a scratch copy, so the test needs no personal data
        work = pathlib.Path(tempfile.mkdtemp(prefix="extract-test-"))
        shutil.copytree(ROOT / "tools", work / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jobs"))
        (work / "master").mkdir()
        shutil.copy2(ROOT / "master" / "master-resume.template.md", work / "master" / "master-resume.md")
        subprocess.run([sys.executable, str(work / "tools" / "build_profile.py")], cwd=str(work), capture_output=True, check=True)
        profile = work / "tools" / "jd-capture-extension" / "data" / "profile.json"
        for name, lo, hi, must_have, must_miss in (("jsonld.html", 40, 100, ["TypeScript", "PostgreSQL", "AWS"], ["Terraform"]),
                                                  ("plain.html", 0, 60, ["AWS"], ["Terraform", "Python"])):
            rec = extract(name)
            tmp = pathlib.Path(tempfile.mkdtemp()) / "rec.json"
            tmp.write_text(json.dumps(rec))
            r = json.loads(subprocess.run(["node", str(ROOT / "tools/score_jd.mjs"), str(tmp), "--profile", str(profile)], capture_output=True, text=True, check=True).stdout)
            self.assertTrue(lo <= r["score"] <= hi, f"{name}: score {r['score']}")
            for t in must_have:
                self.assertIn(t, r["matched"] + r["partial"], f"{name}: {t}")
            for t in must_miss:
                self.assertIn(t, r["missing"] + r["unconfirmed"], f"{name}: {t}")
            if name == "jsonld.html":
                self.assertEqual(r["salary"]["text"], "INR 3,000,000 - 4,500,000 per year")
                self.assertEqual(r["flags"]["india"], "stated")
            else:
                self.assertEqual(r["salary"]["text"], "40-60 LPA")
                self.assertEqual(r["flags"]["india"], "stated")


if __name__ == "__main__":
    unittest.main()
