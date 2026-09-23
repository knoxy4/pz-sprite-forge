"""BADLANDS beehive: a Langstroth-style box hive on legs.

Source mesh: "Bee Hive" by Lisiaasty, CC BY 4.0,
https://sketchfab.com/3d-models/bee-hive-5ac5d5a85d0d41d396565718c0ba7ac3
-- credit it on the Workshop page and in credits.txt.

1x1, four facings.  Cells: the bare hive per facing (the entity's SpriteConfig),
then overlay-only cells per progress stage (SpriteOverlayConfig progress 0/50/100):
honey glazing the landing board, then stringing off its lip to the ground.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_hive.py -- [--samples N] [--only base]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

GLB = Path(r"C:\Users\KNX\dev\bee_hive.glb")
SHEET = "badlands_hive_01"
OUT = ROOT / "build" / "hive_cells"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


#: Real hive: ~0.5 m square box on legs, ~0.75 m to the roof.  Tile = 1.0.
TARGET_W = 0.56
OFFSET_Z = -2.0 / 77.2


def import_hive() -> list:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    bpy.context.view_layer.update()
    worlds = {o.name: o.matrix_world.copy() for o in meshes}
    for o in meshes:
        o.parent = None
        o.matrix_world = worlds[o.name]
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        for s in o.material_slots:
            if s.material and not s.material.name.startswith("toon_"):
                s.material = F.toon_from_pbr(s.material)
    return meshes


def fit(meshes, subject) -> float:
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    scale = TARGET_W / max(hi.x - lo.x, hi.y - lo.y)
    root = bpy.data.objects.new("hive_root", None)
    bpy.context.collection.objects.link(root)
    for o in meshes:
        o.parent = root
    c = (lo + hi) / 2
    root.scale = (scale,) * 3
    # The model's entrance faces +x; the S facing wants it at -y (the front).
    root.rotation_euler = (0.0, 0.0, -math.pi / 2)
    root.location = (-c.y * scale, c.x * scale, -lo.z * scale + OFFSET_Z)
    root.parent = subject
    print(f"hive {hi.x - lo.x:.1f} x {hi.y - lo.y:.1f} x {hi.z - lo.z:.1f} units -> "
          f"scale {scale:.5f}, height {(hi.z - lo.z) * scale:.2f} m")
    return (hi.z - lo.z) * scale


def setup() -> bpy.types.Object:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = SHEET
    props.output_dir = str(OUT)
    props.footprint_x = props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    F.build_rig(bpy.context)
    scene.cycles.samples = int(arg("--samples", "512"))
    scene.cycles.use_denoising = True
    return bpy.data.objects[F.SUBJECT_NAME]


def body_geometry(meshes, lo, hi):
    """Wall extents at mid-height and leg post centres, from the wood mesh."""
    wood = next(o for o in meshes if any(s.material and "Wood" in s.material.name
                                         for s in o.material_slots))
    vs = [wood.matrix_world @ v.co for v in wood.data.vertices]
    H = hi.z - lo.z
    mid = [v for v in vs if lo.z + 0.45 * H < v.z < lo.z + 0.55 * H]
    wall = (min(v.x for v in mid), max(v.x for v in mid), min(v.y for v in mid), max(v.y for v in mid))
    legs_z = lo.z + 0.08 * H
    low = [v for v in vs if v.z < legs_z]
    cx, cy = (wall[0] + wall[1]) / 2, (wall[2] + wall[3]) / 2
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = [v for v in low if (v.x - cx) * sx > 0 and (v.y - cy) * sy > 0]
            legs.append((sum(v.x for v in q) / len(q), sum(v.y for v in q) / len(q),
                         max(v.x for v in q) - min(v.x for v in q)))
    box_bottom = min(v.z for v in vs if lo.z + 0.12 * H < v.z and
                     (abs(v.x - wall[0]) < 0.01 or abs(v.x - wall[1]) < 0.01))
    # Landing board: whatever sticks out past the front wall in the lower half.
    allv = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lip = [v for v in allv if v.y < wall[2] - 0.01 and v.z < lo.z + 0.6 * H and v.z > box_bottom - 0.01]
    lip_box = (min(v.x for v in lip), max(v.x for v in lip), min(v.y for v in lip),
               min(v.z for v in lip), max(v.z for v in lip)) if lip else None
    print("LIP", [round(c, 3) for c in lip_box] if lip_box else None)
    print("WALL", [round(w, 3) for w in wall], "LEGS", [tuple(round(c, 3) for c in l) for l in legs],
          "BOXBOTTOM", round(box_bottom, 3), "LO", round(lo.z, 3))
    return wall, legs, box_bottom, lip_box


def world_box(meshes):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def toon(name, rgb):
    return F.toon_material(name, rgb)


GEOM = None
#: The swarm trap is a nuc box: the hive at this scale.
TRAP_SCALE = 0.62

#: progress stage -> (glaze width fraction of the landing board, honey strings).
#: No bees -- operator call.  Stage 0 is a thin glaze so a working hive reads.
STAGES = {0: (0.25, 0), 50: (0.45, 2), 100: (0.85, 4)}


def overlay(stage, lo, hi, subject) -> list:
    """Honey on the landing board and stringing off its lip, in world space."""
    glaze_w, drips = STAGES[stage]
    honey = toon("hive_honey", (0.95, 0.60, 0.05))
    front = lo.y
    z0 = lo.z + (hi.z - lo.z) * 0.20
    parts = []
    # Honey comes out of the entrance lip only: a glaze over the landing board,
    # strings off its front edge, ending flush with the bottom of the feet (lo.z)
    # in small pools.  Stage sets how many strings run.
    wall, legs, box_bottom, lip = GEOM
    x0, x1, lip_y, lip_z0, lip_z1 = lip
    if glaze_w:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=((x0 + x1) / 2, lip_y + 0.012, lip_z1 + 0.002))
        glaze = bpy.context.active_object
        glaze.scale = ((x1 - x0) * glaze_w, 0.026, 0.004)
        glaze.data.materials.append(honey)
        parts.append(glaze)
    for k in range(drips):
        t = (0.30, 0.68, 0.14, 0.86)[k]
        x = x0 + (x1 - x0) * t
        y = lip_y - 0.004
        top = lip_z0 + 0.002
        length = top - lo.z
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.010,
                                             location=(x, y + 0.004, lip_z1))
        bead = bpy.context.active_object
        bead.scale = (1.2, 1.0, 1.4)
        bead.data.materials.append(honey)
        parts.append(bead)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0070, depth=length,
                                            location=(x, y, lo.z + length / 2))
        s = bpy.context.active_object
        s.data.materials.append(honey)
        parts.append(s)
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.026 + 0.008 * (k % 2), depth=0.004,
                                            location=(x, y, lo.z + 0.002))
        pool = bpy.context.active_object
        pool.data.materials.append(honey)
        parts.append(pool)
    for part in parts:
        part.parent = subject
    return parts


def main() -> None:
    subject = setup()
    meshes = import_hive()
    fit(meshes, subject)
    lo, hi = world_box(meshes)
    global GEOM
    GEOM = body_geometry(meshes, lo, hi)
    if "--measure" in ARGV:
        return
    props = bpy.context.scene.pz_forge
    merged, cells = None, []
    stages = [None] if "--only" in ARGV else [None, 0, 50, 100, "trap"]
    root = bpy.data.objects["hive_root"]
    for stage in stages:
        if stage == "trap":
            # Swarm trap: the same box as a nuc, scaled down on its legs.
            k = TRAP_SCALE
            root.scale = tuple(c * k for c in root.scale)
            root.location = (root.location.x * k, root.location.y * k,
                             (root.location.z - OFFSET_Z) * k + OFFSET_Z)
            for o in meshes:
                o.is_holdout = False
            props.sheet_name = f"{SHEET}_trap"
            manifest = F.render_cells(bpy.context)
            for c in manifest["cells"]:
                cells.append(dict(c, stage="trap"))
            continue
        parts = []
        for o in meshes:
            o.is_holdout = stage is not None
        if stage is not None:
            parts = overlay(stage, lo, hi, subject)
        props.sheet_name = SHEET if stage is None else f"{SHEET}_p{stage}"
        manifest = F.render_cells(bpy.context)
        merged = merged or dict(manifest)
        for c in manifest["cells"]:
            cells.append(dict(c, stage=stage))
        for part in parts:
            bpy.data.objects.remove(part, do_unlink=True)
    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
