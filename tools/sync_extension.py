#!/usr/bin/env python3
"""Copy the shared scorer into the extension (an unpacked extension cannot read files outside its own folder).
Usage: python3 tools/sync_extension.py [--check]   (--check: exit 1 if the copies differ)"""
import pathlib, shutil, sys
ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "jd-scorer"
DST = ROOT / "jd-capture-extension" / "lib"
FILES = ["vocab.js", "score.js"]
def main():
    DST.mkdir(exist_ok=True)
    diff = [f for f in FILES if not (DST / f).exists() or (DST / f).read_bytes() != (SRC / f).read_bytes()]
    if "--check" in sys.argv:
        print("extension lib is current" if not diff else "STALE: " + ", ".join(diff))
        sys.exit(1 if diff else 0)
    for f in FILES:
        shutil.copy2(SRC / f, DST / f)
    print("synced:", ", ".join(FILES))
if __name__ == "__main__":
    main()
