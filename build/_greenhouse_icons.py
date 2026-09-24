"""96px build-menu icons for the greenhouse pieces, cut from the forged packs
(same fit as knx_fences_gen.py: trim, scale to 88 px, centre on 96)."""
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, r"C:\Users\KNX\dev\pz-sprite-forge")
from pzforge.packfile import TexturePack

D = Path(r"C:\Users\KNX\dev\pz-sprite-forge\dist")
TEX = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases\common\media\textures")


def load(pack):
    out = {}
    for page in TexturePack.read(pack).pages:
        img = Image.open(io.BytesIO(page.png)).convert("RGBA")
        for e in page.entries:
            out[e.name] = img.crop((e.x, e.y, e.x + e.w, e.y + e.h))
    return out


s = load(D / r"_greenhouse_build\GreenhouseBuild\42\media\texturepacks\badlands_greenhouse_01.pack")
s.update(load(D / r"_ghroof_build\GhroofBuild\42\media\texturepacks\badlands_ghroof_01.pack"))
ICONS = {"Build_KNX_GreenhouseWall": "badlands_greenhouse_01_2",
         "Build_KNX_GreenhouseDoor": "badlands_greenhouse_01_4",
         "Build_KNX_GreenhouseRoof": "badlands_ghroof_01_0"}
for out, spr in ICONS.items():
    im = s[spr]
    im = im.crop(im.getbbox())
    k = 88 / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    c = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    c.alpha_composite(im, ((96 - im.width) // 2, (96 - im.height) // 2))
    c.save(TEX / f"{out}.png")
    print(out, im.size)
