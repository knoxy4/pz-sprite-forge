"""Make the greenhouse's glass translucent, between render and `pzforge build`.

examples/knx_greenhouse.py renders glass opaque so the style pass shades it like
any paint. Here every pixel whose element-pass id belongs to a part named
glass_* has its alpha capped (the build preserves alpha exactly). Idempotent:
alpha is only ever lowered to the cap. Vanilla window glass sits in alpha bucket
96-127; walls use 104. The roof panel is a floor: frame pixels are hardened to
0/255 so diamonds interlock (the job --floor would do), glass keeps 150 --
more opaque than the walls so the roof reads from outside.

    python build/_greenhouse_glass.py [greenhouse|ghroof]
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(r"C:\Users\KNX\dev\pz-sprite-forge")
which = sys.argv[1] if len(sys.argv) > 1 else "greenhouse"
CELLS = ROOT / "build" / f"{which}_cells"
roof = which == "ghroof"
CAP = 150 if roof else 104

man = json.loads((CELLS / "manifest.json").read_text(encoding="utf-8"))
def srgb(v):
    """The id pass stores LINEAR colours; the PNG holds them sRGB-encoded."""
    v = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return round(255 * v)


ids = [(tuple(srgb(v) for v in c), n.startswith("glass_")) for n, c in man["elements"].items()]
cache = {}


def is_glass(px):
    """Nearest id colour wins; it must be a glass part and within 3 levels."""
    key = px[:3]
    if key not in cache:
        d, g = min((max(abs(key[k] - c[k]) for k in range(3)), g) for c, g in ids)
        cache[key] = g and d <= 3
    return cache[key]


for cell in man["cells"]:
    img = Image.open(CELLS / cell["file"]).convert("RGBA")
    ele = Image.open(CELLS / cell["element"]).convert("RGBA")
    ip, ep = img.load(), ele.load()
    n = 0
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = ip[x, y]
            if a == 0:
                continue
            e = ep[x, y]
            if e[3] > 0 and is_glass(e):
                if a > CAP:
                    ip[x, y] = (r, g, b, CAP)
                n += 1
            elif roof:
                ip[x, y] = (r, g, b, 255 if a >= 128 else 0)
    img.save(CELLS / cell["file"])
    print(f"{cell['file']}: {n} glass px capped at {CAP}")
