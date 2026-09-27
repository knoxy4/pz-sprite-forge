"""Boombuk's Beds: six buildable beds with storage (BADLANDS Furniture DLC, mod BoombuksBeds).

Requested by Boombuk2: "a bed on top of cabinets, like the ones in medical facilities" -- the
vanilla Patient Chair (location_community_medical_01_0..7), which is a bed AND a counter on
the same tiles.  Every piece here follows that pattern: bed + BedType + container per tile.

    group 0  Exam Bunk           1x2  goodBed (+built-in pillow, Lua)  dresser 2 x 40
    group 1  Captains Bed        1x2  goodBed                          dresser 2 x 35
    group 2  Footlocker Cot      1x2  averageBed                       militarylocker 50, foot tile only
    group 3  Pallet Bed          1x2  averageBed                       crate 2 x 30
    group 4  Loft Bunk           1x2  goodBed (tall)                   wardrobe 2 x 40
    group 5  Lift-Up Double Bed  2x2  goodBed (+built-in pillow, Lua)  crate 4 x 30

Sheet boombuk_beds_01, tiledef 6480.  Blender frame: tile (0,0) is centred on the origin,
+X is grid east, grid south is Blender -Y.  Every bed is modelled in its S facing: head at the
north end (Blender +Y, grid row 0), foot to the south.  render_cells spins the rest.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_beds.py -- [--samples N] [--only key]
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = Path(os.environ.get("BEDS_CELLS", r"C:\Users\KNX\dev\_beds\cells"))
SHEET = "boombuk_beds_01"
GRAIN_PATH = ROOT / "build" / "beds_grain.png"
FABRIC_PATH = ROOT / "build" / "beds_fabric.png"
OFFSET_Z = -2.0 / 77.2

HEAD, FOOT = 0.46, -1.46          # bed ends along Y for a 1x2 (S facing)
CY = (HEAD + FOOT) / 2.0          # -0.5, the footprint centre
W = 0.88                          # single-bed width

# Cloned from vanilla furniture_bedding_01_34 (Simple Bed) + the Patient Chair's container
# keys.  Per bed: GroupName/CustomName (moveable name = "Group Custom"), BedType, container.
BASE_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "", "IsLow": "", "IsMoveAble": "",
    "Material": "Nails", "Material2": "Wood", "Material3": "Fabric",
    "PickUpTool": "Hammer", "PlaceTool": "Hammer", "PickUpWeight": "200",
    "bed": "", "solidtrans": "",
}
# key, GroupName, CustomName, BedType, footprint, container, capacity, surface px, extra
BEDS = [
    ("exam", "Exam", "Bunk", "goodBed", (1, 2), "dresser", "40", "27", {}),
    ("captain", "Captains", "Bed", "goodBed", (1, 2), "dresser", "35", "22", {}),
    ("cot", "Footlocker", "Cot", "averageBed", (1, 2), "militarylocker", "50", "17",
     {"Material": "MetalPlates", "Material2": "Fabric", "Material3": "Wood", "PickUpWeight": "120"}),
    ("pallet", "Pallet", "Bed", "averageBed", (1, 2), "crate", "30", "22",
     {"PickUpWeight": "150"}),
    ("loft", "Loft", "Bunk", "goodBed", (1, 2), "wardrobe", "40", "26", {"IsLow": None}),
    ("double", "Lift-Up", "Double Bed", "goodBed", (2, 2), "crate", "30", "24", {}),
]
# The cot's footlocker stands on the foot tile only; foot tile per facing (S modelled).
COT_FOOT = {"S": (0, 1), "E": (1, 0), "N": (0, 0), "W": (0, 0)}


class Builder:
    def __init__(self) -> None:
        self.parts: list[bpy.types.Object] = []

    def _place(self, obj, name, material):
        obj.name = name
        obj.data.materials.append(material)
        self.parts.append(obj)
        return obj

    def box(self, name, centre, size, material, rot=(0.0, 0.0, 0.0)):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(centre[0], centre[1], centre[2] + OFFSET_Z))
        obj = bpy.context.active_object
        obj.scale = size
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def cyl(self, name, centre, radius, length, material, rot=(0.0, 0.0, 0.0), vertices=16):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=vertices,
                                            location=(centre[0], centre[1], centre[2] + OFFSET_Z))
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)


def make_textures() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    spec = material_spec("wood", seed=6480)
    spec = dataclasses.replace(
        spec, octaves=[(s, a * 0.13) for s, a in spec.octaves],
        stroke_count=90, stroke_amplitude=0.06, knot_count=1, knot_depth=0.06)
    write_surface_map(GRAIN_PATH, 512, 512, spec, grain_axis="v")
    write_surface_map(FABRIC_PATH, 512, 512, material_spec("fabric", seed=48))


def materials() -> dict:
    grain, cloth = str(GRAIN_PATH), str(FABRIC_PATH)
    wood = lambda n, c: F.forge_material(n, "wood", c, texture_path=grain, swing=(0.82, 1.12))
    fab = lambda n, c: F.forge_material(n, "fabric", c, texture_path=cloth)
    t = F.toon_material
    PINE = (0.66, 0.50, 0.30)
    OAK = (0.40, 0.21, 0.08)
    return {
        "pine": wood("bb_pine", PINE),
        "pine_light": wood("bb_pine_light", (0.74, 0.58, 0.36)),
        "pine_dark": wood("bb_pine_dark", tuple(c * 0.62 for c in PINE)),
        "oak": wood("bb_oak", OAK),
        "oak_light": wood("bb_oak_light", (0.50, 0.28, 0.11)),
        "oak_dark": wood("bb_oak_dark", tuple(c * 0.55 for c in OAK)),
        "plinth": t("bb_plinth", (0.08, 0.07, 0.06)),
        "steel": t("bb_steel", (0.32, 0.33, 0.33)),
        "chrome": t("bb_chrome", (0.62, 0.63, 0.64)),
        "brass": t("bb_brass", (0.62, 0.46, 0.16)),
        "tape": t("bb_tape", (0.86, 0.80, 0.62)),
        "ink": t("bb_ink", (0.08, 0.08, 0.09)),
        "vinyl": fab("bb_vinyl", (0.16, 0.36, 0.30)),
        "pillow": fab("bb_pillow", (0.80, 0.79, 0.74)),
        "pillow_dingy": fab("bb_pillow_dingy", (0.68, 0.62, 0.48)),
        "olive": fab("bb_olive", (0.26, 0.28, 0.15)),
        "olive_band": t("bb_olive_band", (0.72, 0.66, 0.44)),
        "ticking": fab("bb_ticking", (0.70, 0.72, 0.74)),
        "navy": fab("bb_navy", (0.08, 0.12, 0.26)),
        "sheet": fab("bb_sheet", (0.84, 0.82, 0.76)),
        "canvas": fab("bb_canvas", (0.34, 0.33, 0.19)),
        "wool": fab("bb_wool", (0.36, 0.34, 0.32)),
        "od": t("bb_od", (0.20, 0.23, 0.12)),
        "od_dark": t("bb_od_dark", (0.12, 0.14, 0.07)),
        "rope": t("bb_rope", (0.62, 0.52, 0.32)),
        "crate_red": t("bb_crate_red", (0.55, 0.07, 0.05)),
        "crate_blue": t("bb_crate_blue", (0.06, 0.20, 0.50)),
        "crate_slot": t("bb_crate_slot", (0.04, 0.03, 0.03)),
        "mattress": fab("bb_mattress", (0.66, 0.62, 0.52)),
        "stain": t("bb_stain", (0.46, 0.36, 0.20)),
        "sleepbag": fab("bb_sleepbag", (0.52, 0.12, 0.08)),
        "zip": t("bb_zip", (0.18, 0.18, 0.18)),
        "plaid": fab("bb_plaid", (0.50, 0.14, 0.10)),
        "shirt_a": fab("bb_shirt_a", (0.20, 0.30, 0.46)),
        "shirt_b": fab("bb_shirt_b", (0.52, 0.46, 0.34)),
        "shirt_c": fab("bb_shirt_c", (0.30, 0.34, 0.20)),
        "shirt_d": fab("bb_shirt_d", (0.46, 0.18, 0.16)),
        "upholstery": fab("bb_upholstery", (0.34, 0.34, 0.35)),
        "button": t("bb_button", (0.14, 0.14, 0.15)),
        "burgundy": fab("bb_burgundy", (0.36, 0.06, 0.09)),
        "cream": fab("bb_cream", (0.84, 0.80, 0.66)),
        "book_a": t("bb_book_a", (0.46, 0.10, 0.08)),
        "book_b": t("bb_book_b", (0.12, 0.26, 0.16)),
        "book_c": t("bb_book_c", (0.70, 0.60, 0.30)),
    }


def label(b, m, tag, x_face, y, z, sign):
    """The house motif: a cream tape strip with three hand-inked dashes, on a side face."""
    x = x_face + sign * 0.003
    b.box(f"{tag}_tape", (x, y, z), (0.004, 0.12, 0.032), m["tape"])
    for k in range(3):
        b.box(f"{tag}_ink{k}", (x + sign * 0.002, y - 0.035 + k * 0.035, z), (0.003, 0.022, 0.006), m["ink"])


# ------------------------------------------------------------------ 0 exam bunk
def build_exam(b: Builder, m: dict) -> None:
    b.box("plinth", (0, CY, 0.03), (W - 0.06, 1.86, 0.06), m["plinth"])
    b.box("carcass", (0, CY, 0.30), (W, 1.92, 0.48), m["pine"])
    for s in (-1, 1):
        xf = s * (W / 2 + 0.006)
        for t_ in (0, 1):
            yc = -float(t_)
            for k, z in enumerate((0.19, 0.41)):
                b.box(f"drawer_{s}_{t_}_{k}", (xf, yc, z), (0.012, 0.86, 0.19), m["pine_light"])
                b.box(f"pull_{s}_{t_}_{k}", (s * (W / 2 + 0.022), yc, z + 0.035), (0.02, 0.18, 0.024), m["steel"])
                label(b, m, f"lab_{s}_{t_}_{k}", s * (W / 2 + 0.012), yc - 0.25, z + 0.035, s)
    b.box("foot_board", (0, FOOT - 0.006, 0.30), (W - 0.04, 0.012, 0.40), m["pine_light"])
    b.box("top_frame", (0, CY, 0.555), (W + 0.02, 1.94, 0.03), m["pine_dark"])
    b.box("pad", (0, CY, 0.63), (W - 0.04, 1.86, 0.12), m["vinyl"])
    b.box("pillow", (0, 0.20, 0.745), (0.58, 0.30, 0.10), m["pillow"])
    b.box("blanket", (0, -1.18, 0.72), (W - 0.06, 0.38, 0.06), m["olive"])
    b.box("blanket_band", (0, -1.18, 0.753), (W - 0.06, 0.05, 0.008), m["olive_band"])


# ------------------------------------------------------------------ 1 captains bed
def build_captain(b: Builder, m: dict) -> None:
    b.box("plinth", (0, CY, 0.025), (W - 0.06, 1.86, 0.05), m["plinth"])
    b.box("base", (0, CY, 0.22), (W, 1.92, 0.36), m["oak"])
    for s in (-1, 1):
        xf = s * (W / 2 + 0.006)
        for k, y in enumerate((0.12, -0.50, -1.12)):
            b.box(f"drawer_{s}_{k}", (xf, y, 0.22), (0.012, 0.56, 0.26), m["oak_light"])
            for dy in (-0.15, 0.15):
                b.cyl(f"knob_{s}_{k}_{dy}", (s * (W / 2 + 0.02), y + dy, 0.24), 0.022, 0.03,
                      m["brass"], rot=(0.0, math.pi / 2, 0.0), vertices=12)
    b.box("foot_board", (0, FOOT - 0.006, 0.22), (W - 0.04, 0.012, 0.30), m["oak_light"])
    b.box("headboard", (0, HEAD - 0.03, 0.55), (W + 0.04, 0.06, 1.00), m["oak"])
    b.box("head_cap", (0, HEAD - 0.03, 1.07), (W + 0.08, 0.10, 0.04), m["oak_dark"])
    b.box("head_shelf", (0, HEAD - 0.12, 0.80), (W - 0.10, 0.14, 0.025), m["oak_dark"])
    for k, (x, mat, h) in enumerate(((-0.30, "book_a", 0.16), (-0.25, "book_b", 0.14), (-0.20, "book_c", 0.17))):
        b.box(f"book_{k}", (x, HEAD - 0.12, 0.8125 + h / 2), (0.04, 0.12, h), m[mat])
    b.box("mattress", (0, CY - 0.03, 0.47), (W - 0.04, 1.84, 0.18), m["ticking"])
    b.box("quilt", (0, -0.80, 0.575), (W, 1.28, 0.04), m["navy"])
    for s in (-1, 1):
        b.box(f"quilt_side_{s}", (s * (W / 2 + 0.01), -0.80, 0.49), (0.02, 1.28, 0.16), m["navy"])
    b.box("quilt_foot", (0, FOOT + 0.01, 0.49), (W, 0.02, 0.16), m["navy"])
    b.box("sheet_band", (0, -0.14, 0.585), (W, 0.12, 0.05), m["sheet"])
    b.box("pillow", (0, 0.20, 0.61), (0.60, 0.30, 0.10), m["pillow"])


# ------------------------------------------------------------------ 2 footlocker cot
def build_cot(b: Builder, m: dict) -> None:
    y0, y1 = HEAD - 0.02, -0.92
    yc, ln = (y0 + y1) / 2, y0 - y1
    for s in (-1, 1):
        b.cyl(f"rail_{s}", (s * 0.36, yc, 0.42), 0.022, ln, m["steel"], rot=(math.pi / 2, 0.0, 0.0))
    for k, y in enumerate((y0 - 0.02, y1 + 0.02)):
        b.cyl(f"endbar_{k}", (0, y, 0.42), 0.02, 0.74, m["steel"], rot=(0.0, math.pi / 2, 0.0))
    b.box("canvas", (0, yc, 0.41), (0.70, ln - 0.04, 0.02), m["canvas"])
    for k, y in enumerate((y0 - 0.06, yc, y1 + 0.06)):
        for a in (-0.50, 0.50):
            b.box(f"leg_{k}_{a}", (0, y, 0.21), (0.74, 0.03, 0.03), m["steel"], rot=(0.0, a, 0.0))
    b.cyl("roll", (0, 0.30, 0.48), 0.07, 0.62, m["wool"], rot=(0.0, math.pi / 2, 0.0))
    b.box("fold", (0, -0.45, 0.435), (0.62, 0.50, 0.04), m["olive"])
    fy = -1.21
    b.box("locker", (0, fy, 0.21), (0.84, 0.46, 0.40), m["od"])
    b.box("locker_lid", (0, fy, 0.405), (0.86, 0.48, 0.03), m["od_dark"])
    b.box("locker_skid", (0, fy, 0.012), (0.80, 0.42, 0.024), m["od_dark"])
    for s in (-1, 1):
        b.box(f"latch_{s}", (s * 0.22, fy - 0.235, 0.34), (0.06, 0.012, 0.07), m["brass"])
        b.box(f"handle_{s}", (s * 0.425, fy, 0.27), (0.02, 0.18, 0.025), m["rope"])
        for c in (-1, 1):
            b.box(f"corner_{s}_{c}", (s * 0.415, fy + c * 0.225, 0.21), (0.022, 0.022, 0.40), m["brass"])
    b.box("stencil", (0, fy - 0.234, 0.22), (0.38, 0.004, 0.06), m["tape"])
    for k in range(4):
        b.box(f"stencil_ink{k}", (-0.12 + k * 0.08, fy - 0.237, 0.22), (0.05, 0.003, 0.012), m["ink"])


# ------------------------------------------------------------------ 3 pallet bed
def pallet(b: Builder, m: dict, tag: str, y: float, z: float, w: float = 0.88, d: float = 0.92) -> None:
    for i, dy in enumerate((-d / 2 + 0.05, 0.0, d / 2 - 0.05)):
        b.box(f"{tag}_bot_{i}", (0, y + dy, z + 0.01), (w, 0.10, 0.02), m["pine_dark"])
    for i, x in enumerate((-w / 2 + 0.035, 0.0, w / 2 - 0.035)):
        b.box(f"{tag}_str_{i}", (x, y, z + 0.065), (0.07, d, 0.09), m["pine_dark"])
    for i in range(5):
        dy = -d / 2 + 0.05 + i * (d - 0.10) / 4
        b.box(f"{tag}_top_{i}", (0, y + dy, z + 0.12), (w, 0.10, 0.02), m["pine"])


def crate(b: Builder, m: dict, tag: str, x: float, y: float, colour: str) -> None:
    sx, sy, h = 0.42, 0.40, 0.28
    b.box(f"{tag}_shell", (x, y, h / 2), (sx, sy, h), m[colour])
    for k, z in enumerate((0.08, 0.15, 0.22)):
        for s in (-1, 1):
            b.box(f"{tag}_slx_{k}_{s}", (x + s * (sx / 2 + 0.002), y, z), (0.004, sy - 0.08, 0.03), m["crate_slot"])
            b.box(f"{tag}_sly_{k}_{s}", (x, y + s * (sy / 2 + 0.002), z), (sx - 0.08, 0.004, 0.03), m["crate_slot"])


def build_pallet(b: Builder, m: dict) -> None:
    colours = ("crate_red", "crate_blue", "crate_blue", "crate_red", "crate_red", "crate_blue")
    k = 0
    for x in (-0.22, 0.22):
        for y in (0.24, -0.50, -1.24):
            crate(b, m, f"crate{k}", x, y, colours[k])
            k += 1
    pallet(b, m, "p0", 0.0, 0.28)
    pallet(b, m, "p1", -0.96, 0.28)
    b.box("mattress", (0, CY, 0.49), (0.84, 1.86, 0.16), m["mattress"])
    for k, (x, y, w, d) in enumerate(((0.18, -0.25, 0.18, 0.12), (-0.20, -1.10, 0.14, 0.20))):
        b.box(f"stain_{k}", (x, y, 0.571), (w, d, 0.004), m["stain"])
    b.box("sleepbag", (0.02, -0.72, 0.595), (0.74, 1.20, 0.05), m["sleepbag"])
    b.box("zip", (0.39, -0.72, 0.60), (0.012, 1.18, 0.012), m["zip"])
    b.box("pillow", (0, 0.20, 0.615), (0.52, 0.28, 0.09), m["pillow_dingy"])


# ------------------------------------------------------------------ 4 loft bunk
def build_loft(b: Builder, m: dict) -> None:
    for sx in (-1, 1):
        for y in (HEAD - 0.04, FOOT + 0.04):
            b.box(f"post_{sx}_{y:.2f}", (sx * 0.40, y, 0.86), (0.07, 0.07, 1.72), m["pine"])
        b.box(f"siderail_{sx}", (sx * 0.42, CY, 1.14), (0.05, 1.92, 0.14), m["pine_dark"])
    b.box("platform", (0, CY, 1.20), (W, 1.92, 0.05), m["pine"])
    b.box("mattress", (0, CY, 1.30), (0.82, 1.84, 0.14), m["ticking"])
    b.box("blanket", (0, -0.72, 1.39), (0.84, 1.20, 0.04), m["plaid"])
    b.box("pillow", (0, 0.20, 1.42), (0.56, 0.28, 0.09), m["pillow"])
    for sx in (-1, 1):
        b.box(f"guard_{sx}", (sx * 0.42, 0.0, 1.55), (0.04, 0.86, 0.05), m["pine_light"])
        for y in (0.30, -0.30):
            b.box(f"baluster_{sx}_{y}", (sx * 0.42, y, 1.42), (0.035, 0.035, 0.22), m["pine_light"])
    for sx in (-1, 1):
        b.box(f"ladder_rail_{sx}", (sx * 0.18, FOOT - 0.01, 0.74), (0.04, 0.04, 1.48), m["pine_light"])
    for k in range(4):
        b.box(f"rung_{k}", (0, FOOT - 0.01, 0.28 + k * 0.27), (0.36, 0.035, 0.035), m["pine_light"])
    # under the loft: a hanging rail over the head tile, open shelves on the foot tile
    b.cyl("hang_rail", (0, 0.05, 1.02), 0.013, 0.74, m["steel"], rot=(math.pi / 2, 0.0, 0.0))
    for k, (y, mat) in enumerate(((0.32, "shirt_a"), (0.18, "shirt_b"), (0.04, "shirt_c"), (-0.10, "shirt_d"), (-0.22, "shirt_a"))):
        b.box(f"shirt_{k}", (0, y, 0.70), (0.44, 0.08, 0.60), m[mat])
    for s in (-1, 1):
        b.box(f"shelf_side_{s}", (s * 0.38, -0.95, 0.46), (0.03, 0.66, 0.92), m["pine_dark"])
    for k, z in enumerate((0.04, 0.40, 0.78)):
        b.box(f"shelf_{k}", (0, -0.95, z), (0.76, 0.66, 0.03), m["pine"])
    for k, (z, mat) in enumerate(((0.12, "shirt_c"), (0.48, "shirt_b"), (0.86, "shirt_d"))):
        b.box(f"folded_{k}", (0, -0.95, z), (0.46, 0.34, 0.12), m[mat])
    label(b, m, "lab_l", 0.395, -0.95, 0.33, 1)
    label(b, m, "lab_r", -0.395, -0.95, 0.33, -1)


# ------------------------------------------------------------------ 5 lift-up double
def build_double(b: Builder, m: dict) -> None:
    cx, w2 = 0.5, 1.88
    b.box("plinth", (cx, CY, 0.02), (w2 - 0.08, 1.84, 0.04), m["plinth"])
    b.box("base", (cx, CY, 0.22), (w2, 1.92, 0.38), m["upholstery"])
    for s in (-1, 1):
        b.box(f"seam_{s}", (cx + s * (w2 / 2 + 0.003), CY, 0.36), (0.004, 1.90, 0.012), m["button"])
    b.box("seam_foot", (cx, FOOT - 0.003, 0.36), (w2 - 0.02, 0.004, 0.012), m["button"])
    b.box("strap", (cx, FOOT - 0.008, 0.30), (0.20, 0.012, 0.08), m["button"])

    b.box("headboard", (cx, HEAD - 0.04, 0.62), (w2 + 0.08, 0.10, 1.18), m["upholstery"])
    for r, z in enumerate((0.78, 0.96, 1.12)):
        for c in range(5):
            b.cyl(f"tuft_{r}_{c}", (cx - 0.72 + c * 0.36, HEAD - 0.095, z), 0.018, 0.012, m["button"],
                  rot=(math.pi / 2, 0.0, 0.0), vertices=10)
    b.box("mattress", (cx, CY - 0.02, 0.51), (w2 - 0.04, 1.82, 0.20), m["ticking"])
    b.box("duvet", (cx, -0.76, 0.63), (w2 + 0.02, 1.40, 0.05), m["burgundy"])
    for s in (-1, 1):
        b.box(f"duvet_side_{s}", (cx + s * (w2 / 2 + 0.015), -0.76, 0.53), (0.02, 1.40, 0.16), m["burgundy"])
    b.box("duvet_foot", (cx, FOOT - 0.005, 0.53), (w2 + 0.02, 0.02, 0.16), m["burgundy"])
    b.box("duvet_band", (cx, -0.08, 0.64), (w2 + 0.02, 0.14, 0.06), m["cream"])
    for s in (-1, 1):
        b.box(f"pillow_{s}", (cx + s * 0.45, 0.20, 0.67), (0.72, 0.30, 0.12), m["pillow"])


SOFT = {"pad": 0.035, "pillow": 0.040, "blanket": 0.012, "mattress": 0.035, "quilt": 0.008,
        "sheet_band": 0.012, "roll": 0.0, "fold": 0.010, "sleepbag": 0.018, "base": 0.030,
        "headboard": 0.035, "duvet": 0.015, "shirt": 0.010, "folded": 0.012}
SOFT_MATERIALS = ("vinyl", "pillow", "olive", "ticking", "navy", "sheet", "wool", "mattress",
                  "sleepbag", "plaid", "shirt", "upholstery", "burgundy", "cream")


def soften(parts) -> None:
    for obj in parts:
        if obj.type != "MESH" or not obj.data.materials:
            continue
        if not any(k in obj.data.materials[0].name for k in SOFT_MATERIALS):
            continue
        hits = [p for p in SOFT if obj.name.startswith(p)]
        if not hits:
            continue
        width = SOFT[max(hits, key=len)]
        if width <= 0:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mod = obj.modifiers.new("soft", "BEVEL")
        mod.width = width
        mod.segments = 3
        mod.limit_method = "ANGLE"


BUILDERS = {"exam": build_exam, "captain": build_captain, "cot": build_cot,
            "pallet": build_pallet, "loft": build_loft, "double": build_double}


def tile_props(key, group, custom, bed, container, cap, surface, extra, facing, x, y) -> dict:
    p = dict(BASE_PROPS, GroupName=group, CustomName=custom, BedType=bed, Facing=facing,
             SpriteGridPos=f"{x},{y}", Surface=surface)
    for k, v in extra.items():
        if v is None:
            p.pop(k, None)
        else:
            p[k] = v
    if key != "cot" or COT_FOOT[facing] == (x, y):
        p.update(container=container, ContainerCapacity=cap, ContainerPosition="Low")
    return p


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    make_textures()
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = SHEET
    props.output_dir = str(OUT)
    props.footprint_x, props.footprint_y = 1, 2
    props.facings = "4"
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    props.isolate_tiles = False
    F.build_rig(bpy.context)
    scene.cycles.samples = int(sys.argv[sys.argv.index("--samples") + 1]) \
        if "--samples" in sys.argv else 512
    scene.cycles.use_denoising = True
    subject = bpy.data.objects[F.SUBJECT_NAME]
    m = materials()
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    merged: dict = {}
    elements: dict = {}
    cells: list = []
    for group, (key, gname, cname, bed, fp, cont, cap, surf, extra) in enumerate(BEDS):
        if only and key != only:
            continue
        b = Builder()
        BUILDERS[key](b, m)
        soften(b.parts)
        names = [o.name for o in b.parts]
        for part in b.parts:
            part.parent = subject
        props.footprint_x, props.footprint_y = fp
        props.sheet_name = f"bb_{key}"
        manifest = F.render_cells(bpy.context)
        for n in names:
            obj = bpy.data.objects.get(n)
            if obj is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
        if not merged:
            merged = dict(manifest)
        elements.update(manifest.get("elements", {}))
        for cell in manifest["cells"]:
            tp = tile_props(key, gname, cname, bed, cont, cap, surf, extra,
                            cell["facing"], cell["x"], cell["y"])
            cells.append(dict(cell, group=group, key=key, tile_props=tp))
        print(f"== {key}: {len(names)} parts, {len(manifest['cells'])} cells")

    merged["sheet"] = SHEET
    merged["isolate_tiles"] = False
    merged["footprint"] = [2, 2]
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
