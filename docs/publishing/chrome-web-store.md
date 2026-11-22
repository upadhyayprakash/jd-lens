# Chrome Web Store: sign-up and first listing (manual guide)

Status: draft, 22 Nov 2026. You do the account and payment steps; nothing here needs Claude to log in or pay.
Facts below are from memory of the Chrome Web Store flow. Where I am unsure it says CHECK: confirm on the page or in Google's current
"Chrome Web Store" developer documentation before relying on it.

## Order of work (and why)

1. **Move the extension to its own repo first** (agreed). The listing needs a homepage, a support link and a privacy-policy URL, and the
   package must come from a clean tree with no personal data. Do the repo split, then package from it.
2. Register the developer account (steps A).
3. Create the item with a **placeholder package** to hold the name (steps B). Not for review.
4. Build the real listing: screenshots, the 90-second video, description, privacy answers (steps C).
5. Submit for review, then publish (steps D).

## A. Developer account (you)

1. Use the Google account you want as the publisher. A dedicated account (not your personal inbox) is cleaner; the publisher name is public.
2. Turn on 2-step verification on that account (required, CHECK).
3. Open the Chrome Web Store Developer Dashboard (search "Chrome Web Store developer dashboard"; the address is `chrome.google.com/webstore/devconsole`, CHECK).
4. Accept the developer agreement and pay the **one-time registration fee (about 5 US dollars, CHECK the current amount)** with a card. You pay; I do not enter payment details.
5. In the dashboard's account settings, set the publisher display name and a contact email, and verify the email.
6. Choose **trader or non-trader**. If you will charge money or run this as a business, you are a trader and the dashboard asks for a public address, phone and email for EU buyers (CHECK). A free hobby tool is normally non-trader.

## B. Hold the name: create the item (you, with a package I prepare)

1. Dashboard, **Add new item**, upload a zip. Manifest must be at the zip root.
2. Placeholder package: build it from the new repo, **without** these (personal data or dev-only):
   `data/profile.json`, `data/resume.json`, `data/applications.json`, `mock.js`, `README.md`, `EXTENSION_ID`, `manifest-key.txt`.
   Command (from the extension folder): `zip -r ../jd-lens-placeholder.zip . -x "data/*" mock.js README.md EXTENSION_ID manifest-key.txt`.
   Ask Claude to prepare and check it. Note `panel.html` loads `mock.js`; the placeholder will log a missing-file error. That is fine for a draft that is never submitted.
3. Open the new draft. Set the name to **JD Lens** in the Store listing tab, and a one-line summary. Save as draft.
4. The public link has the form `chromewebstore.google.com/detail/<name-slug>/<extension-id>`. The slug follows the name (probably `jd-lens`) and the ID is assigned by the store. The name part is cosmetic; the ID is what counts (CHECK).
5. **Does a draft hold the name?** I am not sure it does. The sure way to hold it is to publish. To do that safely, publish the finished first version as **Unlisted** (only people with the link can find it), then switch to Public when ready (CHECK that visibility can be changed later; I believe it can).

## B2. Extension ID: do this before any helper install

Our local ID comes from the `key` in `manifest.json`. The store gives the published item its own ID (CHECK). The helper only accepts the ID listed in its `allowed_origins` (set by `tools/jobd/install.py`).
After the first upload, look in the dashboard item, **Package** tab, for the store's public key and the item ID (CHECK where). Then either put the store's key into the dev `manifest.json` so local and store IDs match, or re-run the helper installer with the store ID. Also check whether the store accepts a package whose `manifest.json` contains a `key` (CHECK; remove it from the uploaded copy if it complains).

## C. The listing (needs the repo, the video and the site)

Fill in these tabs; the dashboard flags anything missing:
- **Store listing:** description (lead with the keyword score, then Analysis and Brag Sheet), category (Productivity), language, **icon 128x128** (we have it), **at least 1 screenshot, up to 5, at 1280x800** (or 640x400), optional **small promo tile 440x280** and marquee 1400x560, and a **YouTube link** for the promo video (our 90-second cut; CHECK that the link goes in the video field).
- **Privacy practices:** a **single purpose** statement (for example: "Score a job description against the user's own resume data and track applications"), a **justification for each permission** (`activeTab`, `scripting`, `sidePanel`, `storage`, `nativeMessaging`, and the optional host access), the data-use disclosures (what is read: the job page you click on; stored: locally only), and a **privacy-policy URL**. The policy page goes on the landing site or the repo (I can write it).
- **Remote code:** declare none. The extension ships all its code.
- **Distribution:** visibility (Public, Unlisted or Private), regions, free.
- **Native messaging:** reviewers may ask why `nativeMessaging` is needed. The honest answer: it talks to a local helper the user installs to save applications and run Claude on their own machine. Write this in the justification. Because the helper is a separate install, the listing description must say so plainly.

## D. Review and publish

1. **Submit for review.** Typical review is days, sometimes longer for new accounts and sensitive permissions (CHECK). `nativeMessaging` and host permissions draw closer review.
2. Choose "publish automatically after approval" or "defer publishing" so you control the moment.
3. After it is live: install it from the store on a clean Chrome profile and run the demo flow once.
4. Updates later: bump `version` in `manifest.json`, upload a new zip, resubmit.

## Before you start: decisions for you

- Publisher identity: personal Google account or a dedicated one.
- Trader or non-trader.
- Free forever, or a paid plan later (changes the trader answer).
- Public at launch, or Unlisted first.

## What Claude can do

Prepare the clean package, write the privacy policy and permission justifications, write the description and the listing copy, make the screenshots and promo tile. Claude cannot sign in, pay, or press Submit.

## Icons
- Toolbar and manifest icons (`icons/icon16/32/48/128.png`) are transparent: just the mark in a mid-tone coral to amber, so they read on light and dark toolbars.
- The store listing icon is `icons/store-icon.png` (128 px, dark rounded tile). Upload that one as the listing icon.
- Tab favicon of the panel and Applications pages: `icons/logo-mark.svg` (transparent, switches gradient pair with the browser theme).
- Rebuild: `python3 tools/make_icons.py <render.png> 512 icon` (toolbar set from `logo-toolbar.svg`) and `... 512 store-icon 128` (store icon from `logo.svg`).
