#!/usr/bin/env python3
"""Build readable views of the master resume data and the applications.

Writes (all local, in views/):
  views/master-resume.html   master/master-resume.md as a styled page (light and dark)
  views/master-resume.pdf    the same, printed to PDF with headless Chrome
  views/applications.html    every application: table sorted by fit score, then each file's details

Usage (from the repo root):  python3 tools/build_views.py [--no-pdf]
No third-party packages: a small Markdown converter is included for the subset these files use.
"""
import html, pathlib, re, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIEWS = ROOT / "views"

CSS = """
:root{--bg:#fff;--fg:#1b1d21;--fg2:#4a4f57;--fg3:#6b717a;--rule:#dadcdf;--card:#f6f7f8;--code:#eef0f2;--accent:#1b1d21;--ok:#1f7a4d;--warn:#9a6200;color-scheme:light dark}
@media (prefers-color-scheme:dark){:root{--bg:#15171a;--fg:#e8eaed;--fg2:#b6bbc2;--fg3:#8b919a;--rule:#2d3136;--card:#1d2024;--code:#262a2f;--accent:#e8eaed;--ok:#5fc796;--warn:#e0a84a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Open Sans",sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 24px 80px}
h1{font-size:28px;margin:0 0 4px;letter-spacing:-.01em}h2{font-size:20px;margin:36px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--rule)}
h3{font-size:16px;margin:24px 0 8px}h4{font-size:14px;margin:18px 0 6px;color:var(--fg2)}
p{margin:8px 0}ul,ol{margin:6px 0 10px;padding-left:22px}li{margin:3px 0}
a{color:inherit;text-decoration:underline;text-underline-offset:2px}
code{background:var(--code);border-radius:4px;padding:1px 5px;font:12.5px ui-monospace,Menlo,monospace}
pre{background:var(--code);border-radius:8px;padding:12px 14px;overflow:auto}pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:13.5px}
th,td{border:1px solid var(--rule);padding:6px 9px;text-align:left;vertical-align:top}th{background:var(--card);font-weight:600}
hr{border:0;border-top:1px solid var(--rule);margin:26px 0}
.sub{color:var(--fg3);margin:0 0 20px}.pill{display:inline-block;border:1px solid var(--rule);border-radius:999px;padding:0 9px;font-size:12px;background:var(--card)}
.card{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:12px 16px;margin:12px 0}
.kv{display:grid;grid-template-columns:130px 1fr;gap:4px 12px;font-size:13.5px}.kv dt{color:var(--fg3)}.kv dd{margin:0;overflow-wrap:anywhere}
.score{font-weight:700}input[type=checkbox]{margin-right:6px}
.toc{columns:2;font-size:13.5px}.toc a{text-decoration:none}
@media print{body{font-size:11px}main{max-width:none;padding:0}h2{break-after:avoid}table,pre,.card{break-inside:avoid}@page{size:A4;margin:14mm}}
"""

def inline(s):
    s = html.escape(s, quote=False)
    codes = []
    def keep(m):
        codes.append(m.group(1)); return f"\x00{len(codes)-1}\x00"
    s = re.sub(r"`([^`]+)`", keep, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
    return s

def md_to_html(text, base_level=0):
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    def head(level, txt):
        lv = min(6, level + base_level)
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", txt).lower()).strip("-")
        return f'<h{lv} id="{slug}">{inline(txt)}</h{lv}>'
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1; continue
        if ln.startswith("```"):
            i += 1; buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf), quote=False) + "</code></pre>"); continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            out.append(head(len(m.group(1)), m.group(2))); i += 1; continue
        if re.match(r"^-{3,}\s*$", ln):
            out.append("<hr>"); i += 1; continue
        if ln.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            def cells(r): return [c.strip() for c in r.strip().strip("|").split("|")]
            hdr = cells(ln); i += 2; rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(cells(lines[i])); i += 1
            t = "<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in hdr) + "</tr></thead><tbody>"
            for r in rows:
                t += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
            out.append(t + "</tbody></table>"); continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            stack = []  # (indent, tag)
            while i < n and (re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) or (lines[i].startswith("  ") and lines[i].strip() and stack)):
                l = lines[i]
                m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", l)
                if not m:  # continuation line of the previous item
                    out.append(" " + inline(l.strip())); i += 1; continue
                ind, mark, body = len(m.group(1)), m.group(2), m.group(3)
                tag = "ol" if mark[0].isdigit() else "ul"
                while stack and ind < stack[-1][0]:
                    out.append(f"</li></{stack.pop()[1]}>")
                if not stack or ind > stack[-1][0]:
                    stack.append((ind, tag)); out.append(f"<{tag}><li>")
                else:
                    out.append("</li><li>")
                cb = re.match(r"^\[([ xX])\]\s+(.*)$", body)
                if cb:
                    out.append(f'<input type="checkbox" disabled{" checked" if cb.group(1) != " " else ""}>' + inline(cb.group(2)))
                else:
                    out.append(inline(body))
                i += 1
            while stack:
                out.append(f"</li></{stack.pop()[1]}>")
            continue
        buf = [ln.strip()]; i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|```|\s*\||\s*([-*]|\d+\.)\s+|-{3,}\s*$)", lines[i]):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            fm[k.strip()] = re.sub(r"\s+#.*$", "", v).strip()
        text = text[m.end():]
    return fm, text

def page(title, body, sub=""):
    stamp = datetime.date.today().isoformat()
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main><h1>{html.escape(title)}</h1>"
            f'<p class="sub">{sub} Generated {stamp} by tools/build_views.py. Local file, do not share.</p>{body}</main></body></html>')

def build_master():
    src = (ROOT / "master" / "master-resume.md").read_text()
    body = md_to_html(re.sub(r"^# .*\n", "", src, count=1))
    toc = "".join(f'<li><a href="#{re.sub(r"[^a-z0-9]+","-",h.lower()).strip("-")}">{html.escape(h)}</a></li>'
                  for h in re.findall(r"^## (.*)$", src, re.M))
    body = f'<div class="card"><strong>Sections</strong><ul class="toc">{toc}</ul></div>' + body
    out = VIEWS / "master-resume.html"
    out.write_text(page("Master resume data: Alex Morgan", body, "Source: master/master-resume.md."))
    return out

def build_applications():
    apps = []
    for f in sorted((ROOT / "applications").glob("*.md")):
        if f.name == "INDEX.md":
            continue
        fm, body = frontmatter(f.read_text())
        score = fm.get("fit_score", "")
        apps.append((int(score) if score.isdigit() else -1, f, fm, body))
    apps.sort(key=lambda a: (-a[0], a[1].name))
    rows = ""
    for s, f, fm, _ in apps:
        res = fm.get("resume", "")
        rlink = f'<a href="../{html.escape(res)}">PDF</a>' if res else ""
        src = fm.get("source", "")
        slink = f'<a href="{html.escape(src)}">posting</a>' if src.startswith("http") else html.escape(src)
        rows += (f'<tr><td class="score">{s if s >= 0 else ""}</td><td><a href="#{f.stem}">{html.escape(fm.get("company",""))}</a></td>'
                 f'<td>{html.escape(fm.get("role",""))}</td><td><span class="pill">{html.escape(fm.get("status",""))}</span></td>'
                 f'<td>{html.escape(fm.get("applied",""))}</td><td>{rlink}</td><td>{slink}</td></tr>')
    table = ('<table><thead><tr><th>Score</th><th>Company</th><th>Role</th><th>Status</th><th>Applied</th><th>Resume sent</th><th>Source</th></tr></thead>'
             f"<tbody>{rows}</tbody></table>")
    details = ""
    for s, f, fm, body in apps:
        kv = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v) or '<span class=sub>(blank)</span>'}</dd>" for k, v in fm.items() if k not in ("keywords",))
        details += (f'<section id="{f.stem}"><h2>{html.escape(fm.get("company",""))}: {html.escape(fm.get("role",""))}</h2>'
                    f'<div class="card"><dl class="kv">{kv}</dl><p class="sub">File: applications/{f.name}</p></div>'
                    + md_to_html(re.sub(r"^# .*\n", "", body, count=1, flags=re.M), base_level=1) + "</section>")
    out = VIEWS / "applications.html"
    out.write_text(page("Applications", table + details, f"{len(apps)} applications, sorted by fit score."))
    return out

def build_brag():
    """One printable page per application that has a '## Brag Sheet' section: views/brag/<slug>.html."""
    out_dir = VIEWS / "brag"
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for f in sorted((ROOT / "applications").glob("*.md")):
        if f.name == "INDEX.md":
            continue
        fm, body = frontmatter(f.read_text())
        m = re.search(r"^## Brag Sheet[^\n]*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
        if not m:
            continue
        out = out_dir / f"{f.stem}.html"
        title = f"Brag Sheet: {fm.get('company', '')}, {fm.get('role', '')}"
        out.write_text(page(title, md_to_html(m.group(1).strip(), base_level=1),
                            f"Your quick reference for this application. Source: applications/{f.name}."))
        made.append(out)
    return made

def main():
    VIEWS.mkdir(exist_ok=True)
    made = [build_master(), build_applications()]
    made += build_brag()
    if "--no-pdf" not in sys.argv:
        pdf = VIEWS / "master-resume.pdf"
        subprocess.run([str(ROOT / "tools" / "render_pdf.sh"), str(made[0]), str(pdf)], check=True, capture_output=True)
        made.append(pdf)
    for p in made:
        print(p)

if __name__ == "__main__":
    main()
