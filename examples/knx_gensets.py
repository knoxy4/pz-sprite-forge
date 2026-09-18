"""Badlands Power: four generator variants sharing one roll-cage language.

Measured against the four vanilla generators (tools/show_sprite.py):

    appliances_misc_01_0   Generator          0.492 tiles, 0.625 m, raised 16 px
    appliances_misc_01_4   Generator_Old      0.648 tiles, 0.804 m, raised 10 px
    appliances_misc_01_8   Generator_Yellow   0.492 tiles, 0.625 m, raised 15 px
    appliances_misc_01_12  Generator_Blue     0.492 tiles, 0.536 m, raised 16 px

Two facts drive the design. A vanilla generator is a bright body inside a dark
tubular cage -- the near-black frame is ~23% of the sprite's pixels in every one
of them, and it is what makes the silhouette read as "generator" at 63 px. And
Generator_Old is not a recolour: it is a visibly different machine, an engine on
a frame with an exposed flywheel, at 1.3x the footprint. So variants differ by
body colour, footprint, cage treatment AND one signature part.

Base colours are pzforge spec output, not guesses:
    red     (1.000, 0.316, 0.264)   from appliances_misc_01_0
    yellow  (1.000, 0.754, 0.316)   from appliances_misc_01_8
    blue    (0.080, 0.264, 0.665)   from appliances_misc_01_12
    olive   (1.000, 1.000, 0.374)   from appliances_misc_01_4

Run one variant with:
    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" -b \
        -P examples/knx_gensets.py -- propane
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

CAGE = (0.150, 0.150, 0.160)
CAGE_HI = (0.255, 0.255, 0.270)
GRIME = (0.085, 0.082, 0.078)
STEEL = (0.700, 0.715, 0.745)
RUST = (0.420, 0.205, 0.095)
PLANK = (0.849, 0.583, 0.264)

VARIANTS = {
    "propane": dict(
        sheet="bp_genset_propane",
        w=0.56, d=0.48, h=0.44,
        body=(0.080, 0.264, 0.665),
        caged=True,
        signature="tank",
    ),
    "wasteoil": dict(
        sheet="bp_genset_wasteoil",
        w=0.62, d=0.54, h=0.46,
        body=(0.330, 0.375, 0.135),
        caged=True,
        signature="drum",
    ),
    "scrap": dict(
        sheet="bp_genset_scrap",
        w=0.60, d=0.50, h=0.40,
        body=(0.420, 0.205, 0.095),
        caged=False,
        signature="junk",
    ),
    "diesel": dict(
        sheet="bp_genset_diesel",
        w=0.76, d=0.64, h=0.74,
        body=(0.640, 0.420, 0.095),
        caged=False,
        signature="stack",
    ),
}


def mat(name, colour, rough=0.75):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colour, 1.0)
    b.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.15
    return m


def box(name, centre, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


def cyl(name, centre, radius, depth, material, axis="Z"):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=centre, vertices=12)
    o = bpy.context.active_object
    o.name = name
    if axis == "X":
        o.rotation_euler = (0, 1.5708, 0)
    elif axis == "Y":
        o.rotation_euler = (1.5708, 0, 0)
    o.data.materials.append(material)
    return o


def build_cage(w, d, h, m_cage, m_hi):
    """Four corner posts and a top rail. This is the ~23% of near-black that
    makes a vanilla generator legible, so it is deliberately chunky."""
    parts = []
    post = 0.050
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(f"post_{sx}_{sy}",
                             (sx * w / 2, sy * d / 2, h * 0.58),
                             (post, post, h * 1.05), m_cage))
    top = h * 1.05
    parts.append(box("rail_x_f", (0, -d / 2, top), (w + post, post, post), m_hi))
    parts.append(box("rail_x_b", (0, d / 2, top), (w + post, post, post), m_hi))
    parts.append(box("rail_y_l", (-w / 2, 0, top), (post, d + post, post), m_hi))
    parts.append(box("rail_y_r", (w / 2, 0, top), (post, d + post, post), m_hi))
    mid = h * 0.30
    parts.append(box("rail_mid_l", (-w / 2, 0, mid), (post, d + post, post * 0.8), m_cage))
    parts.append(box("rail_mid_r", (w / 2, 0, mid), (post, d + post, post * 0.8), m_cage))
    parts.append(box("rail_mid_b", (0, d / 2, mid), (w + post, post, post * 0.8), m_cage))
    for sy in (-1, 1):
        parts.append(box(f"foot_{sy}", (0, sy * d / 2, 0.022),
                         (w * 0.92, post * 1.3, 0.044), m_cage))
    return parts


def build(name):
    v = VARIANTS[name]
    w, d, h = v["w"], v["d"], v["h"]
    m_cage = mat("cage", CAGE, 0.6)
    m_hi = mat("cage_hi", CAGE_HI, 0.45)
    m_body = mat("body", v["body"], 0.7)
    m_grime = mat("grime", GRIME, 0.85)
    m_steel = mat("steel", STEEL, 0.35)
    m_rust = mat("rust", RUST, 0.9)
    m_plank = mat("plank", PLANK, 0.85)

    parts = []
    lift = 0.048

    if v["caged"]:
        parts += build_cage(w, d, h, m_cage, m_hi)
        parts.append(box("body", (0, 0, lift + h / 2),
                         (w * 0.98, d * 0.96, h * 1.02), m_body))
        parts.append(box("vent", (0, -d * 0.50, lift + h * 0.30),
                         (w * 0.56, 0.018, h * 0.26), m_grime))
        parts.append(box("panel", (w * 0.50, 0, lift + h * 0.62),
                         (0.020, d * 0.40, h * 0.30), m_grime))

    if v["signature"] == "tank":
        cyl("propane_tank", (0, -d * 0.52, lift + h * 0.46), 0.115, w * 0.92,
            m_steel, axis="X")
        parts.append(box("tank_strap", (0, -d * 0.52, lift + h * 0.46),
                         (0.026, 0.235, 0.235), m_cage))
        parts.append(box("regulator", (w * 0.22, -d * 0.52, lift + h * 0.76),
                         (0.05, 0.05, 0.06), m_cage))
    elif v["signature"] == "drum":
        cyl("oil_drum", (w * 0.74, -d * 0.26, lift + 0.22), 0.145, 0.44, m_rust)
        parts.append(box("filter", (-w * 0.62, -d * 0.30, lift + h * 0.52),
                         (0.090, 0.090, 0.17), m_steel))
        parts.append(box("feed_line", (w * 0.36, -d * 0.26, lift + h * 1.04),
                         (w * 0.62, 0.026, 0.026), m_grime))
    elif v["signature"] == "junk":
        parts.append(box("skid_l", (-w * 0.34, 0, 0.030),
                         (0.085, d * 1.04, 0.060), m_plank))
        parts.append(box("skid_r", (w * 0.34, 0, 0.030),
                         (0.085, d * 1.04, 0.060), m_plank))
        parts.append(box("block", (-w * 0.10, 0, 0.060 + h * 0.42),
                         (w * 0.52, d * 0.62, h * 0.84), m_body))
        cyl("motor", (w * 0.26, 0, 0.060 + h * 0.46), 0.115, d * 0.52,
            m_steel, axis="Y")
        parts.append(box("mismatch_panel", (-w * 0.10, -d * 0.33, 0.060 + h * 0.52),
                         (w * 0.34, 0.016, h * 0.40), m_steel))
        for i, sx in enumerate((-1, 1)):
            parts.append(box(f"rebar_{i}", (sx * w * 0.46, 0, 0.060 + h * 0.60),
                             (0.028, 0.028, h * 1.20), m_rust))
        parts.append(box("rebar_top", (0, 0, 0.060 + h * 1.20),
                         (w * 0.96, 0.028, 0.028), m_rust))
    elif v["signature"] == "stack":
        parts.append(box("skid", (0, 0, 0.034),
                         (w * 1.02, d * 1.02, 0.068), m_cage))
        parts.append(box("canopy", (0, 0, 0.068 + h / 2),
                         (w, d, h), m_body))
        parts.append(box("canopy_lid", (0, 0, 0.068 + h + 0.020),
                         (w * 1.03, d * 1.03, 0.040), m_grime))
        for i in range(4):
            parts.append(box(f"louvre_{i}", (0, -d * 0.51, 0.068 + h * 0.22 + i * 0.075),
                             (w * 0.62, 0.030, 0.052), m_grime))
        cyl("exhaust", (w * 0.36, d * 0.30, 0.068 + h + 0.20), 0.045, 0.40, m_grime)
        parts.append(box("grille", (-w * 0.26, -d * 0.53, 0.068 + h * 0.46),
                         (w * 0.40, 0.030, h * 0.46), m_grime))
        cyl("fuel_cap", (-w * 0.30, d * 0.22, 0.068 + h + 0.055), 0.055, 0.055, m_steel)
        for i in range(5):
            parts.append(box(f"grille_slat_{i}", (-w * 0.26, -d * 0.56, 0.068 + h * 0.30 + i * 0.055),
                             (w * 0.36, 0.014, 0.020), m_cage))
        parts.append(box("hazard", (w * 0.26, -d * 0.53, 0.068 + h * 0.70),
                         (w * 0.26, 0.020, 0.075), m_steel))

    return [o for o in bpy.data.objects if o.name != F.SUBJECT_NAME]


def main():
    argv = sys.argv
    name = argv[argv.index("--") + 1] if "--" in argv else "propane"
    if name not in VARIANTS:
        raise SystemExit(f"unknown variant {name!r}; pick from {list(VARIANTS)}")
    v = VARIANTS[name]

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = v["sheet"]
    props.output_dir = str(ROOT / "build" / f"genset_{name}_cells")
    props.footprint_x = props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False

    F.build_rig(bpy.context)
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True

    subject = bpy.data.objects[F.SUBJECT_NAME]
    for part in build(name):
        if part.parent is None:
            part.parent = subject

    print(f"{name}: footprint {(v['w'] + v['d']) / 2:.3f} tiles, body {v['h']:.2f} m")
    manifest = F.render_cells(bpy.context)
    print(f"rendered {len(manifest['cells'])} cells for {name}")


if __name__ == "__main__":
    main()
