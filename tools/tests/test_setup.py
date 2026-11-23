#!/usr/bin/env python3
"""Setup and the health check, as a brand-new user would meet them: a clean copy of the project with NO master resume, NO data,
NO helper. Runs on a TEMPORARY COPY; the real repo is never touched. Run: python3 -m unittest discover -s tools/tests"""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent


class FreshDownloadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="fresh-")).resolve()
        shutil.copytree(REAL / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jobs", "*.log", "jobd.config.json", "jobd-launcher.sh", "data"))
        (self.tmp / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master")     # what a download ships (no personal data)
        self.mdir = self.tmp / "hosts"
        self.mdir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def py(self, script, *args):
        return subprocess.run([sys.executable, str(self.tmp / "tools" / script), *args], capture_output=True, text=True, timeout=180)

    def doctor(self):
        r = self.py("doctor.py", "--json", "--manifest-dir", str(self.mdir))
        return r.returncode, {x["name"]: x for x in json.loads(r.stdout)}

    def test_fresh_setup_creates_everything_and_explains_the_manual_steps(self):
        r = self.py("setup.py", "--manifest-dir", str(self.mdir))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.tmp / "master" / "master-resume.md").exists())
        data = self.tmp / "tools" / "jd-capture-extension" / "data"
        for f in ("profile.json", "resume.json", "applications.json"):
            self.assertTrue((data / f).exists(), f)
        self.assertTrue((self.mdir / "com.jdlens.helper.json").exists())                      # helper installed into the (temporary) browser folder
        for text in ("Load unpacked", "replace the sample data", "docs/GETTING-STARTED.md"):
            self.assertIn(text, r.stdout)

    def test_setup_with_a_data_folder_keeps_the_data_there_and_the_doctor_agrees(self):
        data = self.tmp.parent / (self.tmp.name + "-my data")
        self.addCleanup(shutil.rmtree, data, ignore_errors=True)
        r = self.py("setup.py", "--manifest-dir", str(self.mdir), "--data-dir", str(data))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((data / "master" / "master-resume.md").exists(), "the sample master goes into the data folder")
        self.assertFalse((self.tmp / "master" / "master-resume.md").exists(), "and not into the engine folder")
        self.assertTrue((data / "applications").is_dir() and (data / "tailored").is_dir())
        prof = json.loads((self.tmp / "tools" / "jd-capture-extension" / "data" / "profile.json").read_text())
        self.assertEqual(prof["repo_path"], str(data))
        code, res = self.doctor()
        self.assertEqual(res["Data folder"]["level"], "ok", res)
        self.assertNotEqual(res["Master resume"]["level"], "fail", res)

    def test_setup_rejects_a_data_folder_without_a_path(self):
        r = self.py("setup.py", "--manifest-dir", str(self.mdir), "--data-dir", "relative/folder")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("full path", r.stdout)

    def test_setup_never_overwrites_your_master_resume(self):
        self.py("setup.py", "--no-helper")
        m = self.tmp / "master" / "master-resume.md"
        m.write_text(m.read_text() + "\n<!-- MY OWN EDIT -->\n")
        r = self.py("setup.py", "--no-helper")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("MY OWN EDIT", m.read_text())
        self.assertIn("already exists", r.stdout)

    def test_doctor_on_a_fresh_setup_has_no_blockers_and_says_what_to_do(self):
        self.py("setup.py", "--no-helper")
        code, d = self.doctor()
        self.assertEqual(code, 0, d)
        self.assertEqual(d["Master resume"]["level"], "warn")                              # still the example template
        self.assertIn("example template", d["Master resume"]["detail"])
        self.assertEqual(d["Local helper"]["level"], "warn")
        self.assertIn("install.py", d["Local helper"]["fix"])
        self.assertEqual(d["Skill profile"]["level"], "ok")

    def test_doctor_after_helper_install_is_green_for_the_helper(self):
        self.py("setup.py", "--manifest-dir", str(self.mdir))
        _, d = self.doctor()
        self.assertEqual(d["Local helper"]["level"], "ok", d["Local helper"])

    def test_doctor_flags_a_moved_project_folder(self):
        self.py("setup.py", "--manifest-dir", str(self.mdir))
        mf = self.mdir / "com.jdlens.helper.json"
        data = json.loads(mf.read_text()); data["path"] = "/nowhere/jobd-launcher.sh"; mf.write_text(json.dumps(data))
        _, d = self.doctor()
        self.assertEqual(d["Local helper"]["level"], "warn")
        self.assertIn("project folder", d["Local helper"]["detail"])

    def test_doctor_fails_without_a_master_resume_and_on_a_broken_one(self):
        code, d = self.doctor()
        self.assertEqual(code, 1)
        self.assertEqual(d["Master resume"]["level"], "fail")
        self.assertIn("setup.py", d["Master resume"]["fix"])
        m = self.tmp / "master" / "master-resume.md"
        shutil.copy2(self.tmp / "master" / "master-resume.template.md", m)
        m.write_text(m.read_text().replace("## 5. Skills inventory", "## 5. Something else"))
        code, d = self.doctor()
        self.assertEqual(code, 1)
        self.assertEqual(d["Master resume"]["level"], "fail")
        self.assertIn("template", d["Master resume"]["fix"])

    def test_the_template_scores_a_job_description(self):
        if not shutil.which("node"):
            self.skipTest("needs node")
        self.py("setup.py", "--no-helper")
        jd = self.tmp / "jd.txt"
        jd.write_text("Requirements\n- 5+ years of React and TypeScript\n- Node.js and PostgreSQL\nNice to have\n- Terraform\n")
        r = subprocess.run(["node", str(self.tmp / "tools" / "score_jd.mjs"), str(jd), "--profile", str(self.tmp / "tools/jd-capture-extension/data/profile.json")],
                           capture_output=True, text=True, timeout=60)
        res = json.loads(r.stdout)
        self.assertGreater(res["score"], 60)
        self.assertIn("Terraform", res["missing"])


if __name__ == "__main__":
    unittest.main()
