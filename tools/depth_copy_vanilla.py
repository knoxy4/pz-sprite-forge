"""Give verbatim copies of vanilla sprites (build/_yard_vanilla_copy.py) vanilla's own depth.

A copied sheet keeps vanilla's indices and pixels but not vanilla's depth data, which is
keyed by sprite NAME. So badlands_fencing_01_8 drew as a whole-tile cube where
fencing_01_8 draws with its own depth texture -- and without vanilla's
`Translucent = true` (tileGeometry.txt), so the copy WROTE depth over its whole face and
hid what stands behind it (the greenhouse-glass bug, 0.1.3).

For every copied index this resolves vanilla's depth the way the game does -- an entry in
tileDepthTextureAssignments.txt (another sprite, or a preset_depthmaps_01 cell) wins, else
the sprite's own cell in DEPTH_<tileset>.png -- and pastes those pixels into
<media>/depthmaps/DEPTH_<ours>.png (8 columns by index, as the engine lays it out). It also
copies vanilla's tileGeometry.txt tile blocks (boxes AND properties such as Translucent)
under our tileset name, merged into <media>/tileGeometry.txt.

    uv run --python 3.12 --with pillow --with numpy python tools/depth_copy_vanilla.py ^
        --vanilla X:/SteamLibrary/steamapps/common/ProjectZomboid/media --media <mod>/common/media ^
        fencing_01:badlands_fencing_01:90 fixtures_doors_fences_01:badlands_gates_01:23 ^
        location_community_police_01:badlands_cell_01:11
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from depth_pack import split_tilesets  # noqa: E402

CW, CH = 128, 256


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True, type=Path, help="ProjectZomboid/media")
    ap.add_argument("--media", required=True, type=Path, help="<mod>/common/media")
    ap.add_argument("pairs", nargs="+", help="vanilla_tileset:our_tileset:highest_index")
    args = ap.parse_args()

    assign = dict(re.findall(r"^\s*(\w+?_\d+) = (\w+?_\d+),", (args.vanilla / "tileDepthTextureAssignments.txt")
                             .read_text(encoding="utf-8"), re.M))
    vgeo = split_tilesets((args.vanilla / "tileGeometry.txt").read_text(encoding="utf-8"))
    sheets: dict[str, np.ndarray | None] = {}

    def depth_sheet(tileset: str):
        if tileset not in sheets:
            p = args.vanilla / "depthmaps" / f"DEPTH_{tileset}.png"
            sheets[tileset] = np.asarray(Image.open(p).convert("RGBA")) if p.exists() else None
        return sheets[tileset]

    def cell_of(sprite: str, hops: int = 0):
        """(pixels or None, how it resolved) for one vanilla sprite name."""
        if sprite in assign and hops < 8:
            return cell_of(assign[sprite], hops + 1)
        tileset, idx = sprite.rsplit("_", 1)
        idx = int(idx)
        sh = depth_sheet(tileset)
        c, r = idx % 8, idx // 8
        if sh is None or (r + 1) * CH > sh.shape[0]:
            return None, sprite
        px = sh[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW]
        return (px if px[..., 3].any() else None), sprite

    geo_path = args.media / "tileGeometry.txt"
    ours_geo = split_tilesets(geo_path.read_text(encoding="utf-8")) if geo_path.exists() else {}
    for spec in args.pairs:
        src, dst, last = spec.split(":")
        last = int(last)
        out = np.zeros((-(-(last + 1) // 8) * CH, 8 * CW, 4), dtype=np.uint8)
        got, via = 0, {}
        for i in range(last + 1):
            px, frm = cell_of(f"{src}_{i}")
            if px is None:
                continue
            c, r = i % 8, i // 8
            out[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW] = px
            got += 1
            if frm != f"{src}_{i}":
                via[i] = frm
        (args.media / "depthmaps").mkdir(parents=True, exist_ok=True)
        Image.fromarray(out, "RGBA").save(args.media / "depthmaps" / f"DEPTH_{dst}.png")

        blocks, n_props = [], 0
        if src in vgeo:
            body = vgeo[src]
            for m in re.finditer(r"(        /\* [^*]+ \*/\n)?        tile\n        \{\n            xy = (\d+)x(\d+),"
                                 r".*?\n        \}\n", body, re.S):
                idx = int(m.group(2)) + 8 * int(m.group(3))
                if idx > last:
                    continue
                blk = m.group(0)
                blk = re.sub(r"/\* [^*]+ \*/", f"/* {dst}_{idx} */", blk) if m.group(1) else \
                    f"        /* {dst}_{idx} */\n" + blk
                n_props += "properties" in blk
                blocks.append(blk)
        if blocks:
            ours_geo[dst] = (f"    tileset\n    {{\n        name = {dst},\n\n" + "\n".join(blocks) + "    }\n")
        else:
            ours_geo.pop(dst, None)
        print(f"{dst}: depth for {got}/{last + 1} slots ({len(via)} via assignment, e.g. "
              f"{dict(list(via.items())[:3])}); {len(blocks)} geometry tiles, {n_props} with properties")

    geo_txt = "tileGeometry\n{\n    VERSION = 2,\n\n" + "\n".join(ours_geo.values()) + "}\n"
    geo_path.write_text(geo_txt, encoding="utf-8", newline="\n")
    print(f"wrote {geo_path} ({len(ours_geo)} tilesets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
