#!/usr/bin/env python3
"""Add a skill to your master resume WITH the evidence that backs it, so it counts when a job description is scored.

  python3 tools/add_skill.py "Python" --group Backend --fact "Used Python for ETL scripts and data analysis at Brightlabs (2019 to 2020)"
        [--level user-confirmed|listed|partial] [--years "since 2019"] [--note "text"] [--no-rebuild] [--dry-run]

What it does (and nothing else):
  1. writes a short fact (F-USR-NN) under section 3 of master/master-resume.md: the evidence
  2. adds the skill to your skills table (section 5) in the group you name, pointing at that fact
     (if the skill is already listed, it raises its level and adds the new evidence instead)
  3. keeps a backup of the file in master/.history/ and rebuilds the skill profile the extension reads
Then press "Rescore saved JDs" in the panel (Resume > Profile) and run "Get the full score" again on a JD that matters.

A skill with no evidence is refused on purpose: the score is only as honest as this file. Never commits anything.
"""
import argparse, datetime, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402  (where the data folder is)
MASTER = paths.DATA / "master" / "master-resume.md"
RANK = {"none": 0, "earlier": 1, "partial": 2, "listed": 3, "user-confirmed": 3}


def die(msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(1)


def table_rows(sec):
    """(start, end, cells) of every data row of every table in the section, whatever the spacing inside the cells."""
    pos = 0
    for line in sec.splitlines(keepends=True):
        start, pos = pos, pos + len(line)
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|\s*$", line.strip()):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 5 and cells[0].lower() != "skill":
                yield start, start + len(line.rstrip("\n")), cells


def section_span(text, num):
    m = re.search(rf"^## {num}\. .*?$", text, re.M)
    if not m:
        die(f"master file has no section '## {num}.' (compare it with master/master-resume.template.md)")
    n = re.search(r"^## \d+\. ", text[m.end():], re.M)
    return m.start(), m.end() + (n.start() if n else len(text) - m.end())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill")
    ap.add_argument("--group", help="skills group in section 5, for example Backend (see the headings in your file)")
    ap.add_argument("--fact", required=True, help="the evidence: where and how you used it (15 to 400 characters)")
    ap.add_argument("--level", default="user-confirmed", choices=["user-confirmed", "listed", "partial"])
    ap.add_argument("--years", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--no-rebuild", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    name, fact = a.skill.strip(), " ".join(a.fact.split())
    for label, v in (("skill", name), ("years", a.years), ("note", a.note)):
        if "|" in v or "\n" in v:
            die(f"the {label} cannot contain a pipe or a newline")
    if not (1 <= len(name) <= 40):
        die("the skill name must be 1 to 40 characters")
    if not (15 <= len(fact) <= 400):
        die("--fact must say where and how you used it (15 to 400 characters). A skill without evidence is not added.")
    if not MASTER.exists():
        die("master/master-resume.md does not exist; run python3 tools/setup.py first")
    text = MASTER.read_text(encoding="utf-8")

    # ---- the skills table
    s5a, s5b = section_span(text, 5)
    sec5 = text[s5a:s5b]
    groups = re.findall(r"^### (.+)$", sec5, re.M)
    existing = None
    for _, _, cells in table_rows(sec5):
        names = [x.strip().lower() for x in cells[0].split(",")]
        if name.lower() in names:
            if len(names) > 1:
                die(f"'{name}' is listed together with other skills in the row '{cells[0]}'. Edit that row by hand, or split it.")
            existing = cells
    if existing is None:
        if not a.group:
            die("which group? add --group with one of: " + ", ".join(groups))
        match = [g for g in groups if g.lower() == a.group.strip().lower()]
        if not match:
            die(f"no group '{a.group}' in section 5. Groups in your file: " + ", ".join(groups))

    # ---- the new fact id and where it goes
    ids = [int(x) for x in re.findall(r"F-USR-(\d+)", text)]
    fid = f"F-USR-{(max(ids) + 1 if ids else 1):02d}"
    fact_line = f"- **{fid}** {fact}"
    s3a, s3b = section_span(text, 3)
    sec3 = text[s3a:s3b]
    today = datetime.date.today().isoformat()
    blk = re.search(r"^### (?:Cross-company skill statements|Skill statements)[^\n]*\n", sec3, re.M)
    if blk:
        after = sec3[blk.end():]
        nxt = re.search(r"^### |\Z", after, re.M)
        block_body = after[:nxt.start()]
        last = list(re.finditer(r"^- \*\*F-USR-\d+\*\*.*$", block_body, re.M))
        ins = blk.end() + (last[-1].end() if last else 0)
        new_sec3 = sec3[:ins] + ("\n" if last else "") + fact_line + ("\n" if not last else "") + sec3[ins:]
    else:
        tail = re.search(r"\n*(?:---\s*\n*)?\Z", sec3)
        cut = tail.start() if tail else len(sec3)
        new_sec3 = sec3[:cut].rstrip("\n") + f"\n\n### Skill statements (user-confirmed {today})\n\n" + fact_line + "\n\n" + sec3[cut:].lstrip("\n")
    text2 = text[:s3a] + new_sec3 + text[s3b:]

    # ---- recompute section 5 in the updated text, then edit the table
    s5a, s5b = section_span(text2, 5)
    sec5 = text2[s5a:s5b]
    if existing is not None:
        start, end, cells = next((st, en, c) for st, en, c in table_rows(sec5) if c[0].strip().lower() == name.lower())
        old_level = cells[1].strip("` ").lower()
        level = a.level if RANK.get(a.level, 0) >= RANK.get(old_level, 0) else old_level
        ev = f"{cells[2]}, {fid}" if cells[2] else fid
        row = f"| {cells[0]} | {level} | {ev} | {a.years or cells[3]} | {a.note or cells[4]} |"
        sec5 = sec5[:start] + row + sec5[end:]
        action = f"raised '{name}' from {old_level} to {level}" if level != old_level else f"added evidence to '{name}' (already {old_level})"
    else:
        g = match[0]
        hm = re.search(rf"^### {re.escape(g)}\s*$", sec5, re.M)
        rest = sec5[hm.end():]
        nxt = re.search(r"^### |\Z", rest, re.M)
        body = rest[:nxt.start()]
        rows = list(re.finditer(r"^\|.*\|[ \t]*$", body, re.M))            # no newline: insert at the end of the last row line
        if not rows:
            die(f"the '{g}' group has no table; compare with master/master-resume.template.md")
        pos = hm.end() + rows[-1].end()
        row = f"| {name} | {a.level} | {fid} | {a.years} | {a.note} |"
        sec5 = sec5[:pos] + "\n" + row + sec5[pos:]
        action = f"added '{name}' to {g} as {a.level}"
    text3 = text2[:s5a] + sec5 + text2[s5b:]

    print(f"{action}\n  evidence {fid}: {fact}\n  row: {row}")
    if a.dry_run:
        print("dry run: nothing written")
        return
    hist = MASTER.parent / ".history"
    hist.mkdir(exist_ok=True)
    shutil.copy2(MASTER, hist / f"master-resume-{datetime.datetime.now():%Y%m%d-%H%M%S-%f}.md")      # microseconds: two edits in one second must not share a backup
    MASTER.write_text(text3, encoding="utf-8")
    print("saved. Backup in master/.history/")
    if not a.no_rebuild:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_profile.py")], cwd=str(ROOT), capture_output=True, text=True)
        print("skill profile rebuilt" if r.returncode == 0 else "could not rebuild the profile: " + (r.stderr or r.stdout)[:200])
    print("Next: in the panel press Rescore saved JDs (Resume > Profile), then Get the full score on a JD that matters.")


if __name__ == "__main__":
    main()
