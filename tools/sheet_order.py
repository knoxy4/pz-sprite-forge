"""Which source cell is at each sheet slot? Pixel-match the packed sheet against the cell PNGs.
The manifest lists cells grouped by piece; the packer regroups by facing, so never assume."""
import json, os, sys
from PIL import Image, ImageChops

CELLS = sys.argv[1] if len(sys.argv) > 1 else r"build\cooklab_cells"
SHEET = sys.argv[2] if len(sys.argv) > 2 else r"dist\KNXCookLab\42\media\knx_cooklab_01.png"

m = json.load(open(os.path.join(CELLS, "manifest.json")))
cw, ch = m["cell"][0], m["cell"][1]
sheet = Image.open(SHEET).convert("RGBA")
cols = sheet.width // cw
rows = sheet.height // ch
print("sheet %dx%d, cell %dx%d -> %d x %d slots" % (sheet.width, sheet.height, cw, ch, cols, rows))

srcs = []
for c in m["cells"]:
    name = c.get("name") or c.get("file")
    p = os.path.join(CELLS, name)
    srcs.append((name, Image.open(p).convert("RGBA")))


def diff(a, b):
    if a.size != b.size:
        return 10 ** 9
    d = ImageChops.difference(a, b)
    return sum(i * n for i, n in enumerate(d.convert("L").histogram()))


print()
print("%-5s %-46s %s" % ("slot", "best source match", "score (0 = identical)"))
for i in range(cols * rows):
    x, y = (i % cols) * cw, (i // cols) * ch
    cell = sheet.crop((x, y, x + cw, y + ch))
    scored = sorted(((diff(cell, im), n) for n, im in srcs))
    s0, n0 = scored[0]
    s1, _ = scored[1]
    flag = "" if s0 == 0 else ("  <-- NOT exact" if s0 > 0 and s0 * 4 > s1 else "")
    print("%-5d %-46s %d%s" % (i, n0, s0, flag))
