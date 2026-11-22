#!/usr/bin/env python3
"""tools/score_app.py: one command that refreshes the profile, runs the shared scorer and saves quick_score.
Runs on a TEMPORARY COPY of the repo pieces, never the real applications. Needs node. Run: python3 -m unittest discover -s tools/tests"""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent


@unittest.skipUnless(shutil.which("node"), "needs node")
class ScoreAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="score-app-")).resolve()
        shutil.copytree(REAL / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jobs", "*.log", "jobd.config.json"))
        shutil.copytree(REAL / "tools" / "tests" / "fixtures" / "applications", self.tmp / "applications")
        (self.tmp / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master" / "master-resume.md")   # the sample master (made-up data)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_app(self, *args):
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / "score_app.py"), *args], capture_output=True, text=True, timeout=120)
        return r.returncode, json.loads(r.stdout)

    def test_scores_and_saves_quick_score(self):
        code, d = self.run_app("northwind-2026-11")
        self.assertEqual(code, 0, d)
        self.assertTrue(d["ok"] and d["quick_score_saved"])
        self.assertGreaterEqual(d["keyword_score"], 80)
        self.assertIn("Express", d["matched"])
        self.assertIn("Vite", d["missing"])
        self.assertTrue(any("Vite (not in master)" in g["terms"] for g in d["gaps"]), d["gaps"])   # an unmet requirement is listed with why
        self.assertNotIn("units", d); self.assertNotIn("requirements", d)
        listing = json.loads(subprocess.run([sys.executable, str(self.tmp / "tools" / "jobs.py"), "list"], capture_output=True, text=True).stdout)
        self.assertEqual({a["slug"]: a["quick_score"] for a in listing["applications"]}["northwind-2026-11"], d["keyword_score"])

    def test_rebuilds_a_stale_profile_itself(self):
        subprocess.run([sys.executable, str(self.tmp / "tools" / "build_profile.py")], capture_output=True)
        m = self.tmp / "master" / "master-resume.md"
        m.write_text(m.read_text().replace("| Kafka | user-confirmed |", "| Kafka | none |"))              # master changed after the profile was built
        code, d = self.run_app("globex-2026-10")
        self.assertEqual(code, 0, d)
        check = subprocess.run([sys.executable, str(self.tmp / "tools" / "build_profile.py"), "--check"], capture_output=True)
        self.assertEqual(check.returncode, 0)

    def test_rejects_bad_input(self):
        for arg in ("../x", "Northwind 2026", "nope-2026-01"):
            code, d = self.run_app(arg)
            self.assertEqual(code, 1); self.assertFalse(d["ok"])
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / "score_app.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
