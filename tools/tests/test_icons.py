#!/usr/bin/env python3
"""The toolbar icons (transparent, mark only) and the store icon (dark tile) must show the whole logo at every size (a render once came out clipped: square corners, or a
cropped fragment). Check: right size, opaque coloured centre, transparent rounded corners, gradient from coral to amber (darker brand shades)."""
import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from make_icons import read_png  # noqa: E402

ICONS = pathlib.Path(__file__).resolve().parent.parent / "jd-capture-extension" / "icons"


class IconTest(unittest.TestCase):
    def test_every_size_shows_the_whole_logo(self):
        for n in (16, 32, 48, 128):
            w, h, px = read_png(ICONS / f"icon{n}.png")
            self.assertEqual((w, h), (n, n))
            for x, y in ((0, 0), (n - 1, 0), (0, n - 1), (n - 1, n - 1)):          # rounded corners: transparent
                self.assertLess(px[y][x][3], 128, f"icon{n}: corner ({x},{y}) is filled, the logo is clipped")
            def at(fx, fy): return px[min(n - 1, int(fy * n / 128))][min(n - 1, int(fx * n / 128))]
            self.assertLess(at(116, 16)[3], 60, f"icon{n}: no dark tile, the toolbar icon is just the mark on a transparent background")
            tl, br = at(46, 54), at(96, 70)                                           # inside the lens disc: warm gradient, coral to amber
            self.assertGreater(tl[0], 180, f"icon{n}: lens disc should be the warm gradient"); self.assertGreater(tl[3], 200, f"icon{n}")
            self.assertGreater(br[1], tl[1], f"icon{n}: gradient should run coral to amber")
            self.assertLess(at(70, 58)[3], 100, f"icon{n}: the person should be cut out of the lens (transparent)")

    def test_store_icon_keeps_the_dark_tile(self):
        """The store listing icon is the app-icon version: dark rounded tile, warm lens, transparent corners."""
        w, h, px = read_png(ICONS / "store-icon.png")
        self.assertEqual((w, h), (128, 128))
        self.assertLess(px[0][0][3], 128)
        r, g, b, a = px[16][116]
        self.assertLess(r, 80); self.assertGreater(a, 200)
        self.assertGreater(px[54][46][0], 200)

    def test_svg_uses_the_brand_pair(self):
        svg = (ICONS / "logo.svg").read_text().upper()
        self.assertIn("#F5A8A0", svg); self.assertIn("#F4C686", svg)


    def test_tab_favicon_has_no_tile_and_pages_use_it(self):
        """The favicon of the panel and Applications tabs is the logo without the dark tile (an SVG, so it can be transparent)."""
        mark = (ICONS / "logo-mark.svg").read_text()
        self.assertNotIn("#1B1722", mark.upper())
        self.assertIn("prefers-color-scheme:dark", mark)
        for page in ("panel.html", "applications.html"):
            self.assertIn('rel="icon" type="image/svg+xml" href="icons/logo-mark.svg"', (ICONS.parent / page).read_text(), page)


if __name__ == "__main__":
    unittest.main()
