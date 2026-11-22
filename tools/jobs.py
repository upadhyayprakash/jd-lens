#!/usr/bin/env python3
"""Read and update job applications. Shared by the /job skill and the Chrome extension's native host.

Every command prints one JSON object to stdout. On error it prints {"ok": false, "error": "..."} and exits 1.
The repo root is the parent of this script's folder, so a copy of tools/ + applications/ elsewhere
(for testing) works on that copy and never touches the real files.

Commands:
  list [--status S]                          summaries of all applications
  show <slug>                                frontmatter, sections, rounds, file paths
  status <slug> <status> [--date D] [--note N] change status (sets applied date when applied; appends to Status history)
  round <slug> --round R [--date D] [--interviewer I] [--notes N] [--result X]   add a row to Rounds
  set <slug> <key> <value>                   set resume, fit_score (also records fit_scored), quick_score or keywords
  save-jd <captured.json>                    create a new application from a captured JD record

Every write first copies the old file to applications/.history/<slug>-<timestamp>.md.
"""
import argparse, datetime, json, os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
APPS = ROOT / "applications"
HISTORY = APPS / ".history"
STATUSES = ["considering", "applied", "screening", "interviewing", "offer", "rejected", "withdrawn"]
SETTABLE = {"resume", "fit_score", "quick_score", "keywords"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class Err(Exception):
    pass


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def app_path(slug):
    if not SLUG_RE.match(slug or ""):
        raise Err(f"invalid slug: {slug!r}")
    p = (APPS / f"{slug}.md").resolve()
    if APPS.resolve() not in p.parents:
        raise Err("path escapes applications/")
    if not p.exists():
        raise Err(f"no such application: {slug}")
    return p


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        raise Err("file has no frontmatter")
    return m.group(1), text[m.end():]


def parse_fm(block):
    fm = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith("#"):
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = re.sub(r"\s+#.*$", "", v).strip()
    return fm


def backup(path):
    HISTORY.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    shutil.copy2(path, HISTORY / f"{path.stem}-{stamp}.md")


def write_atomic(path, text):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def set_fm_key(block, key, value):
    """Replace `key: value` in the frontmatter block, keeping any trailing `# comment`. Add the key if missing."""
    pat = re.compile(rf"^({re.escape(key)}:)([ \t]*)([^#\n]*?)([ \t]*(#.*)?)$", re.M)
    m = pat.search(block)
    if m:
        comment = m.group(4) if m.group(5) else ""
        new = f"{key}: {value}".rstrip() + (("  " + comment.strip()) if comment else "")
        return block[:m.start()] + new + block[m.end():]
    return block.rstrip("\n") + f"\n{key}: {value}"


def refresh_views():
    """Regenerate INDEX.md and the HTML views (no PDF, no Chrome needed)."""
    for script, args in (("jobs_table.py", []), ("build_views.py", ["--no-pdf"])):
        p = ROOT / "tools" / script
        if p.exists():
            subprocess.run([sys.executable, str(p), *args], check=False, capture_output=True, cwd=str(ROOT))


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def table_rows(body, heading):
    """Rows (list of cells) of the Markdown table under `## heading`, without the header and separator."""
    m = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    rows = []
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line.strip()):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells and cells[0].lower() != "date":
                    rows.append(cells)
    return rows


def find_location(body):
    m = re.search(r"^- Location:\s*(.+)$", body, re.M) or re.search(r"Locations? listed:\s*([^\n]+)", body)
    v = m.group(1).strip().rstrip(".") if m else ""
    return "" if v.lower() == "not stated" else v[:160]


def last_activity(fm, history, rounds):
    dates = [fm.get("applied", ""), fm.get("captured", "")] + [r[0] for r in rounds] + [h[0] for h in history]
    dates = [d for d in dates if DATE_RE.match(d or "")]
    return max(dates) if dates else ""


def summary(path):
    block, body = split_fm(path.read_text(encoding="utf-8"))
    fm = parse_fm(block)
    res = fm.get("resume", "")
    history, rounds = table_rows(body, "Status history"), table_rows(body, "Rounds")
    return {
        "slug": path.stem, "company": fm.get("company", ""), "role": fm.get("role", ""),
        "status": fm.get("status", ""), "applied": fm.get("applied", ""), "added": fm.get("captured", ""),
        "fit_score": int(fm["fit_score"]) if fm.get("fit_score", "").isdigit() else None, "fit_scored": fm.get("fit_scored", ""),
        "quick_score": int(fm["quick_score"]) if fm.get("quick_score", "").isdigit() else None,
        "posted": fm.get("posted", ""), "source": fm.get("source", ""), "company_url": fm.get("company_url", ""), "location": find_location(body),
        "last_activity": last_activity(fm, history, rounds),
        "resume": res, "resume_exists": bool(res) and (ROOT / res).exists(),
    }


def safe_url(u):
    """Only plain http(s) origins are stored as the company website."""
    u = str(u or "").strip()
    return u if re.match(r"^https?://[A-Za-z0-9.-]+(:\d+)?/?$", u) else ""


def cmd_list(a):
    rows = [summary(p) for p in sorted(APPS.glob("*.md")) if p.name != "INDEX.md"]
    if a.status:
        rows = [r for r in rows if r["status"] == a.status]
    rows.sort(key=lambda r: (-(r["fit_score"] if r["fit_score"] is not None else -1), r["slug"]))
    out({"ok": True, "applications": rows})


def parse_rounds(body):
    m = re.search(r"^## Rounds\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    rows = []
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line.strip()):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells and cells[0].lower() != "date":
                    rows.append(cells)
    return rows


def cmd_show(a):
    p = app_path(a.slug)
    block, body = split_fm(p.read_text(encoding="utf-8"))
    s = summary(p)
    s["frontmatter"] = parse_fm(block)
    s["sections"] = re.findall(r"^##+ (.*)$", body, re.M)
    s["rounds"] = parse_rounds(body)
    s["history"] = table_rows(body, "Status history")
    s["files"] = {
        "application": str(p),
        "resume": str(ROOT / s["resume"]) if s["resume"] else "",
        "details_html": str(ROOT / "views" / "applications.html") + f"#{p.stem}",
    }
    out({"ok": True, "application": s})


HISTORY_HEADER = "| Date | From | To | Note |\n|------|------|----|------|\n"


def add_history(body, old, new, note, initial_date):
    """Append a row to `## Status history` (created on first use). Past rows are never rewritten."""
    today = datetime.date.today().isoformat()
    row = f"| {today} | {old or '-'} | {new} | {clean_cell(note)} |"
    m = re.search(r"^## Status history\s*\n", body, re.M)
    if not m:
        initial = f"| {initial_date or today} | - | {old} | Added |\n" if old else ""
        return body.rstrip("\n") + "\n\n## Status history\n\n" + HISTORY_HEADER + initial + row + "\n"
    sec_end = re.search(r"^## ", body[m.end():], re.M)
    end = m.end() + sec_end.start() if sec_end else len(body)
    section = body[m.end():end].rstrip("\n")
    return body[:m.end()] + section + "\n" + row + "\n" + ("\n" if sec_end else "") + body[end:]


def cmd_status(a):
    if a.status not in STATUSES:
        raise Err(f"status must be one of: {', '.join(STATUSES)}")
    p = app_path(a.slug)
    text = p.read_text(encoding="utf-8")
    block, body = split_fm(text)
    fm0 = parse_fm(block)
    old = fm0.get("status", "")
    if old != a.status:
        body = add_history(body, old, a.status, a.note, fm0.get("captured") or fm0.get("applied"))
    new_block = set_fm_key(block, "status", a.status)
    if a.status == "applied" and not parse_fm(new_block).get("applied"):
        d = a.date or datetime.date.today().isoformat()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            raise Err("date must be YYYY-MM-DD")
        new_block = set_fm_key(new_block, "applied", d)
    backup(p)
    write_atomic(p, f"---\n{new_block}\n---\n{body}")
    refresh_views()
    out({"ok": True, "slug": a.slug, "status": {"from": old, "to": a.status}})


def clean_cell(s):
    return re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()


def cmd_round(a):
    p = app_path(a.slug)
    text = p.read_text(encoding="utf-8")
    d = a.date or datetime.date.today().isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        raise Err("date must be YYYY-MM-DD")
    row = "| " + " | ".join([d, clean_cell(a.round), clean_cell(a.interviewer), clean_cell(a.notes), clean_cell(a.result)]) + " |"
    m = re.search(r"^## Rounds\s*\n", text, re.M)
    if not m:
        text = text.rstrip("\n") + "\n\n## Rounds\n\n| Date | Round | Interviewer | Notes | Result |\n|------|-------|-------------|-------|--------|\n" + row + "\n"
    else:
        sec_end = re.search(r"^## ", text[m.end():], re.M)
        end = m.end() + sec_end.start() if sec_end else len(text)
        section = text[m.end():end].rstrip("\n")
        text = text[:m.end()] + section + "\n" + row + "\n" + ("\n" if sec_end else "") + text[end:]
    backup(p)
    write_atomic(p, text)
    refresh_views()
    out({"ok": True, "slug": a.slug, "row": row})


def cmd_set(a):
    if a.key not in SETTABLE:
        raise Err(f"key must be one of: {', '.join(sorted(SETTABLE))}")
    if a.key in ("fit_score", "quick_score") and not (a.value.isdigit() and 0 <= int(a.value) <= 100):
        raise Err(f"{a.key} must be an integer 0 to 100")
    if a.key == "keywords" and (len(a.value) > 800 or "\n" in a.value):
        raise Err("keywords must be a single line of at most 800 characters, for example: TypeScript, React, Node.js")
    if a.key == "resume" and (a.value.startswith("/") or ".." in pathlib.PurePosixPath(a.value).parts):
        raise Err("resume must be a path relative to the repo, without ..")
    p = app_path(a.slug)
    block, body = split_fm(p.read_text(encoding="utf-8"))
    new_block = set_fm_key(block, a.key, a.value)
    if a.key == "fit_score":                                   # remember when the judged score was given, so a stale one is visible
        new_block = set_fm_key(new_block, "fit_scored", datetime.date.today().isoformat())
    backup(p)
    write_atomic(p, f"---\n{new_block}\n---\n{body}")
    refresh_views()
    out({"ok": True, "slug": a.slug, a.key: a.value})


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def cmd_save_jd(a):
    rec = json.loads(pathlib.Path(a.file).read_text(encoding="utf-8"))
    for k in ("company", "role", "url", "jd_text"):
        if not (rec.get(k) or "").strip():
            raise Err(f"captured record is missing {k}")
    when = (rec.get("captured_at") or datetime.date.today().isoformat())[:7]
    slug = f"{slugify(rec['company'])}-{when}"
    if not SLUG_RE.match(slug):
        raise Err(f"could not make a valid slug from company {rec['company']!r}")
    path = APPS / f"{slug}.md"
    if path.exists():
        raise Err(f"{slug} already exists; not overwriting")
    qs = rec.get("quick_score") or {}
    fm = ["---", f"company: {clean_cell(rec['company'])}", f"role: {clean_cell(rec['role'])}", "applied:",
          f"source: {clean_cell(rec['url'])}", f"company_url: {safe_url(rec.get('company_url'))}", "resume:",
          "status: considering                # " + " | ".join(STATUSES), "fit_score:",
          f"posted: {rec.get('posted') or ''}", f"captured: {(rec.get('captured_at') or datetime.date.today().isoformat())[:10]}",
          f"quick_score: {qs.get('score', '')}", "keywords:", "---", ""]
    body = [f"# {rec['company']}: {rec['role']}", "", "## Captured", "",
            f"- Location: {clean_cell(rec.get('location_text')) or 'not stated'}",
            f"- Salary as posted: {clean_cell(rec.get('salary_text')) or 'not stated'}",
            f"- Extraction: {rec.get('extraction', 'unknown')}", "",
            "## JD (verbatim)", "", rec["jd_text"].strip(), "",
            "## Questions", "", "None yet.", "",
            "## Rounds", "", "| Date | Round | Interviewer | Notes | Result |", "|------|-------|-------------|-------|--------|", "",
            "## Status history", "", HISTORY_HEADER.rstrip("\n"), f"| {(rec.get('captured_at') or datetime.date.today().isoformat())[:10]} | - | considering | Saved from the extension |", ""]
    write_atomic(path, "\n".join(fm) + "\n".join(body))
    refresh_views()
    out({"ok": True, "slug": slug, "file": str(path)})


def _size(p):
    if p.is_dir():
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    return p.stat().st_size


def delete_targets(slug):
    """Every file or folder that belongs to one application, as (kind, path). Only exact matches: the history snapshots are
    matched by `<slug>-<timestamp>.md`, so deleting `soylent-2026-11` never touches `soylent-2026-11-2`."""
    f = app_path(slug)
    found = [("Application file (JD, scores, proposal, Brag Sheet)", f)]
    snap = re.compile(rf"^{re.escape(slug)}-\d{{8}}-\d{{6}}-\d+\.md$")
    snaps = sorted(x for x in HISTORY.glob(f"{slug}-*.md") if snap.match(x.name)) if HISTORY.exists() else []
    if snaps:
        found.append((f"{len(snaps)} automatic backups of the application file", snaps))
    for label, path in (("Tailored resume folder (HTML, PDF, questions and answers)", ROOT / "tailored" / slug),
                        ("Brag Sheet page", ROOT / "views" / "brag" / f"{slug}.html"),
                        ("Saved capture of the job page", ROOT / "job-inbox" / "done" / f"{slug}.json")):
        if path.exists():
            found.append((label, path))
    return found


def cmd_delete(a):
    """Full wipe of one application. Nothing is erased: every piece moves to .trash/<timestamp>-<slug>/ (same folder layout),
    so it can be put back by hand. --dry-run lists what would move."""
    targets = delete_targets(a.slug)
    items = []
    for label, p in targets:
        paths = p if isinstance(p, list) else [p]
        items.append({"label": label, "paths": [str(x.relative_to(ROOT)) for x in paths], "bytes": sum(_size(x) for x in paths)})
    if a.dry_run:
        out({"ok": True, "dry_run": True, "slug": a.slug, "items": items}); return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    trash = ROOT / ".trash" / f"{stamp}-{a.slug}"
    for _, p in targets:
        for x in (p if isinstance(p, list) else [p]):
            dest = trash / x.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(x), str(dest))
    refresh_views()
    out({"ok": True, "slug": a.slug, "items": items, "trash": str(trash.relative_to(ROOT))})


def pdf_pages(path):
    """Page count of a PDF: pdfinfo when it can be found (Chrome starts the helper with a bare PATH, so look in the usual
    Homebrew places too), otherwise a count of /Type /Page objects."""
    exe = shutil.which("pdfinfo") or next((c for c in ("/opt/homebrew/bin/pdfinfo", "/usr/local/bin/pdfinfo") if os.path.exists(c)), None)
    if exe:
        r = subprocess.run([exe, str(path)], capture_output=True, text=True)
        m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
        if m:
            return int(m.group(1))
    n = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", pathlib.Path(path).read_bytes()))
    return n or None


def cmd_resume_info(a):
    """Pages and size of the tailored resume PDF named in the application file."""
    p = app_path(a.slug)
    block, _ = split_fm(p.read_text(encoding="utf-8"))
    res = parse_fm(block).get("resume", "")
    f = (ROOT / res).resolve() if res else None
    if not f or ROOT.resolve() not in f.parents or not f.is_file():
        out({"ok": True, "found": False}); return
    out({"ok": True, "found": True, "pages": pdf_pages(f), "bytes": f.stat().st_size})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--status"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("show"); s.add_argument("slug"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("status"); s.add_argument("slug"); s.add_argument("status"); s.add_argument("--date"); s.add_argument("--note", default=""); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("round"); s.add_argument("slug"); s.add_argument("--round", required=True)
    s.add_argument("--date"); s.add_argument("--interviewer", default=""); s.add_argument("--notes", default=""); s.add_argument("--result", default="")
    s.set_defaults(fn=cmd_round)
    s = sub.add_parser("set"); s.add_argument("slug"); s.add_argument("key"); s.add_argument("value"); s.set_defaults(fn=cmd_set)
    s = sub.add_parser("save-jd"); s.add_argument("file"); s.set_defaults(fn=cmd_save_jd)
    s = sub.add_parser("resume-info"); s.add_argument("slug"); s.set_defaults(fn=cmd_resume_info)
    s = sub.add_parser("delete"); s.add_argument("slug"); s.add_argument("--dry-run", action="store_true"); s.set_defaults(fn=cmd_delete)
    a = ap.parse_args()
    try:
        a.fn(a)
    except Err as e:
        out({"ok": False, "error": str(e)}); sys.exit(1)
    except (OSError, json.JSONDecodeError) as e:
        out({"ok": False, "error": f"{type(e).__name__}: {e}"}); sys.exit(1)


if __name__ == "__main__":
    main()
