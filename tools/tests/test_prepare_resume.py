#!/usr/bin/env python3
"""tools/prepare_resume.py: the tailored resume starts as the chosen layout with the real contact block and photo. Runs on a TEMPORARY
engine copy and a TEMPORARY data folder; nothing real is read or written."""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent
SLUG = "northwind-2026-11"
LAYOUTS = ("basic", "two-column", "photo")


class PrepareResumeTest(unittest.TestCase):
    def setUp(self):
        base = pathlib.Path(tempfile.mkdtemp(prefix="prep-test-")).resolve()
        self.base, self.engine, self.data = base, base / "engine", base / "my data"
        shutil.copytree(REAL / "tools", self.engine / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jd-*", "jobs", "*.log"))
        shutil.copytree(REAL / "tailored" / "_base", self.engine / "tailored" / "_base")
        (self.engine / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.engine / "master" / "master-resume.template.md")
        (self.data / "master").mkdir(parents=True)
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.data / "master" / "master-resume.md")
        (self.data / "applications").mkdir()
        shutil.copy2(REAL / "tools" / "tests" / "fixtures" / "applications" / f"{SLUG}.md", self.data / "applications")
        self.env = dict({k: v for k, v in os.environ.items() if k != "JD_LENS_DATA"}, JD_LENS_DATA=str(self.data))
        self.master = self.data / "master" / "master-resume.md"

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def tool(self, name, *args, ok=True):
        r = subprocess.run([sys.executable, str(self.engine / "tools" / name), *args], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def prep(self, *args, ok=True):
        return self.tool("prepare_resume.py", SLUG, *args, ok=ok)

    def edit_master(self, **rows):
        t = self.master.read_text()
        for label, value in rows.items():
            t, n = re.subn(rf"(\| {label} \| ).*?( \|)", rf"\g<1>{value}\g<2>", t, count=1)
            self.assertEqual(n, 1, label)
        self.master.write_text(t)

    def test_every_layout_gets_the_file_name_and_the_real_contact_block(self):
        self.edit_master(Name="Jordan Reyes", Email="jordan.reyes@example.org", Phone="+1 (555) 010-0177")
        for layout in LAYOUTS:
            self.tool("prefs.py", "set", "resume_layout", layout)
            r = self.prep("--force")
            f = pathlib.Path(r["file"])
            self.assertEqual(f, self.data / "tailored" / SLUG / "jordan_reyes_resume_northwind.html", layout)
            text = f.read_text()
            for new in ("Jordan Reyes", "jordan.reyes@example.org", "+1 (555) 010-0177"):
                self.assertIn(new, text, f"{layout}: {new}")
            for old in ("Anika Verma", "anika.verma@example.com", "010-0142"):
                self.assertNotIn(old, text, f"{layout}: {old}")
            self.assertEqual(r["sample_values_left"], [], layout)
            self.assertFalse((self.engine / "tailored" / SLUG).exists(), "nothing is written into the engine folder")

    def test_the_sample_master_gives_the_layout_unchanged_apart_from_nothing(self):
        r = self.prep()
        self.assertTrue(r["created"] and r["filled"] == [], r)
        self.assertEqual(pathlib.Path(r["file"]).name, "anika_verma_resume_northwind.html")
        self.assertEqual(pathlib.Path(r["file"]).read_text(), (self.engine / "tailored" / "_base" / "layouts" / "two-column.html").read_text())

    def test_a_row_left_empty_leaves_the_line_out_without_stray_separators(self):
        self.edit_master(Phone="")
        for layout in LAYOUTS:
            self.tool("prefs.py", "set", "resume_layout", layout)
            r = self.prep("--force")
            text = pathlib.Path(r["file"]).read_text()
            self.assertNotIn("010-0142", text, layout)
            self.assertIn("phone", r["left_out"], layout)
            self.assertNotRegex(text, r"\|\s*\|", f"{layout}: a stray separator is left")
            self.assertNotIn("<dt>Phone</dt>", text, layout)

    def test_photo_is_linked_only_when_there_is_one_and_the_layout_has_a_frame(self):
        self.tool("prefs.py", "set", "resume_layout", "photo")
        self.assertFalse(self.prep("--force")["photo_linked"])
        self.assertIn('src="data:image/svg+xml', pathlib.Path(self.prep("--force")["file"]).read_text(), "no photo: the generic avatar stays")
        (self.data / "master" / "photo.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        r = self.prep("--force")
        self.assertTrue(r["photo_linked"])
        text = pathlib.Path(r["file"]).read_text()
        self.assertIn('<img src="../../master/photo.jpg" alt="Profile photo">', text)
        self.assertNotIn("data:image/svg+xml", text)
        self.tool("prefs.py", "set", "resume_layout", "two-column")
        self.assertFalse(self.prep("--force")["photo_linked"], "a layout without a photo frame links nothing")

    def test_an_existing_file_is_kept_unless_forced(self):
        r = self.prep()
        f = pathlib.Path(r["file"]); f.write_text("<html>my edits</html>")
        again = self.prep()
        self.assertFalse(again["created"])
        self.assertEqual(f.read_text(), "<html>my edits</html>")
        self.assertTrue(self.prep("--force")["created"])
        self.assertNotIn("my edits", f.read_text())

    def test_a_layout_of_your_own_in_the_data_folder_wins(self):
        mine = self.data / "tailored" / "_base" / "layouts"; mine.mkdir(parents=True)
        (mine / "two-column.html").write_text("<html><body>my own layout for Anika Verma</body></html>")
        self.edit_master(Name="Jordan Reyes")
        r = self.prep()
        self.assertEqual(r["layout_file"], str(mine / "two-column.html"))
        self.assertEqual(pathlib.Path(r["file"]).read_text(), "<html><body>my own layout for Jordan Reyes</body></html>")

    def test_bad_slug_missing_application_and_missing_name(self):
        self.assertIn("invalid slug", self.tool("prepare_resume.py", "../x", ok=False)["error"])
        self.assertIn("no such application", self.tool("prepare_resume.py", "nope-2026-01", ok=False)["error"])
        t = self.master.read_text().replace("| Name | Anika Verma |\n", "")
        self.master.write_text(t)
        self.assertIn("no Name row", self.prep(ok=False)["error"])


if __name__ == "__main__":
    unittest.main()
