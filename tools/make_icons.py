#!/usr/bin/env python3
"""Make the extension's PNG icons (16, 32, 48, 128) from one large render of icons/logo.svg.
Headless Chrome cannot render tiny windows, so: render logo.svg at 512 px once, then scale down here with an area average.
Usage: python3 tools/make_icons.py <render.png> [crop] [prefix] [sizes]
  default: icon16/32/48/128.png (the toolbar set). For the store listing: ... 512 store-icon 128  ->  store-icon.png
  render.png: a screenshot with logo.svg drawn at 512 px in its top-left corner, on a canvas larger than 512 px (Chrome's
  screenshot viewport can be a little smaller than the window, so render on 800x800). crop defaults to 512."""
import pathlib, struct, sys, zlib

def read_png(path):
    b = pathlib.Path(path).read_bytes()
    assert b[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h, bd, ct = 8, b"", 0, 0, 0, 0
    while pos < len(b):
        n, t = struct.unpack(">I4s", b[pos:pos + 8]); d = b[pos + 8:pos + 8 + n]; pos += 12 + n
        if t == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", d[:10])
        elif t == b"IDAT": idat += d
    assert bd == 8 and ct in (2, 6), "need 8-bit RGB or RGBA"
    bpp = 4 if ct == 6 else 3
    raw, rows, prev = zlib.decompress(idat), [], bytearray(w * bpp)
    i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + w * bpp]); i += 1 + w * bpp
        for x in range(len(line)):
            a = line[x - bpp] if x >= bpp else 0; up = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + up) & 255
            elif f == 3: line[x] = (line[x] + (a + up) // 2) & 255
            elif f == 4:
                p = a + up - c; pa, pb, pc = abs(p - a), abs(p - up), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else up if pb <= pc else c)) & 255
        rows.append(line); prev = line
    px = [[(r[x * bpp], r[x * bpp + 1], r[x * bpp + 2], r[x * bpp + 3] if bpp == 4 else 255) for x in range(w)] for r in rows]
    return w, h, px

def scale(px, w, h, n):
    out, k = [], w / n
    for y in range(n):
        row = []
        for x in range(n):
            x0, x1, y0, y1 = int(x * k), int((x + 1) * k), int(y * k), int((y + 1) * k)
            ra = ga = ba = aa = 0
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    r, g, b, a = px[yy][xx]; ra += r * a; ga += g * a; ba += b * a; aa += a
            c = (x1 - x0) * (y1 - y0)
            row.append((round(ra / aa), round(ga / aa), round(ba / aa), round(aa / c)) if aa else (0, 0, 0, 0))
        out.append(row)
    return out

def write_png(path, px, n):
    raw = b"".join(b"\x00" + bytes(v for p in row for v in p) for row in px)
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    pathlib.Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

if __name__ == "__main__":
    w, h, px = read_png(sys.argv[1])
    crop = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    px = [row[:crop] for row in px[:crop]]; w = h = crop
    out = pathlib.Path(__file__).resolve().parent / "jd-capture-extension" / "icons"
    prefix = sys.argv[3] if len(sys.argv) > 3 else "icon"
    sizes = tuple(int(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else (16, 32, 48, 128)
    for n in sizes:
        name = f"{prefix}{n}.png" if prefix == "icon" else f"{prefix}.png"
        write_png(out / name, scale(px, w, h, n), n); print("wrote", out / name)
