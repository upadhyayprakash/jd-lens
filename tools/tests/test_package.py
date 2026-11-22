#!/usr/bin/env python3
"""The store package: manifest at the root, no personal data, no dev stub, no manifest key (store build)."""
import json, pathlib, subprocess, sys, tempfile, unittest, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class PackageTest(unittest.TestCase):
    def build(self, *flags):
        out = pathlib.Path(tempfile.mkdtemp(prefix="pkg-test-")) / "x.zip"
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "package_extension.py"), "--out", str(out), *flags], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return zipfile.ZipFile(out)

    def test_store_build_is_clean(self):
        z = self.build()
        names = z.namelist()
        self.assertIn("manifest.json", names)
        self.assertFalse([n for n in names if n.startswith("data/") or n in ("mock.js", "README.md", "EXTENSION_ID", "manifest-key.txt")], names)
        self.assertNotIn("key", json.loads(z.read("manifest.json")))
        for page in ("panel.html", "applications.html"):
            self.assertNotIn("mock.js", z.read(page).decode())
        for n in names:                                                       # no personal paths or emails anywhere in the shipped text
            if n.endswith((".js", ".html", ".css", ".json", ".svg")):
                text = z.read(n).decode("utf-8", "ignore")
                self.assertNotIn("/Users/", text, n)

    def test_keep_key_build_keeps_the_local_id(self):
        self.assertIn("key", json.loads(self.build("--keep-key").read("manifest.json")))

    def test_same_bytes_every_build(self):
        a, b = self.build(), self.build()
        self.assertEqual([a.read(n) for n in a.namelist()], [b.read(n) for n in b.namelist()])


if __name__ == "__main__":
    unittest.main()
