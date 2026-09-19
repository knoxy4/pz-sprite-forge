"""BADLANDS Shelving: four more fill-state storage pieces for the Badlands Bookcase mod.

Same three-state idea as bookcase_full.py -- one carcass rendered stocked, picked
over and stripped by deleting named contents between passes -- for:

    group 0  Pantry Shelf        oak, Woodwork     cans, jars, cereal boxes
    group 1  Wine Rack           oak, Woodwork     bottles lying in cubbies
    group 2  Utility Shelving    welded steel      cardboard boxes, paint cans, jugs
    group 3  Gun Rack            welded steel      long guns standing, ammo boxes

Sheet badlands_shelving_01, subject-major thanks to the per-cell group stamp:
index // 12 is the object, (index % 12) // 3 the facing S,E,N,W, index % 3 the
state (0 stocked, 1 picked over, 2 stripped) -- the layout KNXBookcase.lua
already reads.  Every cell carries its full tile_props so the packager writes
them verbatim.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_shelving.py
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

OUT = ROOT / "build" / "shelving_cells"
SHEET = "badlands_shelving_01"
GRAIN_PATH = ROOT / "build" / "shelving_oak_grain.png"
METAL_PATH = ROOT / "build" / "shelving_steel.png"

# Footprint and registration are the bookcase's, solved against vanilla
# furniture_shelving_01_40 (92x204 trim box at (31,38)).
WIDTH = 1.00
DEPTH = 0.40
HEIGHT = 2.02
SIDE = 0.060
OFFSET_Y = 0.206
OFFSET_Z = -2.0 / 77.2
OAK = (0.508, 0.139, 0.025)
PINE = (0.780, 0.560, 0.300)   # pale kitchen pine, so the pantry never reads as the bookcase
STEEL = (0.300, 0.305, 0.300)

# Tile properties.  Wood is the bookcase's block, itself cloned from vanilla
# furniture_shelving_01_40.  Steel is cloned from vanilla's welded Metal Shelves
# (furniture_shelving_01_28) minus the wall-mount keys (attachedN, MoveType
# WallObject, IsHigh, ContainerPosition High): these stand on the floor.
WOOD_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "",
    "ContainerPutSound": "ShelfWoodTransferItem",
    "ContainerTakeSound": "ShelfWoodTransferItem",
    "GroupName": "Oakwood", "IsMoveAble": "",
    "Material": "Wood", "Material2": "Screws", "MaterialType": "Wood",
    "PickUpTool": "Hammer", "PickUpWeight": "200", "PlaceTool": "Hammer",
    "ScrapSize": "Large", "Surface": "80", "container": "shelves", "solid": "",
}
STEEL_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "",
    "ContainerPutSound": "ShelfMetalTransferItem",
    "ContainerTakeSound": "ShelfMetalTransferItem",
    "GroupName": "Badlands Steel", "IsMoveAble": "",
    "Material": "SmallMetalPlates", "Material2": "Screws",
    "MaterialType": "Metal_Light", "PickUpLevel": "1", "PickUpWeight": "150",
    "ScrapSize": "Large", "Surface": "80", "container": "metal_shelves",
    "solid": "",
}
OBJECTS = [
    # key, CustomName, capacity, base props
    ("pantry", "Pantry Shelf", "60", WOOD_PROPS),
    ("wine", "Wine Rack", "40", WOOD_PROPS),
    ("utility", "Utility Shelving", "60", STEEL_PROPS),
    ("gunrack", "Gun Rack", "40", STEEL_PROPS),
]


class Builder:
    """Collects the parts of one object; every part is offset to hug the back
    of its tile exactly like the bookcase, so all five pieces line up."""

    def __init__(self) -> None:
        self.parts: list[bpy.types.Object] = []

    def _place(self, obj, name, material):
        obj.name = name
        obj.data.materials.append(material)
        self.parts.append(obj)
        return obj

    def box(self, name, centre, size, material, rot=(0.0, 0.0, 0.0)):
        loc = (centre[0], centre[1] + OFFSET_Y, centre[2] + OFFSET_Z)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        obj = bpy.context.active_object
        obj.scale = size
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def cyl(self, name, centre, radius, length, material, rot=(0.0, 0.0, 0.0),
            vertices=14):
        loc = (centre[0], centre[1] + OFFSET_Y, centre[2] + OFFSET_Z)
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length,
                                            location=loc, vertices=vertices)
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)


def make_textures() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    # The bookcase's restrained oak grain, verbatim.
    spec = material_spec("wood", seed=48)
    spec = dataclasses.replace(
        spec,
        octaves=[(size, amplitude * 0.11) for size, amplitude in spec.octaves],
        contrast=1.10, stroke_count=70, stroke_amplitude=0.05,
        knot_count=1, knot_depth=0.06,
    )
    write_surface_map(GRAIN_PATH, 512, 512, spec, grain_axis="v")
    # Painted steel, not a rusted drum: every amplitude pulled well down.
    mspec = material_spec("metal", seed=21)
    mspec = dataclasses.replace(
        mspec,
        octaves=[(size, amplitude * 0.35) for size, amplitude in mspec.octaves],
    )
    write_surface_map(METAL_PATH, 512, 512, mspec)


def materials() -> dict:
    grain, steel = str(GRAIN_PATH), str(METAL_PATH)
    t = F.toon_material
    return {
        "oak": F.forge_material("sh_oak", "wood", OAK, texture_path=grain),
        "oak_trim": F.forge_material("sh_oak_trim", "wood",
                                     tuple(c * 0.70 for c in OAK), texture_path=grain),
        "oak_shelf": F.forge_material("sh_oak_shelf", "wood",
                                      tuple(c * 0.78 for c in OAK)),
        "oak_back": F.forge_material("sh_oak_back", "wood",
                                     tuple(c * 0.28 for c in OAK)),
        "pine": F.forge_material("sh_pine", "wood", PINE, texture_path=grain),
        "pine_trim": F.forge_material("sh_pine_trim", "wood",
                                      tuple(c * 0.80 for c in PINE), texture_path=grain),
        "pine_shelf": F.forge_material("sh_pine_shelf", "wood",
                                       tuple(c * 0.86 for c in PINE)),
        "pine_back": F.forge_material("sh_pine_back", "wood",
                                      tuple(c * 0.40 for c in PINE)),
        "steel": F.forge_material("sh_steel", "metal", STEEL, texture_path=steel),
        "steel_dark": F.forge_material("sh_steel_dark", "metal",
                                       tuple(c * 0.55 for c in STEEL)),
        "steel_deck": F.forge_material("sh_steel_deck", "metal",
                                       tuple(c * 0.85 for c in STEEL)),
        # contents -- flat toon paints, muted to sit next to vanilla loot art
        "can": [t("sh_can_%d" % i, p) for i, p in enumerate([
            (0.62, 0.10, 0.06), (0.14, 0.32, 0.10), (0.60, 0.50, 0.12),
            (0.55, 0.53, 0.47), (0.10, 0.22, 0.44)])],
        "tin": t("sh_tin", (0.50, 0.50, 0.47)),
        "jar": t("sh_jar", (0.55, 0.30, 0.06)),
        "lid": t("sh_lid", (0.42, 0.40, 0.36)),
        "cereal": [t("sh_box_%d" % i, p) for i, p in enumerate([
            (0.70, 0.45, 0.08), (0.55, 0.10, 0.08), (0.12, 0.30, 0.50),
            (0.62, 0.58, 0.40)])],
        "bottle": [t("sh_bottle_%d" % i, p) for i, p in enumerate([
            (0.12, 0.30, 0.12), (0.36, 0.16, 0.05), (0.20, 0.24, 0.10),
            (0.40, 0.08, 0.12)])],
        "foil": [t("sh_foil_%d" % i, p) for i, p in enumerate([
            (0.78, 0.60, 0.14), (0.62, 0.08, 0.06), (0.82, 0.78, 0.64),
            (0.20, 0.10, 0.30), (0.10, 0.10, 0.10)])],
        "cardboard": t("sh_cardboard", (0.52, 0.36, 0.18)),
        "cardboard_dark": t("sh_cardboard_dark", (0.40, 0.27, 0.13)),
        "paint": [t("sh_paint_%d" % i, p) for i, p in enumerate([
            (0.60, 0.58, 0.52), (0.55, 0.12, 0.08), (0.12, 0.25, 0.45)])],
        "jug": t("sh_jug", (0.62, 0.60, 0.52)),
        "jug_cap": t("sh_jug_cap", (0.12, 0.25, 0.50)),
        "toolbox": t("sh_toolbox", (0.60, 0.10, 0.06)),
        "stock": t("sh_stock", (0.34, 0.16, 0.05)),
        "gunmetal": t("sh_gunmetal", (0.12, 0.12, 0.12)),
        "ammo": [t("sh_ammo_%d" % i, p) for i, p in enumerate([
            (0.28, 0.32, 0.14), (0.55, 0.42, 0.12), (0.45, 0.10, 0.06)])],
    }


INNER_W = WIDTH - 2 * SIDE
INNER_L = -WIDTH / 2 + SIDE
ITEM_Y = -DEPTH / 2 + 0.030 + (DEPTH - 0.090) / 2   # centre line for contents


def oak_carcass(b: Builder, m: dict, levels, dividers: int = 0,
                wood: str = "oak") -> None:
    """The bookcase carcass with its board count and wood as parameters."""
    b.box("backboard", (0, DEPTH / 2 - 0.013, HEIGHT / 2),
          (INNER_W, 0.026, HEIGHT - 0.10), m[f"{wood}_back"])
    b.box("left_stile", (-(WIDTH - SIDE) / 2, 0, HEIGHT / 2),
          (SIDE, DEPTH, HEIGHT), m[f"{wood}_trim"])
    b.box("right_stile", ((WIDTH - SIDE) / 2, 0, HEIGHT / 2),
          (SIDE, DEPTH, HEIGHT), m[f"{wood}_trim"])
    b.box("base_plinth", (0, 0, 0.05), (WIDTH, DEPTH, 0.100), m[f"{wood}_trim"])
    b.box("top_cap", (0, 0, HEIGHT - 0.031), (WIDTH, DEPTH + 0.030, 0.062),
          m[f"{wood}_trim"])
    for i, level in enumerate(levels):
        b.box(f"shelf_{i}", (0, -0.004, level), (INNER_W, DEPTH - 0.012, 0.038),
              m[f"{wood}_shelf"])
    for d in range(dividers):
        x = INNER_L + INNER_W * (d + 1) / (dividers + 1)
        b.box(f"divider_{d}", (x, -0.004, HEIGHT / 2),
              (0.030, DEPTH - 0.012, HEIGHT - 0.16), m[f"{wood}_trim"])


def steel_frame(b: Builder, m: dict, levels, top: float = HEIGHT) -> None:
    """Welded angle-iron uprights and flat decks with a folded front lip.
    Open back and sides: the wall behind shows through, as on a real rack."""
    post = 0.045
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}",
                  (sx * (WIDTH / 2 - post / 2), sy * (DEPTH / 2 - post / 2), top / 2),
                  (post, post, top), m["steel"])
    for i, level in enumerate(levels):
        b.box(f"deck_{i}", (0, 0, level), (WIDTH - 0.01, DEPTH - 0.01, 0.022),
              m["steel_deck"])
        b.box(f"lip_{i}", (0, -DEPTH / 2 + 0.006, level - 0.018),
              (WIDTH - 0.01, 0.014, 0.050), m["steel"])
    # diagonal cross-brace on the back, what keeps a welded rack from racking
    span = math.hypot(WIDTH, top * 0.9)
    ang = math.atan2(top * 0.9, WIDTH)
    b.box("brace_a", (0, DEPTH / 2 - 0.02, top / 2), (span, 0.012, 0.030),
          m["steel_dark"], rot=(0.0, -ang, 0.0))
    b.box("brace_b", (0, DEPTH / 2 - 0.02, top / 2), (span, 0.012, 0.030),
          m["steel_dark"], rot=(0.0, ang, 0.0))


BOOK_LEVELS = tuple(round(0.100 + i * 0.465, 3) for i in range(4))


def build_pantry(b: Builder, m: dict) -> None:
    oak_carcass(b, m, BOOK_LEVELS, wood="pine")
    right = INNER_L + INNER_W - 0.02
    patterns = [
        ["can", "can", "can", "jar", "jar", "can", "can", "cereal"],
        ["cereal", "cereal", "can", "can", "can", "can", "jar", "jar"],
        ["jar", "jar", "jar", "can", "can", "cereal", "can", "can"],
        ["can", "can", "cereal", "cereal", "jar", "can", "can", "can"],
    ]
    for row, level in enumerate(BOOK_LEVELS):
        z0 = level + 0.019
        x = INNER_L + 0.020 + 0.006 * (row % 2)
        col = 0
        while True:
            kind = patterns[row][col % len(patterns[row])]
            w = {"can": 0.096, "jar": 0.110, "cereal": 0.170}[kind]
            if x + w > right:
                break
            cx = x + w / 2
            n = f"item_{row}_{col}"
            if kind == "can":
                paint = m["can"][(row * 3 + col) % len(m["can"])]
                for k in range(3):  # squat cans stacked three high, bright tin lids
                    zc = z0 + 0.046 + k * 0.096
                    b.cyl(f"{n}_{k}", (cx, ITEM_Y - 0.05, zc), 0.046, 0.074, paint)
                    b.cyl(f"{n}_{k}r", (cx, ITEM_Y - 0.05, zc + 0.041), 0.046,
                          0.014, m["tin"])
            elif kind == "jar":
                b.cyl(f"{n}_j", (cx, ITEM_Y - 0.05, z0 + 0.100), 0.052, 0.200, m["jar"])
                b.cyl(f"{n}_l", (cx, ITEM_Y - 0.05, z0 + 0.212), 0.048, 0.028, m["lid"])
            else:
                paint = m["cereal"][(row + col) % len(m["cereal"])]
                b.box(f"{n}_b", (cx, ITEM_Y, z0 + 0.160), (w - 0.008, 0.070, 0.320), paint)
            x += w + 0.008
            col += 1


def build_wine(b: Builder, m: dict) -> None:
    """Four columns of cubbies, bottles lying neck-out and flush with the front
    so the foil caps carry the read -- deep cubbies swallowed them at tile scale."""
    levels = tuple(round(0.100 + i * 0.310, 3) for i in range(6))
    oak_carcass(b, m, levels, dividers=3)
    col_w = INNER_W / 4
    tops = list(levels[1:]) + [HEIGHT - 0.062]
    front = -DEPTH / 2 + 0.012
    for row, (floor, ceil) in enumerate(zip(levels, tops)):
        z0 = floor + 0.019
        for col in range(4):
            cx = INNER_L + col_w * (col + 0.5)
            spots = [(-0.047, 0.044), (0.047, 0.044), (0.0, 0.124)]
            for k, (dx, dz) in enumerate(spots):
                if z0 + dz + 0.044 > ceil - 0.01:
                    continue
                n = f"item_{row}_{col}_{k}"
                i = row * 3 + col * 2 + k
                glass = m["bottle"][i % len(m["bottle"])]
                foil = m["foil"][i % len(m["foil"])]
                body_c = front + 0.075 + 0.120
                b.cyl(f"{n}_body", (cx + dx, body_c, z0 + dz), 0.043, 0.240, glass,
                      rot=(math.pi / 2, 0, 0))
                b.cyl(f"{n}_neck", (cx + dx, front + 0.040, z0 + dz), 0.016, 0.070,
                      glass, rot=(math.pi / 2, 0, 0))
                b.cyl(f"{n}_foil", (cx + dx, front + 0.004, z0 + dz), 0.019, 0.030,
                      foil, rot=(math.pi / 2, 0, 0))


def build_utility(b: Builder, m: dict) -> None:
    levels = (0.100, 0.575, 1.050, 1.525, 1.980)
    steel_frame(b, m, levels)
    right = WIDTH / 2 - 0.05
    patterns = [
        ["box", "box", "box"],
        ["paint", "paint", "jug", "jug", "paint"],
        ["toolbox", "box", "paint"],
        ["box", "jug", "paint", "paint"],
    ]
    for row, level in enumerate(levels[:4]):
        z0 = level + 0.011
        x = -WIDTH / 2 + 0.05
        col = 0
        while True:
            kind = patterns[row][col % len(patterns[row])]
            w = {"box": 0.290, "paint": 0.170, "jug": 0.140, "toolbox": 0.330}[kind]
            if x + w > right:
                break
            cx = x + w / 2
            n = f"item_{row}_{col}"
            if kind == "box":
                h = 0.30 if row == 0 else 0.24
                b.box(f"{n}_b", (cx, 0.0, z0 + h / 2), (w - 0.01, DEPTH - 0.09, h),
                      m["cardboard"] if col % 2 == 0 else m["cardboard_dark"])
                b.box(f"{n}_t", (cx, -(DEPTH - 0.09) / 2 + 0.002, z0 + h * 0.62),
                      (w - 0.012, 0.004, 0.035), m["cardboard_dark"])  # tape band
            elif kind == "paint":
                paint = m["paint"][(row + col) % len(m["paint"])]
                b.cyl(f"{n}_c", (cx, -0.04, z0 + 0.095), 0.080, 0.190, m["tin"])
                b.cyl(f"{n}_l", (cx, -0.04, z0 + 0.085), 0.081, 0.090, paint)
            elif kind == "jug":
                b.box(f"{n}_j", (cx, -0.02, z0 + 0.125), (w - 0.02, 0.120, 0.250), m["jug"])
                b.cyl(f"{n}_cap", (cx + 0.03, -0.02, z0 + 0.265), 0.022, 0.030,
                      m["jug_cap"])
            else:
                b.box(f"{n}_t", (cx, -0.03, z0 + 0.085), (w - 0.02, 0.180, 0.170),
                      m["toolbox"])
                b.box(f"{n}_h", (cx, -0.03, z0 + 0.185), (0.16, 0.030, 0.030),
                      m["gunmetal"])
            x += w + 0.012
            col += 1


GUN_TOP = 1.85


def build_gunrack(b: Builder, m: dict) -> None:
    levels = (0.100, 0.500, 1.620)
    post = 0.045
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}",
                  (sx * (WIDTH / 2 - post / 2), sy * (DEPTH / 2 - post / 2), GUN_TOP / 2),
                  (post, post, GUN_TOP), m["steel"])
    for i, level in enumerate(levels):
        b.box(f"deck_{i}", (0, 0, level), (WIDTH - 0.01, DEPTH - 0.01, 0.022),
              m["steel_deck"])
        b.box(f"lip_{i}", (0, -DEPTH / 2 + 0.006, level - 0.018),
              (WIDTH - 0.01, 0.014, 0.050), m["steel"])
    b.box("cap", (0, 0, GUN_TOP - 0.015), (WIDTH, DEPTH, 0.030), m["steel"])
    b.box("back_panel", (0, DEPTH / 2 - 0.012, (0.52 + 1.60) / 2),
          (WIDTH - 0.09, 0.016, 1.60 - 0.52), m["steel_dark"])
    # the notched rest bar the barrels lean into
    b.box("rest_bar", (0, 0.05, 1.30), (WIDTH - 0.05, 0.030, 0.040), m["steel"])
    for k in range(7):
        b.box(f"notch_{k}", (-0.36 + k * 0.12 + 0.06, 0.03, 1.325),
              (0.012, 0.035, 0.030), m["steel_dark"])

    # row 1: seven long guns standing butt-down, tilted back into the bar
    tilt = (-0.10, 0.0, 0.0)
    for col in range(7):
        cx = -0.36 + col * 0.12
        n = f"item_1_{col}"
        b.box(f"{n}_stock", (cx, -0.02, 0.51 + 0.16), (0.045, 0.075, 0.320),
              m["stock"], rot=tilt)
        b.box(f"{n}_recv", (cx, 0.015, 0.51 + 0.46), (0.034, 0.060, 0.300),
              m["gunmetal"], rot=tilt)
        b.cyl(f"{n}_barrel", (cx, 0.045, 0.51 + 0.80), 0.011, 0.420,
              m["gunmetal"], rot=tilt)
        if col % 2 == 1:  # every other one wears a forend
            b.box(f"{n}_fore", (cx, 0.03, 0.51 + 0.68), (0.040, 0.050, 0.160),
                  m["stock"], rot=tilt)

    # rows 0 and 2: ammo cans below, carton stacks on top
    for row, level in ((0, 0.100), (2, 1.620)):
        z0 = level + 0.011
        x = -WIDTH / 2 + 0.06
        col = 0
        while x + 0.15 < WIDTH / 2 - 0.05:
            n = f"item_{row}_{col}"
            paint = m["ammo"][(row + col) % len(m["ammo"])]
            if row == 0:
                b.box(f"{n}_can", (x + 0.07, -0.02, z0 + 0.10), (0.130, 0.280, 0.200), paint)
                b.box(f"{n}_lid", (x + 0.07, -0.02, z0 + 0.205), (0.134, 0.284, 0.018),
                      m["gunmetal"])
                x += 0.150
            else:
                for k in range(2):
                    b.box(f"{n}_{k}", (x + 0.05, -0.04, z0 + 0.03 + k * 0.062),
                          (0.095, 0.150, 0.058), paint)
                x += 0.110
            col += 1


def _rc(name: str) -> tuple[int, int]:
    f = name.split("_")
    return int(f[1]), int(f[2])


def looted_shelves(name: str) -> bool:
    """Bookcase rule: bay 1 gutted, bay 3 thinned, bays 0/2 lose their right end."""
    row, col = _rc(name)
    return row == 1 or (row == 3 and col % 2 == 0) or (row in (0, 2) and col >= 4)


def looted_wine(name: str) -> bool:
    """One row cleared, the right column gone from the lower rows, top bottles
    lifted off the upper rows -- a rack somebody has been drinking down."""
    row, col = _rc(name)
    k = int(name.split("_")[3])
    return row == 2 or (col == 3 and row >= 3) or (k == 2 and row < 2)


def looted_utility(name: str) -> bool:
    row, col = _rc(name)
    return row in (1, 2) and col % 2 == 0 or row == 3 or (row == 0 and col >= 2)


def looted_gunrack(name: str) -> bool:
    """Guns go first: four of seven gone, the top cartons half gone."""
    row, col = _rc(name)
    if row == 1:
        return col in (0, 2, 3, 5)
    if row == 2:
        return col >= 3
    return col % 2 == 1


PIECES = [
    (build_pantry, looted_shelves),
    (build_wine, looted_wine),
    (build_utility, looted_utility),
    (build_gunrack, looted_gunrack),
]


def render(props, tag: str) -> dict:
    props.sheet_name = tag
    return F.render_cells(bpy.context)


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
    m = materials()

    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    merged: dict = {}
    elements: dict = {}
    cells: list = []
    for group, ((key, cname, cap, base), (build, looted)) in enumerate(zip(OBJECTS, PIECES)):
        if only and key != only:
            continue
        b = Builder()
        build(b, m)
        for part in b.parts:
            part.parent = subject
        # Work by name: a removed object's Python handle is dead, and even an
        # equality test against it raises.
        items = [o.name for o in b.parts if o.name.startswith("item_")]
        carcass = [o.name for o in b.parts if not o.name.startswith("item_")]
        taken = {n for n in items if looted(n)}
        kept = [n for n in items if n not in taken]

        def drop(names):
            for n in names:
                obj = bpy.data.objects.get(n)
                if obj is not None:
                    bpy.data.objects.remove(obj, do_unlink=True)

        states = [render(props, f"bs_{key}_full")]
        drop(taken)
        states.append(render(props, f"bs_{key}_half"))
        drop(kept)
        states.append(render(props, f"bs_{key}_empty"))
        drop(carcass)
        if not merged:
            merged = dict(states[0])
        tile = dict(base, CustomName=cname, ContainerCapacity=cap)
        # manifest order within a facing is stocked, picked, stripped; the
        # packer's sort is stable, so that is the sheet order too
        for facing in ("S", "E", "N", "W"):
            for s in states:
                for cell in s["cells"]:
                    if cell["facing"] == facing:
                        cells.append(dict(cell, group=group,
                                          tile_props=dict(tile, Facing=facing)))
        for s in states:
            elements.update(s.get("elements", {}))
        print(f"== {key}: {len(items)} content parts, {len(taken)} taken for picked-over")

    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
