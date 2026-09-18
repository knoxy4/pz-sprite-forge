"""Clone a vanilla tile's property block onto a forged tiledef.

A forged tile gets its properties from a category preset -- the keys present on
at least 65% of that category.  For furniture that core set is measured across
710 tiles, most of them low (tables, beds, counters), so it carries ``IsLow``
and ``solidtrans`` and a ``PickUpWeight`` of 75.  None of that is right for a
two-metre bookcase, and no amount of ``--prop`` removes a preset key.

When the forged object has a vanilla counterpart of the same shape, the honest
property block is that counterpart's own -- read out of the shipped tiledefs
rather than reassembled by hand.  This copies it across facing by facing and
applies only the overrides you name.

    python tools/clone_tile_props.py dist/FullBookcases/42/media/fullbookcase_01.tiles \
        --from furniture_shelving_01 --indices 40,41,43,42 \
        --set "CustomName=Full Bookcase"

``--indices`` lists the donor sprite index per target tile, in target order, so
the donor's Facing lands on the matching forged facing.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pzforge.tiledef import TileDefinitions

DEFAULT_MEDIA = Path(
    os.environ.get("PZ_MEDIA")
    or r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")


def donor_props(media: Path, tileset: str, indices: list[int]) -> list[dict[str, str]]:
    for name in ("newtiledefinitions.tiles", "tiledefinitions.tiles"):
        path = media / name
        if not path.exists():
            continue
        defs = TileDefinitions.read(path)
        for ts in defs.tilesets:
            if ts.name != tileset:
                continue
            out = []
            for index in indices:
                col, row = index % ts.cols, index // ts.cols
                props = dict(ts.at(col, row).props)
                if not props:
                    raise SystemExit(f"{tileset}_{index} has no properties")
                out.append(props)
            return out
    raise SystemExit(f"tileset {tileset!r} not found under {media}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="forged .tiles to rewrite in place")
    ap.add_argument("--from", dest="donor", required=True, help="vanilla tileset name")
    ap.add_argument("--indices", required=True,
                    help="donor sprite indices, one per target tile, in target order")
    ap.add_argument("--set", dest="overrides", action="append", default=[],
                    metavar="KEY=VALUE", help="override after cloning; repeatable")
    ap.add_argument("--keep", action="append", default=[], metavar="KEY",
                    help="keep the forged value for this key; repeatable")
    ap.add_argument("--targets", default=None,
                    help="0-based positions among the defined tiles to rewrite; "
                         "default all. Lets one sheet carry two objects.")
    ap.add_argument("--game-media", default=None)
    args = ap.parse_args()

    media = Path(args.game_media) if args.game_media else DEFAULT_MEDIA
    indices = [int(v) for v in args.indices.split(",")]
    overrides = dict(kv.split("=", 1) for kv in args.overrides)

    defs = TileDefinitions.read(args.target)
    target = defs.tilesets[0]
    live = [(col, row) for row in range(target.rows) for col in range(target.cols)
            if target.at(col, row).props]
    if args.targets:
        wanted = [int(v) for v in args.targets.split(",")]
        live = [live[i] for i in wanted]
    if len(live) != len(indices):
        raise SystemExit(f"{len(live)} target tile(s) but {len(indices)} donor index/indices")

    donors = donor_props(media, args.donor, indices)
    for (col, row), props in zip(live, donors):
        tile = target.at(col, row)
        for key in args.keep:
            if key in tile.props:
                props[key] = tile.props[key]
        props.update(overrides)
        tile.props.clear()
        tile.props.update(props)
        print(f"  {target.sprite_name(col, row)}: {len(props)} prop(s), "
              f"Facing={props.get('Facing', '-')}")

    defs.write(args.target)
    Path(str(args.target) + ".txt").write_text(defs.to_text(), encoding="utf-8")
    print(f"rewrote {args.target} (+ .txt) from {args.donor} {indices}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
