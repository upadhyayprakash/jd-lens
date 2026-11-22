# JD Lens logo v2: the sheet behind the lens

Status: option 1 (top-left fold, empty sheet) approved and applied.
Preview: `logo-v2-sheet-fold.html` (same folder), shows each option at 256, 128, 48, 32 and 16 px on the dark tile and on a light background.

## What the mark is today
A dark tile, a job-description sheet drawn as a thick gradient outline, and a solid gradient lens with the candidate cut out of it, in front. The sheet currently has its **fold in the top-right** corner and is empty.

## The change asked for
Move the fold to the **top-left** and keep the sheet **empty** (no lines inside).

## Why this is a sensible change
- The lens and its handle already sit at the lower right. A fold at the top-right adds weight to the same side; a top-left fold balances the mark.
- With the fold on the left, the sheet's top-right is a clean rounded corner. The shape the lens overlaps is plainer, so the lens reads as the focus.
- An empty sheet keeps the mark simple at 16 and 32 px. Text lines behind the lens get cut by it (only the top line survives, the rest become stubs), which looks like noise at small sizes.

## Options compared
| | Option | Verdict |
|---|---|---|
| 0 | Current: top-right fold, empty | Works, slightly right-heavy |
| 1 | **Top-left fold, empty (recommended)** | Balanced, simplest, holds at 16 px |
| 2 | Plain sheet with two lines of text | Tried and parked: only one line fully shows, the others look like stubs behind the lens |

A variant with one short line next to the left fold was drawn and dropped: the lens mask hides it, so it adds nothing.

## Geometry of the recommended option (128 x 128 viewBox)
- Sheet outline: `M34 10H70a16 16 0 0 1 16 16V92a16 16 0 0 1-16 16H26a16 16 0 0 1-16-16V34z`, stroke 8, round joins, gradient stroke.
- Fold crease: `M34 10V34H10`, stroke 7 (the mirror of today's `M62 10V34H86`).
- Everything else is unchanged: the gradient pair `#F5A8A0` to `#F4C686`, the tile `#1B1722` with radius 30, the sheet mask (a gap around the lens), the lens disc (centre 70,70, radius 34) with the candidate cut out, and the handle.

## What changes if approved
1. `tools/jd-capture-extension/icons/logo.svg`: the sheet outline and crease paths.
2. The same two paths in the `LOGO` constant in `tools/jd-capture-extension/common.js` (panel header, Applications page, loader).
3. The static loader copy of the logo in `tools/jd-capture-extension/panel.html`.
4. The four toolbar PNGs (16, 32, 48, 128), re-rendered with `tools/make_icons.py`.
5. The copy used by the demo video: `~/the user/Projects/Remotion Videos/jd-lens-demo/public/logo.svg`.
6. `tools/tests/test_icons.py` needs no change (it checks the tile, the warm lens disc and the cut-out candidate, none of which move).

## Acceptance checks
- The mark is still recognisable at 16 px (document, lens, person).
- Transparent rounded corners on all four PNGs; tile dark; lens disc warm.
- The animated loader still sways the lens only.
- The icon test and a targeted panel render pass.

## Decision
Option 1 was chosen and the files above were changed.
