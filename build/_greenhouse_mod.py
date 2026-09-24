"""Assemble BADLANDS Greenhouse's tile media from the two forged sheets.

One tiledef file (badlands_greenhouse_01, tiledef 6475) holding two tilesets:
  1 badlands_greenhouse_01  walls, corner, post, door (8)   -- vanilla jail-set slot order
  2 badlands_ghroof_01      glass roof panel (1)
plus one pack with both pages, the B42 depth assignments (the vanilla jail
set's own presets, and the vanilla metal floor's for the roof), and the 96px
build icons. Sheets come from examples/knx_greenhouse.py ->
build/_greenhouse_glass.py -> pzforge build (dist/_greenhouse_build,
dist/_ghroof_build). Rerunnable; writes only inside the mod's common/media.
"""
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, r"C:\Users\KNX\dev\pz-sprite-forge")
from pzforge.packfile import TexturePack
from pzforge.tiledef import TileDefinitions

FORGE = Path(r"C:\Users\KNX\dev\pz-sprite-forge\dist")
MOD = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\BadlandsGreenhouse")
MEDIA = MOD / "common" / "media"
FILE = "badlands_greenhouse_01"
SHEETS = [  # (sheet, tileset id, build folder)
    ("badlands_greenhouse_01", 1, r"_greenhouse_build\GreenhouseBuild\42\media"),
    ("badlands_ghroof_01", 2, r"_ghroof_build\GhroofBuild\42\media"),
]
DEPTH = {  # ours -> vanilla sprite whose depth texture we reuse
    "badlands_greenhouse_01_0": "preset_depthmaps_01_4",  # = location_community_police_01_0
    "badlands_greenhouse_01_1": "preset_depthmaps_01_5",
    "badlands_greenhouse_01_2": "preset_depthmaps_01_6",
    "badlands_greenhouse_01_3": "preset_depthmaps_01_7",
    "badlands_greenhouse_01_4": "fixtures_doors_01_0",    # = location_community_police_01_4
    "badlands_greenhouse_01_5": "fixtures_doors_01_1",
    "badlands_greenhouse_01_6": "fixtures_doors_01_2",
    "badlands_greenhouse_01_7": "fixtures_doors_01_3",
    "badlands_ghroof_01_0": "preset_depthmaps_01_0",      # = constructedobjects_01_86
}
ICONS = {"Build_KNX_GreenhouseWall": "badlands_greenhouse_01_2",
         "Build_KNX_GreenhouseDoor": "badlands_greenhouse_01_4",
         "Build_KNX_GreenhouseRoof": "badlands_ghroof_01_0"}

tilesets, pages, version, header = [], [], None, None
for sheet, tid, rel in SHEETS:
    d = FORGE / rel
    t = TileDefinitions.read(d / f"{sheet}.tiles")
    assert [x.name for x in t.tilesets] == [sheet]
    t.tilesets[0].id = tid
    tilesets += t.tilesets
    version = t.version
    p = TexturePack.read(d / "texturepacks" / f"{sheet}.pack")
    pages += p.pages
    header = (p.version, p.has_header)

(MEDIA / "texturepacks").mkdir(parents=True, exist_ok=True)
(MEDIA / "textures").mkdir(parents=True, exist_ok=True)
td = TileDefinitions(tilesets=tilesets, version=version)
td.write(MEDIA / f"{FILE}.tiles")
TexturePack(pages=pages, version=header[0], has_header=header[1]).write(
    MEDIA / "texturepacks" / f"{FILE}.pack")
(FORGE / f"{FILE}.tiles.txt").write_text(td.to_text(), encoding="utf-8", newline="\n")

lines = ["tileDepthTextureAssignments", "{", "    VERSION = 1,"]
lines += [f"    {k} = {v}," for k, v in DEPTH.items()]
lines += ["}", ""]
(MEDIA / "tileDepthTextureAssignments.txt").write_text("\n".join(lines), encoding="utf-8", newline="\n")

cut = {}
for page in pages:
    img = Image.open(io.BytesIO(page.png)).convert("RGBA")
    for e in page.entries:
        cut[e.name] = img.crop((e.x, e.y, e.x + e.w, e.y + e.h))
for out, spr in ICONS.items():
    im = cut[spr]
    im = im.crop(im.getbbox())
    k = 88 / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    c = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    c.alpha_composite(im, ((96 - im.width) // 2, (96 - im.height) // 2))
    c.save(MEDIA / "textures" / f"{out}.png")

# read back
rt = TileDefinitions.read(MEDIA / f"{FILE}.tiles")
rp = TexturePack.read(MEDIA / "texturepacks" / f"{FILE}.pack")
names = {e.name for p in rp.pages for e in p.entries}
for ts in rt.tilesets:
    filled = [i for i, t in enumerate(ts.tiles) if not t.empty]
    missing = [f"{ts.name}_{i}" for i in filled if f"{ts.name}_{i}" not in names]
    print(f"tileset {ts.name} id={ts.id} {ts.cols}x{ts.rows} tiles={len(filled)} unpacked={missing}")
    assert not missing
assert set(DEPTH) <= names
print("pages", [p.name for p in rp.pages], "entries", len(names))
