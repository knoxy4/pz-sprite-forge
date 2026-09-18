"""Verify the rebuilt cook-lab tiledefs: no Electric, no leaked _comment keys,
piece cycling matches the pixel-verified sheet order, facings intact."""
import re, sys

PATH = sys.argv[1] if len(sys.argv) > 1 else r"dist_test\KNXCookLab\42\media\knx_cooklab_01.tiles.txt"
t = open(PATH, encoding="utf-8", errors="replace").read()

tiles = []
for tb in re.finditer(r'tile\s*\{(.*?)\}', t, re.S):
    props = {}
    for line in tb.group(1).splitlines():
        m = re.match(r'\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$', line)
        if m:
            props[m.group(1)] = m.group(2)
    tiles.append(props)

# pixel-verified order (tools/sheet_order.py): piece cycles every sprite, facing every 3
PIECES = ["Glassware Rig", "Burner and Pot", "Jug Rack"]
MATS = {"Glassware Rig": ("Glass", "MetalScrap"),
        "Burner and Pot": ("Mechanical", "MetalScrap"),
        "Jug Rack": ("PlasticHard", "Paper")}
FACINGS = ["S", "E", "N", "W"]

fails = []
print("%-4s %-16s %-13s %-11s %-7s" % ("#", "CustomName", "Material", "Material2", "Facing"))
for i, p in enumerate(tiles):
    want_piece = PIECES[i % 3]
    want_facing = FACINGS[i // 3]
    m1, m2 = MATS[want_piece]
    print("%-4d %-16s %-13s %-11s %-7s" % (
        i, p.get("CustomName", "-"), p.get("Material", "-"),
        p.get("Material2", "-"), p.get("Facing", "-")))
    if p.get("CustomName") != want_piece:
        fails.append("#%d CustomName %r != %r" % (i, p.get("CustomName"), want_piece))
    if p.get("Material") != m1:
        fails.append("#%d Material %r != %r" % (i, p.get("Material"), m1))
    if p.get("Material2") != m2:
        fails.append("#%d Material2 %r != %r" % (i, p.get("Material2"), m2))
    if p.get("Facing") != want_facing:
        fails.append("#%d Facing %r != %r" % (i, p.get("Facing"), want_facing))
    if p.get("ScrapSize") != "Small":
        fails.append("#%d ScrapSize %r != 'Small'" % (i, p.get("ScrapSize")))
    for k in p:
        if k.startswith("_"):
            fails.append("#%d leaked comment key %r" % (i, k))

print()
print("tiles            : %d (expect 12)" % len(tiles))
print("Electric anywhere: %d (expect 0)" % t.count("Electric"))
print("leaked _ keys    : %d (expect 0)" % len(re.findall(r'^\s*_\w+\s*=', t, re.M)))
if len(tiles) != 12:
    fails.append("tile count %d != 12" % len(tiles))
if "Electric" in t:
    fails.append("Electric still present")

print()
if fails:
    print("FAIL (%d)" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS - all 12 tiles correct")
