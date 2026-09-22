"""Depth bake for the walk-in Makeshift Shower (badlands_rain_01_14..21).

B42 draws a tile with no depth texture as a solid full-tile cube (DEPTH_whole_tile), so a
player standing in the stall drew behind all of it. This casts the GAME's own camera rays
(pzforge.tiledepth, a port of TileGeometryUtils) into the exact geometry knx_rain.py
renders -- same builders, same DiagonalMirror / fit_west slots -- and records the
normalized depth of the first hit per pixel.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_rain_depth.py

Writes build/rain_depth/raw_<index>.npy (float32 256x128, -1 = ray missed) and
build/rain_depth/boxes_<index>.json (every part's axis-aligned box, tile scene space).
tools/depth_pack.py then masks each cell with the FINAL sprite's alpha and writes the mod's
common/media/depthmaps/DEPTH_badlands_rain_01.png and common/media/tileGeometry.txt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

import knx_rain as R  # noqa: E402  (module import; its main() does not run)
from pzforge import tiledepth as TD  # noqa: E402

OUT = ROOT / "build" / "rain_depth"
FIRST_INDEX = {"shower": 14, "showerc": 18}   # sheet slot of facing S; E, N, W follow


class Mats(dict):
    """build_shower only needs a material per name; depth does not care which."""

    def __missing__(self, key):
        mat = bpy.data.materials.new(key)
        self[key] = mat
        return mat


def to_scene(v) -> tuple:
    """Blender (x east, y north, z up) -> tile scene space (x east, y up, z south)."""
    return (v[0], v[2], -v[1])


def to_blender(x, y, z) -> Vector:
    return Vector((x, -z, y))


def bake_slot(parts) -> tuple[np.ndarray, list]:
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
    for key, first in FIRST_INDEX.items():
        for k, slot in enumerate(("S", "E", "N", "W")):
            diag, west = R.SHOWER_SLOTS[slot]
            b = R.Builder(0.0)
            R.build_shower(R.DiagonalMirror(b) if diag else b, mats,
                           closed=(key == "showerc"), fit_west=west)
            depth, boxes = bake_slot(b.parts)
            idx = first + k
            np.save(OUT / f"raw_{idx}.npy", depth)
            (OUT / f"boxes_{idx}.json").write_text(json.dumps(boxes, indent=1), encoding="utf-8")
            print(f"== {R.SHEET}_{idx} ({key} {slot}): {int((depth >= 0).sum())} px hit, {len(boxes)} parts")
            for obj in list(b.parts):
                bpy.data.objects.remove(obj, do_unlink=True)


if __name__ == "__main__":
    main()
