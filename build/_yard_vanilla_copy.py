"""Copy the vanilla sprites BADLANDS Furniture's fences, gates and holding cell were
built on into sheets of our own, so no entity of ours claims a vanilla sprite name.

Why: a sprite can belong to one entity SpriteConfig only, and a clash aborts world
load (WorldDictionaryException). Claiming vanilla names means any other mod that makes
the same vanilla piece buildable (e.g. Craftable Tall Wooden Fences 3781002132 on
fencing_01_8/10/13) bricks the player's save. Our own names can't collide.

Each target sheet is a verbatim copy of the vanilla sheet's leading rows: same column
count, same indices, same property blocks, same pack offsets. Index identity keeps
door/gate open-sprite offsets (+2 within the tileset) working, and turns the entity
edit into a plain prefix rename. Output lands in dist/_<key>_build like any other
forged sheet so _furniture_merge.py can append it.
"""
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, r"C:\Users\KNX\dev\pz-sprite-forge")
from pzforge.packfile import PackEntry, PackPage, TexturePack
from pzforge.tiledef import Tile, TileDefinitions, Tileset

MEDIA = Path(r"X:\SteamLibrary\steamapps\common\ProjectZomboid\media")
DIST = Path(r"C:\Users\KNX\dev\pz-sprite-forge\dist")
COPIES = [  # (vanilla sheet, our sheet, highest index we use, build key)
    ("fencing_01", "badlands_fencing_01", 90, "yardfence"),
    ("fixtures_doors_fences_01", "badlands_gates_01", 23, "yardgate"),
    ("location_community_police_01", "badlands_cell_01", 11, "yardcell"),
]
CELL_W, CELL_H = 128, 256

vdefs = TileDefinitions.read(MEDIA / "newtiledefinitions.tiles")
vsets = {t.name: t for t in vdefs.tilesets}
print("reading Tiles2x.pack ...", flush=True)
vpack = TexturePack.read(MEDIA / "texturepacks" / "Tiles2x.pack")
want = {}
for src, _, last, _ in COPIES:
    for i in range(last + 1):
        want[f"{src}_{i}"] = None
found = {}
for page in vpack.pages:
    hits = [e for e in page.entries if e.name in want]
    if not hits:
        continue
    img = Image.open(io.BytesIO(page.png)).convert("RGBA")
    for e in hits:
        found[e.name] = (e, img.crop((e.x, e.y, e.x + e.w, e.y + e.h)))

for src, dst, last, key in COPIES:
    vs = vsets[src]
    rows = last // vs.cols + 1
    tiles, entries, crops = [], [], []
    for i in range(rows * vs.cols):
        props = dict(vs.tiles[i].props) if i < len(vs.tiles) else {}
        name = f"{src}_{i}"
        if props and name not in found:
            if i <= last:
                raise SystemExit(f"{name} has properties but no pack entry")
            print(f"  note: {name} defined but not in Tiles2x; left empty")
            props = {}
        if name in found and not props:
            print(f"  note: {name} is packed but undefined; skipped")
        tiles.append(Tile(props))
        if props:
            e, im = found[name]
            entries.append(PackEntry(f"{dst}_{i}", 0, 0, e.w, e.h, e.ox, e.oy, e.ow, e.oh))
            crops.append(im)
    # shelf-pack the trimmed crops into one page
    atlas_w, x, y, shelf = 2048, 0, 0, 0
    for e in entries:
        if x + e.w > atlas_w:
            x, y, shelf = 0, y + shelf, 0
        e.x, e.y = x, y
        x, shelf = x + e.w, max(shelf, e.h)
    atlas_h = 1
    while atlas_h < y + shelf:
        atlas_h *= 2
    atlas = Image.new("RGBA", (atlas_w, atlas_h))
    for e, im in zip(entries, crops):
        atlas.paste(im, (e.x, e.y))
    buf = io.BytesIO()
    atlas.save(buf, "PNG")
    out = DIST / f"_{key}_build" / f"{key.title()}Build" / "42" / "media"
    (out / "texturepacks").mkdir(parents=True, exist_ok=True)
    TexturePack(pages=[PackPage(f"{dst}0", buf.getvalue(), entries)],
                version=vpack.version, has_header=vpack.has_header).write(
        out / "texturepacks" / f"{dst}.pack")
    td = TileDefinitions(tilesets=[Tileset(dst, dst, vs.cols, rows, 1, tiles)], version=vdefs.version)
    td.write(out / f"{dst}.tiles")
    (out / f"{dst}.tiles.txt").write_text(td.to_text(), encoding="utf-8", newline="\n")
    sheet = Image.new("RGBA", (vs.cols * CELL_W, rows * CELL_H))
    for e, im in zip(entries, crops):
        i = int(e.name.rsplit("_", 1)[1])
        sheet.paste(im, ((i % vs.cols) * CELL_W + e.ox, (i // vs.cols) * CELL_H + e.oy))
    sheet.save(out / f"{dst}.png")
    print(f"{src} -> {dst}: {vs.cols}x{rows}, {len(entries)} sprites, atlas {atlas_w}x{atlas_h}, {out}")
