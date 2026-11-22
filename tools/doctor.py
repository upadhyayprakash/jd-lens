#!/usr/bin/env python3
"""Health check for JD Lens: what is installed, what is missing, and the exact command that fixes each problem.

  python3 tools/doctor.py [--json] [--manifest-dir DIR]

Read-only: it never changes anything. Exit code 1 if something REQUIRED is missing (FAIL), 0 otherwise (WARN items are optional
or cosmetic). Run it after setup, and whenever something does not work.
"""
import json, os, pathlib, platform, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXT = ROOT / "tools" / "jd-capture-extension"
HOST_NAME = "com.jdlens.helper.json"
RESULTS = []


def add(level, name, detail, fix=""):
    RESULTS.append({"level": level, "name": name, "detail": detail, "fix": fix})


def search_path():
    home = pathlib.Path.home()
    extra = [str(home / ".local/bin"), "/opt/homebrew/bin", "/usr/local/bin"] + [str(p) for p in sorted((home / ".nvm/versions/node").glob("*/bin"))]
    cfg = ROOT / "tools" / "jobd" / "jobd.config.json"
    if cfg.exists():
        extra += [str(pathlib.Path(v).parent) for v in json.loads(cfg.read_text()).values() if v]
    return os.pathsep.join(extra + [os.environ.get("PATH", "")])


def run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def host_dir(arg):
    if arg:
        return pathlib.Path(arg)
    home = pathlib.Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Google/Chrome/NativeMessagingHosts"
    if sys.platform.startswith("linux"):
        return home / ".config/google-chrome/NativeMessagingHosts"
    return None


def main():
    as_json = "--json" in sys.argv
    mdir = sys.argv[sys.argv.index("--manifest-dir") + 1] if "--manifest-dir" in sys.argv else None
    sp = search_path()

    # --- system
    if sys.platform == "darwin":
        add("ok", "Operating system", f"macOS {platform.mac_ver()[0]} (the tested platform)")
    else:
        add("warn", "Operating system", f"{platform.system()}: the panel and scoring work, but the helper installer is only tested on macOS",
            "Use the panel without the helper (scoring and reading work), or follow docs/GETTING-STARTED.md, section Other systems")
    v = sys.version_info
    add("ok" if v >= (3, 9) else "fail", "Python 3.9 or newer", f"found {v.major}.{v.minor}.{v.micro}", "Install Python 3.9+ from python.org or Homebrew")
    node = shutil.which("node", path=sp)
    if node:
        code, out = run([node, "--version"])
        major = int(out.lstrip("v").split(".")[0]) if code == 0 and out.lstrip("v")[:1].isdigit() else 0
        add("ok" if major >= 18 else "warn", "Node.js 18 or newer", f"found {out} at {node}", "Install Node 18+ (nodejs.org or nvm)" if major < 18 else "")
    else:
        add("warn", "Node.js 18 or newer", "not found. Needed for Rescore saved JDs and Claude's full score; the panel itself does not need it", "Install Node 18+ (nodejs.org or nvm), then rerun python3 tools/jobd/install.py")
    chrome = pathlib.Path("/Applications/Google Chrome.app")
    found = chrome.exists() if sys.platform == "darwin" else bool(shutil.which("google-chrome") or shutil.which("chromium"))
    add("ok" if found else "fail", "Google Chrome 116 or newer", "found" if found else "not found", "Install Chrome from google.com/chrome (the side panel needs version 116+)")
    code, out = run(["pdfinfo", "-v"]) if shutil.which("pdfinfo", path=sp) else (1, "")
    add("ok" if code == 0 else "warn", "poppler (pdfinfo, pdftotext)", "found" if code == 0 else "not found. Only needed to check tailored resume PDFs", "brew install poppler")
    claude = shutil.which("claude", path=sp)
    if claude:
        code, out = run([claude, "--version"])
        add("ok" if code == 0 else "warn", "Claude Code CLI", f"{out} at {claude}", "Run `claude` once in a terminal and sign in" if code else "")
    else:
        add("warn", "Claude Code CLI (optional)", "not found. Scoring, saving and tracking work without it; Claude steps (full score, tailor, build, answers) need it",
            "Install from claude.com/claude-code, then run `claude` once and sign in")

    # --- your data
    master = ROOT / "master" / "master-resume.md"
    if not master.exists():
        add("fail", "Master resume", "master/master-resume.md does not exist", "python3 tools/setup.py   (creates it from the template)")
    else:
        text = master.read_text(encoding="utf-8")
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            import build_profile as bp  # noqa: E402
            rows = bp.skill_rows(text)
            bp.career_start(text)
            if "EXAMPLE TEMPLATE" in text:
                add("warn", "Master resume", "still the example template (made-up data)", "Replace it with your own details, then python3 tools/build_profile.py")
            elif len(rows) < 3:
                add("warn", "Master resume", f"only {len(rows)} skill rows: scores will be thin", "Fill section 5 (skills) of master/master-resume.md")
            else:
                add("ok", "Master resume", f"{len(rows)} skill rows, career start {bp.career_start(text)}")
        except SystemExit as e:
            add("fail", "Master resume", f"cannot read it: {e}", "Compare with master/master-resume.template.md (same headings and table layout)")
        except Exception as e:  # noqa: BLE001
            add("fail", "Master resume", f"cannot read it: {type(e).__name__}: {e}", "Compare with master/master-resume.template.md")
    data = EXT / "data"
    if (data / "profile.json").exists() and (data / "resume.json").exists():
        code, out = run([sys.executable, str(ROOT / "tools" / "build_profile.py"), "--check"])
        add("ok" if code == 0 else "warn", "Skill profile", out or "built", "python3 tools/build_profile.py" if code else "")
    else:
        add("fail", "Skill profile", "not built yet (the extension reads tools/jd-capture-extension/data/)", "python3 tools/build_profile.py")
    code, out = run([sys.executable, str(ROOT / "tools" / "sync_extension.py"), "--check"])
    add("ok" if code == 0 else "warn", "Extension scorer copy", out, "python3 tools/sync_extension.py" if code else "")

    # --- extension and helper
    try:
        m = json.loads((EXT / "manifest.json").read_text())
        icons_ok = all((EXT / p).exists() for p in m.get("icons", {}).values())
        eid = (EXT / "EXTENSION_ID").read_text().strip()
        add("ok" if icons_ok else "fail", "Extension folder", f"{m['name']} {m['version']}, id {eid}", "Reinstall the project files" if not icons_ok else "")
    except Exception as e:  # noqa: BLE001
        eid = ""
        add("fail", "Extension folder", f"manifest problem: {e}", "Re-download the project")
    hd = host_dir(mdir)
    if hd is None:
        add("warn", "Local helper", "this system is not supported by the installer yet", "See docs/GETTING-STARTED.md, section Other systems")
    else:
        mf = hd / HOST_NAME
        if not mf.exists():
            add("warn", "Local helper", f"not installed ({mf})", "python3 tools/jobd/install.py   (saving JDs, status changes and Claude steps need it)")
        else:
            try:
                d = json.loads(mf.read_text())
                launcher = pathlib.Path(d["path"])
                problems = []
                if not launcher.exists():
                    problems.append("the launcher it points to is missing (did the project folder move?)")
                if f"chrome-extension://{eid}/" not in d.get("allowed_origins", []):
                    problems.append("it allows a different extension ID")
                add("ok" if not problems else "warn", "Local helper", "installed and allows this extension" if not problems else "; ".join(problems),
                    "python3 tools/jobd/install.py" if problems else "")
            except Exception as e:  # noqa: BLE001
                add("warn", "Local helper", f"unreadable manifest: {e}", "python3 tools/jobd/install.py")

    if as_json:
        print(json.dumps(RESULTS, indent=2))
    else:
        sym = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}
        print("JD Lens health check\n")
        for r in RESULTS:
            print(f"  [{sym[r['level']]}] {r['name']}: {r['detail']}")
            if r["fix"] and r["level"] != "ok":
                print(f"         fix: {r['fix']}")
        n = {k: sum(1 for r in RESULTS if r["level"] == k) for k in sym}
        print(f"\n{n['ok']} ok, {n['warn']} warnings, {n['fail']} problems." + ("" if not n["fail"] else " Fix the FAIL items first."))
    sys.exit(1 if any(r["level"] == "fail" for r in RESULTS) else 0)


if __name__ == "__main__":
    main()
