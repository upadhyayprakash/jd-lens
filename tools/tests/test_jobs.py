#!/usr/bin/env python3
"""Tests for tools/jobs.py. Every test runs on a TEMPORARY COPY of the repo pieces
(tools/, applications/, master/), so the real application files are never written.
Run: python3 -m unittest discover -s tools/tests -v
"""
import json, pathlib, shutil, subprocess, sys, tempfile, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent


class JobsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="jobs-test-"))
        shutil.copytree(REAL / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jd-*"))
        shutil.copytree(REAL / "tools" / "tests" / "fixtures" / "applications", self.tmp / "applications")  # frozen fixtures, not the live folder
        (self.tmp / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master" / "master-resume.md")   # the sample master (made-up data)
        self.apps = self.tmp / "applications"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_job(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(self.tmp / "tools" / "jobs.py"), *args], capture_output=True, text=True)
        data = json.loads(r.stdout)
        self.assertEqual(data["ok"], ok, msg=r.stdout + r.stderr)
        self.assertEqual(r.returncode, 0 if ok else 1)
        return data

    def test_delete_full_wipe_moves_everything_to_trash(self):
        """Full wipe of one JD: dry run lists it, the real run moves (never erases) the file, backups, tailored folder, brag page and
        capture into .trash/, and leaves a similarly named application alone."""
        (self.apps / ".history").mkdir(exist_ok=True)
        slug, other = "northwind-2026-11", "northwind-2026-11-2"
        shutil.copy2(self.apps / f"{slug}.md", self.apps / f"{other}.md")
        (self.apps / ".history" / f"{slug}-20261122-010101-123456.md").write_text("old")
        (self.apps / ".history" / f"{other}-20261122-010101-123456.md").write_text("other's backup")
        for rel in (f"tailored/{slug}/resume.html", f"views/brag/{slug}.html", f"job-inbox/done/{slug}.json", f"tailored/{other}/r.html"):
            f = self.tmp / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_text("x")
        d = self.run_job("delete", slug, "--dry-run")
        self.assertTrue(d["dry_run"]); self.assertEqual(len(d["items"]), 5)
        self.assertTrue((self.apps / f"{slug}.md").exists(), "a dry run must not move anything")
        d = self.run_job("delete", slug)
        self.assertFalse((self.apps / f"{slug}.md").exists())
        self.assertFalse((self.tmp / "tailored" / slug).exists())
        self.assertFalse((self.tmp / "views" / "brag" / f"{slug}.html").exists())
        self.assertFalse((self.tmp / "job-inbox" / "done" / f"{slug}.json").exists())
        self.assertFalse((self.apps / ".history" / f"{slug}-20261122-010101-123456.md").exists())
        trash = self.tmp / d["trash"]
        self.assertTrue((trash / "applications" / f"{slug}.md").exists(), "the file must be recoverable from .trash/")
        self.assertTrue((trash / "tailored" / slug / "resume.html").exists())
        self.assertTrue((self.apps / f"{other}.md").exists() and (self.tmp / "tailored" / other / "r.html").exists())
        self.assertTrue((self.apps / ".history" / f"{other}-20261122-010101-123456.md").exists())
        self.run_job("show", slug, ok=False)

    def test_delete_rejects_bad_or_missing_slug(self):
        self.run_job("delete", "../etc", ok=False)
        self.run_job("delete", "nope-2026-01", ok=False)

    def test_resume_info_reports_pages_and_size(self):
        """The Resources tab shows how many pages the tailored PDF has (pdfinfo if present, else a count of page objects)."""
        pdf = self.tmp / "tailored" / "northwind-2026-11" / "r.pdf"
        pdf.parent.mkdir(parents=True)
        pdf.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Pages/Count 2>>endobj\n2 0 obj<</Type/Page>>endobj\n3 0 obj<</Type /Page>>endobj\n")
        self.run_job("set", "northwind-2026-11", "resume", "tailored/northwind-2026-11/r.pdf")
        d = self.run_job("resume-info", "northwind-2026-11")
        self.assertTrue(d["found"]); self.assertEqual(d["pages"], 2); self.assertGreater(d["bytes"], 20)
        self.run_job("set", "northwind-2026-11", "resume", "")
        self.assertFalse(self.run_job("resume-info", "northwind-2026-11")["found"])

    def test_list_sorted_by_score(self):
        d = self.run_job("list")
        self.assertEqual(d["applications"][0]["slug"], "northwind-2026-11")
        self.assertEqual(d["applications"][0]["fit_score"], 86)
        self.assertEqual(len(d["applications"]), 3)

    def test_list_filter(self):
        self.assertEqual(len(self.run_job("list", "--status", "considering")["applications"]), 0)
        self.assertEqual(len(self.run_job("list", "--status", "applied")["applications"]), 3)

    def test_show(self):
        a = self.run_job("show", "northwind-2026-11")["application"]
        self.assertEqual(a["company"], "Northwind")
        self.assertTrue(a["resume_exists"] or a["resume"])  # tailored/ is not copied; path is still reported
        self.assertIn("Rounds", a["sections"])

    def test_status_keeps_comment_and_makes_backup(self):
        before = (self.apps / "northwind-2026-11.md").read_text()
        d = self.run_job("status", "northwind-2026-11", "screening")
        self.assertEqual(d["status"], {"from": "applied", "to": "screening"})
        after = (self.apps / "northwind-2026-11.md").read_text()
        self.assertIn("status: screening", after)
        self.assertIn("# considering | applied", after)  # the comment survived
        backups = list((self.apps / ".history").glob("northwind-2026-11-*.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), before)  # backup is the exact old file

    def test_status_applied_sets_date_when_blank(self):
        shutil.copy2(self.apps / "northwind-2026-11.md", self.apps / "acme-2026-11.md")
        txt = (self.apps / "acme-2026-11.md").read_text().replace("applied: 2026-11-21", "applied:").replace("status: applied", "status: considering")
        (self.apps / "acme-2026-11.md").write_text(txt)
        self.run_job("status", "acme-2026-11", "applied", "--date", "2026-12-01")
        self.assertIn("applied: 2026-12-01", (self.apps / "acme-2026-11.md").read_text())

    def test_rejects_bad_status_slug_and_traversal(self):
        self.run_job("status", "northwind-2026-11", "hired", ok=False)
        self.run_job("show", "../master/master-resume", ok=False)
        self.run_job("show", "Northwind 2026", ok=False)
        self.run_job("show", "nope-2026-01", ok=False)

    def test_round_appends_row_and_escapes_pipes(self):
        self.run_job("round", "northwind-2026-11", "--round", "Recruiter call", "--date", "2026-12-02", "--notes", "a | b", "--result", "advanced")
        txt = (self.apps / "northwind-2026-11.md").read_text()
        self.assertIn("| 2026-12-02 | Recruiter call |  | a / b | advanced |", txt)
        rounds = self.run_job("show", "northwind-2026-11")["application"]["rounds"]
        self.assertEqual(rounds[0][1], "Recruiter call")
        self.run_job("round", "northwind-2026-11", "--round", "Tech 1", "--date", "2026-12-05")
        self.assertEqual(len(self.run_job("show", "northwind-2026-11")["application"]["rounds"]), 2)

    def test_set_validates(self):
        self.run_job("set", "northwind-2026-11", "fit_score", "90")
        self.assertIn("fit_score: 90", (self.apps / "northwind-2026-11.md").read_text())
        self.run_job("set", "northwind-2026-11", "fit_score", "150", ok=False)
        self.run_job("set", "northwind-2026-11", "status", "offer", ok=False)       # not settable here
        self.run_job("set", "northwind-2026-11", "resume", "../../etc/passwd", ok=False)
        self.run_job("set", "northwind-2026-11", "resume", "/etc/passwd", ok=False)

    def test_save_jd_creates_and_refuses_duplicate(self):
        rec = {"company": "Acme Corp", "role": "Senior Engineer", "url": "https://acme.example/jobs/1",
               "captured_at": "2026-12-03T10:00:00+05:30", "location_text": "Remote, India", "salary_text": "$50k - $70k",
               "posted": "2026-12-01", "extraction": "jsonld", "jd_text": "Build things.\nWith TypeScript.",
               "quick_score": {"score": 77}}
        f = self.tmp / "rec.json"
        f.write_text(json.dumps(rec))
        d = self.run_job("save-jd", str(f))
        self.assertEqual(d["slug"], "acme-corp-2026-12")
        txt = (self.apps / "acme-corp-2026-12.md").read_text()
        self.assertIn("status: considering", txt)
        self.assertIn("quick_score: 77", txt)
        self.assertIn("Build things.", txt)
        self.assertEqual(self.run_job("show", "acme-corp-2026-12")["application"]["company"], "Acme Corp")
        self.run_job("save-jd", str(f), ok=False)  # duplicate refused

    def test_save_jd_rejects_incomplete_record(self):
        f = self.tmp / "bad.json"
        f.write_text(json.dumps({"company": "X", "role": "Y", "url": "https://x"}))
        self.run_job("save-jd", str(f), ok=False)

    def test_status_history_is_appended_never_rewritten(self):
        self.run_job("status", "northwind-2026-11", "screening", "--note", "Recruiter replied")
        a = self.run_job("show", "northwind-2026-11")["application"]
        self.assertEqual([h[1:3] for h in a["history"]], [["-", "applied"], ["applied", "screening"]])  # first row records the starting state
        self.assertEqual(a["history"][1][3], "Recruiter replied")
        self.run_job("status", "northwind-2026-11", "interviewing")
        h = self.run_job("show", "northwind-2026-11")["application"]["history"]
        self.assertEqual([x[2] for x in h], ["applied", "screening", "interviewing"])
        self.assertEqual(h[0], a["history"][0])                      # old rows untouched
        self.run_job("status", "northwind-2026-11", "interviewing")       # same status again: no new event
        self.assertEqual(len(self.run_job("show", "northwind-2026-11")["application"]["history"]), 3)

    def test_new_summary_fields(self):
        d = {a["slug"]: a for a in self.run_job("list")["applications"]}
        self.assertEqual(d["northwind-2026-11"]["added"], "2026-11-21")
        self.assertIn("India", d["northwind-2026-11"]["location"])
        self.assertEqual(d["northwind-2026-11"]["last_activity"], "2026-11-21")
        self.run_job("round", "northwind-2026-11", "--round", "Screen", "--date", "2026-12-09", "--notes", "Went well")
        self.assertEqual({a["slug"]: a for a in self.run_job("list")["applications"]}["northwind-2026-11"]["last_activity"], "2026-12-09")

    def test_quick_score_settable(self):
        self.run_job("set", "northwind-2026-11", "quick_score", "77")
        self.assertEqual({a["slug"]: a for a in self.run_job("list")["applications"]}["northwind-2026-11"]["quick_score"], 77)
        self.run_job("set", "northwind-2026-11", "quick_score", "x", ok=False)

    def test_keywords_settable_and_fit_score_records_its_date(self):
        self.run_job("set", "northwind-2026-11", "keywords", "TypeScript, React, C#, Node.js")
        self.assertIn("keywords: TypeScript, React, C#, Node.js", (self.apps / "northwind-2026-11.md").read_text())
        self.run_job("set", "northwind-2026-11", "keywords", "a\nb", ok=False)
        self.run_job("set", "northwind-2026-11", "keywords", "x" * 801, ok=False)
        self.run_job("set", "northwind-2026-11", "fit_score", "77")
        d = {x["slug"]: x for x in self.run_job("list")["applications"]}["northwind-2026-11"]
        self.assertEqual(d["fit_score"], 77)
        self.assertRegex(d["fit_scored"], r"^\d{4}-\d{2}-\d{2}$")

    def test_save_jd_starts_history(self):
        rec = {"company": "Acme", "role": "Eng", "url": "https://a", "jd_text": "x", "captured_at": "2026-12-03T10:00:00+05:30"}
        f = self.tmp / "r.json"; f.write_text(json.dumps(rec))
        self.run_job("save-jd", str(f))
        h = self.run_job("show", "acme-2026-12")["application"]["history"]
        self.assertEqual(h[0][1:3], ["-", "considering"])
        self.run_job("status", "acme-2026-12", "applied")
        self.assertEqual([x[2] for x in self.run_job("show", "acme-2026-12")["application"]["history"]], ["considering", "applied"])

    def test_real_applications_untouched(self):
        real_before = {p.name: p.read_bytes() for p in (REAL / "applications").glob("*.md")}
        self.run_job("status", "northwind-2026-11", "offer")
        real_after = {p.name: p.read_bytes() for p in (REAL / "applications").glob("*.md")}
        self.assertEqual(real_before, real_after)


if __name__ == "__main__":
    unittest.main()
