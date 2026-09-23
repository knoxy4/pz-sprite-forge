"""BADLANDS corrugated sheet fence: the one batch-2 fence vanilla has no art for.

Scrap-yard build: overlapping corrugated sheets (mixed galvanised, rusted and
old red paint) screwed to two 2x4 rails on the yard side.  Wall grammar from
examples/brick_wall.py; 2x4 footprint, isolate_tiles, one sprite per tile:

    (0,0) WallW      (1,0) WallN
    (0,1) NW corner  (1,1) SE post (at its own tile's NW corner)
    (0,2) gate W     (1,2) gate N          closed, hinged at the NW corner
    (0,3) gate W op  (1,3) gate N op       swung 90 deg about that corner

Open-gate placement matches vanilla's picket gate (fixtures_doors_fences_01_8..11):
open W lies N-parallel, open N lies W-parallel, both off the NW corner.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_corrugated.py -- [--samples N]
"""
from __future__ import annotations

import dataclasses
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(ROOT))

import pz_sprite_forge as F  # noqa: E402

SHEET = "badlands_corrugated_01"
OUT = ROOT / "build" / "corrugated_cells"
STREAK = ROOT / "build" / "corrugated_streak.png"
GRAIN = ROOT / "build" / "corrugated_grain.png"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

H = 1.90          # sheet top
GATE_H = 1.80
BASE = 0.03       # gap under the sheets
T = 0.02          # sheet plane inset from the tile edge
AMP = 0.011       # corrugation half-depth
PERIOD = 0.068    # rib pitch (about 2.7 in)
RAILS = (0.32, 1.52)
POST = 0.09


def _r(*k) -> float:
    h = 2166136261
    for v in k:
        for ch in str(v):
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def maps() -> None:
    from pzforge.texture import material_spec, write_surface_map
    m = material_spec("metal", seed=113)
    write_surface_map(STREAK, 512, 512, dataclasses.replace(m, stroke_amplitude=0.22))
    w = material_spec("wood", seed=57)
    w = dataclasses.replace(w, octaves=[(s, a * 0.3) for s, a in w.octaves], knot_count=1)
    write_surface_map(GRAIN, 512, 512, w, grain_axis="v")


def materials() -> dict:
    fm = F.forge_material
    rust = (0.42, 0.20, 0.08)
    return {
        "galv": fm("cor_galv", "metal", (0.60, 0.62, 0.63), texture_path=STREAK, accent=rust,
                   swing=(0.72, 1.12)),
        "rust": fm("cor_rust", "metal", (0.44, 0.25, 0.13), texture_path=STREAK,
                   accent=(0.30, 0.13, 0.05), swing=(0.70, 1.18)),
        "red": fm("cor_red", "metal", (0.52, 0.19, 0.14), texture_path=STREAK, accent=rust,
                  swing=(0.72, 1.12)),
        "wood": fm("cor_wood", "wood", (0.46, 0.34, 0.22), texture_path=GRAIN),
        "screw": F.toon_material("cor_screw", (0.30, 0.30, 0.31)),
        "latch": F.toon_material("cor_latch", (0.16, 0.16, 0.17)),
    }


def corrugated(name, length, height, mat, parts):
    """A sheet in local space: run along +X, height +Z, ribs as a sine in Y."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    nu = max(8, int(length / PERIOD * 8))
    cols = []
    for i in range(nu + 1):
        u = length * i / nu
        y = AMP * math.sin(2 * math.pi * u / PERIOD)
        cols.append((bm.verts.new((u, y, 0.0)), bm.verts.new((u, y, height))))
    for a, b in zip(cols, cols[1:]):
        bm.faces.new((a[0], b[0], b[1], a[1]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    mod = o.modifiers.new("thick", "SOLIDIFY")
    mod.thickness = 0.004
    mod.offset = 0
    parts.append(o)
    return o


def box(name, centre, size, mat, parts, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
    o = bpy.context.active_object
    o.name, o.scale = name, size
    o.rotation_euler.z = rot
    o.data.materials.append(mat)
    parts.append(o)
    return o


def to_world(origin, heading, u, n, z):
    """Local run coords -> world: u along heading, n along the left normal."""
    ch, sh = math.cos(heading), math.sin(heading)
    return (origin[0] + u * ch - n * sh, origin[1] + u * sh + n * ch, z)


def run(key, origin, heading, length, M, parts, cam_side, top=H, rails=True, sheets=2):
    """A fence run from origin along heading. cam_side = +1/-1: which normal
    side the rails (and so the camera) are on."""
    tints = ("galv", "rust", "red")
    edges = [0.0]
    for s in range(1, sheets):
        edges.append(length * s / sheets + (_r(key, "edge", s) - 0.5) * 0.08)
    edges.append(length)
    for s in range(sheets):
        a = max(0.0, edges[s] - (0.03 if s else 0.0))
        b = edges[s + 1]
        tint = tints[int(_r(key, "tint", s) * 3) % 3]
        hgt = top - BASE - _r(key, "h", s) * 0.07
        o = corrugated(f"{key}_sheet{s}", b - a, hgt, M[tint], parts)
        n = -cam_side * 0.006 * (s % 2)
        o.location = to_world(origin, heading, a, n, BASE + _r(key, "z", s) * 0.02)
        o.rotation_euler.z = heading
    if not rails:
        return
    for z in RAILS:
        if z > top:
            continue
        c = to_world(origin, heading, length / 2, cam_side * (AMP + 0.028), z)
        box(f"{key}_rail{z}", c, (length - 0.01, 0.04, 0.085), M["wood"], parts, heading)
        for k in range(int(length / 0.2)):
            u = 0.1 + k * 0.2 + (_r(key, z, k) - 0.5) * 0.03
            c = to_world(origin, heading, u, cam_side * (AMP + 0.004), z + 0.02)
            box(f"{key}_screw{z}_{k}", c, (0.012, 0.01, 0.012), M["screw"], parts, heading)


def gate(key, hinge, heading, M, parts, cam_side):
    """Gate leaf hinged at `hinge`, running along heading: sheet skin, a Z of
    2x4s on the camera side, and a latch at the free end."""
    L = 0.92
    run(key, hinge, heading, L, M, parts, cam_side, top=GATE_H, rails=False, sheets=2)
    off = cam_side * (AMP + 0.028)
    for z in (0.22, GATE_H - 0.22):
        box(f"{key}_bar{z}", to_world(hinge, heading, L / 2, off, z),
            (L - 0.02, 0.04, 0.085), M["wood"], parts, heading)
    # diagonal brace from bottom hinge side to top latch side
    a = to_world(hinge, heading, 0.06, off, 0.26)
    b = to_world(hinge, heading, L - 0.06, off, GATE_H - 0.26)
    mid = tuple((p + q) / 2 for p, q in zip(a, b))
    horiz = math.hypot(b[0] - a[0], b[1] - a[1])
    ln = math.hypot(horiz, b[2] - a[2])
    o = box(f"{key}_brace", mid, (ln, 0.04, 0.08), M["wood"], parts, heading)
    o.rotation_euler = (0.0, -math.atan2(b[2] - a[2], horiz), heading)
    o.rotation_mode = "XYZ"
    box(f"{key}_latch", to_world(hinge, heading, L - 0.07, cam_side * (AMP + 0.06), 1.0),
        (0.10, 0.02, 0.03), M["latch"], parts, heading)


def build(M) -> list:
    p: list = []
    S, E, N, W = -math.pi / 2, 0.0, math.pi / 2, math.pi
    # (0,0) WallW: x = -0.5+T, runs south from y=+0.5; camera side is +x.
    #   heading S (-y): left normal is +x -> cam_side +1.
    run("w", (-0.5 + T, 0.5), S, 1.0, M, p, +1)
    # (1,0) WallN: y = 0.5-T, runs east from x=0.5; camera side is -y.
    #   heading E (+x): left normal is +y -> cam_side -1.
    run("n", (0.5, 0.5 - T), E, 1.0, M, p, -1)
    # (0,1) world (0,-1): NW corner. N arm stops 2 mm short of the east edge.
    run("cw", (-0.5 + T, -0.5), S, 1.0, M, p, +1)
    run("cn", (-0.5 + T + 0.01, -0.5 - T), E, 0.978 - T, M, p, -1)
    # (1,1) world (1,-1): SE post at its own tile's NW corner.
    box("post", (0.5 + POST / 2, -0.5 - POST / 2, (H + 0.06) / 2), (POST, POST, H + 0.06), M["wood"], p)
    # (0,2) world (0,-2): gate W, hinge at NW corner (-0.5, -1.5).
    gate("gw", (-0.5 + T, -1.5 - 0.03), S, M, p, +1)
    # (1,2) world (1,-2): gate N, hinge at NW corner (0.5, -1.5).
    gate("gn", (0.5 + 0.03, -1.5 - T), E, M, p, -1)
    # (0,3) world (0,-3): gate W open -- swung about the NW corner into the tile,
    #   lying N-parallel just inside the north edge.
    gate("gwo", (-0.5 + 0.06, -2.5 - 0.06), E, M, p, -1)
    # (1,3) world (1,-3): gate N open -- lying W-parallel just inside the west edge.
    gate("gno", (0.5 + 0.06, -2.5 - 0.06), S, M, p, +1)
    return p


PROPS_COMMON = {"CanScrap": "", "Material": "MetalPlates", "Material2": "Wood",
                "MaterialType": "Metal", "GroupName": "Badlands Corrugated"}


def tile_props(i, j):
    s = lambda k: f"{SHEET}_{k}"
    wall = dict(PROPS_COMMON, CloseSneakBonus="500", wall="")
    door = {"CanScrap": "", "CustomName": "Fence gate", "Material": "Door",
            "Material2": "MetalPlates", "MaterialType": "Metal"}
    return {
        (0, 0): dict(wall, WallW="", TallHoppableW=""),
        (1, 0): dict(wall, WallN="", TallHoppableN=""),
        (0, 1): dict(wall, WallNW="", TallHoppableN="", TallHoppableW="",
                     CornerNorthWall=s(1), CornerWestWall=s(0)),
        (1, 1): {"CanScrap": "", "Material": "Wood", "NoWallLighting": "", "WallSE": "", "wall": ""},
        (0, 2): dict(door, doorW="", attachedW=""),
        (1, 2): dict(door, doorN="", attachedN=""),
        (0, 3): dict(door, attachedW=""),
        (1, 3): dict(door, attachedN=""),
    }[(i, j)]


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    maps()
    F.register()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    pr = sc.pz_forge
    pr.sheet_name = SHEET
    pr.output_dir = str(OUT)
    pr.footprint_x, pr.footprint_y = 2, 4
    pr.facings = "1"
    pr.isolate_tiles = True
    pr.show_guide = False
    pr.contrast_boost = 1.0
    pr.toon_shading = True
    F.build_rig(bpy.context)
    sc.cycles.samples = int(ARGV[ARGV.index("--samples") + 1]) if "--samples" in ARGV else 512
    sc.cycles.use_denoising = True
    subject = bpy.data.objects[F.SUBJECT_NAME]
    for o in build(materials()):
        o.parent = subject
    manifest = F.render_cells(bpy.context)
    for c in manifest["cells"]:
        c["group"] = 0
        c["tile_props"] = tile_props(c["x"], c["y"])
    manifest["isolate_tiles"] = True
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"rendered {len(manifest['cells'])} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
