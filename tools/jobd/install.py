#!/usr/bin/env python3
"""Install (or remove) the native messaging host for the JD Lens Chrome extension.

What it does:
  1. writes tools/jobd/jobd-launcher.sh   (a 2-line script Chrome runs; it starts host.py with this Python)
  2. writes tools/jobd/jobd.config.json   (absolute paths to python, node and claude, found now)
  3. writes the host manifest com.jdlens.helper.json into Chrome's NativeMessagingHosts folder,
     allowing ONLY this extension's ID (tools/jd-capture-extension/EXTENSION_ID) to start the host.

Usage:  python3 tools/jobd/install.py [--uninstall] [--dry-run] [--manifest-dir DIR] [--extension-id ID]
Re-run it if the repo folder moves, or Python / Claude is reinstalled elsewhere.
"""
import argparse, json, os, pathlib, shutil, stat, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
NAME = "com.jdlens.helper"
DEFAULT_DIR = pathlib.Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--manifest-dir", default=str(DEFAULT_DIR))
    ap.add_argument("--extension-id")
    a = ap.parse_args()
    mdir = pathlib.Path(a.manifest_dir)
    manifest = mdir / f"{NAME}.json"

    if a.uninstall:
        for f in (manifest, HERE / "jobd-launcher.sh", HERE / "jobd.config.json"):
            if f.exists():
                print("remove", f)
                if not a.dry_run:
                    f.unlink()
        return

    ext_id = a.extension_id or (ROOT / "tools" / "jd-capture-extension" / "EXTENSION_ID").read_text().strip()
    if len(ext_id) != 32 or not ext_id.isalpha() or not ext_id.islower():
        sys.exit(f"bad extension id: {ext_id!r}")
    py = sys.executable  # keep the stable path (for example /opt/homebrew/opt/python@3.14/...), not the versioned Cellar path
    claude = shutil.which("claude") or ""
    node = shutil.which("node") or ""
    launcher = HERE / "jobd-launcher.sh"
    config = {"python": py, "claude": claude, "node": node}
    body = {"name": NAME, "description": "JD Lens local helper (reads and updates your job application files)",
            "path": str(launcher), "type": "stdio", "allowed_origins": [f"chrome-extension://{ext_id}/"]}

    print(f"python : {py}\nclaude : {claude or 'NOT FOUND (Claude actions will be unavailable)'}\nnode   : {node or 'not found'}")
    print(f"host   : {launcher}\nmanifest: {manifest}\nallowed: {body['allowed_origins'][0]}")
    if a.dry_run:
        print("dry run: nothing written")
        return
    launcher.write_text(f'#!/bin/sh\nexec "{py}" "{HERE / "host.py"}"\n')
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    (HERE / "jobd.config.json").write_text(json.dumps(config, indent=2) + "\n")
    mdir.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(body, indent=2) + "\n")
    print("installed. Reload the extension in chrome://extensions if it was already open.")


if __name__ == "__main__":
    main()
