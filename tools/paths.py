#!/usr/bin/env python3
"""Where things live: the engine (this code) and the data folder (your resume data).

  CODE   the engine: the folder that holds tools/ (the extension, the helper, the scorer, the layouts).
  DATA   your data folder: master/, applications/, tailored/, views/, job-inbox/, .trash/ and master/preferences.json.

By default they are the same folder (a plain clone works exactly as before). To keep your data somewhere else, point the
tools at it; the first of these that is set wins:

  1. the JD_LENS_DATA environment variable (used by tests and by the helper when it starts Claude)
  2. "data_dir" in jdlens.config.json next to tools/ (git-ignored; written by `python3 tools/paths.py set <folder>`)
  3. the engine folder itself

  python3 tools/paths.py show            where the engine and the data folder are, and which rule picked the data folder
  python3 tools/paths.py set <folder>    use this folder for your data (it is created if it does not exist)
  python3 tools/paths.py clear           go back to keeping data in the engine folder
  python3 tools/paths.py init <folder>   create the folders and the sample master resume in <folder> (never overwrites)
"""
import json, os, pathlib, sys, tempfile

CODE = pathlib.Path(__file__).resolve().parent.parent
CONFIG = CODE / "jdlens.config.json"
DATA_FOLDERS = ("master", "applications", "tailored", "views", "job-inbox")


class PathsError(Exception):
    pass


def _read_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def source():
    """Which rule picks the data folder: 'env', 'config' or 'engine'."""
    if os.environ.get("JD_LENS_DATA"):
        return "env"
    return "config" if _read_config().get("data_dir") else "engine"


def data_root():
    env = os.environ.get("JD_LENS_DATA")
    if env:
        return pathlib.Path(env).expanduser().resolve()
    d = _read_config().get("data_dir")
    return pathlib.Path(d).expanduser().resolve() if d else CODE


DATA = data_root()


def _check_folder(folder):
    p = pathlib.Path(str(folder)).expanduser()
    if not p.is_absolute():
        raise PathsError("give the full path of the folder")
    if p.exists() and not p.is_dir():
        raise PathsError(f"{p} is a file, not a folder")
    if p.resolve() in (pathlib.Path("/"), pathlib.Path.home().resolve()):
        raise PathsError("pick a folder of its own, not your home folder or the disk root")
    return p


def init_data_folder(folder):
    """Create the data folders and, when there is no master resume yet, copy the made-up sample one into it.
    Returns whether the sample was added. An existing master resume is never touched."""
    p = _check_folder(folder)
    for d in DATA_FOLDERS[:4]:
        (p / d).mkdir(parents=True, exist_ok=True)
    master, template = p / "master" / "master-resume.md", CODE / "master" / "master-resume.template.md"
    if master.exists() or not template.is_file():
        return False
    import shutil
    shutil.copy2(template, master)
    return True


def set_data_dir(folder):
    p = _check_folder(folder)
    p.mkdir(parents=True, exist_ok=True)
    cfg = _read_config()
    cfg["data_dir"] = str(p.resolve())
    _write_config(cfg)
    return cfg["data_dir"]


def clear_data_dir():
    cfg = _read_config()
    cfg.pop("data_dir", None)
    if cfg:
        _write_config(cfg)
    else:
        try:
            CONFIG.unlink()
        except OSError:
            pass


def _write_config(cfg):
    fd, tmp = tempfile.mkstemp(dir=str(CONFIG.parent), prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    os.replace(tmp, CONFIG)


def info():
    d = data_root()
    return {"engine": str(CODE), "data": str(d), "source": source(), "separate": d != CODE,
            "has_master": (d / "master" / "master-resume.md").is_file(),
            "has_applications": (d / "applications").is_dir()}


def main():
    a = sys.argv[1:]
    try:
        if a[:1] == ["show"] or not a:
            print(json.dumps({"ok": True, **info()}))
        elif a[:1] == ["set"] and len(a) == 2:
            set_data_dir(a[1])
            print(json.dumps({"ok": True, **info()}))
        elif a[:1] == ["init"] and len(a) == 2:
            added = init_data_folder(a[1])
            print(json.dumps({"ok": True, "folder": str(pathlib.Path(a[1]).expanduser()), "sample_added": added}))
        elif a[:1] == ["clear"]:
            clear_data_dir()
            print(json.dumps({"ok": True, **info()}))
        else:
            print(__doc__)
            sys.exit(2)
    except PathsError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
