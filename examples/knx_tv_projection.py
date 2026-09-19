"""BadlandsClutter: early-90s rear-projection television, one tile.

A floor-standing big-screen set of the 1990-93 generation, the living-room
status piece of the period (PZ is set in 1993, so no flat panels):

* tall black cabinet, ~0.98 m wide, 1.30 m tall -- a 46-inch 4:3 screen
  (0.84 x 0.63 m) in a gloss bezel on the upper front;
* lower front: two cloth speaker grilles either side of a control door with a
  silver trim strip (left blank -- no maker's name);
* walnut-veneer side panels on the lower cabinet, a plinth, and the
  projector's sloped back: the cabinet is 0.58 m deep at the floor and
  0.30 m at the top, with vent slats and cables down to the floor;
* a VCR and a tape on the top, because that is where it went.

Screens are rendered as SEPARATE passes of the screen plane alone, with an
emission image, so the overlay sprites land pixel-exact on the body sprite.
See knx_tv_screens.py for why they sit at +16/+32/+48/+64.

Pipeline:
    uv run --python 3.12 --with pillow python examples/knx_tv_screens.py textures
    blender -b -P examples/knx_tv_projection.py
    uv run --python 3.12 --with pillow python examples/knx_tv_screens.py assemble
    uv run --python 3.12 --with pillow python -m pzforge.cli build build/tv_projection_cells ...
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "tv_projection_cells"
TEX = ROOT / "build" / "tv_screens"
SHEET = "badlandsclutter_tv_01"

W = 0.980          # cabinet width (X)
D_BASE = 0.580     # depth at the floor
D_TOP = 0.300      # depth at the top: the sloped projector back
H = 1.300
LOWER = 0.520      # top of the speaker section
FY = -0.290        # front face plane (the S camera sees -Y)
SCR_W, SCR_H = 0.840, 0.630
SCR_Z = LOWER + 0.050 + SCR_H / 2 + 0.035


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "examples" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def tv_materials(g) -> dict:
    m = g.materials()
    m.update({
        "walnut": F.forge_material("tv_walnut", "wood", (0.330, 0.190, 0.095)),
        "grille": F.forge_material("tv_grille", "fabric", (0.155, 0.140, 0.130)),
        "gloss": F.forge_material("tv_gloss", "metal", (0.040, 0.040, 0.042),
                                  hue=g.KEEP_HUE),
        "screen_off": F.forge_material("tv_screen_off", "metal",
                                       (0.075, 0.095, 0.095), hue=g.KEEP_HUE),
        "glare": F.forge_material("tv_glare", "metal", (0.150, 0.180, 0.185),
                                  hue=g.KEEP_HUE),
        "vcr_black": F.forge_material("tv_vcr", "metal", (0.090, 0.090, 0.092),
                                      hue=g.KEEP_HUE),
        "tape_label": F.forge_material("tv_tape_label", "metal",
                                       (0.860, 0.840, 0.760), hue=g.KEEP_HUE),
    })
    return m


def mesh_obj(k, name, verts, faces, material):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return k._add(obj, name, material)


def build_body(k, m) -> None:
    # Plinth, recessed.
    k.box("tv_plinth", (0, FY + D_BASE / 2 + 0.010, 0.030),
          (W - 0.030, D_BASE - 0.040, 0.060), m["gap"])
    # Lower cabinet.
    k.box("tv_lower", (0, FY + D_BASE / 2, 0.060 + (LOWER - 0.060) / 2),
          (W, D_BASE, LOWER - 0.060), m["black_plastic"], bevel=0.008)
    for sx in (-1, 1):
        k.box(f"tv_walnut_{sx}", (sx * (W / 2 + 0.006), FY + D_BASE / 2,
                                  0.060 + (LOWER - 0.060) / 2),
              (0.012, D_BASE - 0.030, LOWER - 0.080), m["walnut"], bevel=0.004)
    # Upper housing: a prism, vertical front, back sloping from D_BASE to D_TOP.
    y0, yb, yt = FY, FY + D_BASE, FY + D_TOP
    hw = W / 2
    verts = [(-hw, y0, LOWER), (hw, y0, LOWER), (hw, yb, LOWER), (-hw, yb, LOWER),
             (-hw, y0, H), (hw, y0, H), (hw, yt, H), (-hw, yt, H)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
             (2, 6, 7, 3), (3, 7, 4, 0)]
    upper = mesh_obj(k, "tv_upper", verts, faces, m["black_plastic"])
    mod = upper.modifiers.new("bevel", "BEVEL")
    mod.width = 0.008
    mod.segments = 2
    mod.limit_method = "ANGLE"
    k.box("tv_waist", (0, FY - 0.004, LOWER), (W + 0.004, 0.012, 0.016), m["steel"])

    # Screen: gloss bezel, dark tube, a diagonal glare band.
    k.box("tv_bezel", (0, FY - 0.004, SCR_Z), (SCR_W + 0.070, 0.010, SCR_H + 0.060),
          m["gloss"], bevel=0.010)
    k.box("tv_screen", (0, FY - 0.008, SCR_Z), (SCR_W, 0.004, SCR_H),
          m["screen_off"])
    k.box("tv_glare", (-SCR_W * 0.18, FY - 0.0105, SCR_Z + SCR_H * 0.12),
          (SCR_W * 0.10, 0.001, SCR_H * 0.90), m["glare"], rot=(0, 0.55, 0))
    # Top trim cap.
    k.box("tv_cap", (0, FY + D_TOP / 2, H + 0.008), (W, D_TOP, 0.016),
          m["gloss"], bevel=0.004)

    # Lower front: speaker grilles, control door, silver strip, buttons, lamp.
    gz = 0.060 + (LOWER - 0.060) * 0.46
    for sx in (-1, 1):
        k.box(f"tv_grille_{sx}", (sx * W * 0.32, FY - 0.004, gz),
              (W * 0.30, 0.008, (LOWER - 0.060) * 0.74), m["grille"], bevel=0.004)
    k.box("tv_door", (0, FY - 0.004, gz - 0.050), (W * 0.28, 0.008, 0.200),
          m["black_plastic"], bevel=0.006)
    k.box("tv_door_gap", (0, FY - 0.009, gz + 0.050), (W * 0.28, 0.003, 0.004),
          m["gap"])
    k.box("tv_strip", (0, FY - 0.006, gz + 0.110), (W * 0.28, 0.006, 0.030),
          m["chrome"])
    for i in range(4):
        k.box(f"tv_button_{i}", (-0.075 + i * 0.050, FY - 0.010, gz + 0.075),
              (0.030, 0.008, 0.014), m["black_plastic"])
    k.cyl("tv_power_lamp", (0.110, FY - 0.010, gz + 0.075), 0.007, 0.006,
          m["estop"], axis="Y", verts=12)

    # Back: vent slats on the slope, a rating sticker, cables to the floor.
    slope = math.atan2(D_BASE - D_TOP, H - LOWER)
    for i in range(6):
        t = 0.20 + i * 0.11
        z = LOWER + (H - LOWER) * t
        y = FY + D_BASE - (D_BASE - D_TOP) * t + 0.004
        k.box(f"tv_vent_{i}", (0.10, y, z), (W * 0.46, 0.006, 0.020), m["gap"],
              rot=(slope, 0, 0))
    k.box("tv_sticker", (-0.30, FY + D_BASE - (D_BASE - D_TOP) * 0.55 + 0.005,
                         LOWER + (H - LOWER) * 0.55),
          (0.10, 0.004, 0.060), m["sticker_white"], rot=(slope, 0, 0))
    k.path("tv_coax", [(-0.20, FY + D_BASE - 0.02, LOWER + 0.10),
                       (-0.24, FY + D_BASE + 0.05, LOWER - 0.10),
                       (-0.26, FY + D_BASE + 0.08, 0.012)], 0.009, m["hose"])
    k.path("tv_power_cord", [(0.30, FY + D_BASE - 0.02, 0.20),
                             (0.34, FY + D_BASE + 0.06, 0.06),
                             (0.40, FY + D_BASE + 0.12, 0.010)], 0.008, m["hose"])

    # VCR and a tape on top.
    vz = H + 0.016
    k.box("tv_vcr", (0.10, FY + 0.15, vz + 0.042), (0.400, 0.260, 0.084),
          m["vcr_black"], bevel=0.006)
    k.box("tv_vcr_slot", (0.05, FY + 0.019, vz + 0.055), (0.200, 0.004, 0.018),
          m["gap"])
    k.box("tv_vcr_clock", (0.21, FY + 0.019, vz + 0.050), (0.070, 0.004, 0.018),
          m["lamp_green"])
    k.box("tv_tape", (-0.27, FY + 0.16, vz + 0.013), (0.190, 0.105, 0.026),
          m["black_plastic"], bevel=0.003, rot=(0, 0, 0.25))
    k.box("tv_tape_label", (-0.27, FY + 0.16, vz + 0.027), (0.120, 0.060, 0.002),
          m["tape_label"], rot=(0, 0, 0.25))


def screen_material(key: str):
    mat = bpy.data.materials.new(f"tv_scr_{key}")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(TEX / f"{key}.png"), check_existing=True)
    tex.interpolation = "Cubic"
    emit = nodes.new("ShaderNodeEmission")
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(tex.outputs["Color"], emit.inputs["Color"])
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def build_screen(k, key: str) -> None:
    """The lit screen alone, 3 mm proud of the tube so nothing on the body
    can occlude it; the overlay sprite then sits exactly over the tube."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, FY - 0.013, SCR_Z))
    plane = bpy.context.active_object
    plane.scale = (SCR_W, SCR_H, 1.0)
    plane.rotation_euler = (math.pi / 2, 0, 0)
    k._add(plane, f"tv_screen_{key}", screen_material(key))


def render(props, name: str, build_fn) -> dict:
    before = set(bpy.data.objects)
    build_fn()
    subject = bpy.data.objects[F.SUBJECT_NAME]
    for obj in bpy.data.objects:
        if obj not in before and obj is not subject and obj.parent is None:
            obj.parent = subject
    props.sheet_name = name
    manifest = F.render_cells(bpy.context)
    for obj in list(bpy.data.objects):
        if obj not in before:
            bpy.data.objects.remove(obj, do_unlink=True)
    return manifest


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    g = load("knx_gensets")
    g.make_texture()
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.output_dir = str(OUT)
    props.footprint_x = props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    F.build_rig(bpy.context)
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True

    mats = tv_materials(g)
    passes = {"sheet": SHEET}
    passes["body"] = render(props, "tv_body", lambda: build_body(g.Kit(), mats))
    # Kit instances are throwaway: render() tracks objects by identity.
    for key in ("test", "alt1", "alt2", "alt3"):
        passes[key] = render(props, f"tv_{key}", lambda key=key: build_screen(g.Kit(), key))
        print(f"   {key}: {len(passes[key]['cells'])} cell(s)")
    (OUT / "passes.json").write_text(json.dumps(passes, indent=2))
    print(f"rendered body + 4 screen passes to {OUT}")


if __name__ == "__main__":
    main()
