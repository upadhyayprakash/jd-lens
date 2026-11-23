#!/usr/bin/env python3
"""tools/add_skill.py: add a skill with evidence to the master resume. Runs on a TEMPORARY COPY, never your real master file.
Run: python3 -m unittest discover -s tools/tests"""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent
FACT = "Used Python for ETL scripts and data analysis at Example Corp (2019 to 2020)"


class AddSkillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="addskill-")).resolve()
        shutil.copytree(REAL / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jobs", "*.log", "jobd.config.json", "data"))
        (self.tmp / "tools/jd-capture-extension/data").mkdir(parents=True, exist_ok=True)
        (self.tmp / "master").mkdir()
        (self.tmp / "applications").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master" / "master-resume.md")
        self.master = self.tmp / "master" / "master-resume.md"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *args):
        return subprocess.run([sys.executable, str(self.tmp / "tools" / "add_skill.py"), *args], capture_output=True, text=True, timeout=120)

    def profile(self):
        return json.loads((self.tmp / "tools/jd-capture-extension/data/profile.json").read_text())

    def groups(self):
        import re
        return re.findall(r"^### (.+)$", self.master.read_text().split("## 5.")[1].split("## 6.")[0], re.M)

    def test_the_file_structure_stays_intact(self):
        """Regression: a new row once swallowed the next group's heading, silently deleting that group."""
        before = self.groups()
        self.add("Python", "--group", "Backend", "--fact", FACT)
        self.add("Pandas", "--group", "Data", "--fact", "Used Pandas to clean and join the weekly billing exports at Example Corp")
        self.add("Vitest", "--group", "Frontend", "--fact", "Wrote the Vitest unit tests for the checkout widgets at Example Corp")
        self.assertEqual(self.groups(), before)
        t = self.master.read_text()
        for line in t.splitlines():
            if line.startswith("|") and "###" in line:
                self.fail("a heading got glued onto a table row: " + line)
        for g in before:
            self.assertIn(f"\n### {g}\n", t)
        import re
        skills = t.split("## 5.")[1].split("## 6.")[0]
        for table in re.findall(r"(?:^\|.*\|[ \t]*\n)+", skills, re.M):           # every skills row still has 5 cells
            for row in table.strip().splitlines():
                if not set(row) <= set("|-: "):
                    self.assertEqual(len(row.strip().strip("|").split("|")), 5, row)

    def test_adds_fact_row_backup_and_rebuilds_the_profile(self):
        r = self.add("Python", "--group", "Backend", "--fact", FACT, "--years", "2019 to 2020")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t = self.master.read_text()
        self.assertIn(f"- **F-USR-01** {FACT}", t)
        self.assertIn("| Python | user-confirmed | F-USR-01 | 2019 to 2020 |", t)
        self.assertLess(t.index("F-USR-01"), t.index("## 4."))                              # the fact sits in section 3
        self.assertTrue(list((self.tmp / "master" / ".history").glob("master-resume-*.md")))
        rows = {x["skills"]: x for x in self.profile()["rows"]}
        self.assertEqual(rows["Python"]["level"], "user-confirmed")
        self.assertEqual(rows["Python"]["evidence"], ["F-USR-01"])
        rd = json.loads((self.tmp / "tools/jd-capture-extension/data/resume.json").read_text())
        self.assertIn("F-USR-01", rd["facts"])

    def test_second_skill_gets_the_next_id_and_the_table_stays_valid(self):
        self.add("Python", "--group", "Backend", "--fact", FACT)
        r = self.add("Terraform", "--group", "Infra and delivery", "--fact", "Wrote the Terraform modules for the staging environment at Example Corp", "--level", "listed")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t = self.master.read_text()
        self.assertIn("**F-USR-02**", t)
        self.assertIn("| Terraform | listed | F-USR-02 |", t)
        self.assertEqual(sum(1 for x in self.profile()["rows"] if x["skills"] in ("Python", "Terraform")), 2)

    def test_existing_skill_is_upgraded_not_duplicated(self):
        self.assertIn("| Go | earlier |", self.master.read_text())          # the sample master already lists Go as an older-resume-only skill
        r = self.add("Go", "--fact", "Wrote the Go microservice for order validation at Northwind Labs in 2021")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("raised 'Go' from earlier to user-confirmed", r.stdout)
        t = self.master.read_text()
        self.assertEqual(t.count("| Go |"), 1)
        self.assertIn("| Go | user-confirmed | F-USR-01 |", t)

    def test_every_edit_keeps_its_own_backup_even_within_one_second(self):
        original = self.master.read_text()
        self.add("Python", "--group", "Backend", "--fact", FACT)
        self.add("Terraform", "--group", "Infra and delivery", "--fact", "Wrote the Terraform modules for the staging environment at Example Corp")
        backups = sorted((self.tmp / "master" / ".history").glob("master-resume-*.md"))
        self.assertEqual(len(backups), 2)
        self.assertIn(original, [b.read_text() for b in backups])                           # the untouched original is recoverable

    def test_refuses_bad_input_and_leaves_the_file_alone(self):
        before = self.master.read_text()
        for args in (("Python", "--group", "Backend", "--fact", "too short"),                       # no real evidence
                     ("Python", "--group", "Nope", "--fact", FACT),                                  # unknown group
                     ("Python", "--fact", FACT),                                                     # group missing for a new skill
                     ("Py|thon", "--group", "Backend", "--fact", FACT)):                             # would break the table
            r = self.add(*args)
            self.assertEqual(r.returncode, 1, args)
            self.assertIn("error:", r.stderr)
        self.assertEqual(self.master.read_text(), before)
        self.assertFalse((self.tmp / "master" / ".history").exists())

    def test_multi_skill_rows_are_not_guessed_at(self):
        self.master.write_text(self.master.read_text().replace("| Jest | listed |", "| Mocha, Chai | listed |"))
        r = self.add("Chai", "--fact", "Wrote the Chai assertions for the billing API at Example Corp")
        self.assertEqual(r.returncode, 1)
        self.assertIn("listed together", r.stderr)

    def test_dry_run_writes_nothing(self):
        before = self.master.read_text()
        r = self.add("Python", "--group", "Backend", "--fact", FACT, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("dry run", r.stdout)
        self.assertEqual(self.master.read_text(), before)

    def test_adding_python_changes_a_real_score(self):
        if not shutil.which("node"):
            self.skipTest("needs node")
        jd = self.tmp / "jd.txt"
        jd.write_text("Requirements\n- Strong Python and Pandas\n")
        score = lambda: json.loads(subprocess.run(["node", str(self.tmp / "tools/score_jd.mjs"), str(jd), "--profile", str(self.tmp / "tools/jd-capture-extension/data/profile.json")], capture_output=True, text=True).stdout)
        subprocess.run([sys.executable, str(self.tmp / "tools/build_profile.py")], capture_output=True)
        before = score()
        self.assertIn("Python", before["missing"])
        self.add("Python", "--group", "Backend", "--fact", FACT)
        after = score()
        self.assertIn("Python", after["matched"])
        self.assertIn("Pandas", after["missing"])                                                    # Pandas is a separate skill: still a gap
        self.assertGreater(after["score"], before["score"])
        self.add("Pandas", "--group", "Data", "--fact", "Used Pandas to clean and join the weekly billing exports at Example Corp")
        self.assertEqual(score()["score"], 100)


if __name__ == "__main__":
    unittest.main()
