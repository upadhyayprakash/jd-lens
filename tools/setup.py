#!/usr/bin/env python3
"""One-command setup for JD Lens. Safe to run again: it never overwrites your master resume.

  python3 tools/setup.py [--no-helper] [--manifest-dir DIR] [--data-dir FOLDER]

  0. with --data-dir, keeps your data (master resume, applications, tailored resumes) in FOLDER instead of this folder
  1. creates the folders the tools use
  2. creates master/master-resume.md from the template if you do not have one yet
  3. builds the skill profile the extension reads
  4. installs the local helper (a small program Chrome starts on demand; skip with --no-helper)
  5. runs the health check and tells you the two manual steps (load the extension, fill your resume)
"""
import pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402  (where the data folder is)
DATA = paths.DATA
EXT = ROOT / "tools" / "jd-capture-extension"


def step(n, text):
    print(f"\n[{n}] {text}")


def run(args):
    r = subprocess.run([sys.executable, *map(str, args)], cwd=str(ROOT), capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("    " + out.replace("\n", "\n    "))
    return r.returncode


def main():
    global DATA
    no_helper = "--no-helper" in sys.argv
    if "--data-dir" in sys.argv:
        try:
            paths.set_data_dir(sys.argv[sys.argv.index("--data-dir") + 1])
        except (IndexError, paths.PathsError) as e:
            print("--data-dir needs the full path of a folder:", e)
            return 1
        DATA = paths.data_root()
    mdir = ["--manifest-dir", sys.argv[sys.argv.index("--manifest-dir") + 1]] if "--manifest-dir" in sys.argv else []
    print("JD Lens setup")
    step(1, "Folders")
    for d in ("master", "applications", "tailored", "views"):
        (DATA / d).mkdir(parents=True, exist_ok=True)
    (ROOT / "tools" / "jd-capture-extension" / "data").mkdir(parents=True, exist_ok=True)
    print("    ok" + (f" (your data folder: {DATA})" if DATA != ROOT else ""))
    step(2, "Master resume")
    master, template = DATA / "master" / "master-resume.md", ROOT / "master" / "master-resume.template.md"
    created = False
    if master.exists():
        print("    master/master-resume.md already exists, leaving it alone")
    elif template.exists():
        shutil.copy2(template, master)
        created = True
        print("    created master/master-resume.md from the template (made-up sample data)")
    else:
        print("    no template found; create master/master-resume.md by hand")
        return 1
    step(3, "Skill profile (what the extension reads)")
    if run(["tools/sync_extension.py"]) or run(["tools/build_profile.py"]):
        print("    could not build the profile: fix master/master-resume.md (compare with the template), then rerun")
        return 1
    step(4, "Local helper")
    if no_helper:
        print("    skipped (--no-helper). Install later with: python3 tools/jobd/install.py")
    elif run(["tools/jobd/install.py", *mdir]):
        print("    the helper did not install; the panel still scores pages. See the message above.")
    step(5, "Health check")
    run(["tools/doctor.py", *mdir])
    print("\nTwo things only you can do:")
    if created:
        print("  1. Open master/master-resume.md and replace the sample data with your own (the file explains how).")
        print("     Then: python3 tools/build_profile.py")
    print("  " + ("2" if created else "1") + f". In Chrome: chrome://extensions, turn on Developer mode, Load unpacked, choose:\n     {EXT}")
    print("     Then pin JD Lens, open a job page and click its icon.")
    print("\nFull guide: docs/GETTING-STARTED.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
