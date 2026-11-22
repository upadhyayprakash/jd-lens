# JD Lens release checklist

Updated 22 Nov 2026. "Prep" can happen before the repo split; "Publish" waits for it (see the last section).

## Ready (prep done)
- [x] Clean store package: `python3 tools/package_extension.py` builds `dist/jd-lens-<version>.zip` (no personal data, no dev stub, no manifest key). Tested in `tools/tests/test_package.py`.
- [x] The panel gets its profile and resume data from the helper (`get_data`), so a store install works without a `data/` folder. Before this, a store build would have shown "No skill profile yet" forever.
- [x] Icons: transparent toolbar set, `icons/store-icon.png` (listing), `icons/logo-mark.svg` (tab favicon).
- [x] Listing copy, permission justifications and data disclosures: `store-listing.md`.
- [x] Privacy policy draft: `privacy-policy.md`.
- [x] Account and submission walkthrough: `chrome-web-store.md`.

## Do next (needs you or the recordings)
- [ ] Record the four demo parts, then the voiceover (or keep the muted cut). Send the clips.
- [ ] Screenshots at 1280 x 800 (up to 5) from the real app: plan in `store-listing.md`. A small promo tile (440 x 280) is optional.
- [x] Decided (23 Nov 2026): publisher is the owner's personal Gmail account, non-trader, Unlisted first then Public once tested.
- [x] Licence: AGPLv3 (23 Nov 2026). `LICENSE` and a README Licence section added.
- [x] Contact address added to the privacy policy (prakash.upadhyay93@yahoo.com). No alias for now: add one before switching to Public if spam is a worry, then update the policy and the dashboard contact email.

## Decide before publishing
- [ ] **Rename the native-host ID.** It is `com.jdlens.helper` today (in `background.js`, `common.js`, `tools/jobd/install.py`). A public package should carry a neutral ID such as `com.jdlens.helper`. It needs a helper reinstall (`python3 tools/jobd/install.py`) and a migration step that removes the old manifest. Not done yet, so your current setup keeps working while you record.
- [ ] **Extension ID.** The store assigns its own ID, so the helper's `allowed_origins` must list it. See section B2 of `chrome-web-store.md`.
- [ ] **Who can use it.** The extension needs the helper and a master resume in the repo's format, plus Claude Code for the AI steps. The listing says so plainly. Decide whether the repo (or a trimmed "starter" repo) is public so others can install the helper.

## Known risks for review
- `nativeMessaging` and optional host access draw closer review; the justifications are written.
- A listing that depends on a separate install must say so (it does).
- The favicon request goes to the company's own site; it is disclosed in the policy and the privacy tab answers.

## Does the repo split have to come first?
Prep (above) does not. These do, so wait for the split:
1. The final package, built from the clean new repo.
2. The privacy-policy URL and the homepage and support links (they point at the new repo or its Pages site).
3. The helper's `allowed_origins`, which needs the store's extension ID from the first upload.
4. The native-host rename (cleanest to do in the new repo, once).
