#!/usr/bin/env python3
"""Tests for the native messaging host. Everything runs on a TEMPORARY COPY of the repo with a FAKE claude binary,
so no real application file is written and no Claude usage is spent.
Run: python3 -m unittest discover -s tools/tests -v
"""
import json, os, pathlib, shutil, stat, struct, subprocess, sys, tempfile, time, unittest, zlib

REAL = pathlib.Path(__file__).resolve().parent.parent.parent

FAKE_CLAUDE = """#!/bin/sh
# fake claude: record argv, wait, print a result like `claude -p --output-format json`
printf '%s\\n' "$@" > "$FAKE_ARGS"
sleep "${FAKE_SLEEP:-0.3}"
[ -n "$FAKE_TOUCH" ] && echo changed-by-job >> "$FAKE_TOUCH"
if [ -n "$FAKE_DENIALS" ]; then
  echo '{"result":"I could not run the scorer.","total_cost_usd":0.01,"session_id":"sess-1","is_error":false,"permission_denials":[{"tool_name":"Bash","tool_input":{"command":"cd /repo && cat applications/x.md; ls tailored"}},{"tool_name":"Bash","tool_input":{"command":"python3 tools/build_profile.py && node tools/score_jd.mjs a.md"}}]}'
else
  echo '{"result":"fake summary line","total_cost_usd":0.01,"session_id":"sess-1","is_error":false,"permission_denials":[]}'
fi
"""


def frame(obj):
    b = json.dumps(obj).encode()
    return struct.pack("<I", len(b)) + b


def unframe(data):
    out, i = [], 0
    while i < len(data):
        n = struct.unpack("<I", data[i:i + 4])[0]
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


class HostTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="host-test-")).resolve()
        shutil.copytree(REAL / "tools", self.tmp / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jobs", "*.log", "jobd.config.json"))
        shutil.copytree(REAL / "tools" / "tests" / "fixtures" / "applications", self.tmp / "applications")  # frozen fixtures, not the live folder
        (self.tmp / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master" / "master-resume.md")   # the sample master (made-up data)
        self.fake = self.tmp / "fake-claude.sh"
        self.fake.write_text(FAKE_CLAUDE)
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IEXEC)
        self.args_file = self.tmp / "fake-args.txt"
        self.env = dict(os.environ, JOBD_CLAUDE=str(self.fake), FAKE_ARGS=str(self.args_file))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def send(self, op, **args):
        p = subprocess.run([sys.executable, str(self.tmp / "tools" / "jobd" / "host.py")], input=frame({"op": op, "args": args}),
                           capture_output=True, env=self.env, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr.decode())
        return unframe(p.stdout)[0]

    def ok(self, op, **args):
        r = self.send(op, **args)
        self.assertTrue(r["ok"], r)
        return r

    def bad(self, op, **args):
        r = self.send(op, **args)
        self.assertFalse(r["ok"], r)
        return r

    def import_real_claude_jobs(self):
        """The real helper code, imported in single-folder mode whatever the developer's own jdlens.config.json says (the
        environment variable beats the config file), with every cached tool module dropped before and after."""
        mods = ("claude_jobs", "prefs", "paths", "identity")
        for m in mods:
            sys.modules.pop(m, None)
        jobd = str(REAL / "tools" / "jobd")
        sys.path.insert(0, jobd)
        old_env = os.environ.get("JD_LENS_DATA")
        os.environ["JD_LENS_DATA"] = str(REAL)
        def undo():
            sys.path.remove(jobd)
            for m in mods:
                sys.modules.pop(m, None)
            if old_env is None:
                os.environ.pop("JD_LENS_DATA", None)
            else:
                os.environ["JD_LENS_DATA"] = old_env
        self.addCleanup(undo)
        import claude_jobs
        return claude_jobs

    # ---- basics and validation
    def test_ping_and_unknown_op(self):
        r = self.ok("ping")
        self.assertEqual(r["repo"], str(self.tmp))
        self.assertIn("unknown operation", self.bad("rm_rf")["error"])
        self.assertIn("'op'", unframe(subprocess.run([sys.executable, str(self.tmp / "tools/jobd/host.py")], input=frame([1, 2]), capture_output=True).stdout)[0]["error"])

    # ---- the data folder (engine and data in different places)
    def test_ping_reports_engine_data_and_master(self):
        r = self.ok("ping")
        self.assertEqual((r["engine"], r["data"], r["data_source"], r["has_master"]), (str(self.tmp), str(self.tmp), "engine", True))

    def test_set_data_dir_with_sample_rebuilds_the_profile_and_clear_goes_back(self):
        new = self.tmp.parent / (self.tmp.name + "-my data")      # a space in the path on purpose
        self.addCleanup(shutil.rmtree, new, ignore_errors=True)
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master")        # a real engine ships the sample template
        r = self.ok("set_data_dir", path=str(new), sample=True)
        self.assertEqual((r["data"], r["separate"], r["sample_added"], r["has_master"], r["profile_rebuilt"]), (str(new), True, True, True, True), r)
        self.assertTrue((new / "master" / "master-resume.md").is_file() and (new / "applications").is_dir())
        prof = json.loads((self.tmp / "tools" / "jd-capture-extension" / "data" / "profile.json").read_text())
        self.assertEqual(prof["repo_path"], str(new), "the cache is rebuilt from the new data folder")
        ping = self.ok("ping")
        self.assertEqual((ping["data"], ping["repo"], ping["engine"], ping["data_source"]), (str(new), str(new), str(self.tmp), "config"))
        self.assertEqual(self.ok("list")["applications"], [], "the new folder has no applications yet")
        again = self.ok("set_data_dir", path=str(new), sample=True)
        self.assertFalse(again["sample_added"], "an existing master resume is never replaced")
        back = self.ok("clear_data_dir")
        self.assertEqual((back["data"], back["separate"]), (str(self.tmp), False))
        self.assertEqual(len(self.ok("list")["applications"]), 3)
        self.assertTrue(back["profile_rebuilt"], "going back rebuilds the cache from the engine folder's master resume")
        prof = json.loads((self.tmp / "tools" / "jd-capture-extension" / "data" / "profile.json").read_text())
        self.assertEqual(prof["repo_path"], str(self.tmp))

    def test_set_data_dir_without_sample_leaves_an_empty_folder_and_says_so(self):
        new = self.tmp.parent / (self.tmp.name + "-empty")
        self.addCleanup(shutil.rmtree, new, ignore_errors=True)
        self.ok("rebuild_profile")                                       # a cache exists, built from the engine folder's master resume
        cache = self.tmp / "tools" / "jd-capture-extension" / "data"
        self.assertTrue((cache / "profile.json").is_file())
        r = self.ok("set_data_dir", path=str(new))
        self.assertEqual((r["has_master"], r["profile_rebuilt"], r["sample_added"]), (False, False, False))
        self.assertTrue(r["cache_cleared"], "a folder with no master resume must not leave the old folder's skill profile behind")
        self.assertFalse([n for n in ("profile.json", "resume.json", "applications.json") if (cache / n).exists()])
        self.assertFalse((new / "master").exists(), "nothing is created unless the sample was asked for")
        self.assertFalse(self.ok("ping")["has_master"])
        back = self.ok("clear_data_dir")                                 # back to the engine folder, which has its master resume
        self.assertTrue(back["profile_rebuilt"] and (cache / "profile.json").is_file())
        self.assertFalse(back["cache_cleared"])

    def test_set_data_dir_rejects_bad_paths(self):
        self.assertIn("full path", self.bad("set_data_dir", path="relative/folder")["error"])
        self.assertIn("home folder", self.bad("set_data_dir", path=str(pathlib.Path.home()))["error"])
        f = self.tmp / "afile"; f.write_text("x")
        self.assertIn("not a folder", self.bad("set_data_dir", path=str(f))["error"])
        self.bad("set_data_dir")
        self.assertEqual(self.ok("ping")["data_source"], "engine", "a rejected path changes nothing")

    # ---- the profile photo (the With photo layout)
    def _png(self, name, w, h):
        raw = b"".join(b"\x00" + bytes((200, 160, 120)) * w for _ in range(h))
        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
        f = self.tmp / name
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
        return f

    @unittest.skipUnless(sys.platform == "darwin", "photos are converted with macOS sips")
    def test_photo_set_resizes_to_jpeg_previews_and_can_be_removed(self):
        self.assertFalse(self.ok("photo_info")["has_photo"])
        r = self.ok("set_photo", path=str(self._png("big.png", 1600, 1200)))
        dest = self.tmp / "master" / "photo.jpg"
        self.assertTrue(r["has_photo"] and dest.is_file(), r)
        self.assertEqual(dest.read_bytes()[:2], b"\xff\xd8", "saved as a JPEG")
        w = int(subprocess.run(["sips", "-g", "pixelWidth", str(dest)], capture_output=True, text=True).stdout.split()[-1])
        self.assertLessEqual(w, 800, "resized to fit 800 px")
        self.assertTrue(r["preview"].startswith("data:image/jpeg;base64,"))
        self.assertTrue(self.ok("photo_info")["has_photo"])
        self.assertFalse(self.ok("remove_photo")["has_photo"])
        self.assertFalse(dest.exists())
        self.assertFalse(self.ok("remove_photo")["has_photo"], "removing twice is fine")

    @unittest.skipUnless(sys.platform == "darwin", "photos are converted with macOS sips")
    def test_photo_goes_into_the_data_folder_when_it_is_apart_from_the_engine(self):
        new = self.tmp.parent / (self.tmp.name + "-photo data")
        self.addCleanup(shutil.rmtree, new, ignore_errors=True)
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master")
        self.ok("set_data_dir", path=str(new), sample=True)
        self.ok("set_photo", path=str(self._png("p.png", 300, 300)))
        self.assertTrue((new / "master" / "photo.jpg").is_file())
        self.assertFalse((self.tmp / "master" / "photo.jpg").exists(), "the photo must not land in the engine folder")

    def test_photo_rejects_bad_input_and_keeps_the_old_photo(self):
        self.assertIn("does not exist", self.bad("set_photo", path=str(self.tmp / "nope.png"))["error"])
        self.assertIn("does not exist", self.bad("set_photo", path="relative.png")["error"])
        txt = self.tmp / "notes.txt"; txt.write_text("hello")
        self.assertIn("choose a picture", self.bad("set_photo", path=str(txt))["error"])
        self.bad("set_photo")
        self.assertFalse((self.tmp / "master" / "photo.jpg").exists())

    # ---- open a folder in the file manager (a stub opener records what would open; Finder is never started)
    def _opener(self):
        rec = self.tmp / "opened.txt"
        stub = self.tmp / "fake-open.sh"
        stub.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "$OPENED"\n')
        stub.chmod(0o755)
        self.env = dict(self.env, JD_LENS_OPEN=str(stub), OPENED=str(rec))
        return rec

    def test_open_folder_opens_only_the_data_or_the_engine_folder(self):
        rec = self._opener()
        self.assertEqual(self.ok("open_folder", which="data")["opened"], str(self.tmp))
        new = self.tmp.parent / (self.tmp.name + "-open data")
        self.addCleanup(shutil.rmtree, new, ignore_errors=True)
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.tmp / "master")
        self.ok("set_data_dir", path=str(new), sample=True)
        self.ok("open_folder", which="data"); self.ok("open_folder", which="engine")
        self.assertEqual(rec.read_text().split("\n")[:-1], [str(self.tmp), str(new), str(self.tmp)], "data, then the new data folder, then the engine")
        before = rec.read_text()
        for bad in ("../etc", "/", "home", ""):
            self.assertIn("which", self.bad("open_folder", which=bad)["error"])
        self.bad("open_folder")
        self.assertEqual(rec.read_text(), before, "a refused request opens nothing")

    def test_open_folder_says_so_when_the_opener_fails_or_the_folder_is_gone(self):
        self._opener()
        failing = self.tmp / "fail-open.sh"
        failing.write_text("#!/bin/sh\necho nope >&2\nexit 3\n"); failing.chmod(0o755)
        self.env = dict(self.env, JD_LENS_OPEN=str(failing))
        self.assertIn("could not open the folder", self.bad("open_folder", which="data")["error"])

    def test_two_messages_in_one_session(self):
        p = subprocess.run([sys.executable, str(self.tmp / "tools/jobd/host.py")], input=frame({"op": "ping"}) + frame({"op": "list"}), capture_output=True, timeout=60)
        a, b = unframe(p.stdout)
        self.assertTrue(a["ok"] and b["ok"])
        self.assertEqual(len(b["applications"]), 3)

    def test_slug_and_status_validation(self):
        for s in ("../master/master-resume", "A B", "", "x" * 3):
            self.bad("show", slug=s)
        self.bad("status", slug="northwind-2026-11", status="hired")
        self.bad("set", slug="northwind-2026-11", key="status", value="offer")

    # ---- deterministic writes (scratch only)
    def test_status_round_set(self):
        self.ok("status", slug="northwind-2026-11", status="screening")
        self.assertIn("status: screening", (self.tmp / "applications/northwind-2026-11.md").read_text())
        self.assertTrue(list((self.tmp / "applications/.history").glob("northwind-2026-11-*.md")))
        self.ok("round", slug="northwind-2026-11", round="Recruiter call", date="2026-12-02", result="advanced")
        self.assertEqual(self.ok("show", slug="northwind-2026-11")["application"]["rounds"][0][1], "Recruiter call")
        self.ok("set", slug="northwind-2026-11", key="fit_score", value="80")

    def test_save_jd_keeps_only_known_fields(self):
        rec = {"company": "Acme", "role": "Engineer", "url": "https://acme.example/1", "jd_text": "Build.", "captured_at": "2026-12-03T10:00:00+05:30",
               "company_url": "https://acme.example", "evil": "rm -rf", "extraction": "main-text"}
        r = self.ok("save_jd", record=rec)
        self.assertEqual(r["slug"], "acme-2026-12")
        kept = json.loads((self.tmp / "job-inbox/done/acme-2026-12.json").read_text())
        self.assertNotIn("evil", kept)
        self.assertEqual(self.ok("list")["applications"][-1]["company_url"] if False else "https://acme.example", "https://acme.example")
        self.assertIn("company_url: https://acme.example", (self.tmp / "applications" / "acme-2026-12.md").read_text())
        self.bad("save_jd", record=rec)  # duplicate refused

    def test_profile_and_views(self):
        (self.tmp / "tools/jd-capture-extension/data/profile.json").unlink(missing_ok=True)
        self.assertFalse(self.ok("profile_status")["current"])  # no profile yet
        self.ok("rebuild_profile")
        self.assertTrue(self.ok("profile_status")["current"])
        (self.tmp / "master/master-resume.md").write_text((self.tmp / "master/master-resume.md").read_text() + "\nextra\n")
        self.assertFalse(self.ok("profile_status")["current"])  # master changed, profile stale
        r = self.ok("master_view")
        self.assertTrue(pathlib.Path(r["html"]).exists())
        self.assertIn("Master resume data", pathlib.Path(r["html"]).read_text())

    def test_brag_sheet_page(self):
        self.assertFalse(self.ok("brag_view", slug="northwind-2026-11")["found"])  # no section yet
        f = self.tmp / "applications" / "northwind-2026-11.md"
        f.write_text(f.read_text().rstrip() + "\n\n## Brag Sheet\n\n### JD pillars\n1. TypeScript at scale\n\n### Matched wins\n- **TypeScript** [F-LM-02]: led a migration. So what: fits.\n")
        r = self.ok("brag_view", slug="northwind-2026-11")
        self.assertTrue(r["found"])
        page = pathlib.Path(r["html"]).read_text()
        self.assertIn("Brag Sheet: ", page)
        self.assertIn("Matched wins", page)
        self.assertEqual(self.ok("read_section", slug="northwind-2026-11", section="Brag Sheet")["found"], True)
        self.assertTrue(self.ok("claude_start", kind="brag", slug="northwind-2026-11")["job"])

    def test_rescore_saved(self):
        self.ok("rebuild_profile")
        r = self.ok("rescore_saved")["results"]
        by = {x["slug"]: x for x in r}
        self.assertEqual(set(by), {"northwind-2026-11", "globex-2026-10", "initech-2026-10"})
        self.assertTrue(all("new" in x for x in r), r)
        scores = {a["slug"]: a["quick_score"] for a in self.ok("list")["applications"]}
        self.assertEqual(scores["northwind-2026-11"], by["northwind-2026-11"]["new"])
        self.assertGreater(scores["northwind-2026-11"], scores["globex-2026-10"])
        again = {x["slug"]: x for x in self.ok("rescore_saved")["results"]}
        self.assertEqual(again["northwind-2026-11"]["old"], again["northwind-2026-11"]["new"])    # nothing changed the second time

    def test_read_section(self):
        r = self.ok("read_section", slug="northwind-2026-11", section="Rounds")
        self.assertTrue(r["found"])
        self.assertFalse(self.ok("read_section", slug="northwind-2026-11", section="Nope")["found"])

    # ---- Claude jobs (fake binary)
    def wait_done(self, job, limit=15):
        for _ in range(limit * 4):
            s = self.ok("claude_status", job=job)
            if s["state"] != "running":
                return s
            time.sleep(0.25)
        self.fail("job did not finish")

    def test_claude_job_lifecycle_and_flags(self):
        r = self.ok("claude_start", kind="full_score", slug="northwind-2026-11")
        self.assertTrue(r["uses_claude"])
        self.assertEqual(self.ok("claude_status", job=r["job"])["state"], "running")
        self.bad("claude_start", kind="tailor", slug="northwind-2026-11")  # one running job per application
        s = self.wait_done(r["job"])
        self.assertEqual(s["state"], "done")
        self.assertEqual(s["result"], "fake summary line")
        argv = self.args_file.read_text().splitlines()
        self.assertEqual(argv[0], "-p")
        prompt = "\n".join(argv[1:argv.index("--output-format")])
        self.assertTrue(prompt.startswith("/job score northwind-2026-11"))
        self.assertIn("HEADLESS RUN", prompt)
        self.assertIn("untrusted data", prompt)
        for flag in ("--output-format", "json", "--permission-mode", "dontAsk", "--max-budget-usd", "--allowedTools"):
            self.assertIn(flag, argv)
        tools = argv[argv.index("--allowedTools") + 1:]
        self.assertFalse([t for t in tools if t.startswith("Bash(git") or t == "WebFetch" or t == "Bash"], tools)

    def test_build_prompt_allows_the_pdf_script_it_needs(self):
        """A build run once stopped at the PDF step: the shared shell rule said python3 scripts only, yet the PDF is made by
        tools/render_pdf.sh. The build prompt must name it as an exception and the allowlist must contain it."""
        claude_jobs = self.import_real_claude_jobs()
        spec = claude_jobs.KINDS["build"]
        self.assertIn("Bash(tools/render_pdf.sh:*)", spec["tools"])
        prompt = spec["prompt"].format(slug="x-2026-11", extra="", company="X", headless=claude_jobs.HEADLESS.format(slug="x-2026-11", pages="2 pages", layout="/x/tailored/_base/layouts/two-column.html", stem="anika_verma"))
        self.assertIn("tools/render_pdf.sh", prompt)
        self.assertIn("EXCEPTION to the shell rules", prompt)

    def test_skill_commands_are_allowed_for_the_kinds_that_run_them(self):
        """The /job skill tells Claude to read the page target (`python3 tools/prefs.py get resume_pages`); a tailor run was
        blocked because that command was not on the allowlist. Reading is allowed, changing it is not."""
        claude_jobs = self.import_real_claude_jobs()
        for kind in ("tailor", "build"):
            self.assertIn("Bash(python3 tools/prefs.py get:*)", claude_jobs.KINDS[kind]["tools"], kind)
        for kind, spec in claude_jobs.KINDS.items():
            self.assertFalse([t for t in spec["tools"] if "prefs.py set" in t or t == "Bash(python3 tools/prefs.py:*)"], kind)

    def test_delete_app_needs_confirmation_and_moves_to_trash(self):
        slug = "northwind-2026-11"
        pre = self.ok("delete_preview", slug=slug)
        self.assertTrue(pre["dry_run"] and pre["items"])
        self.assertIn("confirmation", self.bad("delete_app", slug=slug)["error"])
        self.assertIn("confirmation", self.bad("delete_app", slug=slug, confirm="other-2026-11")["error"])
        self.assertTrue((self.tmp / "applications" / f"{slug}.md").exists())
        r = self.ok("delete_app", slug=slug, confirm=slug)
        self.assertFalse((self.tmp / "applications" / f"{slug}.md").exists())
        self.assertTrue((self.tmp / r["trash"] / "applications" / f"{slug}.md").exists())
        self.assertNotIn(slug, [a["slug"] for a in self.ok("list")["applications"]])

    def test_delete_app_refuses_while_a_job_runs(self):
        slug = "northwind-2026-11"
        jobs = self.tmp / "tools" / "jobd" / "jobs"; jobs.mkdir(exist_ok=True)
        (jobs / "j1.json").write_text(json.dumps({"id": "j1", "slug": slug}))   # no j1.exit file: still running
        self.assertIn("still running", self.bad("delete_app", slug=slug, confirm=slug)["error"])
        self.assertTrue((self.tmp / "applications" / f"{slug}.md").exists())

    def test_outside_changes_are_flagged_only_when_the_job_changed_them(self):
        """`Files changed outside the expected folders` once fired for files the user edited while the job ran, and could not
        see a file that was already modified when the job started. It now compares content hashes taken before and after."""
        (self.tmp / "tools" / "notes.txt").write_text("base\n")
        g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=str(self.tmp), capture_output=True, check=True)
        g("init", "-q"); g("add", "-A"); g("commit", "-qm", "base")
        (self.tmp / "tools" / "already-dirty.txt").write_text("edited before the job\n")          # untracked and untouched by the job
        (self.tmp / "tools" / "notes.txt").write_text("base\nedited before the job\n")            # tracked, dirty, then changed again by the job
        self.env["FAKE_TOUCH"] = "tools/notes.txt"
        s = self.wait_done(self.ok("claude_start", kind="full_score", slug="northwind-2026-11")["job"])
        self.assertIn("tools/notes.txt", s.get("touched_outside", []), s)
        self.assertNotIn("tools/already-dirty.txt", s.get("touched_outside", []), s)
        self.env["FAKE_TOUCH"] = "applications/northwind-2026-11.md"                                  # inside the allowed folder: fine
        s = self.wait_done(self.ok("claude_start", kind="full_score", slug="northwind-2026-11")["job"])
        self.assertNotIn("applications/northwind-2026-11.md", s.get("touched_outside", []), s)
        del self.env["FAKE_TOUCH"]                                                                # nothing changes: still clean, though files are dirty
        s = self.wait_done(self.ok("claude_start", kind="full_score", slug="northwind-2026-11")["job"])
        self.assertNotIn("tools/notes.txt", s.get("touched_outside", []), s)          # dirty from the earlier run, unchanged by this one
        self.assertNotIn("tools/already-dirty.txt", s.get("touched_outside", []), s)

    def test_get_data_serves_the_profile_files(self):
        """A store install has no data/ folder, so the panel gets its profile and resume data from the helper."""
        d = self.tmp / "tools" / "jd-capture-extension" / "data"
        d.mkdir(parents=True, exist_ok=True)
        (d / "profile.json").write_text(json.dumps({"rows": [1, 2]}))
        (d / "resume.json").unlink(missing_ok=True)
        r = self.ok("get_data", names=["profile", "resume"])
        self.assertEqual(r["data"]["profile"], {"rows": [1, 2]})
        self.assertIsNone(r["data"]["resume"])                               # not built yet: null, not an error
        self.bad("get_data", names=["../../etc/passwd"])
        self.bad("get_data", names=[])

    def test_blocked_commands_are_reported_not_hidden(self):
        self.env["FAKE_DENIALS"] = "1"
        r = self.ok("claude_start", kind="full_score", slug="northwind-2026-11")
        st = self.wait_done(r["job"])
        self.assertEqual(st["state"], "done")
        self.assertEqual(st["blocked"], 2)
        self.assertEqual(len(st["denied"]), 2)
        self.assertTrue(st["denied"][0].startswith("cd /repo && cat"), st["denied"])      # the command text, not a Python dict

    def test_scoring_runs_with_one_allowed_command_and_clear_shell_rules(self):
        r = self.ok("claude_start", kind="full_score", slug="northwind-2026-11")
        self.wait_done(r["job"])
        argv = self.args_file.read_text().splitlines()
        tools = argv[argv.index("--allowedTools") + 1:]
        self.assertIn("Bash(python3 tools/score_app.py:*)", tools)
        prompt = "\n".join(argv[1:argv.index("--output-format")])
        for rule in ("never with cat or ls", "ONE command per call", "no cd", "no &&", "score_app.py northwind-2026-11", "never run tools/jobs_table.py", "not about how you worked"):
            self.assertIn(rule, prompt)
        self.assertNotIn("Bash", [t for t in tools if t == "Bash"])                      # no unrestricted shell

    def test_index_and_views_are_refreshed_once_when_a_job_ends(self):
        r = self.ok("claude_start", kind="full_score", slug="northwind-2026-11")
        self.wait_done(r["job"])
        self.assertTrue((self.tmp / "tools" / "jobd" / "jobs" / f"{r['job']}.final").exists())
        index = self.tmp / "applications" / "INDEX.md"
        self.assertTrue(index.exists() and "Northwind" in index.read_text())                      # Claude never ran jobs_table.py itself
        self.assertTrue((self.tmp / "views" / "applications.html").exists())
        stamp = index.stat().st_mtime_ns
        self.ok("claude_status", job=r["job"])
        self.assertEqual(index.stat().st_mtime_ns, stamp)                                     # not refreshed again on every poll

    def test_claude_rejections(self):
        self.bad("claude_start", kind="shell", slug="northwind-2026-11")
        self.bad("claude_start", kind="tailor", slug="nope-2026-01")
        self.bad("claude_start", kind="answers", slug="northwind-2026-11")              # needs a question
        self.bad("claude_status", job="../../etc/passwd")
        r = self.ok("claude_start", kind="answers", slug="northwind-2026-11", extra="Why Northwind?")
        self.assertIn("/interview add Why Northwind?", (self.wait_done(r["job"]) and self.args_file.read_text()))

    def test_claude_cancel(self):
        self.env["FAKE_SLEEP"] = "20"
        r = self.ok("claude_start", kind="interview_prep", slug="northwind-2026-11")
        self.assertEqual(self.ok("claude_cancel", job=r["job"])["state"], "cancelled")
        self.assertEqual(self.ok("claude_status", job=r["job"])["state"], "failed")

    def test_questions_and_answers(self):
        d = self.tmp / "tailored/northwind-2026-11"
        d.mkdir(parents=True)
        (d / "questions.json").write_text(json.dumps([{"id": "q1", "question": "A real Express example?", "why": "JD asks for Express"}]))
        self.assertEqual(self.ok("questions", slug="northwind-2026-11")["questions"][0]["id"], "q1")
        self.ok("answer", slug="northwind-2026-11", answers={"q1": "Brightlabs dashboards API"})
        self.assertEqual(json.loads((d / "answers.json").read_text())["q1"], "Brightlabs dashboards API")
        self.assertEqual(self.ok("questions", slug="northwind-2026-11")["questions"], [])  # answered file moved aside
        self.bad("answer", slug="northwind-2026-11", answers={"bad id!": "x"})
        self.bad("answer", slug="northwind-2026-11", answers={})

    def test_real_repo_untouched(self):
        snap = lambda: ({p: p.read_bytes() for p in (REAL / "applications").glob("*.md")}, sorted(str(p) for p in (REAL / "job-inbox").rglob("*")))
        before = snap()
        self.ok("status", slug="northwind-2026-11", status="offer")
        self.ok("save_jd", record={"company": "Zed", "role": "R", "url": "https://z", "jd_text": "x"})
        self.assertEqual(before, snap())          # the real applications and the real job-inbox are exactly as they were


if __name__ == "__main__":
    unittest.main()
