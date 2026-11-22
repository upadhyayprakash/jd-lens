#!/usr/bin/env python3
"""End-to-end check with REAL Chrome: load the unpacked extension in a throwaway profile, open its panel, and confirm
the panel can reach the native host (Chrome starts tools/jobd/jobd-launcher.sh and gets a reply).

Uses Chrome's DevTools protocol over a pipe (Extensions.loadUnpacked). Nothing touches your normal Chrome profile:
the host manifest is installed into the throwaway profile's own NativeMessagingHosts folder.
Only READ operations run (the panel calls ping, profile_status and list on start).
Usage: python3 tools/tests/e2e_extension.py
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXT = ROOT / "tools" / "jd-capture-extension"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
EXPECT_ID = (EXT / "EXTENSION_ID").read_text().strip()


class CDP:
    def __init__(self, proc, wfd, rfd):
        self.proc, self.w, self.r, self.n, self.buf = proc, wfd, rfd, 0, b""

    def send(self, method, params=None, session=None, timeout=30):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        os.write(self.w, json.dumps(msg).encode() + b"\0")
        end = time.time() + timeout
        while time.time() < end:
            while b"\0" not in self.buf:
                self.buf += os.read(self.r, 65536)
            raw, self.buf = self.buf.split(b"\0", 1)
            m = json.loads(raw)
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})
        raise TimeoutError(method)


def main():
    prof = pathlib.Path(tempfile.mkdtemp(prefix="jdfit-e2e-"))
    (prof / "NativeMessagingHosts").mkdir()
    subprocess.run([sys.executable, str(ROOT / "tools/jobd/install.py"), "--manifest-dir", str(prof / "NativeMessagingHosts")], check=True, capture_output=True)
    c2p_r, c2p_w = os.pipe()   # our writes -> chrome fd 3
    p2c_r, p2c_w = os.pipe()   # chrome fd 4 -> our reads

    def child():
        os.dup2(c2p_r, 3); os.dup2(p2c_w, 4)

    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={prof}", "--remote-debugging-pipe",
                             "--enable-unsafe-extension-debugging", "--no-first-run", "--window-size=420,1400", "about:blank"],
                            preexec_fn=child, pass_fds=(3, 4), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(c2p_r); os.close(p2c_w)
    cdp = CDP(proc, c2p_w, p2c_r)
    ok = True
    try:
        res = cdp.send("Extensions.loadUnpacked", {"path": str(EXT)})
        ext_id = res["id"]
        print("extension loaded, id:", ext_id)
        if ext_id != EXPECT_ID:
            print("FAIL: id differs from EXTENSION_ID (manifest key problem)"); ok = False
        pages = (("panel.html?screen=settings", "settings", ["connected", "Resume file", "Claude"]),
                 ("panel.html?screen=resume&tab=profile", "resume", ["Master resume", "Open as HTML", "Profile management"]),
                 ("panel.html?screen=resume&tab=skills", "skills", ["Frontend", "Backend"]),
                 ("applications.html", "applications", ["Applications", "Total saved", "Northwind"]))
        for path, label, want in pages:
            t = cdp.send("Target.createTarget", {"url": f"chrome-extension://{ext_id}/{path}"})["targetId"]
            sess = cdp.send("Target.attachToTarget", {"targetId": t, "flatten": True})["sessionId"]
            text = ""
            for _ in range(40):
                time.sleep(0.5)
                r = cdp.send("Runtime.evaluate", {"expression": "document.body.dataset.error || document.getElementById('app').innerText", "returnByValue": True}, session=sess)
                text = r["result"].get("value", "").replace("\n", " | ")
                if all(w.lower() in text.lower() for w in want):
                    break
            print(f"--- {label} ---\n{text[:300]}")
            for w in want:
                if w.lower() not in text.lower():
                    print(f"FAIL: {label} is missing {w!r}"); ok = False
            if label == "settings" and "not connected" in text:
                print("FAIL: helper not connected"); ok = False
            if label == "applications" and "read only" in text:
                print("FAIL: applications page fell back to the read-only snapshot"); ok = False
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)
    print("\nE2E", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
