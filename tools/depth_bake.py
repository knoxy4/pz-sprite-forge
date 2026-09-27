"""Bake B42 tile depth for ANY forge recipe by re-running it with render_cells in depth mode.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P tools/depth_bake.py -- ^
        examples/knx_closet.py build/depth/closet

The recipe runs exactly as it does for a render (same builders, same states, same facing
spin and footprint re-centring, same isolate_tiles hiding), but PZF_DEPTH=1 makes every
render_cells call cast the game's camera rays (pzforge.tiledepth) into the scene instead of
rendering. Its OUT is redirected to the given folder, so the real render manifest and cells
are never touched. Result: <out>/manifest.json in the recipe's own cell order, plus
<cell>_D.npy / <cell>_D.json per cell. Pack with tools/depth_pack.py --manifest.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 2:
        raise SystemExit("usage: blender -b -P tools/depth_bake.py -- <recipe.py> <out dir>")
    recipe, out = (ROOT / argv[0]).resolve(), (ROOT / argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for stale in list(out.glob("*_D.npy")) + list(out.glob("*_D.json")):
        stale.unlink()
    os.environ["PZF_DEPTH"] = "1"
    for p in (ROOT, ROOT / "blender", ROOT / "examples", recipe.parent):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    spec = importlib.util.spec_from_file_location(recipe.stem, recipe)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[recipe.stem] = mod
    spec.loader.exec_module(mod)
    # Redirect OUT on the recipe AND on any example module it drives (knx_scrapshelf sets
    # knx_shelving.OUT and calls into it), so the real cells and manifest stay untouched.
    examples = (ROOT / "examples").resolve()
    hit = []
    for name, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        if f and hasattr(m, "OUT") and Path(f).resolve().parent in (examples, recipe.parent):
            m.OUT = out
            hit.append(name)
    if not hit:
        raise SystemExit(f"{recipe.name} has no module-level OUT to redirect")
    print(f"depth_bake: OUT redirected on {', '.join(hit)}")
    # a variant recipe (knx_scrapshelf) patches its base module and runs the base's main
    run = getattr(mod, "main", None) or next(
        (sys.modules[n].main for n in hit if n != recipe.stem and hasattr(sys.modules[n], "main")), None)
    if run is None:
        raise SystemExit(f"{recipe.name}: no main() to run")
    run()
    print(f"depth_bake: {recipe.name} -> {out}")


if __name__ == "__main__":
    main()
