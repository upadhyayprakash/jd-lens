#!/usr/bin/env python3
"""Keyword-score a saved application's JD with the shared scorer. ONE command, no shell chaining, safe to allow in a headless run.

  python3 tools/score_app.py <slug>

Steps: make sure the skill profile matches the master file (rebuild it if not), run tools/score_jd.mjs on
applications/<slug>.md, record the keyword score as `quick_score` in the application file (through tools/jobs.py, so a backup
is kept), and print a JSON summary: score, must and nice counts, matched / partial / missing / unconfirmed skills, the
requirements that are not fully met (`gaps`), years asked, salary and flags. The judged `fit_score` is NOT set here:
that is the /job skill's call, made on top of this first pass.
"""
import json, os, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import paths  # noqa: E402  (where the data folder is)


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(1)


def node_bin():
    cfg = ROOT / "tools" / "jobd" / "jobd.config.json"
    if cfg.exists():
        n = json.loads(cfg.read_text()).get("node")
        if n and os.path.exists(n):
            return n
    path = os.pathsep.join(["/opt/homebrew/bin", "/usr/local/bin", os.environ.get("PATH", "")])
    return shutil.which("node", path=path)


def main():
    if len(sys.argv) != 2 or not re.match(r"^[a-z0-9][a-z0-9-]*$", sys.argv[1]):
        fail("usage: python3 tools/score_app.py <slug>   (slug like northwind-2026-11)")
    slug = sys.argv[1]
    md = paths.DATA / "applications" / f"{slug}.md"
    if not md.exists():
        fail(f"no such application: {slug}")
    node = node_bin()
    if not node:
        fail("node not found; run tools/jobd/install.py")
    if subprocess.run([sys.executable, str(ROOT / "tools" / "build_profile.py"), "--check"], capture_output=True).returncode != 0:
        b = subprocess.run([sys.executable, str(ROOT / "tools" / "build_profile.py")], capture_output=True, text=True)
        if b.returncode:
            fail("could not rebuild the skill profile: " + (b.stderr or b.stdout)[:200])
    r = subprocess.run([node, str(ROOT / "tools" / "score_jd.mjs"), str(md)], capture_output=True, text=True, timeout=60)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        fail("scoring failed: " + (r.stderr or r.stdout)[:200])
    data.pop("requirements", None)
    out = {"ok": True, "slug": slug, "keyword_score": data.get("score"), "must": data.get("must"), "nice": data.get("nice"),
           "matched": data.get("matched"), "partial": data.get("partial"), "missing": data.get("missing"), "unconfirmed": data.get("unconfirmed"),
           "unscored_soft_requirements": data.get("unscored"), "gaps": data.get("gaps", []), "years": data.get("years"),
           "salary": data.get("salary"), "flags": data.get("flags")}
    if out["keyword_score"] is not None:
        s = subprocess.run([sys.executable, str(ROOT / "tools" / "jobs.py"), "set", slug, "quick_score", str(out["keyword_score"])], capture_output=True, text=True)
        out["quick_score_saved"] = s.returncode == 0
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
