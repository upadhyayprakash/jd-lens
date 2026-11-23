#!/usr/bin/env python3
"""The contact block and file-name stem (tools/identity.py), the layout choice (prefs.py layout) and the three shipped layouts.
Runs on TEMPORARY copies; the real master resume and preferences are never read or written."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent


class IdentityTest(unittest.TestCase):
    def setUp(self):
        base = pathlib.Path(tempfile.mkdtemp(prefix="identity-test-")).resolve()
        self.base, self.engine, self.data = base, base / "engine", base / "my data"
        shutil.copytree(REAL / "tools", self.engine / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jd-*", "jobs", "*.log"))
        shutil.copytree(REAL / "tailored" / "_base", self.engine / "tailored" / "_base")
        (self.engine / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.engine / "master" / "master-resume.md")
        self.env = {k: v for k, v in os.environ.items() if k != "JD_LENS_DATA"}

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def tool(self, name, *args, env=None):
        r = subprocess.run([sys.executable, str(self.engine / "tools" / name), *args], capture_output=True, text=True, env=env or self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def test_the_sample_master_gives_a_contact_block_and_a_file_stem(self):
        d = self.tool("identity.py")
        self.assertEqual((d["name"], d["file_stem"], d["email"], d["phone"]), ("Anika Verma", "anika_verma", "anika.verma@example.com", "+1 (555) 010-0142"))
        for k in ("location", "portfolio", "linkedin", "github", "headline", "education"):
            self.assertTrue(d[k], k)

    def test_a_row_with_a_note_in_its_label_and_missing_rows(self):
        m = self.engine / "master" / "master-resume.md"
        t = m.read_text().replace("| Headline |", "| Headline (Oct 2026) |").replace("| Phone | +1 (555) 010-0142 |\n", "").replace("Anika Verma |\n| Location", "Zoë O'Brien-Lee |\n| Location")
        m.write_text(t)
        d = self.tool("identity.py")
        self.assertTrue(d["headline"].startswith("Senior Software Engineer"), "'Headline (Oct 2026)' is the headline row")
        self.assertEqual(d["phone"], "", "a missing row comes back empty, so a layout can leave the line out")
        self.assertEqual(d["file_stem"], "zo_o_brien_lee")

    def test_no_master_resume_gives_empty_values_and_a_safe_stem(self):
        (self.engine / "master" / "master-resume.md").unlink()
        d = self.tool("identity.py")
        self.assertEqual((d["name"], d["file_stem"]), ("", "resume"))

    # ---- which layout file a build starts from ----
    def test_layout_is_the_shipped_file_unless_the_data_folder_has_its_own(self):
        d = self.tool("prefs.py", "layout")
        self.assertEqual((d["layout"], d["yours"]), ("two-column", False))
        self.assertEqual(d["file"], str(self.engine / "tailored" / "_base" / "layouts" / "two-column.html"))
        self.tool("prefs.py", "set", "resume_layout", "photo")
        self.assertTrue(self.tool("prefs.py", "layout")["file"].endswith("layouts/photo.html"))
        # a data folder of its own, with its own copy of the layout: that one wins
        (self.data / "master").mkdir(parents=True)
        shutil.copy2(self.engine / "master" / "master-resume.md", self.data / "master" / "master-resume.md")
        env = dict(self.env, JD_LENS_DATA=str(self.data))
        self.assertEqual(self.tool("prefs.py", "layout", env=env)["yours"], False, "no layout of its own yet: the shipped one")
        mine = self.data / "tailored" / "_base" / "layouts"
        mine.mkdir(parents=True)
        (mine / "two-column.html").write_text("<html>mine</html>")
        self.tool("prefs.py", "set", "resume_layout", "two-column", env=env)
        d = self.tool("prefs.py", "layout", env=env)
        self.assertEqual((d["file"], d["yours"]), (str(mine / "two-column.html"), True))

    # ---- the shipped layouts carry the sample contact block the skill replaces ----
    def test_every_layout_has_the_sample_contact_values_from_the_sample_master(self):
        d = self.tool("identity.py")
        for name in ("basic", "two-column", "photo"):
            html = (REAL / "tailored" / "_base" / "layouts" / f"{name}.html").read_text()
            for k in ("name", "email", "phone", "github"):
                self.assertIn(d[k], html, f"{name} layout is missing the sample {k}: {d[k]!r}")


if __name__ == "__main__":
    unittest.main()
