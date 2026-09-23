"""BADLANDS spike pit: a square hole with sharpened stakes, and its spent state.

Single facing, 1x1, two cells:  0 armed (stakes up)   1 spent (stakes snapped)

The hole is modelled for real -- walls and floor below z=0 -- and a HOLDOUT
ground plane with a hole cut in it hides everything below ground outside the
opening, so the game's own floor shows round the pit and only the inside of
the hole draws.  A low spoil rim sits on top at ground level.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_spikepit.py -- [--samples N]
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

SHEET = "badlands_spikepit_01"
OUT = ROOT / "build" / "spikepit_cells"
GRAIN = ROOT / "build" / "spikepit_grain.png"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

HOLE = 0.74       # opening, square
DEPTH = 0.55
STAKES = [(x, y) for x in (-0.22, 0.0, 0.22) for y in (-0.22, 0.0, 0.22)]


def _r(*k) -> float:
    h = 2166136261
    for v in k:
        for ch in str(v):
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def _j(s, *k):
    return (_r(*k) - 0.5) * 2 * s


def maps():
    from pzforge.texture import material_spec, write_surface_map
    w = material_spec("wood", seed=71)
    w = dataclasses.replace(w, octaves=[(s, a * 0.25) for s, a in w.octaves], knot_count=0,
                            stroke_count=90, stroke_amplitude=0.08)
    write_surface_map(GRAIN, 512, 512, w, grain_axis="v")


def materials():
    t = F.toon_material
    return {
        "wall": t("pit_wall", (0.30, 0.21, 0.13)),
        "wall_dark": t("pit_wall_dark", (0.17, 0.12, 0.08)),
        "floor": t("pit_floor", (0.12, 0.09, 0.06)),
        "spoil": [t(f"pit_spoil_{i}", p) for i, p in enumerate([
            (0.42, 0.31, 0.19), (0.36, 0.27, 0.17), (0.47, 0.36, 0.23)])],
        "stake": F.forge_material("pit_stake", "wood", (0.58, 0.44, 0.28), texture_path=GRAIN),
        "tip": t("pit_tip", (0.80, 0.68, 0.48)),
        "split": t("pit_split", (0.74, 0.62, 0.42)),
        "holdout": t("pit_holdout", (0.0, 0.0, 0.0)),
    }


def box(parts, name, c, s, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=c)
    o = bpy.context.active_object
    o.name, o.scale, o.rotation_euler = name, s, rot
    o.data.materials.append(mat)
    parts.append(o)
    return o


def cone(parts, name, c, r, h, mat, rot=(0, 0, 0), verts=6):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=0.0, depth=h, location=c)
    o = bpy.context.active_object
    o.name, o.rotation_euler = name, rot
    o.data.materials.append(mat)
    parts.append(o)
    return o


def cyl(parts, name, c, r, h, mat, rot=(0, 0, 0), verts=6):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=c)
    o = bpy.context.active_object
    o.name, o.rotation_euler = name, rot
    o.data.materials.append(mat)
    parts.append(o)
    return o


def ground_with_hole(parts, mat):
    """A 3x3-tile ground plane with the opening cut out: the holdout."""
    me = bpy.data.meshes.new("ground")
    bm = bmesh.new()
    a, h = 1.5, HOLE / 2
    outer = [bm.verts.new(p) for p in ((-a, -a, 0), (a, -a, 0), (a, a, 0), (-a, a, 0))]
    inner = [bm.verts.new(p) for p in ((-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0))]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("ground_holdout", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    o.is_holdout = True
    parts.append(o)
    return o


def pit(m):
    p: list = []
    ground_with_hole(p, m["holdout"])
    h = HOLE / 2
    # walls: the far two (N, W edges of the hole, facing the camera) are lit,
    # the near two only show their top lip -- the holdout hides the rest.
    box(p, "wall_n", (0, h + 0.02, -DEPTH / 2), (HOLE + 0.04, 0.04, DEPTH), m["wall"])
    box(p, "wall_w", (-h - 0.02, 0, -DEPTH / 2), (0.04, HOLE + 0.04, DEPTH), m["wall"])
    box(p, "wall_s", (0, -h - 0.02, -DEPTH / 2), (HOLE + 0.04, 0.04, DEPTH), m["wall_dark"])
    box(p, "wall_e", (h + 0.02, 0, -DEPTH / 2), (0.04, HOLE + 0.04, DEPTH), m["wall_dark"])
    box(p, "floor", (0, 0, -DEPTH - 0.01), (HOLE + 0.04, HOLE + 0.04, 0.02), m["floor"])
    # spoil rim: rounded lumps of dug earth, lowest on the camera side
    k = 0
    for side in range(4):
        for i in range(7):
            u = -h - 0.04 + (i + 0.5) * (HOLE + 0.08) / 7 + _j(0.03, "u", side, i)
            off = h + 0.06 + _j(0.035, "o", side, i)
            x, y = {0: (u, off), 1: (-off, u), 2: (u, -off), 3: (off, u)}[side]
            hgt = (0.05 if side in (0, 1) else 0.03) + _r("h", side, i) * 0.03
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.5, location=(x, y, 0.0))
            o = bpy.context.active_object
            o.name = f"spoil_{k}"
            o.scale = (0.19 + _j(0.04, "w", k), 0.15 + _j(0.03, "d", k), hgt * 2.4)
            o.rotation_euler = (0, 0, _r("r", k) * math.pi)
            o.data.materials.append(m["spoil"][k % 3])
            p.append(o)
            k += 1
    return p


def stakes(m, spent):
    p: list = []
    for n, (x, y) in enumerate(STAKES):
        x += _j(0.03, "sx", n)
        y += _j(0.03, "sy", n)
        lean = (_j(0.14, "lx", n), _j(0.14, "ly", n), 0)
        base_z = -DEPTH
        if spent and _r("gone", n) < 0.75:
            # snapped: a stump with a pale jagged top just under the rim
            stump = 0.40 + _r("st", n) * 0.18
            cyl(p, f"item_stump_{n}", (x, y, base_z + stump / 2), 0.022, stump, m["stake"], rot=lean)
            for s in range(2):
                cone(p, f"item_split_{n}_{s}", (x + 0.008 * s, y, base_z + stump + 0.02),
                     0.012, 0.05 + 0.03 * s, m["split"], rot=(0.3 - 0.6 * s, 0.2, 0))
            continue
        L = DEPTH + 0.10 + _r("len", n) * 0.10
        cyl(p, f"item_stake_{n}", (x, y, base_z + L / 2), 0.022, L, m["stake"], rot=lean)
        # tip sits where the leaning shaft ends
        tx = x + math.sin(lean[1]) * L / 2 * 2 * 0.5
        ty = y - math.sin(lean[0]) * L / 2 * 2 * 0.5
        cone(p, f"item_tip_{n}", (tx, ty, base_z + L + 0.035), 0.023, 0.07, m["tip"], rot=lean)
    if spent:
        # broken-off tops thrown across the hole, resting on the rim
        for k, (ang, dx) in enumerate(((0.7, -0.05), (-0.5, 0.12))):
            cyl(p, f"item_lying_{k}", (dx, 0.02 * k, 0.02), 0.02, 0.62, m["stake"],
                rot=(math.pi / 2, 0, ang))
    return p


PROPS = {"BlocksPlacement": "", "IsLow": "", "CustomName": "Spike Pit",
         "GroupName": "Badlands Traps", "Material": "Wood", "MaterialType": "Wood"}


def main():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    maps()
    F.register()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    pr = sc.pz_forge
    pr.sheet_name = SHEET
    pr.output_dir = str(OUT)
    pr.footprint_x = pr.footprint_y = 1
    pr.facings = "1"
    pr.show_guide = False
    pr.contrast_boost = 1.0
    pr.toon_shading = True
    F.build_rig(bpy.context)
    sc.cycles.samples = int(ARGV[ARGV.index("--samples") + 1]) if "--samples" in ARGV else 512
    sc.cycles.use_denoising = True
    subject = bpy.data.objects[F.SUBJECT_NAME]
    m = materials()
    base = pit(m)
    for o in base:
        o.parent = subject
    cells = []
    merged = None
    for g, spent in enumerate((False, True)):
        parts = stakes(m, spent)
        for o in parts:
            o.parent = subject
        pr.sheet_name = f"{SHEET}_{'spent' if spent else 'armed'}"
        man = F.render_cells(bpy.context)
        merged = merged or dict(man)
        for c in man["cells"]:
            cells.append(dict(c, group=g, tile_props=dict(PROPS)))
        for o in parts:
            bpy.data.objects.remove(o, do_unlink=True)
    merged["sheet"] = SHEET
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
