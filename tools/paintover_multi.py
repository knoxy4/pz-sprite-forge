"""Paintover for MULTI-TILE objects: paint each object once per facing, not once per cell.

tools/paintover.py paints raw cells one at a time.  A multi-tile object's raw cells are the
same object seen through cameras one tile apart, each clipping a different part of it, so
painting them separately gives every tile its own generation and the tile seam shows.  This
wraps it:

    prep   compose each (group, facing)'s raw cells onto one canvas at the game's tile offsets
           ((x - y) * cw/2, (x + y) * cw/4) -> <cells>_comp/ + a manifest paintover.py reads
    (run)  tools/paintover.py <cells>_comp --groups g --subject ...     (one run per group)
    split  cut the painted canvas back into every original cell, under that cell's ORIGINAL
           alpha (the retouch rule), copy the aux passes (normal/element/light/tile) and write
           <out>/manifest.json; optional --rename-group "Painted {}" rewrites each cell's
           tile_props GroupName so the painted set is its own moveable.

    uv run --with pillow python tools/paintover_multi.py prep  build/x_cells
    uv run --with pillow python tools/paintover_multi.py split build/x_cells --painted build/x_cells_comp_paint --out build/x_cells_paint
    python -m pzforge.cli build build/x_cells_paint --no-style ...
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageFilter

AUX = ("normal", "element", "light", "tile")


def _offsets(cells, cw):
    raw = [((c["x"] - c["y"]) * (cw // 2), (c["x"] + c["y"]) * (cw // 4)) for c in cells]
    mx, my = min(o[0] for o in raw), min(o[1] for o in raw)
    return [(ox - mx, oy - my) for ox, oy in raw]


def _groups(manifest):
    out: dict = {}
    for c in manifest["cells"]:
        out.setdefault((c.get("group", 0), c["facing"]), []).append(c)
    return out


def comp_name(group, facing) -> str:
    return f"comp_g{group}_{facing}.png"


def prep(cells_dir: Path, out: Path) -> None:
    manifest = json.loads((cells_dir / "manifest.json").read_text(encoding="utf-8"))
    cw, ch = manifest["cell"]
    out.mkdir(parents=True, exist_ok=True)
    comp_cells = []
    for (g, f), cells in sorted(_groups(manifest).items()):
        offs = _offsets(cells, cw)
        canvas = Image.new("RGBA", (max(o[0] for o in offs) + cw, max(o[1] for o in offs) + ch), (0, 0, 0, 0))
        for c, o in sorted(zip(cells, offs), key=lambda t: (t[0]["x"] + t[0]["y"], t[0]["x"])):
            canvas.alpha_composite(Image.open(cells_dir / c["file"]).convert("RGBA"), o)
        canvas.save(out / comp_name(g, f))
        comp_cells.append({"file": comp_name(g, f), "facing": f, "group": g, "x": 0, "y": 0})
    (out / "manifest.json").write_text(json.dumps(
        {"sheet": manifest.get("sheet"), "cell": manifest["cell"], "cells": comp_cells}, indent=2), encoding="utf-8")
    print(f"prep: {len(comp_cells)} composed canvas(es) -> {out}")


def lift_black(paint: Image.Image, render: Image.Image, luma: int = 28, size: int = 5, k: float = 0.62) -> tuple[Image.Image, int]:
    """FLUX sometimes paints a thin side face (a headboard edge, a locker end) as a solid black
    slab. Where the paint is near-black in a blob at least `size` px thick but the render is
    not dark, take the render's colour darkened by `k`. Thin dark lines (outlines, seams) are
    narrower than `size` and survive the opening untouched."""
    pl = paint.convert("L").point(lambda v: 255 if v < luma else 0)
    thick = pl.filter(ImageFilter.MinFilter(size)).filter(ImageFilter.MaxFilter(size))
    rl = render.convert("L").point(lambda v: 255 if v >= luma * 2 else 0)
    mask = Image.composite(thick, Image.new("L", thick.size, 0), rl)
    shaded = render.convert("RGB").point(lambda v: int(v * k))
    out = paint.copy()
    out.paste(Image.merge("RGBA", (*shaded.split(), paint.split()[3])), (0, 0), mask)
    return out, sum(1 for v in mask.getdata() if v)


def split(cells_dir: Path, painted: Path, out: Path, rename_group: str, lift: bool = False) -> None:
    manifest = json.loads((cells_dir / "manifest.json").read_text(encoding="utf-8"))
    comp_dir = cells_dir.with_name(cells_dir.name + "_comp")
    cw, _ch = manifest["cell"]
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for (g, f), cells in _groups(manifest).items():
        comp = Image.open(painted / comp_name(g, f)).convert("RGBA")
        if lift and (comp_dir / comp_name(g, f)).exists():
            comp, n_lift = lift_black(comp, Image.open(comp_dir / comp_name(g, f)).convert("RGBA"))
            if n_lift:
                print(f"lift-black: {comp_name(g, f)} {n_lift} px")
        for c, (ox, oy) in zip(cells, _offsets(cells, cw)):
            src = Image.open(cells_dir / c["file"]).convert("RGBA")
            region = comp.crop((ox, oy, ox + src.width, oy + src.height))
            final = Image.merge("RGBA", (*region.convert("RGB").split(), src.split()[3]))
            final.save(out / c["file"])
            for key in AUX:
                if c.get(key) and (cells_dir / c[key]).exists():
                    shutil.copy2(cells_dir / c[key], out / c[key])
            n += 1
    if rename_group:
        for c in manifest["cells"]:
            tp = c.get("tile_props")
            if tp and tp.get("GroupName"):
                tp["GroupName"] = rename_group.format(tp["GroupName"])
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"split: {n} cell(s) -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("prep", "split"))
    ap.add_argument("cells", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--painted", type=Path, help="split: paintover.py output for the composed canvases")
    ap.add_argument("--rename-group", default="", help='split: e.g. "Painted {}" for tile_props GroupName')
    ap.add_argument("--lift-black", action="store_true",
                    help="split: replace thick solid-black paint over a non-dark render (see lift_black)")
    a = ap.parse_args()
    if a.mode == "prep":
        prep(a.cells, a.out or a.cells.with_name(a.cells.name + "_comp"))
    else:
        split(a.cells, a.painted or a.cells.with_name(a.cells.name + "_comp_paint"),
              a.out or a.cells.with_name(a.cells.name + "_paint"), a.rename_group, a.lift_black)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
