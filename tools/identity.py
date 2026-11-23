#!/usr/bin/env python3
"""Who the resume is for: the contact block and the file-name stem, read from Section 1 of your master resume.

  python3 tools/identity.py         JSON: name, file_stem, headline, location, email, phone, portfolio, linkedin, github, education

The values come only from the table under `## 1.` in master/master-resume.md (in your data folder). A row that is missing or empty
is returned as "" so a layout can leave that line out. The file stem is the name in lower case with spaces as underscores
(Anika Verma gives anika_verma), used for tailored resume file names like anika_verma_resume_<company>.pdf."""
import json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402  (where the data folder is)

FIELDS = {"name": "name", "location": "location", "email": "email", "phone": "phone", "portfolio": "portfolio", "linkedin": "linkedin",
          "github": "github", "headline": "headline", "education": "education"}


def read(text=None):
    if text is None:
        f = paths.DATA / "master" / "master-resume.md"
        text = f.read_text(encoding="utf-8") if f.is_file() else ""
    m = re.search(r"^## 1\..*?(?=^## 2\.)", text, re.S | re.M)
    out = {k: "" for k in FIELDS}
    for line in (m.group(0) if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or line.lstrip()[:1] != "|":
            continue
        label = re.sub(r"\s*\(.*?\)\s*", "", cells[0]).strip().lower()          # "Headline (Oct 2026)" is the headline row
        if label in FIELDS and not set(cells[0]) <= set("-: "):
            out[FIELDS[label]] = cells[1]
    stem = re.sub(r"[^a-z0-9]+", "_", out["name"].lower()).strip("_")
    out["file_stem"] = stem or "resume"
    return out


if __name__ == "__main__":
    print(json.dumps(dict(ok=True, **read())))
