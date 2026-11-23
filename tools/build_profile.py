#!/usr/bin/env python3
"""Build the data files the Chrome extension reads, from the master resume and the applications.

Writes to tools/jd-capture-extension/data/:
  profile.json       skills tables (skill text, level, evidence IDs), career start, domain words, repo path, master hash, stats
  resume.json        the readable resume for the panel: summaries, experience facts, skills by group, awards, certifications,
                     education (no phone, email or other contact details)
  applications.json  short summary of each application (from tools/jobs.py list)

Deliberately NOT included: contact details, compensation, notes, stories, answers, summaries,
project descriptions, anything outside the skills tables. Run `--show` to print exactly what is held.

Usage (repo root):  python3 tools/build_profile.py [--show] [--check]
  --show   print profile.json after writing
  --check  do not write; exit 0 if profile.json matches the current master file, 1 if stale
"""
import datetime, hashlib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402  (where the data folder is)
MASTER = paths.DATA / "master" / "master-resume.md"
CACHE = ROOT / "tools" / "jd-capture-extension" / "data"      # the generated files the extension reads (they stay with the extension)
LEVELS = {"listed", "user-confirmed", "partial", "earlier", "none"}
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
# Domain words the scorer may match JD text against. A word is included only if it appears in the master file.
DOMAINS = {
    "SaaS": r"\bSaaS\b", "payments": r"\bpayments?\b", "fintech": r"\bfintech\b", "ed-tech": r"\bed-?tech\b",
    "real-time": r"\breal-?time\b", "video streaming": r"\bvideo (?:streaming|platform)\b", "e-commerce": r"\be-?commerce\b",
    "analytics": r"\banalytics\b", "dashboards": r"\bdashboards?\b", "AI": r"\bLLMs?\b", "machine learning": r"\bmachine learning\b|\bML\b",
}


def master_text():
    return MASTER.read_text(encoding="utf-8")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def career_start(text):
    m = re.search(r"\|\s*Career start\s*\|\s*(\w{3})\w*\s+(\d{4})", text)
    if not m:
        raise SystemExit("master file has no 'Career start' row")
    return f"{m.group(2)}-{MONTHS[m.group(1)[:3].title()]:02d}"


def skill_rows(text):
    m = re.search(r"^## 5\. Skills inventory\s*\n(.*?)(?=^## 6\.)", text, re.S | re.M)
    if not m:
        raise SystemExit("master file has no section '## 5. Skills inventory'")
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "skill":
            continue
        level = cells[1].strip("` ").lower()
        if level not in LEVELS:
            continue
        rows.append({"skills": cells[0], "level": level, "evidence": re.findall(r"F-[A-Z]+-\d+", cells[2])})
    return rows


FACT_RE = re.compile(r"^- \*\*(F-[A-Z]+-\d+)\*\*\s*(?:\(([^)]*)\))?\s*(.*)$")
CUT_RE = re.compile(r"\s+(?:Tags:|Story:|Numbers?:|Related:)")


def clean_fact(text):
    needs = "`confirm`" in text
    text = CUT_RE.split(text)[0].replace("`", "").strip()
    return text, needs


def section(text, num):
    m = re.search(rf"^## {num}\. .*?\n(.*?)(?=^## \d+\. |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def parse_heading(h):
    """'### Payly Financial, Senior Fullstack Developer (Lead) (May 2022 to Aug 2024, Bengaluru)'"""
    meta = ""
    m = re.search(r"\(([^()]*)\)\s*$", h)
    if m:
        meta, h = m.group(1), h[:m.start()].strip()
    depth, cut = 0, -1
    for i, ch in enumerate(h):
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            cut = i
            break
    company, title = (h[:cut], h[cut + 1:]) if cut >= 0 else (h, "")
    period, _, loc = meta.partition(", ")
    return {"company": company.strip(), "title": title.strip(), "period": period.strip(), "location": loc.strip()}


def resume_data(text):
    out = {"schema": 1, "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "master_modified": datetime.datetime.fromtimestamp(MASTER.stat().st_mtime).astimezone().isoformat(timespec="seconds")}
    m = re.search(r"\|\s*Headline[^|]*\|\s*([^|]+?)\s*\|", text)
    out["headline"] = m.group(1) if m else ""
    m = re.search(r"\|\s*Education\s*\|\s*([^|]+?)\s*\|", text)
    out["education"] = m.group(1) if m else ""
    out["career_start"] = career_start(text)
    out["summaries"] = []
    for line in section(text, 2).splitlines():
        m = re.match(r"^- \*\*(S-[A-Z]+)(?: \(([^)]*)\))?:\*\*\s*(.*?)(?:\s*\[(F-[^\]]+)\])?$", line)
        if m:
            out["summaries"].append({"id": m.group(1), "note": m.group(2) or "", "text": m.group(3).strip(), "facts": re.findall(r"F-[A-Z]+-\d+", m.group(4) or "")})
    facts, companies, cur = {}, [], None
    for line in section(text, 3).splitlines():
        if line.startswith("### "):
            cur = dict(parse_heading(line[4:]), facts=[])
            companies.append(cur)
            continue
        m = FACT_RE.match(line)
        if m and cur is not None:
            status = (m.group(2) or "user-confirmed").split(",")[0].strip()
            body, needs = clean_fact(m.group(3))
            f = {"id": m.group(1), "status": status, "text": body, "needs_confirm": needs}
            cur["facts"].append(f)
            facts[f["id"]] = dict(f, where=cur["company"])
    out["companies"] = companies
    groups = {"F-AW": "awards", "F-CE": "certifications", "F-OW": "open_work", "F-OTH": "other"}
    for g in groups.values():
        out[g] = []
    for line in section(text, 4).splitlines():
        m = FACT_RE.match(line)
        if m:
            status = (m.group(2) or "user-confirmed").split(",")[0].strip()
            body, needs = clean_fact(m.group(3))
            f = {"id": m.group(1), "status": status, "text": body, "needs_confirm": needs}
            out[groups.get(m.group(1).rsplit("-", 1)[0], "other")].append(f)
            facts[f["id"]] = dict(f, where="Awards and more")
    out["facts"] = facts
    skills, cur = [], None
    for line in section(text, 5).splitlines():
        if line.startswith("### "):
            cur = {"group": line[4:].strip(), "rows": []}
            skills.append(cur)
            continue
        if cur is None or not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "skill" or cells[1].strip("` ").lower() not in LEVELS:
            continue
        cur["rows"].append({"skills": cells[0], "level": cells[1].strip("` ").lower(), "evidence": re.findall(r"F-[A-Z]+-\d+", cells[2]),
                            "years": cells[3] if len(cells) > 3 else "", "notes": cells[-1].replace("`", "") if len(cells) > 4 else ""})
    out["skills"] = skills
    return out


def domain_words(text):
    return sorted(k for k, rx in DOMAINS.items() if re.search(rx, text, re.I if k not in ("AI",) else 0))


def applications():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "jobs.py"), "list"], capture_output=True, text=True)
    data = json.loads(r.stdout)
    return data["applications"] if data.get("ok") else []


def build():
    text = master_text()
    rows = skill_rows(text)
    return {
        "schema": 1,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "master_sha256": sha(text),
        "repo_path": str(paths.DATA),
        "career_start": career_start(text),
        "domains": domain_words(text),
        "rows": rows,
        "master_modified": datetime.datetime.fromtimestamp(MASTER.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        "stats": {"skill_rows": len(rows), "evidence_entries": len({e for r in rows for e in r["evidence"]})},
    }


def main():
    if not MASTER.exists():
        print(f"No master resume at {MASTER}.\nRun `python3 tools/setup.py` (it creates one from the sample), or choose your data folder in the panel's Settings.", file=sys.stderr)
        sys.exit(1)
    CACHE.mkdir(parents=True, exist_ok=True)
    pf = CACHE / "profile.json"
    if "--check" in sys.argv:
        ok = pf.exists() and json.loads(pf.read_text()).get("master_sha256") == sha(master_text())
        print("profile is current" if ok else "profile is STALE (run tools/build_profile.py)")
        sys.exit(0 if ok else 1)
    prof = build()
    pf.write_text(json.dumps(prof, indent=2, ensure_ascii=False) + "\n")
    (CACHE / "resume.json").write_text(json.dumps(resume_data(master_text()), indent=2, ensure_ascii=False) + "\n")
    apps = {"schema": 1, "generated_at": prof["generated_at"], "applications": applications()}
    (CACHE / "applications.json").write_text(json.dumps(apps, indent=2, ensure_ascii=False) + "\n")
    print(f"profile.json: {len(prof['rows'])} skill rows, career start {prof['career_start']}, {len(prof['domains'])} domain words")
    print(f"applications.json: {len(apps['applications'])} applications")
    print("resume.json: written")
    if "--show" in sys.argv:
        print(pf.read_text())


if __name__ == "__main__":
    main()
