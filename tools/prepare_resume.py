#!/usr/bin/env python3
"""Start a tailored resume: copy the chosen layout into the application's folder with your contact block and photo filled in.

  python3 tools/prepare_resume.py <slug> [--force]

Writes tailored/<slug>/<name>_resume_<company>.html in your data folder (for example anika_verma_resume_northwind.html). The layout
is the one chosen in Settings (yours in the data folder's tailored/_base/layouts/ if you have one, otherwise the shipped one).
The layouts carry made-up sample contact details; every one of them is replaced by the matching row of section 1 of your master
resume, and a line whose row is empty is left out. With the photo layout and a master/photo.jpg, the photo is linked in.
Nothing is invented: a value comes from your master resume or it is not there.

If the file already exists it is left alone (it may hold edits) unless you pass --force. With --force it starts over from the layout, and the
previous HTML (and the PDF next to it) are first copied to tailored/<slug>/.history/, so nothing is lost. Prints one line of JSON."""
import html, json, pathlib, re, shutil, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import identity, paths, prefs  # noqa: E402

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FIELDS = ("name", "email", "phone", "location", "portfolio", "linkedin", "github", "headline")


class PrepError(Exception):
    pass


def company_of(slug):
    f = paths.DATA / "applications" / f"{slug}.md"
    if not f.is_file():
        raise PrepError(f"no such application: {slug}")
    m = re.search(r"^company:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
    return re.sub(r"[^a-z0-9]+", "", (m.group(1).strip() if m else slug).split()[0].lower()) or slug.split("-")[0]


def sample_identity():
    t = paths.CODE / "master" / "master-resume.template.md"
    return identity.read(t.read_text(encoding="utf-8")) if t.is_file() else {}


def _drop_row(text, sample):
    """Remove the `<div><dt>Label</dt><dd>...sample...</dd></div>` row that holds this sample value."""
    pat = re.compile(r"[ \t]*<div><dt>[^<]*</dt><dd>(?:(?!</dd>).)*?" + re.escape(sample) + r"(?:(?!</dd>).)*?</dd></div>[ \t]*\n?", re.S)
    return pat.subn("", text)


def fill(text, mine, sample):
    """Swap the sample contact values for the real ones. Returns (text, replaced, removed)."""
    replaced, removed = [], []
    for k in FIELDS:
        s, r = sample.get(k, ""), mine.get(k, "")
        if not s or s == r:
            continue
        s_esc = html.escape(s, quote=False)
        if s_esc not in text and s not in text:
            continue
        if r:
            text = text.replace(s_esc, html.escape(r, quote=False)).replace(s, html.escape(r, quote=False))
            replaced.append(k)
        else:
            text, n = _drop_row(text, s_esc)
            if not n:                                           # an inline contact line: take the value out and tidy the separators
                text = text.replace(s_esc, "")
                text = re.sub(r"(\s*\|\s*){2,}", " | ", text)
                text = re.sub(r">\s*\|\s*", ">", text)
                text = re.sub(r"\s*\|\s*<", "<", text)
            removed.append(k)
    return text, replaced, removed


def set_photo(text):
    pat = re.compile(r'(<div class="photo"><img src=")[^"]*(" alt=")[^"]*(")')
    return pat.subn(r"\1../../master/photo.jpg\2Profile photo\3", text)


def prepare(slug, force=False):
    if not SLUG_RE.match(slug or ""):
        raise PrepError(f"invalid slug: {slug!r}")
    company = company_of(slug)
    mine = identity.read()
    if not mine["name"]:
        raise PrepError("section 1 of master/master-resume.md has no Name row; add it, then run this again")
    layout = pathlib.Path(prefs.layout_file())
    if not layout.is_file():
        raise PrepError(f"layout file not found: {layout}")
    out = paths.DATA / "tailored" / slug / f"{mine['file_stem']}_resume_{company}.html"
    info = {"ok": True, "file": str(out), "layout": prefs.load()["resume_layout"], "layout_file": str(layout), "created": False}
    if out.exists() and not force:
        return dict(info, note="already exists; edit it, or pass --force to start over")
    backup = []
    if out.exists():                                        # starting over: keep what was there (a rebuild is not a reason to lose it)
        hist = out.parent / ".history"
        hist.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        for old in (out, out.with_suffix(".pdf")):
            if old.is_file():
                n, dest = 0, hist / f"{old.stem}-{stamp}{old.suffix}"
                while dest.exists():                        # two start-overs in one second must not replace each other's backup
                    n += 1
                    dest = hist / f"{old.stem}-{stamp}-{n}{old.suffix}"
                shutil.copy2(old, dest)
                backup.append(str(dest))
    text, replaced, removed = fill(layout.read_text(encoding="utf-8"), mine, sample_identity())
    photo = False
    if (paths.DATA / "master" / "photo.jpg").is_file():
        text, n = set_photo(text)
        photo = bool(n)
    leftover = [k for k, v in sample_identity().items() if k in FIELDS and v and v != mine.get(k) and v in text]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return dict(info, created=True, filled=replaced, left_out=removed, photo_linked=photo, sample_values_left=leftover, backed_up=backup)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    try:
        if len(args) != 1:
            raise PrepError("usage: python3 tools/prepare_resume.py <slug> [--force]")
        print(json.dumps(prepare(args[0], "--force" in sys.argv)))
    except PrepError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
