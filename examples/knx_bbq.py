"""BADLANDS engine-bay barbecue: the front clip of a '90s sedan, cut at the
firewall, engine pulled, a firebox and grate dropped in where it used to sit.

Our own geometry -- no vehicle mod's mesh is used or referenced.  One tile, four
facings, sheet badlands_bbq_01 (index = facing S,E,N,W).  The nose faces -y,
which is the S facing (the seating recipe's convention: backrests sit at +y).

Tile props are vanilla's charcoal kettle, appliances_cooking_01_35, verbatim
except name/group/weight: IsoType=IsoBarbecue + container=barbecue and NO
propaneTank key -- that absence is what makes it burn charcoal and wood.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_bbq.py -- [--samples N]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "bbq_cells"
SHEET = "badlands_bbq_01"
PAINT_PATH = ROOT / "build" / "bbq_paint.png"
OFFSET_Z = -2.0 / 77.2

BBQ_PROPS = {
    "BlocksPlacement": "", "CanScrap": "", "ContainerCapacity": "15",
    "CustomName": "Engine Bay Barbecue", "GroupName": "Badlands",
    "IsMoveAble": "", "IsoType": "IsoBarbecue",
    "Material": "SmallMetalPlates", "Material2": "MetalScrap",
    "MaterialType": "Metal", "PickUpWeight": "200", "ScrapSize": "Medium",
    "container": "barbecue", "solidtrans": "",
}

# Body envelope, metres (1 tile = 1.0).  A real front clip is ~1.8 m wide; this
# is squeezed to the tile the way vanilla squeezes cars into furniture scale.
W = 0.90            # fender to fender
Y_NOSE = -0.44      # bumper face
Y_WALL = 0.40       # firewall (the cut)
Z_SILL = 0.16       # bottom of the body, sitting on blocks
Z_DECK = 0.60       # fender tops / hood line


class Builder:
    def __init__(self) -> None:
        self.parts: list[bpy.types.Object] = []

    def _place(self, obj, name, material):
        obj.name = name
        obj.data.materials.append(material)
        self.parts.append(obj)
        return obj

    def box(self, name, centre, size, material, rot=(0.0, 0.0, 0.0)):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(centre[0], centre[1], centre[2] + OFFSET_Z))
        obj = bpy.context.active_object
        obj.scale = size
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def span(self, name, x0, x1, y0, y1, z0, z1, material):
        return self.box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                        (x1 - x0, y1 - y0, z1 - z0), material)

    def cyl(self, name, centre, radius, length, material, rot=(0.0, 0.0, 0.0),
            vertices=16):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius, depth=length, vertices=vertices,
            location=(centre[0], centre[1], centre[2] + OFFSET_Z))
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def rod(self, name, a, b, radius, material, vertices=8):
        d = [q - p for p, q in zip(a, b)]
        length = math.sqrt(sum(c * c for c in d))
        mid = [(p + q) / 2 for p, q in zip(a, b)]
        obj = self.cyl(name, mid, radius, length, material, vertices=vertices)
        obj.rotation_euler = (0.0, math.acos(d[2] / length), math.atan2(d[1], d[0]))
        return obj


def make_texture() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    spec = material_spec("metal", seed=86)
    spec = dataclasses.replace(
        spec, octaves=[(s, a * 0.5) for s, a in spec.octaves],
        stroke_amplitude=0.08)
    write_surface_map(PAINT_PATH, 512, 256, spec)


def materials() -> dict:
    tex = PAINT_PATH
    rust = (0.40, 0.21, 0.10)
    t = F.toon_material
    return {
        # Black-and-white patrol scheme: white nose and fenders, black hood.
        "body": F.forge_material("bbq_body", "metal", (0.63, 0.62, 0.59),
                                 texture_path=tex, accent=rust, swing=(0.80, 1.12)),
        "body_cut": F.forge_material("bbq_body_cut", "metal", (0.46, 0.45, 0.43),
                                     texture_path=tex, accent=rust, swing=(0.75, 1.10)),
        "hood": F.forge_material("bbq_hood", "metal", (0.13, 0.13, 0.14),
                                 texture_path=tex, swing=(0.80, 1.30)),
        "amber": t("bbq_amber", (0.80, 0.45, 0.08)),
        "plate": t("bbq_plate", (0.74, 0.72, 0.62)),
        "firebox": F.forge_material("bbq_firebox", "metal", (0.24, 0.23, 0.21),
                                    texture_path=tex, accent=rust),
        "grate": t("bbq_grate", (0.33, 0.32, 0.30)),
        "coal": t("bbq_coal", (0.055, 0.050, 0.048)),
        "ember": t("bbq_ember", (0.64, 0.24, 0.06)),
        "ash": t("bbq_ash", (0.56, 0.54, 0.51)),
        "chrome": t("bbq_chrome", (0.56, 0.57, 0.58)),
        "grille": t("bbq_grille", (0.07, 0.07, 0.075)),
        "lamp": t("bbq_lamp", (0.80, 0.82, 0.76)),
        "rubber": t("bbq_rubber", (0.075, 0.075, 0.080)),
        "hub": t("bbq_hub", (0.40, 0.40, 0.40)),
        "block": t("bbq_block", (0.47, 0.46, 0.43)),
        "rust": t("bbq_rust", rust),
        "cut": t("bbq_cut", (0.30, 0.25, 0.21)),
    }


def build(b: Builder, m: dict) -> None:
    hx, fx = W / 2, W / 2 - 0.10          # outer / inner fender faces
    nose_back = -0.34                      # rear of the radiator support

    # --- stance: front tyres in the arches, cinder blocks under the cut ------
    wy, wr = -0.06, 0.19
    for sx in (-1, 1):
        b.cyl(f"tyre_{sx}", (sx * (hx - 0.07), wy, wr), wr, 0.13, m["rubber"],
              rot=(0.0, math.radians(90), 0.0), vertices=24)
        b.cyl(f"hub_{sx}", (sx * (hx - 0.005), wy, wr), 0.085, 0.012, m["hub"],
              rot=(0.0, math.radians(90), 0.0), vertices=16)
        b.span(f"block_{sx}", sx * 0.38 - 0.10, sx * 0.38 + 0.10,
               0.20, 0.38, 0.0, Z_SILL, m["block"])

    # --- fenders, split around the wheel opening -----------------------------
    for sx in (-1, 1):
        x0, x1 = sorted((sx * fx, sx * hx))
        b.span(f"fender_front_{sx}", x0, x1, Y_NOSE + 0.04, wy - wr - 0.01,
               Z_SILL, Z_DECK, m["body"])
        b.span(f"fender_top_{sx}", x0, x1, wy - wr - 0.01, wy + wr + 0.01,
               2 * wr + 0.02, Z_DECK, m["body"])
        b.span(f"fender_rear_{sx}", x0, x1, wy + wr + 0.01, Y_WALL - 0.04,
               Z_SILL, Z_DECK, m["body"])

    # --- nose: radiator support, grille, lamps, bumper -----------------------
    b.span("nose", -fx, fx, Y_NOSE + 0.04, nose_back, Z_SILL, Z_DECK - 0.02,
           m["body"])
    b.span("grille", -0.22, 0.22, Y_NOSE + 0.030, Y_NOSE + 0.045, 0.33, 0.51,
           m["grille"])
    for i, z in enumerate((0.37, 0.42, 0.47)):
        b.span(f"grille_bar_{i}", -0.22, 0.22, Y_NOSE + 0.022, Y_NOSE + 0.032,
               z - 0.008, z + 0.008, m["chrome"])
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.25, sx * 0.41))
        b.span(f"lamp_{sx}", x0, x1, Y_NOSE + 0.028, Y_NOSE + 0.042, 0.39, 0.49,
               m["lamp"])
    b.span("bumper", -hx - 0.02, hx + 0.02, Y_NOSE - 0.02, Y_NOSE + 0.04,
           0.20, 0.31, m["chrome"])
    b.span("plate", -0.08, 0.08, Y_NOSE - 0.032, Y_NOSE - 0.020, 0.215, 0.295,
           m["plate"])
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.29, sx * 0.39))
        b.span(f"turn_{sx}", x0, x1, Y_NOSE + 0.028, Y_NOSE + 0.042, 0.335, 0.37,
               m["amber"])
        b.span(f"marker_{sx}", sx * hx - 0.006, sx * hx + 0.006, Y_NOSE + 0.06,
               Y_NOSE + 0.13, 0.40, 0.45, m["amber"])
    b.span("bumper_strip", -hx - 0.02, hx + 0.02, Y_NOSE - 0.028, Y_NOSE - 0.018,
           0.235, 0.265, m["rubber"])

    # --- engine bay: firebox tub, coal bed, grate ----------------------------
    bx, by0, by1 = fx - 0.005, nose_back, Y_WALL - 0.04
    b.span("bay_floor", -fx, fx, by0, by1, Z_SILL, 0.30, m["body_cut"])
    b.span("firebox", -bx + 0.03, bx - 0.03, by0 + 0.02, by1 - 0.02, 0.30, 0.50,
           m["firebox"])
    b.span("coal_bed", -bx + 0.05, bx - 0.05, by0 + 0.04, by1 - 0.04, 0.50, 0.515,
           m["coal"])
    # Lumps: a fixed scatter, not random -- renders must be reproducible.
    lumps = [(-0.22, -0.20, "coal"), (-0.08, -0.24, "ember"), (0.10, -0.18, "coal"),
             (0.24, -0.22, "coal"), (-0.18, -0.04, "ember"), (0.02, -0.06, "coal"),
             (0.18, -0.02, "ember"), (-0.26, 0.10, "coal"), (-0.06, 0.12, "ash"),
             (0.12, 0.14, "coal"), (0.26, 0.10, "ember"), (-0.14, 0.24, "coal"),
             (0.06, 0.26, "ember"), (0.22, 0.24, "ash")]
    for i, (x, y, mat) in enumerate(lumps):
        s = 0.050 + 0.012 * ((i * 7) % 3)
        b.box(f"lump_{i}", (x, y, 0.525), (s, s * 0.85, s * 0.6), m[mat],
              rot=(0.0, 0.0, math.radians((i * 37) % 90)))
    gz = 0.585
    for sy in (-1, 1):
        b.span(f"grate_rail_{sy}", -bx + 0.02, bx - 0.02,
               (by0 + 0.03) if sy < 0 else (by1 - 0.05),
               (by0 + 0.05) if sy < 0 else (by1 - 0.03), gz - 0.012, gz + 0.012,
               m["grate"])
    n = 11
    for i in range(n):
        x = -bx + 0.05 + i * (2 * bx - 0.10) / (n - 1)
        b.rod(f"grate_{i}", (x, by0 + 0.04, gz), (x, by1 - 0.04, gz), 0.008,
              m["grate"], vertices=6)

    # --- firewall: the cut, left raw along the top ---------------------------
    b.span("firewall", -hx, hx, Y_WALL - 0.06, Y_WALL, Z_SILL, Z_DECK + 0.06,
           m["body_cut"])
    b.span("cut_edge", -hx, hx, Y_WALL - 0.065, Y_WALL + 0.005, Z_DECK + 0.06,
           Z_DECK + 0.075, m["cut"])
    # Brake-booster hole and a wiring grommet: the firewall is the whole N/W view.
    b.cyl("booster_hole", (-0.18, Y_WALL + 0.001, 0.46), 0.075, 0.004, m["grille"],
          rot=(math.radians(90), 0.0, 0.0), vertices=20)
    b.cyl("grommet", (0.20, Y_WALL + 0.001, 0.50), 0.03, 0.004, m["rubber"],
          rot=(math.radians(90), 0.0, 0.0), vertices=12)
    b.span("rust_streak", 0.02, 0.10, Y_WALL - 0.002, Y_WALL + 0.003, 0.30,
           Z_DECK + 0.06, m["rust"])

    # --- hood: rear-hinged, propped up as the lid ----------------------------
    theta, length = math.radians(72), 0.70
    hinge_y, hinge_z = Y_WALL - 0.07, Z_DECK + 0.02
    b.box("hood", (0.0, hinge_y - length / 2 * math.cos(theta),
                   hinge_z + length / 2 * math.sin(theta)),
          (W - 0.04, length, 0.028), m["hood"], rot=(-theta, 0.0, 0.0))
    tip = (0.30, hinge_y - 0.48 * math.cos(theta), hinge_z + 0.48 * math.sin(theta))
    b.rod("hood_prop", (0.30, nose_back + 0.02, Z_DECK - 0.02), tip, 0.007,
          m["grate"], vertices=6)


#: Name prefix -> bevel width.  Vanilla vehicles and appliances have no hard box
#: edges; an unbevelled body reads as a crate with a grille painted on.
ROUND = {"fender_": 0.035, "nose": 0.03, "bumper": 0.015, "hood": 0.012,
         "firewall": 0.012, "block_": 0.008, "firebox": 0.01}


def soften(parts) -> None:
    for obj in parts:
        hits = [p for p in ROUND if obj.name.startswith(p)]
        if not hits or obj.name.startswith("bumper_strip"):
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mod = obj.modifiers.new("round", "BEVEL")
        mod.width = ROUND[max(hits, key=len)]
        mod.segments = 3
        mod.limit_method = "ANGLE"


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    make_texture()
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
    scene.cycles.samples = int(sys.argv[sys.argv.index("--samples") + 1]) \
        if "--samples" in sys.argv else 512
    scene.cycles.use_denoising = True

    subject = bpy.data.objects[F.SUBJECT_NAME]
    b = Builder()
    build(b, materials())
    soften(b.parts)
    for part in b.parts:
        part.parent = subject
    manifest = F.render_cells(bpy.context)
    cells = [dict(c, tile_props=dict(BBQ_PROPS, Facing=c["facing"]))
             for c in manifest["cells"]]
    manifest["sheet"] = SHEET
    manifest["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                       encoding="utf-8")
    print(f"rendered {len(cells)} cell(s), {len(b.parts)} parts, to {OUT}")


if __name__ == "__main__":
    main()
