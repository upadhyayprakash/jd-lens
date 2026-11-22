#!/usr/bin/env python3
"""The resume page-count setting (tools/prefs.py): default, validation, persistence, and what check_resume and the headless
prompt do with it. Runs on a temporary copy of tools/ so the real master/preferences.json is never touched."""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent


class PrefsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="prefs-test-")).resolve()
        shutil.copytree(REAL / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jd-*", "jobs"))
        (self.tmp / "master").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_prefs(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / "prefs.py"), *args], capture_output=True, text=True)
        d = json.loads(r.stdout)
        self.assertEqual(d["ok"], ok, r.stdout + r.stderr)
        return d

    def test_default_is_two_pages(self):
        self.assertEqual(self.run_prefs("get", "resume_pages")["value"], 2)

    def test_set_and_persist(self):
        for v, want in (("1", 1), ("3", 3), ("any", "any"), ("2", 2)):
            self.assertEqual(self.run_prefs("set", "resume_pages", v)["prefs"]["resume_pages"], want)
            self.assertEqual(self.run_prefs("get", "resume_pages")["value"], want)
        self.assertTrue((self.tmp / "master" / "preferences.json").exists())

    def test_rejects_bad_values(self):
        self.run_prefs("set", "resume_pages", "7", ok=False)
        self.run_prefs("set", "resume_pages", "lots", ok=False)
        self.run_prefs("set", "nonsense", "1", ok=False)

    def test_a_corrupt_file_falls_back_to_the_default(self):
        (self.tmp / "master" / "preferences.json").write_text('{"resume_pages": "banana"}')
        self.assertEqual(self.run_prefs("get", "resume_pages")["value"], 2)

    def test_prompt_phrase_and_check_target(self):
        sys.path.insert(0, str(self.tmp / "tools"))
        for m in ("prefs", "check_resume"):
            sys.modules.pop(m, None)
        import prefs
        self.assertEqual((prefs.pages_target(), prefs.pages_phrase()), (2, "2 pages"))
        prefs.set_pref("resume_pages", 1)
        self.assertEqual((prefs.pages_target(), prefs.pages_phrase()), (1, "1 page"))
        prefs.set_pref("resume_pages", "any")
        self.assertIsNone(prefs.pages_target())
        self.assertIn("no page target", prefs.pages_phrase())
        sys.path.remove(str(self.tmp / "tools")); sys.modules.pop("prefs", None)


if __name__ == "__main__":
    unittest.main()
