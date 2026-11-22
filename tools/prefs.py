#!/usr/bin/env python3
"""Per-user preferences for the job pipeline, kept in master/preferences.json (next to the master resume).

  python3 tools/prefs.py get              all preferences as JSON
  python3 tools/prefs.py get resume_pages one value
  python3 tools/prefs.py set resume_pages 2     (1, 2, 3, 4 or any)

resume_pages: how long a tailored resume should be. A number is checked by tools/check_resume.py and told to Claude as
the trim target; "any" means no page target (nothing is trimmed or padded to a count). Default 2, which is what this
pipeline did before the setting existed."""
import argparse, json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILE = ROOT / "master" / "preferences.json"
DEFAULTS = {"resume_pages": 2}
PAGE_CHOICES = (1, 2, 3, 4, "any")


class PrefError(Exception):
    pass


def normalise(key, value):
    if key not in DEFAULTS:
        raise PrefError(f"unknown preference: {key!r}")
    if key == "resume_pages":
        v = "any" if str(value).strip().lower() in ("any", "none", "0", "no limit") else value
        try:
            v = v if v == "any" else int(v)
        except (TypeError, ValueError):
            raise PrefError(f"resume_pages must be one of {list(PAGE_CHOICES)}")
        if v not in PAGE_CHOICES:
            raise PrefError(f"resume_pages must be one of {list(PAGE_CHOICES)}")
        return v
    return value


def load():
    prefs = dict(DEFAULTS)
    try:
        raw = json.loads(FILE.read_text(encoding="utf-8"))
        for k, v in raw.items():
            try:
                prefs[k] = normalise(k, v)
            except PrefError:
                pass                      # a bad value in the file falls back to the default
    except (OSError, json.JSONDecodeError):
        pass
    return prefs


def save(prefs):
    FILE.parent.mkdir(exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(FILE.parent), prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)
        f.write("\n")
    os.replace(tmp, FILE)


def set_pref(key, value):
    prefs = load()
    prefs[key] = normalise(key, value)
    save(prefs)
    return prefs


def pages_target():
    """The page count to check and trim to, or None for 'any'."""
    v = load()["resume_pages"]
    return None if v == "any" else v


def pages_phrase():
    v = load()["resume_pages"]
    return "any number of pages (no page target; do not trim or pad to a count)" if v == "any" else f"{v} page{'s' if v != 1 else ''}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get"); g.add_argument("key", nargs="?")
    s = sub.add_parser("set"); s.add_argument("key"); s.add_argument("value")
    a = ap.parse_args()
    try:
        if a.cmd == "get":
            prefs = load()
            if a.key and a.key not in prefs:
                raise PrefError(f"unknown preference: {a.key!r}")
            print(json.dumps({"ok": True, "prefs": prefs} if not a.key else {"ok": True, "key": a.key, "value": prefs[a.key]}))
        else:
            print(json.dumps({"ok": True, "prefs": set_pref(a.key, a.value)}))
    except PrefError as e:
        print(json.dumps({"ok": False, "error": str(e)})); sys.exit(1)


if __name__ == "__main__":
    main()
