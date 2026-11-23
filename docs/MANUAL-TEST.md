# Manual test: data folder, layouts, contact details

A checklist for trying JD Lens in a real Chrome by hand. It uses a throwaway Chrome profile and a throwaway data folder, so nothing of yours is touched. Allow about 20 minutes. Claude steps use your own Claude sign-in (a full pass costs well under a dollar).

## Where to run the commands

Every `python3 tools/...` command below is run **in Terminal, from the engine folder**: the folder where you cloned or downloaded JD Lens, the one that contains `tools/`, `docs/` and `README.md`. For example, if you cloned it to `~/jd-lens`:

```
cd ~/jd-lens
```

Run that `cd` first in each new Terminal window. A command run from any other folder fails with "can't open file ... tools/...". Commands that start with `cat`, `rm` or `ls` and name a full path work from anywhere. The data folder used below, `~/JD Lens Test Data`, is a different folder, so don't `cd` into it for the `python3 tools/...` commands.

## 0. Set up (once)

1. **A throwaway Chrome profile.** Chrome, profile picture, Add profile, continue without an account, name it "JD Lens test". Do the rest of this checklist in that window. (The extension has a fixed ID, so loading it in your main profile could clash with an install you already have.)
2. **Install the engine with a data folder of its own.** In Terminal, `cd` to the engine folder (see above), then run:
   ```
   python3 tools/setup.py --data-dir "$HOME/JD Lens Test Data"
   ```
   Expect `11 ok, 1 warnings, 0 problems` (the warning is "still the example template"). The sample master resume lands in `JD Lens Test Data/master/`, not in the engine folder.
3. **Load the extension** in the test profile: `chrome://extensions`, Developer mode, Load unpacked, choose `tools/jd-capture-extension` in the engine folder. Pin it.

## 1. Data folder (Settings, "Your data folder")

- [ ] The card shows `.../JD Lens Test Data`, "Set by this setting" and Master resume "found".
- [ ] "Local helper" shows a **Data folder** row and an **Engine** row (two different folders).
- [ ] Settings, **Choose folder...** opens the macOS folder picker. Cancel does nothing.
- [ ] Pick a new empty folder, leave "Add the sample master resume" ticked, **Use this folder**. A toast says the sample was added, and the folder now has `master/`, `applications/`, `tailored/`, `views/`.
- [ ] **Use the engine folder** switches back (the card says "the default: the engine folder"). Switch to the test folder again before continuing.
- [ ] With a folder that has no master resume and the box unticked, the Overview shows the **No master resume in your data folder yet** banner.

## 2. Layouts (Settings, "Tailored resume layout")

- [ ] Three previews: Basic, Two column, With photo. Two column is selected by default.
- [ ] Click **With photo**: a toast confirms it, and `JD Lens Test Data/master/preferences.json` contains `"resume_layout": "photo"`.
- [ ] Both light and dark themes show the cards clearly.

## 3. The build, end to end

1. Open a real job posting, click the JD Lens icon, **Save JD**. Check that `JD Lens Test Data/applications/<company>-<yyyy-mm>.md` exists and the engine folder's `applications/` does not.
2. **Get the full score** (Use Claude), then **Tailor your resume**, then **Approve and build PDF**.
3. **Open resume (PDF)** opens the PDF itself. Check:
   - [ ] The layout is the one you chose (photo: beige sidebar with a round avatar).
   - [ ] The file is named `<your_name>_resume_<company>.pdf` (the sample name is `anika_verma`).
   - [ ] The contact block shows the values from section 1 of the master resume.
4. **Change your identity and rebuild.** Edit section 1 of `JD Lens Test Data/master/master-resume.md` (Name, Email, Phone), then run **Request changes** or build again. The new name, email and phone appear, the old sample ones are gone, and the file name changes.
5. **Photo:** Settings, **Profile photo**, **Choose photo...**, pick any picture (PNG, JPEG or HEIC). The preview appears, and `JD Lens Test Data/master/photo.jpg` exists (and is not in the engine folder). Rebuild with the photo layout: the avatar is replaced by the picture. **Remove photo** brings the avatar back.
6. **Your own layout:** in Terminal, from the engine folder, copy a shipped layout into your data folder, then edit the copy and change something visible (a colour):
   ```
   mkdir -p "$HOME/JD Lens Test Data/tailored/_base/layouts"
   cp tailored/_base/layouts/two-column.html "$HOME/JD Lens Test Data/tailored/_base/layouts/"
   ```
   Choose Two column in Settings and rebuild: your change shows. `python3 tools/prefs.py layout` (same folder) prints which file is used.

## 4. Terminal fallbacks and the Applications page

- [ ] Under a step, **Run in a terminal instead** shows `cd "<data folder>" && claude --add-dir "<engine folder>" "/job ..."`.
- [ ] Panel, **Details** (or the toolbar icon) opens the Applications page with the same data. Add an interview round and change a status: the application file in the data folder changes.
- [ ] **Delete JD and data** lists the files, and they move to `JD Lens Test Data/.trash/` (they are not erased).

## 5. Clean up

In Terminal, from the engine folder (`cd` there first):

```
python3 tools/jobd/install.py --uninstall     # removes the helper registration
python3 tools/paths.py clear                  # back to the engine folder
rm -rf "$HOME/JD Lens Test Data"             # deletes the throwaway data folder (works from any folder)
```
Then remove the "JD Lens test" Chrome profile.
