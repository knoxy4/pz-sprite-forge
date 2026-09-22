"""Pack baked per-tile depth (examples/*_depth.py) into a mod's B42 depth texture.

    uv run --python 3.12 --with pillow --with numpy python tools/depth_pack.py ^
        --raw build/rain_depth --sheet dist/_rain_build/RainBuild/42/media/badlands_rain_01.png ^
        --tileset badlands_rain_01 --media <mod>/common/media

For each raw_<index>.npy: the mask is the FINAL sprite's alpha from the built sheet (after
the style pass: contour, strokes, grounding), because the tileWithDepth shader discards
every opaque pixel that has no depth. Sprite pixels the geometry missed take the nearest
hit (pzforge.tiledepth.fill_to_mask). The build FAILS when a sprite pixel stays uncovered
or the fill reaches too far -- that means the render and the bake no longer line up.

Writes <media>/depthmaps/DEPTH_<tileset>.png (cells without a raw file stay empty, so those
tiles keep the engine default) and <media>/tileGeometry.txt, which the engine needs to
exist before it scans the mod's depthmaps folder at all; its boxes also let the debug
Tile Geometry editor show the stall. No `properties` blocks: those set live sprite props.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pzforge import tiledepth as TD  # noqa: E402

MAX_FILL_STEPS = 6          # px; a real render/bake misregistration shows up as far more
MAX_FILL_SHARE = 0.08       # of the sprite's pixels


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--sheet", required=True, type=Path)
    ap.add_argument("--tileset", required=True)
    ap.add_argument("--media", required=True, type=Path)
    args = ap.parse_args()

    sheet = np.asarray(Image.open(args.sheet).convert("RGBA"))
    rows, cols = sheet.shape[0] // TD.CELL_H, sheet.shape[1] // TD.CELL_W
    out = np.zeros((rows * TD.CELL_H, cols * TD.CELL_W, 4), dtype=np.uint8)
    blocks, failed = [], False
    for raw in sorted(args.raw.glob("raw_*.npy"), key=lambda p: int(p.stem.split("_")[1])):
        idx = int(raw.stem.split("_")[1])
        c, r = idx % cols, idx // cols
        ys, xs = slice(r * TD.CELL_H, (r + 1) * TD.CELL_H), slice(c * TD.CELL_W, (c + 1) * TD.CELL_W)
        mask = sheet[ys, xs, 3] > 0
        geo = np.load(raw)
        hit = geo >= 0
        iou = (hit & mask).sum() / max(1, (hit | mask).sum())
        depth, filled, steps, unfilled = TD.fill_to_mask(geo, mask)
        share = filled / max(1, mask.sum())
        bad = unfilled > 0 or steps > MAX_FILL_STEPS or share > MAX_FILL_SHARE
        failed |= bad
        print(f"{'FAIL' if bad else 'ok  '} {args.tileset}_{idx}: sprite {mask.sum()} px, geometry IoU {iou:.3f}, "
              f"filled {filled} px ({share:.1%}) within {steps} px, uncovered {unfilled}")
        out[ys, xs] = TD.encode_cell(depth)

        boxes = json.loads((args.raw / f"boxes_{idx}.json").read_text(encoding="utf-8"))
        body = "".join(TD.geometry_box_block(bx["min"], bx["max"]) + "\n" for bx in boxes)
        blocks.append(f"        /* {args.tileset}_{idx} */\n        tile\n        {{\n"
                      f"            xy = {c}x{r},\n\n{body}        }}\n")
    if failed:
        print("depth_pack: FAILED -- nothing written")
        return 1

    (args.media / "depthmaps").mkdir(parents=True, exist_ok=True)
    png = args.media / "depthmaps" / f"DEPTH_{args.tileset}.png"
    Image.fromarray(out, "RGBA").save(png)
    geo_txt = ("tileGeometry\n{\n    VERSION = 2,\n\n    tileset\n    {\n"
               f"        name = {args.tileset},\n\n" + "\n".join(blocks) + "    }\n}\n")
    (args.media / "tileGeometry.txt").write_text(geo_txt, encoding="utf-8", newline="\n")
    print(f"wrote {png} ({out.shape[1]}x{out.shape[0]}) and {args.media / 'tileGeometry.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
