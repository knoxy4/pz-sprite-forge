"""Multi-tile paintover: paint each facing of a multi-tile object ONCE as a whole, then cut
it back into its tile cells. paintover.py paints cell by cell, so the two halves of a 2x1
were painted independently and disagreed (bench E grew a lamp panel on one half).

    python tools/paintover_multitile.py compose <cells> <whole_dir>
    python tools/paintover.py <whole_dir> --out <whole_paint> ...   (as usual)
    python tools/paintover_multitile.py split <cells> <whole_paint> <out_cells>
"""
import json, shutil, sys
from pathlib import Path
from PIL import Image

HALF_W, QUARTER = 64, 32   # 2:1 iso: tile (x,y) sits at ((x-y)*64, (x+y)*32) on screen


def layout(cells):
    offs = {c["file"]: ((c["x"] - c["y"]) * HALF_W, (c["x"] + c["y"]) * QUARTER) for c in cells}
    mx = min(o[0] for o in offs.values()); my = min(o[1] for o in offs.values())
    return {k: (o[0] - mx, o[1] - my) for k, o in offs.items()}


def by_facing(manifest):
    out = {}
    for c in manifest["cells"]:
        out.setdefault(c["facing"], []).append(c)
    return out


def compose(src: Path, dst: Path):
    m = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    dst.mkdir(parents=True, exist_ok=True)
    cells = []
    for f, cs in by_facing(m).items():
        off = layout(cs)
        ims = {c["file"]: Image.open(src / c["file"]).convert("RGBA") for c in cs}
        w = max(off[k][0] + im.width for k, im in ims.items()); h = max(off[k][1] + im.height for k, im in ims.items())
        canvas = Image.new("RGBA", (w, h))
        # far tiles first so nearer ones win any shared edge pixel
        for c in sorted(cs, key=lambda c: c["x"] + c["y"]):
            canvas.alpha_composite(ims[c["file"]], off[c["file"]])
        name = f"whole_{f}.png"; canvas.save(dst / name)
        cells.append({"file": name, "facing": f, "group": 0, "x": 0, "y": 0,
                      "parts": [{"file": c["file"], "off": off[c["file"]]} for c in cs]})
    (dst / "manifest.json").write_text(json.dumps({"cells": cells}, indent=2), encoding="utf-8")
    print("composed", len(cells), "facings")


def split(src: Path, whole: Path, dst: Path):
    m = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    wm = json.loads((whole / "manifest.json").read_text(encoding="utf-8"))
    dst.mkdir(parents=True, exist_ok=True)
    for wc in wm["cells"]:
        painted = Image.open(whole / wc["file"]).convert("RGBA")
        for part in wc["parts"]:
            cell = Image.open(src / part["file"]).convert("RGBA")
            ox, oy = part["off"]
            rgb = painted.crop((ox, oy, ox + cell.width, oy + cell.height))
            out = Image.new("RGBA", cell.size)
            out.paste(rgb.convert("RGB"), (0, 0))
            out.putalpha(cell.split()[3])          # alpha invariant: the tile's own mask
            out.save(dst / part["file"])
    for c in m["cells"]:
        for key in ("normal", "element", "light"):
            if c.get(key) and (src / c[key]).exists():
                shutil.copy2(src / c[key], dst / c[key])
    shutil.copy2(src / "manifest.json", dst / "manifest.json")
    print("split into", dst)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "compose":
        compose(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        split(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
