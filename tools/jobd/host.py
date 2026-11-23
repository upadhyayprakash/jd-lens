#!/usr/bin/env python3
"""Native messaging host for the JD Lens Chrome extension (ADR-0002).

Chrome starts this program per use and talks to it over stdin/stdout: each message is a 4-byte little-endian length
followed by UTF-8 JSON. There is no server and no port. Only the extension ID in the host manifest can call it.

Request:  {"op": "<name>", "args": {...}}      Response: {"ok": true, ...} or {"ok": false, "error": "..."}
Only the operations in OPS exist. Nothing here runs an arbitrary command or path. Writes go through tools/jobs.py,
which keeps a backup in applications/.history/. Each operation is logged to tools/jobd/jobd.log (no message contents).
"""
import base64, datetime, hashlib, json, os, pathlib, re, shutil, struct, subprocess, sys, tempfile, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import claude_jobs  # noqa: E402

ROOT = HERE.parent.parent                 # the engine
sys.path.insert(0, str(ROOT / "tools"))
import paths  # noqa: E402  (where your data folder is)
DATA = paths.DATA                            # your data folder (the same folder as the engine unless you set one)
VERSION = "1.0.0"
MAX_OUT = 900_000          # Chrome accepts at most 1 MB from a native host
MAX_IN = 2_000_000
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RECORD_KEYS = {"company", "company_url", "role", "url", "jd_text", "captured_at", "location_text", "salary_text", "posted",
               "extraction", "source_title", "quick_score"}
LOG = HERE / "jobd.log"


class OpError(Exception):
    pass


def log(op, ok, note=""):
    try:
        with LOG.open("a") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {op} {'ok' if ok else 'FAIL'} {note}\n")
    except OSError:
        pass


def run_script(*args, timeout=120):
    r = subprocess.run([sys.executable, *map(str, args)], cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise OpError((r.stderr or r.stdout or "script failed").strip()[:500])
    if not data.get("ok", True):
        raise OpError(data.get("error", "failed"))
    return data


def jobs(*args):
    return run_script(ROOT / "tools" / "jobs.py", *args)


def need(args, key, typ=str):
    v = args.get(key)
    if not isinstance(v, typ) or (typ is str and not v.strip()):
        raise OpError(f"missing or invalid argument: {key}")
    return v


def slug_arg(args):
    s = need(args, "slug")
    if not SLUG_RE.match(s):
        raise OpError("invalid slug")
    return s


# ---- operations -----------------------------------------------------------------------------------
def op_ping(a):
    return {"version": VERSION, "repo": str(DATA), "engine": str(ROOT), "data": str(DATA), "data_source": paths.source(), "has_master": (DATA / "master" / "master-resume.md").is_file(), "python": sys.executable,
            "claude": shutil.which("claude", path=claude_jobs._path()) or claude_jobs._config().get("claude"),
            "node": shutil.which("node", path=claude_jobs._path()) or claude_jobs._config().get("node")}


def op_list(a):
    return jobs("list", *(["--status", a["status"]] if a.get("status") else []))


def op_show(a):
    return jobs("show", slug_arg(a))


def op_status(a):
    cmd = ["status", slug_arg(a), need(a, "status")]
    if a.get("date"):
        cmd += ["--date", str(a["date"])]
    if a.get("note"):
        cmd += ["--note", str(a["note"])[:300]]
    return jobs(*cmd)


def op_round(a):
    cmd = ["round", slug_arg(a), "--round", need(a, "round")]
    for k in ("date", "interviewer", "notes", "result"):
        if a.get(k):
            cmd += [f"--{k}", str(a[k])[:2000]]
    return jobs(*cmd)


def op_set(a):
    return jobs("set", slug_arg(a), need(a, "key"), str(need(a, "value")))


def op_save_jd(a):
    rec = need(a, "record", dict)
    clean = {k: v for k, v in rec.items() if k in RECORD_KEYS}
    if len(json.dumps(clean)) > 600_000:
        raise OpError("record too large")
    d = pathlib.Path(tempfile.mkdtemp(prefix="jobd-"))
    try:
        f = d / "record.json"
        f.write_text(json.dumps(clean))
        res = jobs("save-jd", f)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    keep = DATA / "job-inbox" / "done"
    keep.mkdir(parents=True, exist_ok=True)
    (keep / f"{res['slug']}.json").write_text(json.dumps(clean, indent=2, ensure_ascii=False))
    return res


def op_delete_preview(a):
    return jobs("delete", slug_arg(a), "--dry-run")


def op_delete_app(a):
    """Full wipe of one application (moved to .trash/, not erased). The caller must send confirm == the slug."""
    slug = slug_arg(a)
    if a.get("confirm") != slug:
        raise OpError("confirmation missing: send confirm equal to the slug")
    job = claude_jobs.running(slug)
    if job:
        raise OpError(f"a Claude job is still running for {slug} ({job}). Cancel it or wait, then delete.")
    return jobs("delete", slug)


def op_resume_info(a):
    return jobs("resume-info", slug_arg(a))


def op_get_prefs(a):
    return run_script(ROOT / "tools" / "prefs.py", "get")


def op_set_pref(a):
    return run_script(ROOT / "tools" / "prefs.py", "set", need(a, "key"), str(need(a, "value", (str, int))))


def op_open_folder(a):
    """Open the data folder or the engine folder in the file manager (Finder). Only these two folders can be opened."""
    target = {"data": DATA, "engine": ROOT}.get(need(a, "which"))
    if target is None:
        raise OpError("which must be 'data' or 'engine'")
    if not target.is_dir():
        raise OpError("that folder does not exist yet")
    opener = os.environ.get("JD_LENS_OPEN") or ("open" if sys.platform == "darwin" else "xdg-open")
    r = subprocess.run([opener, str(target)], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        raise OpError("could not open the folder: " + (r.stderr or r.stdout).strip()[:200])
    return {"opened": str(target)}


def op_data_dir(a):
    """Where the engine and the user's data folder are, and whether the data folder has a master resume yet."""
    return paths.info()


def op_choose_data_dir(a):
    """Ask macOS for a folder (a native folder picker). Returns {"path": ...} or {"cancelled": true}; nothing is changed yet."""
    if sys.platform != "darwin":
        raise OpError("the folder picker is only available on macOS; set the folder with: python3 tools/paths.py set <folder>")
    script = 'POSIX path of (choose folder with prompt "Choose the folder that holds your JD Lens data (your master resume and applications)")'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        if "-128" in r.stderr:                      # the user pressed Cancel
            return {"cancelled": True}
        raise OpError("could not open the folder picker: " + r.stderr.strip()[:200])
    return {"path": r.stdout.strip().rstrip("/") or r.stdout.strip()}


def _sync_cache(info):
    """Make the extension's generated cache (the skill profile it scores with) match the data folder: rebuild it from the master
    resume there, or clear it when there is none, so the panel never scores against a folder you have left."""
    out = {"profile_rebuilt": False, "cache_cleared": False}
    if info["has_master"]:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_profile.py")], cwd=str(ROOT), capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, JD_LENS_DATA=""))
        out["profile_rebuilt"] = r.returncode == 0
        if r.returncode != 0:
            out["profile_error"] = (r.stderr or r.stdout).strip()[-400:]
    else:
        for n in ("profile.json", "resume.json", "applications.json"):
            f = DATA_DIR / n
            if f.exists():
                f.unlink()
                out["cache_cleared"] = True
    return out


def op_set_data_dir(a):
    """Use this folder for the user's data. `sample` adds the made-up sample master resume if the folder has none. Whatever the folder
    already holds is used as it is (nothing is copied, merged or deleted). The skill profile the extension reads is rebuilt from the new
    folder (or cleared when it has no master resume), so the panel scores against the right resume straight away."""
    path = need(a, "path")
    try:
        added = paths.init_data_folder(path) if a.get("sample") else False
        paths.set_data_dir(path)
    except paths.PathsError as e:
        raise OpError(str(e))
    info = paths.info()
    return dict(info, sample_added=added, **_sync_cache(info))

def op_clear_data_dir(a):
    """Go back to keeping the data in the engine folder. Nothing in the folder you leave is touched."""
    paths.clear_data_dir()
    info = paths.info()
    return dict(info, **_sync_cache(info))

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".gif", ".tif", ".tiff", ".bmp", ".webp"}
PHOTO_MAX_BYTES = 25_000_000


def _photo_file():
    return DATA / "master" / "photo.jpg"


def _photo_info():
    f = _photo_file()
    if not f.is_file():
        return {"has_photo": False}
    info = {"has_photo": True, "path": str(f), "bytes": f.stat().st_size}
    with tempfile.TemporaryDirectory() as td:        # a small preview for the panel (the panel cannot read your files itself)
        small = pathlib.Path(td) / "preview.jpg"
        r = subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "160", str(f), "--out", str(small)], capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and small.is_file():
            info["preview"] = "data:image/jpeg;base64," + base64.b64encode(small.read_bytes()).decode()
    return info


def op_photo_info(a):
    """Whether the data folder has a profile photo (master/photo.jpg), with a small preview of it."""
    return _photo_info()


def op_choose_photo(a):
    """A native macOS file picker for a picture. Returns {"path": ...} or {"cancelled": true}; nothing is changed yet."""
    if sys.platform != "darwin":
        raise OpError("the file picker is only available on macOS; copy a JPEG to master/photo.jpg in your data folder instead")
    script = 'POSIX path of (choose file of type {"public.image"} with prompt "Choose your profile photo (it stays on your computer)")'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        if "-128" in r.stderr:
            return {"cancelled": True}
        raise OpError("could not open the file picker: " + r.stderr.strip()[:200])
    return {"path": r.stdout.strip()}


def op_set_photo(a):
    """Use this picture as the profile photo: resized to fit 800 px and saved as master/photo.jpg in the data folder."""
    src = pathlib.Path(need(a, "path"))
    if not src.is_absolute() or not src.is_file():
        raise OpError("that file does not exist")
    if src.suffix.lower() not in PHOTO_EXT:
        raise OpError("choose a picture (JPEG, PNG or HEIC)")
    if src.stat().st_size > PHOTO_MAX_BYTES:
        raise OpError("that picture is larger than 25 MB; choose a smaller one")
    dest = _photo_file()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(".photo-new.jpg")
    r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", "-Z", "800", str(src), "--out", str(tmp)],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not tmp.is_file() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise OpError("could not read that picture: " + (r.stderr or r.stdout).strip()[:200])
    os.replace(tmp, dest)
    return _photo_info()


def op_remove_photo(a):
    _photo_file().unlink(missing_ok=True)
    return _photo_info()


DATA_DIR = ROOT / "tools" / "jd-capture-extension" / "data"


def op_get_data(a):
    """The skill profile and resume data the panel scores with. A store-installed extension has no data/ folder of its own
    (it is built from the user's master resume), so the panel asks the helper, which reads the files build_profile.py wrote."""
    names = a.get("names")
    if not isinstance(names, list) or not names or any(n not in ("profile", "resume", "applications") for n in names):
        raise OpError("names must be a list of profile, resume or applications")
    out = {}
    for n in names:
        f = DATA_DIR / f"{n}.json"
        try:
            out[n] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        except (OSError, json.JSONDecodeError):
            out[n] = None
    return {"data": out}


def op_profile_status(a):
    pf = ROOT / "tools" / "jd-capture-extension" / "data" / "profile.json"
    master = DATA / "master" / "master-resume.md"
    sha = hashlib.sha256(master.read_text(encoding="utf-8").encode("utf-8")).hexdigest() if master.exists() else None
    if not pf.exists():
        return {"current": False, "reason": "no profile built yet"}
    p = json.loads(pf.read_text())
    return {"current": p.get("master_sha256") == sha, "generated_at": p.get("generated_at"), "rows": len(p.get("rows", []))}


def op_rebuild_profile(a):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_profile.py")], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise OpError((r.stderr or r.stdout)[:500])
    return {"output": r.stdout.strip()}


def op_rebuild_views(a):
    cmd = [sys.executable, str(ROOT / "tools" / "build_views.py")] + ([] if a.get("pdf") else ["--no-pdf"])
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=180)
    if r.returncode:
        raise OpError((r.stderr or r.stdout)[:500])
    return {"files": r.stdout.split()}


def op_master_view(a):
    v = DATA / "views"
    master = DATA / "master" / "master-resume.md"
    html, pdf = v / "master-resume.html", v / "master-resume.pdf"
    stale = not html.exists() or html.stat().st_mtime < master.stat().st_mtime
    want_pdf = bool(a.get("pdf"))
    if stale or (want_pdf and (not pdf.exists() or pdf.stat().st_mtime < master.stat().st_mtime)):
        op_rebuild_views({"pdf": want_pdf})
    return {"html": str(html), "pdf": str(pdf) if pdf.exists() else "", "applications_html": str(v / "applications.html")}


def op_brag_view(a):
    """Path of the printable Brag Sheet page for one application (rebuilt first, so it matches the application file)."""
    slug = slug_arg(a)
    op_rebuild_views({})
    f = DATA / "views" / "brag" / f"{slug}.html"
    return {"html": str(f) if f.exists() else "", "found": f.exists()}


def op_rescore_saved(a):
    """Recalculate the keyword score of every saved JD with the current skill profile (after the master file changes)."""
    node = claude_jobs._config().get("node") or shutil.which("node", path=claude_jobs._path())
    if not node:
        raise OpError("node not found; run tools/jobd/install.py")
    if not (ROOT / "tools" / "jd-capture-extension" / "data" / "profile.json").exists():
        raise OpError("build the skill profile first (python3 tools/build_profile.py)")
    results = []
    for app in jobs("list")["applications"]:
        md = DATA / "applications" / f"{app['slug']}.md"
        r = subprocess.run([node, str(ROOT / "tools" / "score_jd.mjs"), str(md)], capture_output=True, text=True, timeout=60)
        try:
            new = json.loads(r.stdout).get("score")
        except json.JSONDecodeError:
            results.append({"slug": app["slug"], "error": (r.stderr or "scoring failed").strip()[:160]})
            continue
        if new is None:
            results.append({"slug": app["slug"], "skipped": "no recognisable requirements"})
            continue
        if app.get("quick_score") != new:
            jobs("set", app["slug"], "quick_score", str(new))
        results.append({"slug": app["slug"], "old": app.get("quick_score"), "new": new})
    return {"results": results}


def op_read_section(a):
    slug = slug_arg(a)
    name = need(a, "section")
    text = (DATA / "applications" / f"{slug}.md").read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(name)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return {"section": name, "text": (m.group(1).strip() if m else "")[:30000], "found": bool(m)}


def op_claude_start(a):
    return claude_jobs.start(need(a, "kind"), slug_arg(a), str(a.get("extra", "")))


def op_claude_status(a):
    return claude_jobs.status(need(a, "job"))


def op_claude_cancel(a):
    return claude_jobs.cancel(need(a, "job"))


def op_questions(a):
    return {"questions": claude_jobs.questions(slug_arg(a))}


def op_answer(a):
    return claude_jobs.answer(slug_arg(a), a.get("answers"))


OPS = {
    "ping": op_ping, "list": op_list, "show": op_show, "status": op_status, "round": op_round, "set": op_set,
    "save_jd": op_save_jd, "get_data": op_get_data, "get_prefs": op_get_prefs, "resume_info": op_resume_info, "set_pref": op_set_pref, "delete_preview": op_delete_preview, "delete_app": op_delete_app, "profile_status": op_profile_status, "rebuild_profile": op_rebuild_profile,
    "rebuild_views": op_rebuild_views, "brag_view": op_brag_view, "master_view": op_master_view, "read_section": op_read_section, "rescore_saved": op_rescore_saved,
    "claude_start": op_claude_start, "claude_status": op_claude_status, "claude_cancel": op_claude_cancel,
    "questions": op_questions, "answer": op_answer,
    "photo_info": op_photo_info, "choose_photo": op_choose_photo, "set_photo": op_set_photo, "remove_photo": op_remove_photo,
    "open_folder": op_open_folder, "data_dir": op_data_dir, "choose_data_dir": op_choose_data_dir, "set_data_dir": op_set_data_dir, "clear_data_dir": op_clear_data_dir,
}


def handle(msg):
    if not isinstance(msg, dict) or not isinstance(msg.get("op"), str):
        raise OpError("request must be an object with an 'op'")
    fn = OPS.get(msg["op"])
    if not fn:
        raise OpError(f"unknown operation: {msg['op']}")
    args = msg.get("args") or {}
    if not isinstance(args, dict):
        raise OpError("args must be an object")
    return fn(args)


# ---- native messaging framing ---------------------------------------------------------------------
def read_message():
    raw = sys.stdin.buffer.read(4)
    if len(raw) < 4:
        return None
    n = struct.unpack("<I", raw)[0]
    if n > MAX_IN:
        raise OpError("message too large")
    return json.loads(sys.stdin.buffer.read(n).decode("utf-8"))


def write_message(obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if len(data) > MAX_OUT:
        data = json.dumps({"ok": False, "error": "response too large; ask for a narrower result"}).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)) + data)
    sys.stdout.buffer.flush()


def main():
    while True:
        op = "?"
        try:
            msg = read_message()
            if msg is None:
                return
            op = msg.get("op", "?") if isinstance(msg, dict) else "?"
            res = handle(msg)
            write_message(dict({"ok": True}, **res))
            log(op, True)
        except (OpError, claude_jobs.JobError) as e:
            write_message({"ok": False, "error": str(e)})
            log(op, False, str(e)[:120])
        except subprocess.TimeoutExpired:
            write_message({"ok": False, "error": "operation timed out"})
            log(op, False, "timeout")
        except Exception as e:  # never crash silently: Chrome would only show "host exited"
            write_message({"ok": False, "error": f"{type(e).__name__}: {e}"[:300]})
            log(op, False, type(e).__name__)


if __name__ == "__main__":
    main()
