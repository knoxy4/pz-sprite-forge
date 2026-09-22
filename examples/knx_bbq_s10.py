"""BADLANDS engine-bay barbecue, v2: the front clip of a 1990 Chevy S10.

Source mesh: "Chevy S10 pickup 1990 (clean)" by zhe_kan, CC BY 4.0,
https://skfb.ly/pEMxE -- credit it on the Workshop page.  Brand marks are
stripped here: the bowtie (Clean.007), the fuel-injection badge (Clean.002),
the side decals (Clean.013) and the wheel-cap logo material.

Pipeline: import glb -> drop cab/glass/spare/badges -> join -> bisect at the
A-pillar keeping the nose -> lift the hood faces out and hinge them open ->
drop a firebox, coal bed and grate into the bay -> close the cut with a
firewall -> scale to the tile -> textured toon materials -> 4 facings.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_bbq_s10.py -- [--samples N] [--fit 1x1|2x1]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

GLB = ROOT / "assets" / "s10" / "source" / "Chevy S10 pickup 1990 (clean).glb"
SHEET = "badlands_bbq_01"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


FIT = arg("--fit", "2x1")
OUT = ROOT / "build" / f"bbq_s10_cells_{FIT}"

# Model units (the glb is ~2.7x metres).  Nose is -y, matching the S facing.
DROP = {"Clean.001", "Clean.002", "Clean.006", "Clean.007", "Clean.010",
        "Clean.013", "Clean.015", "Clean.016", "Clean.017"}
CUT_Y = -3.40            # just behind the front tyre, at the A-pillar
HOOD_OPEN = math.radians(68)
M_PER_UNIT = 4.90 / 13.17  # a real S10 is ~4.9 m long

BBQ_PROPS = {
    "BlocksPlacement": "", "CanScrap": "", "ContainerCapacity": "15",
    "CustomName": "Engine Bay Barbecue", "GroupName": "Badlands",
    "IsMoveAble": "", "IsoType": "IsoBarbecue",
    "Material": "SmallMetalPlates", "Material2": "MetalScrap",
    "MaterialType": "Metal", "PickUpWeight": "200", "ScrapSize": "Medium",
    "container": "barbecue", "solidtrans": "",
}


def import_clip() -> bpy.types.Object:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    imported = [o for o in bpy.data.objects if o not in before]
    for o in imported:
        if o.type != "MESH" or o.name in DROP:
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = "s10_clip"
    body.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bm = bmesh.new()
    bm.from_mesh(body.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, CUT_Y, 0),
                           plane_no=(0, 1, 0), clear_outer=True)
    bm.to_mesh(body.data)
    bm.free()
    return body


def split_hood(body) -> bpy.types.Object:
    """Faces of body paint on top of the bay between the fenders are the hood."""
    paint = {i for i, s in enumerate(body.material_slots)
             if s.material and s.material.name.startswith("Car_paint")}
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    pick = [f for f in bm.faces
            if f.material_index in paint and f.normal.z > HOOD_NZ
            and f.calc_center_median().z > HOOD_Z
            and abs(f.calc_center_median().x) < HOOD_X
            and f.calc_center_median().y < CUT_Y - 0.25]
    print(f"hood: {len(pick)} faces")
    hood_bm = bmesh.new()
    vmap = {}
    for f in pick:
        vs = []
        for v in f.verts:
            if v.index not in vmap:
                vmap[v.index] = hood_bm.verts.new(v.co)
            vs.append(vmap[v.index])
        nf = hood_bm.faces.new(vs)
        nf.material_index = f.material_index
    uv_src = bm.loops.layers.uv.active
    if uv_src is not None:
        uv_dst = hood_bm.loops.layers.uv.new()
        for f, nf in zip(pick, hood_bm.faces):
            for l, nl in zip(f.loops, nf.loops):
                nl[uv_dst].uv = l[uv_src].uv
    bmesh.ops.delete(bm, geom=pick, context="FACES")
    bm.to_mesh(body.data)
    bm.free()

    mesh = bpy.data.meshes.new("s10_hood")
    hood_bm.to_mesh(mesh)
    hood_bm.free()
    for s in body.material_slots:
        mesh.materials.append(s.material)
    hood = bpy.data.objects.new("s10_hood", mesh)
    bpy.context.collection.objects.link(hood)
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    hinge = Vector((0.0, max(ys), max(zs)))
    for v in mesh.vertices:
        v.co -= hinge
    hood.location = hinge
    hood.rotation_euler = (-HOOD_OPEN, 0.0, 0.0)
    return hood


HOOD_Z = 2.05
HOOD_X = 1.95
HOOD_NZ = 0.35


def box(name, lo, hi, mat, parts):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=[(a + b) / 2 for a, b in zip(lo, hi)])
    o = bpy.context.active_object
    o.scale = [b - a for a, b in zip(lo, hi)]
    o.name = name
    o.data.materials.append(mat)
    parts.append(o)
    return o


def rod(name, a, b, r, mat, parts):
    d = [q - p for p, q in zip(a, b)]
    length = math.sqrt(sum(c * c for c in d))
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length, vertices=8,
                                        location=[(p + q) / 2 for p, q in zip(a, b)])
    o = bpy.context.active_object
    o.rotation_euler = (0.0, math.acos(d[2] / length), math.atan2(d[1], d[0]))
    o.name = name
    o.data.materials.append(mat)
    parts.append(o)
    return o


def bay(body) -> list:
    """Firebox, coal bed and grate sized off the cut body; firewall on the cut."""
    t = F.toon_material
    m = {"steel": t("bbq_firebox", (0.20, 0.19, 0.18)),
         "coal": t("bbq_coal", (0.05, 0.045, 0.045)),
         "ember": t("bbq_ember", (0.66, 0.25, 0.06)),
         "ash": t("bbq_ash", (0.52, 0.50, 0.47)),
         "grate": t("bbq_grate", (0.30, 0.29, 0.28)),
         "wall": t("bbq_wall", (0.24, 0.24, 0.25)),
         "cut": t("bbq_cut", (0.30, 0.24, 0.20))}
    ys = [v.co.y for v in body.data.vertices]
    y0, y1 = min(ys) + 0.45, CUT_Y - 0.12
    x = HOOD_X - 0.05
    parts: list = []
    box("firebox", (-x, y0, 1.05), (x, y1, 1.98), m["steel"], parts)
    box("coal_bed", (-x + 0.1, y0 + 0.1, 1.98), (x - 0.1, y1 - 0.1, 2.02), m["coal"], parts)
    span_x, span_y = 2 * x - 0.3, (y1 - y0) - 0.3
    for i in range(22):
        u, v = ((i * 0.618) % 1.0), ((i * 0.382 + 0.17) % 1.0)
        kind = ("ember", "coal", "coal", "ash")[i % 4]
        s = 0.14 + 0.04 * (i % 3)
        cx, cy = -x + 0.15 + u * span_x, y0 + 0.15 + v * span_y
        o = box(f"lump_{i}", (cx - s / 2, cy - s / 2, 2.02), (cx + s / 2, cy + s / 2, 2.02 + s * 0.55),
                m[kind], parts)
        o.rotation_euler = (0.0, 0.0, math.radians((i * 37) % 90))
    gz = 2.17
    n = 13
    for i in range(n):
        gx = -x + 0.12 + i * (2 * x - 0.24) / (n - 1)
        rod(f"grate_{i}", (gx, y0 + 0.08, gz), (gx, y1 - 0.08, gz), 0.022, m["grate"], parts)
    for yy in (y0 + 0.08, y1 - 0.08):
        box(f"grate_rail_{yy:.2f}", (-x + 0.05, yy - 0.04, gz - 0.03), (x - 0.05, yy + 0.04, gz + 0.03),
            m["grate"], parts)
    if FIT == "2x1":
        box("divider", (-0.04, y0, 1.05), (0.04, y1, gz + 0.02), m["steel"], parts)
    box("firewall", (-2.36, CUT_Y - 0.10, 0.95), (2.36, CUT_Y, 2.55), m["wall"], parts)
    box("cut_edge", (-2.36, CUT_Y - 0.11, 2.55), (2.36, CUT_Y + 0.01, 2.60), m["cut"], parts)
    return parts


def convert_materials(objs) -> None:
    done: dict = {}
    for o in objs:
        for s in o.material_slots:
            src = s.material
            if src is None or src.name.startswith(("toon_", "bbq_")):
                continue
            if src.name not in done:
                done[src.name] = F.toon_from_pbr(src, soft=src.name.startswith("Tire"))
            s.material = done[src.name]


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = SHEET
    props.output_dir = str(OUT)
    props.footprint_x = 2 if FIT == "2x1" else 1
    props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    F.build_rig(bpy.context)
    scene.cycles.samples = int(arg("--samples", "512"))
    scene.cycles.use_denoising = True
    subject = bpy.data.objects[F.SUBJECT_NAME]

    body = import_clip()
    hood = split_hood(body)
    for s in body.material_slots:        # wheel-cap logo -> plain rim
        if s.material and s.material.name.startswith("Logo_wheel"):
            s.material = bpy.data.materials.get("Rim") or s.material
    parts = [body, hood] + bay(body)
    convert_materials([body, hood])

    xs = [(body.matrix_world @ v.co).x for v in body.data.vertices]
    ys = [(body.matrix_world @ v.co).y for v in body.data.vertices]
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
    width, depth = max(xs) - min(xs), max(ys) - min(ys)
    scale = M_PER_UNIT if FIT == "2x1" else 0.94 / width
    root = bpy.data.objects.new("clip_root", None)
    bpy.context.collection.objects.link(root)
    for p in parts:
        p.parent = root
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    root.scale = (scale,) * 3
    # Tile (0,0) is centred on the origin and tile (1,0) sits at +x, so a 2x1
    # piece centres on x = 0.5 -- the footprint centre render_cells spins about.
    fx0 = (props.footprint_x - 1) / 2.0
    root.location = (fx0 - cx * scale, -cy * scale, -min(zs) * scale - 2.0 / 77.2)
    root.parent = subject
    print(f"clip {width:.2f} x {depth:.2f} units -> {width * scale:.2f} x "
          f"{depth * scale:.2f} m at scale {scale:.3f} ({FIT})")

    manifest = F.render_cells(bpy.context)
    # Both tiles are live IsoBarbecues (vanilla's two-tile Primitive Forge,
    # crafted_01_45/46, does the same): a divider splits the firebox into two
    # burners, one per tile, each with its own fuel.  SpriteGridPos is what the
    # moveable pickup and the entity SpriteConfig rows key on.
    cells = [dict(c, tile_props=dict(BBQ_PROPS, Facing=c["facing"],
                                     SpriteGridPos=f"{c['x']},{c['y']}"))
             for c in manifest["cells"]]
    manifest["sheet"] = SHEET
    manifest["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
