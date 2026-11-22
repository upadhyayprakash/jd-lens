#!/usr/bin/env python3
"""Build a clean zip of the JD Lens extension for the Chrome Web Store.

  python3 tools/package_extension.py                 -> dist/jd-lens-<version>.zip (store build: no manifest "key")
  python3 tools/package_extension.py --keep-key      -> keep the manifest "key" (a build that keeps the local extension ID)
  python3 tools/package_extension.py --out path.zip

Left out on purpose: data/ (your skill profile, resume and applications), mock.js (the dev stub; its script tags are removed from the
pages), README.md, EXTENSION_ID, manifest-key.txt and the icon sources. Fails if a staged file mentions a home-directory path or an
email address, or if the manifest points at a file that is not in the package."""
import argparse, json, pathlib, re, shutil, sys, tempfile, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXT = ROOT / "tools" / "jd-capture-extension"
SKIP_NAMES = {"data", "mock.js", "README.md", "EXTENSION_ID", "manifest-key.txt", ".DS_Store", "__pycache__", "logo.svg", "logo-toolbar.svg", "store-icon.png"}
TEXT_EXT = {".js", ".html", ".css", ".json", ".svg", ".md", ".txt"}
BAD = [(re.compile(r"/Users/[A-Za-z0-9._-]+"), "a home-directory path"), (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"), "an email address")]


def stage(dst, keep_key):
    for p in sorted(EXT.rglob("*")):
        rel = p.relative_to(EXT)
        if any(part in SKIP_NAMES for part in rel.parts) or p.is_dir():
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
    for page in dst.glob("*.html"):                      # the dev stub is not shipped, so its script tag goes too
        page.write_text(re.sub(r'\s*<script src="mock\.js"></script>', "", page.read_text(encoding="utf-8")), encoding="utf-8")
    m = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))
    if not keep_key:
        m.pop("key", None)
    (dst / "manifest.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    return m


def check(dst, m):
    problems = []
    refs = [m.get("background", {}).get("service_worker"), m.get("side_panel", {}).get("default_path")]
    refs += list(m.get("icons", {}).values()) + list(m.get("action", {}).get("default_icon", {}).values())
    for r in filter(None, refs):
        if not (dst / r).exists():
            problems.append(f"manifest points at {r}, which is not in the package")
    for p in dst.rglob("*"):
        if p.is_file() and p.suffix in TEXT_EXT:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for rx, what in BAD:
                for hit in rx.findall(text):
                    problems.append(f"{p.relative_to(dst)} contains {what}: {hit}")
            if p.suffix == ".html" and "mock.js" in text:
                problems.append(f"{p.relative_to(dst)} still loads mock.js")
    if (dst / "data").exists():
        problems.append("data/ is in the package")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out"); ap.add_argument("--keep-key", action="store_true")
    a = ap.parse_args()
    version = json.loads((EXT / "manifest.json").read_text())["version"]
    out = pathlib.Path(a.out) if a.out else ROOT / "dist" / f"jd-lens-{version}.zip"
    with tempfile.TemporaryDirectory(prefix="jdlens-pkg-") as t:
        dst = pathlib.Path(t) / "pkg"
        m = stage(dst, a.keep_key)
        problems = check(dst, m)
        if problems:
            print("NOT packaged:"); [print(" -", p) for p in problems]; sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        files = sorted(f for f in dst.rglob("*") if f.is_file())
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                zi = zipfile.ZipInfo(str(f.relative_to(dst)), date_time=(2026, 1, 1, 0, 0, 0))   # fixed time: same bytes every build
                zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
                z.writestr(zi, f.read_bytes())
    print(f"{out}  ({out.stat().st_size // 1024} KB, {len(files)} files, version {version}, manifest key {'kept' if a.keep_key else 'removed'})")


if __name__ == "__main__":
    main()
