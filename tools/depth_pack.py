"""Pack baked per-tile depth into a mod's B42 depth texture and tileGeometry.txt.

Two sources of raw depth:

  --manifest build/depth/closet/manifest.json     (tools/depth_bake.py, any recipe)
      cells are placed exactly as pzforge's build_sheet places them: sorted by
      (group, facing rank, y, x), stable over manifest order. --ref-manifest (the real
      render manifest) makes the build FAIL unless both list the same cells in the
      same order.
  --raw build/rain_depth                          (legacy examples/*_depth.py)
      raw_<index>.npy + boxes_<index>.json, index = sheet slot.

    uv run --python 3.12 --with pillow --with numpy python tools/depth_pack.py ^
        --manifest build/depth/closet/manifest.json --ref-manifest build/closet_cells/manifest.json ^
        --sheet <mod>/42/media/badlands_closet_01.png --tileset badlands_closet_01 --media <mod>/common/media

For each cell: the mask is the FINAL sprite's alpha from the shipped sheet (after the style
pass: contour, strokes, grounding), because the tileWithDepth shader discards every opaque
pixel that has no depth. Sprite pixels the geometry missed take the nearest hit
(pzforge.tiledepth.fill_to_mask). The build FAILS when a sprite pixel stays uncovered, the
fill reaches too far, or geometry and sprite disagree (IoU) -- that means the render and the
bake no longer line up. Nothing is written on a failure.

Writes <media>/depthmaps/DEPTH_<tileset>.png (cells without depth stay empty, so those
tiles keep the engine default) and MERGES this tileset's block into <media>/tileGeometry.txt,
keeping every other tileset already in it. The engine needs that file to exist before it
scans the mod's depthmaps folder at all; its boxes also let the debug Tile Geometry editor
show the piece. No `properties` blocks: those set live sprite props.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pzforge import tiledepth as TD  # noqa: E402

MAX_FILL_STEPS = 6          # px; a real render/bake misregistration shows up as far more
MAX_FILL_SHARE = 0.08       # of the sprite's pixels


def sheet_order(manifest: dict) -> list[dict]:
    """pzforge.sheet.build_sheet's placement, without loading any images."""
    rank = {f: i for i, f in enumerate(manifest.get("facings", ["S"]))}
    cells = list(manifest["cells"])
    return sorted(cells, key=lambda c: (int(c.get("group", 0)), rank.get(c.get("facing", "S"), 0),
                                        c.get("y", 0), c.get("x", 0)))


def split_tilesets(text: str) -> dict[str, str]:
    """tileGeometry.txt -> {tileset name: its full `tileset { ... }` block}, in file order."""
    out: dict[str, str] = {}
    for m in re.finditer(r"^[ \t]*tileset\s*\{", text, re.M):
        depth, i = 0, m.end() - 1
        while True:
            ch = text[i]
            depth += (ch == "{") - (ch == "}")
            i += 1
            if depth == 0:
                break
        block = text[m.start():i]
        name = re.search(r"name\s*=\s*([^,\s]+)", block).group(1)
        out[name] = block.rstrip() + "\n"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--manifest", type=Path)
    src.add_argument("--raw", type=Path)
    ap.add_argument("--ref-manifest", type=Path)
    ap.add_argument("--sheet", required=True, type=Path)
    ap.add_argument("--tileset", required=True)
    ap.add_argument("--media", required=True, type=Path)
    ap.add_argument("--min-iou", type=float, default=0.80,
                    help="fail a cell whose geometry silhouette and sprite alpha overlap less than this")
    ap.add_argument("--island-px", type=int, default=0,
                    help="tolerate up to N sprite pixels per cell that no 4-connected hit can reach "
                         "(diagonal-only AA specks); they take the raw ray hit there, else the nearest known depth")
    ap.add_argument("--max-boxes", type=int, default=8,
                    help="largest N part boxes per tile in tileGeometry.txt (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="check only, write nothing")
    args = ap.parse_args()

    if args.manifest:
        man = json.loads(args.manifest.read_text(encoding="utf-8"))
        ordered = sheet_order(man)
        if args.ref_manifest:
            ref = sheet_order(json.loads(args.ref_manifest.read_text(encoding="utf-8")))
            a, b = [c["file"] for c in ordered], [c["file"] for c in ref]
            if a != b:
                first = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                print(f"depth_pack: FAILED -- bake lists {len(a)} cells, render {len(b)}; first "
                      f"difference at slot {first}: {a[first:first + 1]} vs {b[first:first + 1]}")
                return 1
        base = args.manifest.parent
        jobs = [(k, base / c["depth"], base / c["boxes"]) for k, c in enumerate(ordered)]
    else:
        jobs = []
        for raw in sorted(args.raw.glob("raw_*.npy"), key=lambda p: int(p.stem.split("_")[1])):
            idx = int(raw.stem.split("_")[1])
            jobs.append((idx, raw, args.raw / f"boxes_{idx}.json"))

    sheet = np.asarray(Image.open(args.sheet).convert("RGBA"))
    rows, cols = sheet.shape[0] // TD.CELL_H, sheet.shape[1] // TD.CELL_W
    if args.manifest and len(jobs) > rows * cols:
        print(f"depth_pack: FAILED -- {len(jobs)} cells but the sheet holds {rows * cols}")
        return 1
    # The engine lays EVERY mod depth texture out 8 columns wide by sprite index
    # (TileDepthTextures.createTileset: numColumns = 8), and tileGeometry.txt's xy uses the
    # same index grid -- whatever the sprite sheet's own width (badlands_bookcase_01 is 12).
    n_slots = max((j[0] for j in jobs), default=-1) + 1
    out = np.zeros((-(-n_slots // 8) * TD.CELL_H, 8 * TD.CELL_W, 4), dtype=np.uint8)
    blocks, failed, n_ok, n_empty, ious = [], False, 0, 0, []
    for idx, raw, boxes_path in jobs:
        sc_, sr_ = idx % cols, idx // cols
        mask = sheet[sr_ * TD.CELL_H:(sr_ + 1) * TD.CELL_H, sc_ * TD.CELL_W:(sc_ + 1) * TD.CELL_W, 3] > 0
        c, r = idx % 8, idx // 8
        ys, xs = slice(r * TD.CELL_H, (r + 1) * TD.CELL_H), slice(c * TD.CELL_W, (c + 1) * TD.CELL_W)
        if not mask.any():
            n_empty += 1
            continue
        geo = np.load(raw)
        hit = geo >= 0
        iou = (hit & mask).sum() / max(1, (hit | mask).sum())
        depth, filled, steps, unfilled = TD.fill_to_mask(geo, mask)
        if 0 < unfilled <= args.island_px:
            hole_y, hole_x = np.nonzero(mask & (depth < 0))
            ky, kx = np.nonzero(depth >= 0)
            for y, x in zip(hole_y, hole_x):
                if geo[y, x] >= 0:
                    depth[y, x] = geo[y, x]
                else:
                    k = int(np.argmin((ky - y) ** 2 + (kx - x) ** 2))
                    depth[y, x] = depth[ky[k], kx[k]]
            filled += unfilled
            unfilled = 0
        share = filled / max(1, mask.sum())
        # a rim fill of 1-2 px is contour/AA; a big share only matters when it reaches further
        bad = (unfilled > 0 or steps > MAX_FILL_STEPS or iou < args.min_iou
               or (share > MAX_FILL_SHARE and steps > 2))
        ious.append(iou)
        failed |= bad
        n_ok += not bad
        if bad or not args.manifest:
            print(f"{'FAIL' if bad else 'ok  '} {args.tileset}_{idx}: sprite {mask.sum()} px, geometry IoU "
                  f"{iou:.3f}, filled {filled} px ({share:.1%}) within {steps} px, uncovered {unfilled}")
        out[ys, xs] = TD.encode_cell(depth)

        boxes = json.loads(boxes_path.read_text(encoding="utf-8"))
        # the depth texture carries the detail; boxes only feed the debug Tile Geometry editor,
        # so keep the biggest few instead of one per sock (the game parses this file at load)
        vol = lambda bx: max(0.0, float(np.prod([h - l for l, h in zip(bx["min"], bx["max"])])))
        boxes = sorted(boxes, key=vol, reverse=True)[:args.max_boxes] if args.max_boxes > 0 else boxes
        body = "".join(TD.geometry_box_block(bx["min"], bx["max"]) + "\n" for bx in boxes)
        blocks.append(f"        /* {args.tileset}_{idx} */\n        tile\n        {{\n"
                      f"            xy = {c}x{r},\n\n{body}        }}\n")
    print(f"depth_pack: {args.tileset}: {n_ok} ok, {len(jobs) - n_ok - n_empty} failed, {n_empty} empty cells; "
          f"IoU min {min(ious, default=0):.3f} median {float(np.median(ious)) if ious else 0:.3f}")
    if failed:
        print("depth_pack: FAILED -- nothing written")
        return 1
    if args.dry_run:
        print("depth_pack: dry run -- nothing written")
        return 0

    (args.media / "depthmaps").mkdir(parents=True, exist_ok=True)
    png = args.media / "depthmaps" / f"DEPTH_{args.tileset}.png"
    Image.fromarray(out, "RGBA").save(png)
    geo_path = args.media / "tileGeometry.txt"
    existing = split_tilesets(geo_path.read_text(encoding="utf-8")) if geo_path.exists() else {}
    existing[args.tileset] = (f"    tileset\n    {{\n        name = {args.tileset},\n\n"
                              + "\n".join(blocks) + "    }\n")
    geo_txt = "tileGeometry\n{\n    VERSION = 2,\n\n" + "\n".join(existing.values()) + "}\n"
    geo_path.write_text(geo_txt, encoding="utf-8", newline="\n")
    print(f"wrote {png} ({out.shape[1]}x{out.shape[0]}) and {geo_path} ({len(existing)} tilesets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
