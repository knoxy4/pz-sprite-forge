"""Build-menu icons for BADLANDS Furniture, cut from the mod's own tilesheets.

Vanilla build icons (UI2.pack, e.g. Build_Chair) are 48x48 RGBA: the object in
its S facing, outlined, filling the frame on transparent. Ours are made the same
way, from the S sprite each entity already declares, so the icon in the build
menu is the thing you are about to place.

    uv run --python 3.12 --with pillow python examples/knx_furniture_icons.py [--check]

It reads `42/media/scripts/entities/*.txt` for each entity's `face S` sprite,
cuts that cell out of the matching `42/media/<sheet>.png` (uniform 128x256
grid), trims, scales to fit, and writes `42/media/textures/Build_KNX<Name>.png`.
`--check` renders a contact sheet instead of writing into the mod.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases")
MOD = ROOT / "42" / "media"
#: Vanilla's own build icons are 48x48, but the UI scales them, and this art is
#: painted rather than pixel art, so it ships at 2x like Neat Building's (96).
ICON = 96
#: Leave air at the edge so the drawn contour is never clipped by the frame.
FIT = 92
CELL_W, CELL_H = 128, 256

#: entity script name -> icon name. Keeping the map explicit means a renamed
#: entity fails loudly here instead of silently shipping a stale icon.
ICONS = {
    "KNX_Bookcase": "Build_KNXBookcase",
    "KNX_PantryShelf": "Build_KNXPantryShelf",
    "KNX_WineRack": "Build_KNXWineRack",
    "KNX_UtilityShelving": "Build_KNXUtilityShelving",
    "KNX_GunRack": "Build_KNXGunRack",
    "KNX_PalletRecliner": "Build_KNXPalletRecliner",
    "KNX_TireChair": "Build_KNXTireChair",
    "KNX_PatchworkArmchair": "Build_KNXPatchworkArmchair",
    "KNX_RainDrum": "Build_KNXRainDrum",
    "KNX_RainStand": "Build_KNXRainStand",
    "KNX_RainTwin": "Build_KNXRainTwin",
    "KNX_RainRack": "Build_KNXRainRack",
    "KNX_WashStation": "Build_KNXWashStation",
    "KNX_Shower": "Build_KNXShower",
    "KNX_VCRStack": "Build_KNXVCRStack",
    "KNX_TapeRack": "Build_KNXTapeRack",
    "KNX_MedicalTable": "Build_KNXMedicalTable",
    "KNX_ClosetRod": "Build_KNXClosetRod",
    "KNX_LinenShelf": "Build_KNXLinenShelf",
    "KNX_BootCubby": "Build_KNXBootCubby",
    "KNX_OverheadShelf": "Build_KNXOverheadShelf",
    "KNX_CoatPegs": "Build_KNXCoatPegs",
    "KNX_CrateWardrobe": "Build_KNXCrateWardrobe",
    "KNX_EngineBayBBQ": "Build_KNXEngineBayBBQ",
}

ENTITY = re.compile(r"^\s*entity\s+(\w+)\s*$", re.M)
FACE_S = re.compile(r"face\s+S\s*\{\s*layer\s*\{\s*row\s*=\s*([A-Za-z0-9_ ]+?)\s*,", re.S)


def south_sprites() -> dict[str, str]:
    """entity name -> its S-face sprite, e.g. badlands_seating_01_0."""
    out: dict[str, str] = {}
    for path in sorted((MOD / "scripts" / "entities").glob("*.txt")):
        if path.name.endswith("_xuiSkin.txt"):
            continue
        text = path.read_text(encoding="utf-8")
        marks = [(m.start(), m.group(1)) for m in ENTITY.finditer(text)]
        for i, (start, name) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
            face = FACE_S.search(text, start, end)
            if face:
                out[name] = face.group(1)
    return out


#: Sheets whose pieces carry fill stages, and how many each piece carries.
#: An entity's faces point at the empty sprite, because a thing you just built
#: is empty -- but an empty carcass is a poor icon, so the icon comes off the
#: fullest one, index - index % stages. Keep this in step with
#: KNXBookcase.SHEETS in the mod.
FILL_SHEETS = {"badlands_bookcase_01": 3, "badlands_shelving_01": 3,
               "badlands_theater_01": 10, "badlands_medical_01": 10,
               "badlands_closet_01": 4}


def cell(sprite: str) -> Image.Image:
    sheet_name, index = sprite.rsplit("_", 1)
    stages = FILL_SHEETS.get(sheet_name)
    if stages:
        index = str(int(index) - int(index) % stages)
    sheet = Image.open(MOD / f"{sheet_name}.png").convert("RGBA")
    cols = sheet.width // CELL_W
    i = int(index)
    x, y = (i % cols) * CELL_W, (i // cols) * CELL_H
    return sheet.crop((x, y, x + CELL_W, y + CELL_H))


def south_art(row: str) -> Image.Image:
    """One sprite, or a 2x1 row laid out as the game draws it: each step
    east along the grid moves half a cell right and a quarter cell down."""
    names = row.split()
    if len(names) == 1:
        return cell(names[0])
    canvas = Image.new("RGBA", (CELL_W + (len(names) - 1) * CELL_W // 2,
                                CELL_H + (len(names) - 1) * CELL_W // 4), (0, 0, 0, 0))
    for i, name in enumerate(names):
        canvas.alpha_composite(cell(name), (i * CELL_W // 2, i * CELL_W // 4))
    return canvas


def make_icon(sprite: str) -> Image.Image:
    art = south_art(sprite)
    box = art.getbbox()
    if box is None:
        raise SystemExit(f"{sprite}: empty cell")
    art = art.crop(box)
    scale = min(FIT / art.width, FIT / art.height)
    size = (max(1, round(art.width * scale)), max(1, round(art.height * scale)))
    # LANCZOS keeps the painted shading readable at 48px; NEAREST aliases the
    # drawn contour into a dotted line at these reduction factors (~1:4).
    art = art.resize(size, Image.LANCZOS)
    icon = Image.new("RGBA", (ICON, ICON), (0, 0, 0, 0))
    icon.alpha_composite(art, ((ICON - size[0]) // 2, (ICON - size[1]) // 2))
    # A resized edge leaves a fringe of near-transparent pixels that reads as
    # haze against the dark menu; vanilla icons have hard edges.
    px = icon.load()
    for yy in range(ICON):
        for xx in range(ICON):
            r, g, b, a = px[xx, yy]
            px[xx, yy] = (r, g, b, 0 if a < 24 else (255 if a > 160 else a))
    return icon


def main() -> int:
    check = "--check" in sys.argv
    sprites = south_sprites()
    missing = [e for e in ICONS if e not in sprites]
    if missing:
        raise SystemExit(f"entities with no S face: {missing}")
    # Loose PNGs under common/media/textures, the way Neat Building ships its
    # build icons: texture packs are a client-only asset, so a headless server
    # can only resolve an icon that is a real file on disk.
    out_dir = (Path(__file__).resolve().parents[1] / "build" / "knx_furniture_icons"
               if check else ROOT / "common" / "media" / "textures")
    out_dir.mkdir(parents=True, exist_ok=True)
    for entity, icon_name in ICONS.items():
        icon = make_icon(sprites[entity])
        icon.save(out_dir / f"{icon_name}.png")
        print(f"{icon_name:32s} <- {sprites[entity]}")
    print(f"{len(ICONS)} icon(s) -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
