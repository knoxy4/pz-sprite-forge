"""Depth bake for Boombuk's Beds (boombuk_beds_01_0..55).

A B42 tile with no depth texture draws as a solid full-tile cube, so a sleeper would draw
behind the whole bed.  Borrowing vanilla bed depth maps is no good either: the tileWithDepth
shader discards every sprite pixel whose depth texel is empty, so any part that pokes out of
the vanilla silhouette (a taller headboard, the loft ladder) would vanish.  So, as for the
Makeshift Shower (knx_rain_depth.py): cast the game's own camera rays (pzforge.tiledepth)
into the exact geometry knx_beds.py renders, one footprint tile at a time, with the same
facing spin and footprint re-centring as render_cells.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_beds_depth.py

Writes build/beds_depth/raw_<index>.npy + boxes_<index>.json; then
    uv run --with pillow --with numpy python tools/depth_pack.py --raw build/beds_depth ^
        --sheet <build>/42/media/boombuk_beds_01.png --tileset boombuk_beds_01 --media <mod>/common/media
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

import knx_beds as B  # noqa: E402  (module import; its main() does not run)
from pzforge import tiledepth as TD  # noqa: E402

OUT = ROOT / "build" / "beds_depth"
FACINGS = ("S", "E", "N", "W")


class Mats(dict):
    def __missing__(self, key):
        mat = bpy.data.materials.new(key)
        self[key] = mat
        return mat


def to_scene(v) -> tuple:
    """Blender (x east, y north, z up) -> tile scene space (x east, y up, z south)."""
    return (v[0], v[2], -v[1])


def to_blender(x, y, z) -> Vector:
    return Vector((x, -z, y))


def bake(parts) -> tuple[np.ndarray, list]:
    bpy.context.view_layer.update()
    bm = bmesh.new()
    boxes = []
    for obj in parts:
        me = obj.to_mesh()
        me.transform(obj.matrix_world)
        bm.from_mesh(me)
        obj.to_mesh_clear()
        corners = [to_scene(obj.matrix_world @ Vector(c)) for c in obj.bound_box]
        lo = [min(c[i] for c in corners) for i in range(3)]
        hi = [max(c[i] for c in corners) for i in range(3)]
        # only this tile's own parts go in tileGeometry (debug editor); the bake sees all
        if lo[0] < 0.5 and hi[0] > -0.5 and lo[2] < 0.5 and hi[2] > -0.5:
            boxes.append({"name": obj.name, "min": lo, "max": hi})
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    origins, dirs = TD.pixel_rays()
    n = origins.shape[1]
    hits = np.zeros((3, n))
    ok = np.zeros(n, dtype=bool)
    for i in range(n):
        loc, _nrm, _idx, _dist = bvh.ray_cast(to_blender(*origins[:, i]), to_blender(*dirs[:, i]), 10.0)
        if loc is not None:
            hits[:, i] = to_scene(loc)
            ok[i] = True
    depth = np.full(n, -1.0, dtype=np.float32)
    depth[ok] = TD.normalized(TD.depth_of_points(hits[:, ok]))
    return depth.reshape(TD.CELL_H, TD.CELL_W), boxes


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    OUT.mkdir(parents=True, exist_ok=True)
    mats = Mats()
    index = 0
    for key, _g, _c, _bed, (fpx, fpy), *_rest in B.BEDS:
        b = B.Builder()
        B.BUILDERS[key](b, mats)
        root = bpy.data.objects.new("depth_root", None)
        bpy.context.collection.objects.link(root)
        for p in b.parts:
            p.parent = root
        c0 = Vector(((fpx - 1) / 2.0, -(fpy - 1) / 2.0, 0.0))
        for f, facing in enumerate(FACINGS):
            swap = f % 2 == 1
            fx, fy = (fpy, fpx) if swap else (fpx, fpy)
            c1 = Vector(((fx - 1) / 2.0, -(fy - 1) / 2.0, 0.0))
            spin = Matrix.Rotation(math.radians(90.0 * f), 4, "Z")
            base = c1 - (spin @ c0)
            tiles = sorted(((x, y) for y in range(fy) for x in range(fx)), key=lambda t: (t[1], t[0]))
            for (x, y) in tiles:
                root.rotation_euler = (0.0, 0.0, math.radians(90.0 * f))
                root.location = base - Vector((x, -y, 0.0))
                depth, boxes = bake(b.parts)
                np.save(OUT / f"raw_{index}.npy", depth)
                (OUT / f"boxes_{index}.json").write_text(json.dumps(boxes, indent=1), encoding="utf-8")
                print(f"== {B.SHEET}_{index} ({key} {facing} {x},{y}): {int((depth >= 0).sum())} px hit, "
                      f"{len(boxes)} boxes")
                index += 1
        for obj in list(b.parts) + [root]:
            bpy.data.objects.remove(obj, do_unlink=True)
    print(f"baked {index} cells to {OUT}")


if __name__ == "__main__":
    main()
