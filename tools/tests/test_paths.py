#!/usr/bin/env python3
"""The data folder (tools/paths.py): by default it is the engine folder, and it can be set elsewhere (environment variable or
jdlens.config.json). With it set, the tools read and write the data there, and a Claude run starts in the data folder with the
engine added. Every test runs on a TEMPORARY engine copy and a TEMPORARY data folder; Claude is replaced by a stub script."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time, unittest

REAL = pathlib.Path(__file__).resolve().parent.parent.parent
APP = "northwind-2026-11"


class PathsTest(unittest.TestCase):
    def setUp(self):
        base = pathlib.Path(tempfile.mkdtemp(prefix="paths-test-")).resolve()
        self.base, self.engine, self.data = base, base / "engine", base / "my data"      # a space in the data path on purpose
        shutil.copytree(REAL / "tools", self.engine / "tools", ignore=shutil.ignore_patterns("tests", "__pycache__", "jd-*", "jobs", "*.log"))
        (self.engine / "master").mkdir()
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.engine / "master" / "master-resume.template.md")
        self.env = {k: v for k, v in os.environ.items() if k != "JD_LENS_DATA"}

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def tool(self, name, *args, env=None, ok=True):
        r = subprocess.run([sys.executable, str(self.engine / "tools" / name), *args], capture_output=True, text=True, env=env or self.env)
        self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr)
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stdout

    def seed_data(self):
        """A data folder with the sample master and the frozen fixture applications."""
        (self.data / "master").mkdir(parents=True)
        shutil.copy2(REAL / "master" / "master-resume.template.md", self.data / "master" / "master-resume.md")
        shutil.copytree(REAL / "tools" / "tests" / "fixtures" / "applications", self.data / "applications")
        return dict(self.env, JD_LENS_DATA=str(self.data))

    # ---- where the data folder is ----
    def test_default_is_the_engine_folder(self):
        d = self.tool("paths.py", "show")
        self.assertEqual((d["source"], d["separate"], d["data"]), ("engine", False, str(self.engine)))

    def test_config_env_and_clear(self):
        d = self.tool("paths.py", "set", str(self.data))
        self.assertEqual((d["source"], d["separate"], d["data"]), ("config", True, str(self.data)))
        self.assertTrue(self.data.is_dir(), "set creates the folder")
        self.assertEqual(self.tool("paths.py", "show")["data"], str(self.data), "the setting persists")
        other = self.base / "other"
        d = self.tool("paths.py", "show", env=dict(self.env, JD_LENS_DATA=str(other)))
        self.assertEqual((d["source"], d["data"]), ("env", str(other)), "the environment variable wins over the config file")
        d = self.tool("paths.py", "clear")
        self.assertEqual((d["source"], d["separate"]), ("engine", False))
        self.assertFalse((self.engine / "jdlens.config.json").exists())

    def test_check_says_whether_a_folder_has_a_master_resume_and_changes_nothing(self):
        self.assertFalse(self.tool("paths.py", "check", str(self.data))["has_master"], "a folder that does not exist yet")
        self.assertFalse(self.data.exists(), "checking must not create the folder")
        self.seed_data()
        self.assertTrue(self.tool("paths.py", "check", str(self.data))["has_master"])
        before = (self.data / "master" / "master-resume.md").read_text()
        self.tool("paths.py", "init", str(self.data))
        self.assertEqual((self.data / "master" / "master-resume.md").read_text(), before, "init never replaces an existing master resume")
        self.tool("paths.py", "check", "relative/folder", ok=False)

    def test_set_rejects_a_relative_path_and_a_file(self):
        self.tool("paths.py", "set", "relative/folder", ok=False)
        f = self.base / "afile"; f.write_text("x")
        self.tool("paths.py", "set", str(f), ok=False)

    # ---- the tools use it ----
    def test_tools_read_and_write_the_data_folder_not_the_engine(self):
        env = self.seed_data()
        apps = self.tool("jobs.py", "list", env=env)
        self.assertTrue(len(apps["applications"]) >= 3, "jobs.py lists the applications in the data folder")
        self.assertEqual(self.tool("prefs.py", "set", "resume_layout", "photo", env=env)["prefs"]["resume_layout"], "photo")
        self.assertTrue((self.data / "master" / "preferences.json").is_file())
        self.assertFalse((self.engine / "master" / "preferences.json").exists(), "settings must not land in the engine folder")
        self.tool("jobs_table.py", env=env)
        self.assertTrue((self.data / "applications" / "INDEX.md").is_file())
        self.tool("build_views.py", "--no-pdf", env=env)
        self.assertTrue((self.data / "views" / "applications.html").is_file())
        self.assertFalse((self.engine / "views").exists(), "views must not land in the engine folder")
        self.assertFalse((self.engine / "applications").exists())

    def test_profile_is_built_from_the_data_folder_and_kept_with_the_extension(self):
        env = self.seed_data()
        self.tool("build_profile.py", env=env)
        prof = json.loads((self.engine / "tools" / "jd-capture-extension" / "data" / "profile.json").read_text())
        self.assertEqual(prof["repo_path"], str(self.data))
        self.assertTrue(len(prof["rows"]) >= 5)

    # ---- Claude runs ----
    def run_claude_job(self, env):
        stub = self.base / "claude-stub.sh"
        out = self.base / "stub-out.txt"
        stub.write_text(f"#!{sys.executable}\nimport json, os, sys\n"
                        "open(os.environ['STUB_OUT'], 'w').write(json.dumps({'cwd': os.path.realpath(os.getcwd()), 'data': os.environ.get('JD_LENS_DATA'), 'args': sys.argv[1:]}))\n"
                        "print('{\"result\": \"ok\", \"is_error\": false, \"total_cost_usd\": 0}')\n")
        stub.chmod(0o755)
        env = dict(env, JOBD_CLAUDE=str(stub), STUB_OUT=str(out))
        code = ("import sys, json; sys.path.insert(0, 'tools/jobd'); import claude_jobs; "
                f"print(json.dumps(claude_jobs.start('tailor', '{APP}')))")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(self.engine), env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        job = json.loads(r.stdout.strip().splitlines()[-1])["job"]
        done = self.engine / "tools" / "jobd" / "jobs" / f"{job}.exit"
        for _ in range(100):
            if done.exists():
                break
            time.sleep(0.1)
        self.assertTrue(done.exists(), "the stub run should finish")
        rec = json.loads(out.read_text())
        return rec["args"], rec["cwd"], rec["data"]

    def test_claude_runs_in_the_data_folder_with_the_engine_added(self):
        env = self.seed_data()
        args, cwd, data_env = self.run_claude_job(env)
        self.assertEqual(cwd, os.path.realpath(self.data), "the run starts in the data folder")
        self.assertEqual(data_env, str(self.data), "the run's tools are told the same data folder")
        self.assertEqual(args[args.index("--add-dir") + 1], str(self.engine), "the engine (and its /job skill) is added")
        allowed = args[args.index("--allowedTools") + 1:]
        tools = str(self.engine / "tools")
        self.assertIn(f"Bash(python3 {tools}/jobs.py:*)", allowed, "allowlists carry the engine's absolute tools path")
        self.assertFalse([a for a in allowed if a.startswith("Bash(") and "tools/" in a and tools not in a], allowed)
        prompt = args[args.index("-p") + 1]
        self.assertIn(f"run it as `{tools}/<name>`", prompt)
        self.assertIn(f"tailored/{APP}/questions.json", prompt, "data paths stay relative to the data folder")
        self.assertIn(str(self.engine / "tailored" / "_base" / "layouts" / "two-column.html"), prompt, "the prompt names the chosen layout file")
        self.assertIn("anika_verma_resume_<company>", prompt, "and the file-name stem from the master resume")
        self.assertIn(f"prepare_resume.py {APP} --force", prompt, "a build always starts fresh")
        self.assertIn("never reuse or just re-check an existing file", prompt)

    def test_claude_runs_in_the_engine_folder_when_there_is_one_folder(self):
        (self.engine / "applications").mkdir()
        shutil.copy2(REAL / "tools" / "tests" / "fixtures" / "applications" / f"{APP}.md", self.engine / "applications")
        args, cwd, _ = self.run_claude_job(self.env)
        self.assertEqual(cwd, os.path.realpath(self.engine))
        self.assertNotIn("--add-dir", args)
        allowed = args[args.index("--allowedTools") + 1:]
        self.assertIn("Bash(python3 tools/jobs.py:*)", allowed, "nothing changes in single-folder mode")


if __name__ == "__main__":
    unittest.main()
