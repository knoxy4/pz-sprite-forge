"""Projection TV: screen art, overlay post-pass and sheet assembly (Pillow side).

Two stages, run with uv (Blender's Python has no Pillow):

    uv run --python 3.12 --with pillow python examples/knx_tv_screens.py textures
        -> build/tv_screens/*.png, the four screen images the Blender recipe
           maps onto the screen plane.
    (blender -b -P examples/knx_tv_projection.py)
    uv run --python 3.12 --with pillow python examples/knx_tv_screens.py assemble
        -> build/tv_projection_cells/manifest.json: body cells, glow-dressed
           overlay cells and transparent placeholders, grouped so each lands on
           its engine-required sheet index; plus build/Item_TvProjection.png.

Why the indices matter (decompiled IsoTelevision.setupDefaultScreens):
the engine loads a TV's screens as IsoSprite(name, base + i) for i = 16, 32,
48, 64. +16 is the test pattern (no signal), +32/+48/+64 rotate as the
"alternate" screens while something is on. Vanilla draws overlays only for
the two facings whose screen faces the camera (appliances_television_01_16/_17
exist, _18/_19 do not), carries no tile properties on them, and wraps each in
a soft white glow.

Screen art follows vanilla's alternate screens: pale blue-grey field, flat
mid-tone silhouettes, no text. The test screen is SMPTE-style bars.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "build" / "tv_screens"
CELLS = ROOT / "build" / "tv_projection_cells"
ICON = ROOT / "build" / "Item_TvProjection.png"
W, H = 256, 192                       # 4:3, the set's screen aspect

FIELD = (206, 220, 230)
MID = (150, 166, 182)
DARK = (118, 134, 152)
BODY_START = 0
FACINGS = ["S", "E", "N", "W"]
SCREEN_FACINGS = ("S", "E")           # the two facings whose screen is visible
OFFSETS = {"test": 16, "alt1": 32, "alt2": 48, "alt3": 64}
SHEET_CELLS = 72                      # 9 rows of 8: overlays end at 64+3


def textures() -> None:
    TEX.mkdir(parents=True, exist_ok=True)

    # Test screen: seven SMPTE bars over a short reverse-castellation strip.
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    bars = [(192, 192, 192), (192, 192, 0), (0, 192, 192), (0, 192, 0),
            (192, 0, 192), (192, 0, 0), (0, 0, 192)]
    bw = W / 7
    for i, c in enumerate(bars):
        d.rectangle((round(i * bw), 0, round((i + 1) * bw), int(H * 0.72)), fill=c)
    low = [(0, 0, 192), (19, 19, 19), (192, 0, 192), (19, 19, 19),
           (0, 192, 192), (19, 19, 19), (192, 192, 192)]
    for i, c in enumerate(low):
        d.rectangle((round(i * bw), int(H * 0.72), round((i + 1) * bw), H), fill=c)
    im.save(TEX / "test.png")

    # alt1: evening news -- anchor at a desk, inset box over the shoulder.
    im = Image.new("RGB", (W, H), FIELD)
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(H * 0.74), W, H), fill=DARK)                 # desk
    d.ellipse((96, 40, 150, 100), fill=MID)                           # head
    d.rounded_rectangle((70, 92, 176, 150), 24, fill=MID)             # shoulders
    d.rectangle((150, 118, 176, 150), fill=MID)
    d.rectangle((24, 24, 84, 70), fill=MID)                           # inset
    d.polygon([(30, 64), (48, 38), (60, 52), (70, 42), (80, 64)], fill=DARK)
    d.rectangle((0, int(H * 0.86), W, int(H * 0.92)), fill=MID)       # lower third
    im.save(TEX / "alt1.png")

    # alt2: western -- mesa horizon, a rider on the flat.
    im = Image.new("RGB", (W, H), FIELD)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 118), (40, 112), (58, 84), (104, 84), (118, 110),
               (170, 116), (190, 96), (222, 96), (236, 114), (W, 118),
               (W, H), (0, H)], fill=MID)
    d.rectangle((0, 150, W, H), fill=DARK)
    d.ellipse((120, 128, 160, 150), fill=DARK)                        # horse
    d.rectangle((126, 146, 130, 164), fill=DARK)
    d.rectangle((150, 146, 154, 164), fill=DARK)
    d.polygon([(156, 132), (170, 118), (174, 126), (162, 138)], fill=DARK)
    d.ellipse((132, 108, 146, 122), fill=DARK)                        # rider
    d.rectangle((134, 118, 144, 134), fill=DARK)
    d.rectangle((126, 104, 152, 108), fill=DARK)                      # hat brim
    im.save(TEX / "alt2.png")

    # alt3: sitcom -- two people on a couch, lamp between them.
    im = Image.new("RGB", (W, H), FIELD)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 34), fill=MID)                              # wall trim
    d.rounded_rectangle((20, 118, 236, 176), 14, fill=DARK)           # couch
    for cx in (72, 184):
        d.ellipse((cx - 22, 52, cx + 22, 96), fill=MID)               # heads
        d.rounded_rectangle((cx - 36, 90, cx + 36, 150), 20, fill=MID)
    d.rectangle((124, 60, 132, 118), fill=MID)                        # lamp
    d.polygon([(110, 60), (146, 60), (138, 38), (118, 38)], fill=FIELD,
              outline=MID)
    im.save(TEX / "alt3.png")
    print(f"screen textures -> {TEX}")


def glow(cell: Image.Image) -> Image.Image:
    """Vanilla's halo: the screen shape grown and blurred, white at low alpha,
    under the unchanged screen pixels."""
    a = cell.getchannel("A")
    if not a.getbbox():
        return cell
    halo_a = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.2))
    halo_a = halo_a.point(lambda v: int(v * 0.55))
    halo = Image.new("RGBA", cell.size, (236, 242, 246, 0))
    halo.putalpha(halo_a)
    return Image.alpha_composite(halo, cell)


def icon(body_s: Image.Image) -> Image.Image:
    """32 px inventory icon from the S body cell: crop, fit, hard alpha,
    1 px outline in a darkened version of the edge colour (vanilla idiom)."""
    crop = body_s.crop(body_s.getbbox())
    scale = 29 / max(crop.size)
    small = crop.resize((max(1, round(crop.width * scale)),
                         max(1, round(crop.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    out.alpha_composite(small, ((32 - small.width) // 2, (32 - small.height) // 2))
    px = out.load()
    for y in range(32):
        for x in range(32):
            r, g, b, al = px[x, y]
            px[x, y] = (r, g, b, 255 if al >= 110 else 0)
    ring = []
    for y in range(32):
        for x in range(32):
            if px[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 32 and 0 <= ny < 32 and px[nx, ny][3]:
                    r, g, b, _ = px[nx, ny]
                    ring.append((x, y, (int(r * .3), int(g * .3), int(b * .3), 255)))
                    break
    for x, y, c in ring:
        px[x, y] = c
    return out


def assemble() -> None:
    passes = json.loads((CELLS / "passes.json").read_text())
    body = passes["body"]["cells"]
    by_face = {c["facing"]: c for c in body}
    cells: list[dict] = []
    placed: set[int] = set()

    for i, face in enumerate(FACINGS):
        rec = dict(by_face[face], group=BODY_START + i)
        cells.append(rec)
        placed.add(BODY_START + i)

    for key, off in OFFSETS.items():
        for rec in passes[key]["cells"]:
            face = rec["facing"]
            index = off + FACINGS.index(face)
            path = CELLS / rec["file"]
            if face in SCREEN_FACINGS:
                glow(Image.open(path).convert("RGBA")).save(path)
            else:
                Image.new("RGBA", Image.open(path).size, (0, 0, 0, 0)).save(path)
            cells.append({"file": rec["file"], "facing": face, "x": 0, "y": 0,
                          "group": index, "raw": True, "tile_props": {}})
            placed.add(index)

    size = Image.open(CELLS / body[0]["file"]).size
    blank = "blank.png"
    Image.new("RGBA", size, (0, 0, 0, 0)).save(CELLS / blank)
    for index in range(SHEET_CELLS):
        if index not in placed:
            cells.append({"file": blank, "facing": "S", "x": 0, "y": 0,
                          "group": index, "raw": True, "tile_props": {}})

    manifest = dict(passes["body"])
    manifest["sheet"] = passes["sheet"]
    manifest["isolate_tiles"] = True
    manifest["cells"] = sorted(cells, key=lambda c: c["group"])
    (CELLS / "manifest.json").write_text(json.dumps(manifest, indent=2))
    icon(Image.open(CELLS / by_face["S"]["file"]).convert("RGBA")).save(ICON)
    print(f"assembled {len(cells)} cells ({len(placed)} real) -> {CELLS}; icon -> {ICON}")


if __name__ == "__main__":
    {"textures": textures, "assemble": assemble}[sys.argv[1]]()
