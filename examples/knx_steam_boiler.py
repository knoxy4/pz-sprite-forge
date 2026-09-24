"""Badlands Power Steam DLC: the Moming Moumou vertical biomass steam generator.

After the operator's reference photo: a stainless vertical boiler shell on a blue
plinth, round blue firebox door low on the front with a glass fire window, a smaller
blue inspection hatch above it, pressure gauges and a safety valve on the crown, a
flue stack, a red vertical maker's strip down the front-right, a grey electrical box
on the right flank and a blower motor low at the back.

Sheet badlands_steam_01:
    0-3  the boiler, cold (firebox window dark)
    4-7  overlay: fire in the window + a steam plume off the stack (running)

The overlay renders the boiler as a holdout, the bank-overlay trick from
knx_gensets.build_bank, so it lines up pixel for pixel with the tile and the shell
hides the fire on the back facings.

Scale: a small real unit is ~0.6 m across and ~1.8 m to the top of the stack. Scaled
down to sit beside vanilla furniture (fridge-height shell, stack clear above it),
the same liberty the diesel frame set takes.

Run headlessly:
    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_steam_boiler.py
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

OUT = ROOT / "build" / "badlands_steam_cells"
SHEET = "badlands_steam_01"


def load(name: str):
    path = ROOT / "examples" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


G = load("knx_gensets")


def materials() -> dict:
    m = G.materials()
    t = G.TEXTURE_PATH

    def worn(name, colour):
        return F.forge_material(name, "metal", colour, texture_path=t, hue=G.KEEP_HUE)

    def flat(name, colour):
        return F.forge_material(name, "metal", colour, hue=G.KEEP_HUE)

    def glow(name, colour):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        nodes.clear()
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*colour, 1.0)
        emit.inputs["Strength"].default_value = 1.0
        out = nodes.new("ShaderNodeOutputMaterial")
        links.new(emit.outputs["Emission"], out.inputs["Surface"])
        return mat

    m.update({
        "stainless": worn("s_stainless", (0.780, 0.790, 0.800)),
        "stainless_d": worn("s_stainless_d", (0.560, 0.570, 0.585)),
        "blue": worn("s_blue", (0.090, 0.300, 0.720)),
        "blue_d": flat("s_blue_d", (0.050, 0.170, 0.430)),
        "red_strip": flat("s_red_strip", (0.760, 0.070, 0.080)),
        "glyph": flat("s_glyph", (0.940, 0.930, 0.880)),
        "soot": flat("s_soot", (0.050, 0.045, 0.042)),
        "gauge_face": flat("s_gauge_face", (0.930, 0.930, 0.900)),
        "box_grey": worn("s_box_grey", (0.720, 0.720, 0.700)),
        # Fire is a light source, not a lit surface: plain emission, so the toon key
        # light cannot shade it down to mustard (v1 contact sheet).
        "fire": glow("s_fire", (1.000, 0.300, 0.030)),
        "fire_hot": glow("s_fire_hot", (1.000, 0.750, 0.200)),
        "steam": flat("s_steam", (0.880, 0.880, 0.890)),
    })
    return m


R = 0.245           # shell radius
Z0, Z1 = 0.110, 1.200   # shell bottom / top
DOOR = (-0.040, 0.400)  # firebox door x, z on the -Y face


def front(x: float) -> float:
    """-Y surface of the shell at x."""
    return -math.sqrt(max(0.0, R * R - x * x))


def build_boiler(k, m, overlay: bool = False) -> None:
    first = len(k.parts)
    # Plinth and feet.
    k.box("s_plinth", (0, 0, 0.055), (0.600, 0.600, 0.090), m["blue"], bevel=0.010)
    k.box("s_plinth_lip", (0, 0, 0.104), (0.540, 0.540, 0.012), m["blue_d"])
    # Shell, crown, weld seams.
    k.cyl("s_shell", (0, 0, (Z0 + Z1) / 2), R, Z1 - Z0, m["stainless"], verts=48)
    k.sphere("s_crown", (0, 0, Z1), R, m["stainless"], scale=(1, 1, 0.22))
    for i, z in enumerate((0.300, 0.720, 1.080)):
        k.torus(f"s_seam_{i}", (0, 0, z), R + 0.002, 0.004, m["stainless_d"])
    # Firebox door: blue ring, dark door, glass window (fire goes here in the overlay).
    dx, dz = DOOR
    fy = front(dx)
    k.cyl("s_door_ring", (dx, fy - 0.010, dz), 0.125, 0.030, m["blue"], axis="Y", verts=32)
    k.cyl("s_door", (dx, fy - 0.022, dz), 0.105, 0.020, m["blue_d"], axis="Y", verts=32)
    k.cyl("s_window", (dx, fy - 0.030, dz), 0.075, 0.012, m["soot"], axis="Y", verts=32)
    k.box("s_hinge", (dx - 0.128, fy - 0.020, dz), (0.024, 0.030, 0.090), m["blue_d"])
    k.rod("s_latch", (dx + 0.090, fy - 0.045, dz + 0.030), (dx + 0.140, fy - 0.045, dz - 0.030),
          0.008, m["chrome"])
    # Inspection hatch above.
    hx, hz = -0.010, 0.760
    hy = front(hx)
    k.cyl("s_hatch", (hx, hy - 0.012, hz), 0.070, 0.024, m["blue"], axis="Y", verts=28)
    k.rod("s_hatch_handle", (hx - 0.030, hy - 0.035, hz), (hx + 0.030, hy - 0.035, hz),
          0.007, m["chrome"])
    # Ash drawer at the foot of the front.
    k.box("s_ash", (dx, -0.285, 0.170), (0.200, 0.080, 0.110), m["blue"], bevel=0.006)
    k.box("s_ash_slot", (dx, -0.327, 0.170), (0.150, 0.004, 0.050), m["soot"])
    # Red maker's strip down the front-right, with pale glyph blocks on it.
    a = math.radians(-50)
    sx, sy = (R + 0.004) * math.cos(a), (R + 0.004) * math.sin(a)
    k.box("s_strip", (sx, sy, 0.700), (0.070, 0.008, 0.820), m["red_strip"],
          rot=(0, 0, a + math.pi / 2))
    for i in range(9):
        k.box(f"s_glyph_{i}", (sx + 0.003 * math.cos(a), sy + 0.003 * math.sin(a), 1.050 - i * 0.080),
              (0.040, 0.006, 0.050), m["glyph"], rot=(0, 0, a + math.pi / 2))
    # Crown fittings: stack, gauges on risers, safety valve.
    k.cyl("s_stack", (0.060, 0.070, 1.420), 0.055, 0.400, m["stainless_d"], verts=24)
    k.cyl("s_stack_cap", (0.060, 0.070, 1.630), 0.070, 0.030, m["stainless_d"], verts=24)
    for i, (gx, gz) in enumerate(((-0.130, 1.380), (-0.020, 1.330))):
        k.rod(f"s_riser_{i}", (gx, -0.060, Z1 + 0.030), (gx, -0.060, gz - 0.050), 0.010, m["brass"])
        k.cyl(f"s_gauge_{i}", (gx, -0.070, gz), 0.052, 0.024, m["stainless_d"], axis="Y", verts=28)
        k.cyl(f"s_gauge_face_{i}", (gx, -0.084, gz), 0.044, 0.004, m["gauge_face"], axis="Y", verts=28)
        k.rod(f"s_needle_{i}", (gx, -0.088, gz), (gx + 0.025, -0.088, gz + 0.020), 0.003, m["estop"])
    k.cyl("s_valve", (0.150, -0.060, Z1 + 0.070), 0.020, 0.090, m["brass"], verts=16)
    k.cyl("s_valve_top", (0.150, -0.060, Z1 + 0.125), 0.030, 0.020, m["brass"], verts=16)
    # Water sight glass on the front-left.
    b = math.radians(-125)
    gx, gy = (R + 0.020) * math.cos(b), (R + 0.020) * math.sin(b)
    k.rod("s_glass", (gx, gy, 0.620), (gx, gy, 0.920), 0.009, m["chrome"])
    for z in (0.610, 0.930):
        k.box(f"s_glass_cock_{z}", (gx, gy, z), (0.030, 0.030, 0.022), m["brass"])
    # Electrical box on the right flank, lamps facing +X.
    k.box("s_ebox", (R + 0.040, -0.020, 0.860), (0.070, 0.230, 0.300), m["box_grey"], bevel=0.008)
    for i, mat in enumerate(("lamp_green", "estop", "sticker_yellow")):
        k.cyl(f"s_lamp_{i}", (R + 0.077, -0.090 + i * 0.060, 0.930), 0.013, 0.008, m[mat],
              axis="X", verts=12)
    k.box("s_ebox_panel", (R + 0.077, -0.020, 0.820), (0.004, 0.160, 0.090), m["gap"])
    k.path("s_conduit", [(R + 0.040, 0.060, 0.710), (R + 0.040, 0.090, 0.300),
                         (0.200, 0.200, 0.120)], 0.010, m["hose"])
    # Blower motor low at the back, feed pipe down the left.
    k.cyl("s_blower", (0.180, 0.230, 0.230), 0.075, 0.140, m["rubber"], axis="X", verts=24)
    k.box("s_blower_duct", (0.090, 0.230, 0.230), (0.060, 0.060, 0.060), m["blue_d"])
    k.path("s_feed", [(-R - 0.010, 0.060, 0.950), (-R - 0.040, 0.060, 0.900),
                      (-R - 0.040, 0.060, 0.150), (-0.290, 0.150, 0.130)], 0.014, m["blue"])

    if overlay:
        for part in k.parts[first:]:
            part.is_holdout = True
        # Fire behind the window glass: a bed of glow, two tongues of flame.
        wy = fy - 0.038
        k.cyl("s_fire_bed", (dx, wy, dz), 0.074, 0.006, m["fire"], axis="Y", verts=32)
        k.sphere("s_flame_a", (dx - 0.020, wy - 0.002, dz - 0.010), 0.046, m["fire_hot"],
                 scale=(1.0, 0.15, 1.4))
        k.sphere("s_flame_b", (dx + 0.028, wy - 0.002, dz - 0.020), 0.034, m["fire_hot"],
                 scale=(1.0, 0.15, 1.3))
        # Wisps rather than a stack: offset puffs, growing and flattening downwind.
        for i, (ox, oy, oz, r) in enumerate(((0.000, 0.000, 1.690, 0.045),
                                             (0.040, -0.020, 1.735, 0.055),
                                             (0.030, 0.030, 1.760, 0.040),
                                             (0.095, -0.030, 1.790, 0.065),
                                             (0.150, -0.060, 1.815, 0.055),
                                             (0.120, 0.010, 1.830, 0.045))):
            k.sphere(f"s_plume_{i}", (0.060 + ox, 0.070 + oy, oz), r, m["steam"],
                     scale=(1.3, 1.1, 0.7))


def render_subject(props, sheet: str, build_fn) -> dict:
    before = set(bpy.data.objects)
    build_fn()
    subject = bpy.data.objects[F.SUBJECT_NAME]
    for obj in bpy.data.objects:
        if obj not in before and obj is not subject and obj.parent is None:
            obj.parent = subject
    props.sheet_name = sheet
    manifest = F.render_cells(bpy.context)
    for obj in list(bpy.data.objects):
        if obj not in before:
            bpy.data.objects.remove(obj, do_unlink=True)
    return manifest


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    G.make_texture()
    mats = materials()

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
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True

    order = [
        ("bs_boiler", lambda: build_boiler(G.Kit(), mats)),
        ("bs_fire", lambda: build_boiler(G.Kit(), mats, overlay=True)),
    ]
    manifests = [(s, render_subject(props, s, fn)) for s, fn in order]

    merged = dict(manifests[0][1])
    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    elements: dict = {}
    cells: list = []
    for group, (_, manifest) in enumerate(manifests):
        elements.update(manifest.get("elements", {}))
        extra = {"group": group}
        if group == 1:
            extra["tile_props"] = {}
        cells.extend(dict(cell, **extra) for cell in manifest["cells"])
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"merged {len(cells)} cell(s) into {SHEET} at {OUT}")


if __name__ == "__main__":
    main()
