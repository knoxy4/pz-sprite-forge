"""What vanilla actually puts on (a) Material=Glass tiles, (b) plastic jug/container tiles,
(c) science-lab tilesets, (d) crafted burners. Used to replace the `appliance` preset's
Material=Electric on the cook-lab tiles with something real."""
import collections, glob, os, re

MEDIA = os.environ.get("PZ_MEDIA") or r"X:\SteamLibrary\steamapps\common\ProjectZomboid\media"


def all_txts():
    seen = set()
    for p in glob.glob(os.path.join(MEDIA, "**", "*.tiles.txt"), recursive=True):
        if p not in seen:
            seen.add(p)
            yield p


def tiles(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    for ts in re.finditer(r'tileset\s*\{(.*?)\n\}', t, re.S):
        body = ts.group(1)
        fm = re.search(r'file\s*=\s*(\S+)', body)
        fname = fm.group(1) if fm else "?"
        for i, tb in enumerate(re.finditer(r'tile\s*\{(.*?)\}', body, re.S)):
            props = {}
            for line in tb.group(1).splitlines():
                m = re.match(r'\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$', line)
                if m:
                    props[m.group(1)] = m.group(2)
            yield fname, i, props


def show(label, pred, limit=10):
    print("=" * 78)
    print(label)
    print("=" * 78)
    n = 0
    dedup = set()
    for p in all_txts():
        for fname, i, props in tiles(p):
            if not pred(fname, props):
                continue
            sig = (fname, props.get("CustomName"), props.get("Material"),
                   props.get("Material2"), props.get("ScrapSize"))
            if sig in dedup:
                continue
            dedup.add(sig)
            keep = {k: v for k, v in props.items() if k != "xy"}
            print("  %-32s #%-3d %s" % (fname, i, keep))
            n += 1
            if n >= limit:
                return
    if n == 0:
        print("  (none)")


LABSET = re.compile(r'laborator|schoollab|science|medical|hospital|clinic', re.I)
JUG = re.compile(r'jug|canister|jerry|bottle|container|bucket', re.I)

show("(a) every Material=Glass tile, in full",
     lambda f, p: p.get("Material") == "Glass", 12)
print()
show("(b) plastic-material tiles (PlasticHard / Plastic / PlasticBag)",
     lambda f, p: p.get("Material") in ("PlasticHard", "Plastic"), 12)
print()
show("(c) science/lab tilesets - anything with a CustomName",
     lambda f, p: bool(LABSET.search(f)) and "CustomName" in p, 14)
print()
show("(d) jug / canister / bottle named tiles",
     lambda f, p: bool(JUG.search(p.get("CustomName", "") + p.get("GroupName", ""))), 12)

print()
print("=" * 78)
print("Material values that co-occur with ScrapSize, and their ScrapSize")
print("=" * 78)
pairs = collections.Counter()
for p in all_txts():
    for fname, i, props in tiles(p):
        if "Material" in props:
            pairs[(props["Material"], props.get("ScrapSize", "-"))] += 1
for (m, s), n in pairs.most_common(28):
    print("  %-16s ScrapSize=%-8s %5d" % (m, s, n))
