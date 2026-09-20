"""BADLANDS closet set: six makeshift wardrobe pieces built from planks, 2x4s
and salvaged crates.

Every piece hugs the back of its tile like the bookcase and the shelving, so a
whole closet wall lines up. Four fill stages each, fullest first, in the layout
KNXBookcase.lua reads: index = piece * 16 + facing * 4 + stage.

Shelf labels are hand-lettered strips -- the motif that runs through this whole
batch, and the thing that makes a plank read as somebody's closet instead of a
warehouse rack.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_closet.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "closet_cells"
SHEET = "badlands_closet_01"
GRAIN_PATH = ROOT / "build" / "closet_grain.png"
METAL_PATH = ROOT / "build" / "closet_steel.png"
STAGES = 4

# Wall pieces: same back-hug as the bookcase so the set lines up.
OFFSET_Y = 0.206
OFFSET_Z = -2.0 / 77.2

PINE = (0.735, 0.520, 0.285)     # fresh plank
FIR = (0.560, 0.385, 0.205)      # 2x4 framing, a shade browner
STEEL = (0.300, 0.305, 0.300)

# Cloned from vanilla's wardrobe block (clothingrack keys) minus the things a
# nailed-together plank cannot claim. The rod pieces take the wardrobe loot
# table; the crate column takes crate loot; the cubby is a shoe rack.
WOOD_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "",
    "ContainerPutSound": "ClothingRackTransferItem",
    "ContainerTakeSound": "ClothingRackTransferItem",
    "GroupName": "Badlands Closet", "IsMoveAble": "",
    "Material": "Wood", "Material2": "Nails", "MaterialType": "Wood",
    "PickUpTool": "Hammer", "PickUpWeight": "150", "PlaceTool": "Hammer",
    "ScrapSize": "Large", "Surface": "80", "container": "wardrobe", "solid": "",
}
SHELF_PROPS = dict(WOOD_PROPS, container="shelves",
                   ContainerPutSound="ShelfWoodTransferItem",
                   ContainerTakeSound="ShelfWoodTransferItem")
CRATE_PROPS = dict(WOOD_PROPS, container="crate", PickUpWeight="180",
                   ContainerPutSound="ShelfWoodTransferItem",
                   ContainerTakeSound="ShelfWoodTransferItem")

OBJECTS = [
    # key, CustomName, capacity, base props
    ("closetrod", "Closet Shelf and Rod", "50", WOOD_PROPS),
    ("linenshelf", "Linen Shelf", "60", SHELF_PROPS),
    ("bootcubby", "Boot Cubby", "40", SHELF_PROPS),
    ("hatshelf", "Overhead Shelf", "30", SHELF_PROPS),
    ("pegboard", "Coat Pegs", "25", WOOD_PROPS),
    ("cratewardrobe", "Crate Wardrobe", "60", CRATE_PROPS),
]


class Builder:
    """Collects the parts of one object, every part offset to hug the back of
    its tile exactly like the bookcase."""

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

    def torus(self, name, centre, major, minor, material, rot=(0.0, 0.0, 0.0)):
        loc = (centre[0], centre[1] + OFFSET_Y, centre[2] + OFFSET_Z)
        bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                         major_segments=20, minor_segments=8,
                                         location=loc)
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)


def make_textures() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    spec = material_spec("wood", seed=37)
    spec = dataclasses.replace(spec, contrast=1.04)
    write_surface_map(GRAIN_PATH, 512, 512, spec)
    mspec = material_spec("metal", seed=12)
    mspec = dataclasses.replace(
        mspec,
        octaves=[(size, amplitude * 0.35) for size, amplitude in mspec.octaves],
    )
    write_surface_map(METAL_PATH, 512, 512, mspec)


def materials() -> dict:
    t = F.toon_material
    w = F.forge_material
    return {
        "pine": w("cl_pine", "wood", PINE, texture_path=str(GRAIN_PATH)),
        "pine_dark": w("cl_pine_dark", "wood", tuple(c * 0.80 for c in PINE),
                       texture_path=str(GRAIN_PATH)),
        "fir": w("cl_fir", "wood", FIR, texture_path=str(GRAIN_PATH)),
        "fir_dark": w("cl_fir_dark", "wood", tuple(c * 0.78 for c in FIR),
                      texture_path=str(GRAIN_PATH)),
        "steel": w("cl_steel", "metal", STEEL, texture_path=str(METAL_PATH)),
        # Packaging and lettering are flat paint: no grain anywhere near them.
        "card": t("cl_card", (0.560, 0.410, 0.230)),
        "card_dark": t("cl_card_dark", (0.430, 0.310, 0.170)),
        "label": t("cl_label", (0.800, 0.775, 0.700)),
        "ink": t("cl_ink", (0.135, 0.125, 0.115)),
        "black": t("cl_black", (0.100, 0.100, 0.110)),
        "leather": t("cl_leather", (0.430, 0.285, 0.170)),
        "leather_dark": t("cl_leather_dark", (0.300, 0.200, 0.125)),
        # Somebody's laundry: washed-out, nothing saturated.
        "cloth": [t("cl_cloth_%d" % i, p) for i, p in enumerate([
            (0.380, 0.450, 0.545), (0.520, 0.500, 0.420), (0.430, 0.470, 0.375),
            (0.600, 0.560, 0.500), (0.470, 0.330, 0.310), (0.330, 0.370, 0.420),
            (0.560, 0.480, 0.360), (0.400, 0.410, 0.440)])],
    }


def cloth(m, i):
    return m["cloth"][i % len(m["cloth"])]


def label(b, m, tag, x, z, w=0.170, y=None, dashes=3):
    """A strip of tape with somebody's handwriting on it. The lettering is
    three short ink dashes -- at sprite scale that is exactly what handwriting
    looks like, and it never renders as garbled text."""
    yy = -0.148 if y is None else y
    b.box(f"{tag}_strip", (x, yy, z), (w, 0.006, 0.042), m["label"])
    for i in range(dashes):
        dx = (i - (dashes - 1) / 2) * (w / (dashes + 0.6))
        b.box(f"{tag}_ink{i}", (x + dx, yy - 0.005, z),
              (w / (dashes + 1.9), 0.004, 0.011), m["ink"])


def folded(b, m, tag, x, y, z, count, size=(0.150, 0.130, 0.036), seed=0):
    """A stack of folded clothes: each layer a hair off square, with a shadow
    seam down the fold so it does not read as a solid block."""
    w, d, h = size
    for i in range(count):
        yaw = (0.055 if (i + seed) % 2 else -0.045) * (1 + i * 0.35)
        zz = z + h / 2 + i * h
        b.box(f"item_{tag}_{i}", (x, y, zz), (w, d, h), cloth(m, seed + i),
              rot=(0.0, 0.0, yaw))
        b.box(f"item_{tag}_{i}_fold", (x, y - d / 2 - 0.002, zz),
              (w * 0.86, 0.004, h * 0.30), cloth(m, seed + i + 4),
              rot=(0.0, 0.0, yaw))


def hanger(b, m, tag, x, z_rod, drop, seed=0, wide=0.170):
    """A garment on a wire hanger: the hook over the rod, shoulders, body."""
    b.cyl(f"item_{tag}_0_hook", (x, 0.0, z_rod + 0.020), 0.006, 0.048,
          m["steel"], rot=(1.5708, 0.0, 0.0), vertices=8)
    b.box(f"item_{tag}_0_bar", (x, 0.0, z_rod - 0.048), (wide * 0.80, 0.014, 0.012),
          m["steel"])
    b.box(f"item_{tag}_0_top", (x, 0.0, z_rod - 0.086), (wide, 0.075, 0.070),
          cloth(m, seed))
    b.box(f"item_{tag}_0_body", (x, 0.0, z_rod - 0.086 - drop / 2),
          (wide * 0.88, 0.062, drop), cloth(m, seed))
    b.box(f"item_{tag}_0_seam", (x, -0.034, z_rod - 0.086 - drop / 2),
          (0.012, 0.006, drop * 0.92), cloth(m, seed + 3))


def bootpair(b, m, tag, x, y, z, seed=0, tall=0.120):
    """A pair of boots, toes out, one leaning on the other."""
    for i, (dx, lean) in enumerate(((-0.046, 0.05), (0.046, -0.09))):
        leather = m["leather"] if (seed + i) % 2 else m["leather_dark"]
        b.box(f"item_{tag}_{i}_shaft", (x + dx, y + 0.012, z + tall / 2),
              (0.068, 0.072, tall), leather, rot=(0.0, lean, 0.0))
        b.box(f"item_{tag}_{i}_toe", (x + dx, y - 0.048, z + 0.026),
              (0.066, 0.096, 0.052), leather)
        b.box(f"item_{tag}_{i}_sole", (x + dx, y - 0.030, z + 0.008),
              (0.072, 0.140, 0.018), m["black"])


def duffel(b, m, tag, x, y, z, seed=0, length=0.230):
    b.cyl(f"item_{tag}_0_body", (x, y, z + 0.062), 0.062, length, cloth(m, seed),
          rot=(0.0, 1.5708, 0.0), vertices=12)
    b.box(f"item_{tag}_0_strap", (x, y - 0.040, z + 0.062),
          (length * 0.70, 0.010, 0.022), m["leather_dark"])


def hat(b, m, tag, x, y, z, seed=0):
    b.cyl(f"item_{tag}_0_brim", (x, y, z + 0.012), 0.088, 0.016, cloth(m, seed),
          vertices=16)
    b.cyl(f"item_{tag}_0_crown", (x, y, z + 0.052), 0.056, 0.070, cloth(m, seed),
          vertices=16)
    b.torus(f"item_{tag}_0_band", (x, y, z + 0.030), 0.058, 0.008,
            m["leather_dark"])


DEPTH = 0.300


def bracket(b, m, tag, x, z_top, depth=DEPTH):
    """Shelf on 2x4s: a cleat behind it and a knee brace under each end."""
    b.box(f"{tag}_cleat", (x, depth / 2 - 0.018, z_top - 0.062),
          (0.045, 0.036, 0.090), m["fir"])
    b.box(f"{tag}_arm", (x, 0.010, z_top - 0.030),
          (0.038, depth - 0.050, 0.038), m["fir"])
    b.box(f"{tag}_knee", (x, -0.020, z_top - 0.120), (0.032, 0.190, 0.032),
          m["fir_dark"], rot=(0.75, 0.0, 0.0))


def build_closetrod(b, m) -> None:
    z = 1.472
    b.box("backrail", (0.0, DEPTH / 2 - 0.012, z - 0.070),
          (0.940, 0.032, 0.088), m["fir"])
    for sx in (-1, 1):
        bracket(b, m, f"br{sx}", sx * 0.395, z)
    b.box("shelf", (0.0, 0.0, z), (0.940, DEPTH, 0.030), m["pine"])
    b.box("shelf_lip", (0.0, -DEPTH / 2 + 0.008, z - 0.022),
          (0.940, 0.018, 0.024), m["pine_dark"])
    b.cyl("rod", (0.0, -0.018, 1.352), 0.016, 0.900, m["steel"],
          rot=(0.0, 1.5708, 0.0), vertices=12)
    for sx in (-1, 1):
        b.box(f"rodend_{sx}", (sx * 0.452, -0.018, 1.352),
              (0.028, 0.060, 0.060), m["fir_dark"])
    label(b, m, "lbl0", -0.300, z - 0.024, w=0.190,
          y=-DEPTH / 2 - 0.004)

    for i, x in enumerate((-0.360, -0.216, -0.072, 0.072, 0.216, 0.360)):
        hanger(b, m, f"hang{i}", x, 1.352, 0.34 + 0.055 * (i % 3), seed=i)
    folded(b, m, "fold0", -0.320, 0.010, z + 0.015, 3, seed=1)
    folded(b, m, "fold1", 0.300, 0.010, z + 0.015, 2, seed=5)
    duffel(b, m, "bag0", 0.030, 0.010, z + 0.015, seed=3)


def build_linenshelf(b, m) -> None:
    levels = (0.120, 0.520, 0.920, 1.320)
    for sx in (-1, 1):
        b.box(f"upright_{sx}", (sx * 0.442, 0.0, 0.760),
              (0.044, DEPTH, 1.520), m["fir"])
    b.box("backrail", (0.0, DEPTH / 2 - 0.012, 1.470), (0.900, 0.028, 0.090),
          m["fir_dark"])
    b.box("footrail", (0.0, DEPTH / 2 - 0.012, 0.040), (0.900, 0.028, 0.080),
          m["fir_dark"])
    for i, z in enumerate(levels):
        b.box(f"shelf{i}", (0.0, 0.0, z), (0.900, DEPTH, 0.028), m["pine"])
        b.box(f"shelf{i}_lip", (0.0, -DEPTH / 2 + 0.008, z - 0.024),
              (0.900, 0.016, 0.026), m["pine_dark"])
        label(b, m, f"lbl{i}", -0.250 + 0.160 * (i % 2), z - 0.026,
              w=0.180, y=-DEPTH / 2 - 0.004)

    n = 0
    for li, z in enumerate(levels[:3]):
        for xi, x in enumerate((-0.290, 0.000, 0.290)):
            folded(b, m, f"lin{n}", x, 0.005, z + 0.014,
                   2 + (li + xi) % 3, seed=n)
            n += 1
    folded(b, m, "lin9", -0.250, 0.005, levels[3] + 0.014, 2, seed=2)
    duffel(b, m, "bag0", 0.180, 0.005, levels[3] + 0.014, seed=6)


def build_bootcubby(b, m) -> None:
    top, mid, floor = 0.646, 0.330, 0.022
    for sx in (-1, 1):
        b.box(f"side_{sx}", (sx * 0.440, 0.0, 0.335), (0.036, DEPTH, 0.660),
              m["fir"])
    b.box("base", (0.0, 0.0, floor), (0.920, DEPTH, 0.030), m["pine"])
    b.box("mid", (0.0, 0.0, mid), (0.880, DEPTH, 0.026), m["pine"])
    b.box("top", (0.0, 0.0, top), (0.940, DEPTH + 0.020, 0.032), m["pine"])
    b.box("backer", (0.0, DEPTH / 2 - 0.010, 0.335), (0.880, 0.020, 0.620),
          m["pine_dark"])
    for i, x in enumerate((-0.148, 0.148)):
        for j, (z, h) in enumerate(((0.175, 0.280), (0.485, 0.290))):
            b.box(f"div{i}{j}", (x, 0.0, z), (0.024, DEPTH - 0.020, h),
                  m["fir_dark"])
    for i, x in enumerate((-0.295, 0.000, 0.295)):
        label(b, m, f"lbl{i}", x, 0.318, w=0.150, y=-DEPTH / 2 - 0.004,
              dashes=2)

    for i, x in enumerate((-0.295, 0.000, 0.295)):
        bootpair(b, m, f"boot{i}", x, 0.010, 0.040, seed=i)
        bootpair(b, m, f"boot{i + 3}", x, 0.010, 0.348, seed=i + 2,
                 tall=0.105)
    folded(b, m, "fold0", -0.280, 0.010, top + 0.018, 3, seed=4)
    duffel(b, m, "bag0", 0.160, 0.010, top + 0.018, seed=1)


def build_hatshelf(b, m) -> None:
    z = 1.620
    b.box("backrail", (0.0, DEPTH / 2 - 0.012, z - 0.070),
          (0.940, 0.032, 0.088), m["fir"])
    for sx in (-1, 1):
        bracket(b, m, f"br{sx}", sx * 0.395, z)
    b.box("shelf", (0.0, 0.0, z), (0.940, DEPTH, 0.032), m["pine"])
    b.box("guard", (0.0, -DEPTH / 2 + 0.010, z + 0.046), (0.940, 0.018, 0.060),
          m["pine_dark"])
    label(b, m, "lbl0", 0.230, z + 0.046, w=0.200, y=-DEPTH / 2 + 0.000)

    hat(b, m, "hat0", -0.320, 0.020, z + 0.016, seed=3)
    hat(b, m, "hat1", -0.120, 0.020, z + 0.016, seed=6)
    duffel(b, m, "bag0", 0.140, 0.015, z + 0.016, seed=0)
    duffel(b, m, "bag1", 0.330, 0.015, z + 0.016, seed=4, length=0.180)
    folded(b, m, "fold0", 0.030, 0.015, z + 0.016, 2, seed=7)


def build_pegboard(b, m) -> None:
    z = 1.430
    b.box("board", (0.0, DEPTH / 2 - 0.006, z), (0.920, 0.026, 0.440),
          m["pine"])
    for dz in (0.200, -0.200):
        b.box(f"batten{dz:+.0f}".replace("+", "p").replace("-", "n"),
              (0.0, DEPTH / 2 - 0.022, z + dz), (0.920, 0.028, 0.060),
              m["fir"])
    pegs = (-0.352, -0.176, 0.000, 0.176, 0.352)
    for i, x in enumerate(pegs):
        b.cyl(f"peg{i}", (x, DEPTH / 2 - 0.070, z + 0.126), 0.014, 0.110,
              m["fir_dark"], rot=(1.5708, 0.0, 0.0), vertices=10)
        label(b, m, f"lbl{i}", x, z - 0.090, w=0.110,
              y=DEPTH / 2 - 0.022, dashes=2)

    shapes = ((0.175, 0.44), (0.140, 0.26), (0.160, 0.36), (0.132, 0.30))
    for i, x in enumerate(pegs[:4]):
        wide, drop = shapes[i]
        yy = DEPTH / 2 - 0.110
        tilt = 0.035 if i % 2 else -0.028
        b.box(f"item_coat{i}_0_yoke", (x, yy, z + 0.096),
              (wide * 0.55, 0.062, 0.058), cloth(m, i + 1), rot=(0.0, tilt, 0.0))
        b.box(f"item_coat{i}_0_top", (x, yy, z + 0.044),
              (wide, 0.070, 0.070), cloth(m, i + 1), rot=(0.0, tilt, 0.0))
        b.box(f"item_coat{i}_0_body", (x, yy, z - 0.010 - drop / 2),
              (wide * 0.82, 0.056, drop), cloth(m, i + 1), rot=(0.0, tilt, 0.0))
        b.box(f"item_coat{i}_0_hem", (x, yy, z - 0.014 - drop),
              (wide * 0.90, 0.060, 0.030), cloth(m, i + 5), rot=(0.0, tilt, 0.0))
        b.box(f"item_coat{i}_0_seam", (x, yy - 0.032, z - 0.010 - drop / 2),
              (0.011, 0.006, drop * 0.88), cloth(m, i + 4), rot=(0.0, tilt, 0.0))
    hat(b, m, "hat0", pegs[4], DEPTH / 2 - 0.105, z + 0.086, seed=2)
    b.cyl("item_sack0_0_strap", (pegs[4], DEPTH / 2 - 0.105, z + 0.020), 0.040,
          0.010, m["leather_dark"], rot=(1.5708, 0.0, 0.0), vertices=12)
    b.box("item_sack0_0_body", (pegs[4], DEPTH / 2 - 0.112, z - 0.085),
          (0.130, 0.080, 0.170), cloth(m, 5))


def crate(b, m, tag, x, z, w=0.430, h=0.352, d=0.330, yaw=0.0):
    """One salvaged crate: five boards, open to the front."""
    t = 0.022
    b.box(f"{tag}_floor", (x, 0.0, z + t / 2), (w, d, t), m["pine"],
          rot=(0.0, 0.0, yaw))
    b.box(f"{tag}_roof", (x, 0.0, z + h - t / 2), (w, d, t), m["pine"],
          rot=(0.0, 0.0, yaw))
    for sx in (-1, 1):
        b.box(f"{tag}_side{sx}", (x + sx * (w / 2 - t / 2), 0.0, z + h / 2),
              (t, d, h), m["pine_dark"], rot=(0.0, 0.0, yaw))
    b.box(f"{tag}_back", (x, d / 2 - t / 2, z + h / 2), (w - 2 * t, t, h),
          m["fir"], rot=(0.0, 0.0, yaw))
    b.box(f"{tag}_rail", (x, -d / 2 + 0.010, z + h - 0.055),
          (w - 2 * t, 0.016, 0.040), m["fir_dark"], rot=(0.0, 0.0, yaw))


def build_cratewardrobe(b, m) -> None:
    cols = (-0.232, 0.232)
    rows = (0.008, 0.368, 0.728, 1.088)
    n = 0
    for ri, z in enumerate(rows):
        for ci, x in enumerate(cols):
            yaw = 0.014 if (ri + ci) % 2 else -0.011
            crate(b, m, f"cr{ri}{ci}", x, z, yaw=yaw)
            label(b, m, f"lbl{ri}{ci}", x, z + 0.296, w=0.140,
                  y=-0.330 / 2 - 0.004, dashes=2)
            folded(b, m, f"cl{n}", x, 0.005, z + 0.030,
                   2 + (ri + ci) % 2, size=(0.185, 0.155, 0.040), seed=n)
            n += 1
    b.box("lid", (0.0, 0.0, 1.452), (0.940, 0.350, 0.028), m["pine"])
    b.box("lid_lip", (0.0, -0.170, 1.434), (0.940, 0.018, 0.026),
          m["pine_dark"])
    label(b, m, "lbltop", 0.270, 1.436, w=0.200, y=-0.182)
    folded(b, m, "cl8", -0.280, 0.010, 1.468, 3, seed=5)
    duffel(b, m, "bag0", 0.090, 0.010, 1.468, seed=2)
    hat(b, m, "hat0", 0.320, 0.010, 1.468, seed=7)


def unit_of(name):
    """The physical thing a part belongs to. Parts are named
    item_<tag>_<index>[_<part>], so the first three tokens are the unit: a
    folded layer and its shadow seam share one, and a cut cannot split them."""
    return "_".join(name.split("_")[:3])


def in_group(name, group):
    """A group token matches a tag exactly, or exactly plus a number -- so
    "bag" catches bag0 and bag1 without a shorter token swallowing a longer
    one the way "towel" used to swallow "towelr"."""
    tag = name.split("_")[1] if name.count("_") >= 2 else ""
    return tag == group or (tag.startswith(group) and tag[len(group):].isdigit())


def order_by(*groups):
    def order(names):
        out = []
        for g in groups:
            out += sorted(n for n in names if in_group(n, g))
        return out
    return order


# Scavenger logic, piece by piece: the light, useful, carryable things go
# first; boots and heavy linen sit there until somebody makes a second trip.
BUILDERS = [
    (build_closetrod, order_by("bag", "fold1", "fold0", "hang")),
    (build_linenshelf, order_by("bag", "lin9", "lin8", "lin7", "lin6", "lin5",
                                "lin4", "lin3", "lin2", "lin1", "lin0")),
    (build_bootcubby, order_by("bag", "fold", "boot5", "boot4", "boot3",
                               "boot2", "boot1", "boot0")),
    (build_hatshelf, order_by("hat", "fold", "bag")),
    (build_pegboard, order_by("hat", "sack", "coat3", "coat2", "coat1",
                              "coat0")),
    (build_cratewardrobe, order_by("hat", "bag", "cl8", "cl7", "cl6", "cl5",
                                   "cl4", "cl3", "cl2", "cl1", "cl0")),
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
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True
    subject = bpy.data.objects[F.SUBJECT_NAME]
    m = materials()

    merged: dict = {}
    elements: dict = {}
    cells: list = []
    for group, ((key, cname, cap, base), (build, order)) in enumerate(
            zip(OBJECTS, BUILDERS)):
        b = Builder()
        build(b, m)
        for part in b.parts:
            part.parent = subject
        items = [o.name for o in b.parts if o.name.startswith("item_")]
        carcass = [o.name for o in b.parts if not o.name.startswith("item_")]
        seq = order(items)
        seq += [n for n in items if n not in seq]
        seen = set()
        seq = [n for n in seq if not (n in seen or seen.add(n))]

        # One physical thing is several objects. Bundle them, in the order the
        # scavenger logic put them in, so a cut can never strand a sub-part.
        units, at = [], {}
        for n in seq:
            key = unit_of(n)
            if key in at:
                units[at[key]].append(n)
            else:
                at[key] = len(units)
                units.append([n])

        def drop(names):
            for n in names:
                obj = bpy.data.objects.get(n)
                if obj is not None:
                    bpy.data.objects.remove(obj, do_unlink=True)

        # Space the stages by visual mass, not part count -- a dozen folds
        # weigh less on screen than one hanging coat.
        def mass(name):
            o = bpy.data.objects.get(name)
            if not o:
                return 1.0
            d = o.dimensions
            return (d.x + d.y) * 0.5 * d.z + d.x * d.y * 0.5

        # Raw silhouette is too lumpy to pace by on its own -- three cartons
        # carry more of it than forty small parts, so whole stages would land
        # on the same cut. Compress the range and blend it with an even count
        # split: the order still reads as scavenging, the walk stays smooth.
        raw = [sum(mass(n) for n in u) ** 0.55 for u in units]
        mean = (sum(raw) / len(raw)) if raw else 1.0
        weights = [0.5 * r + 0.5 * mean for r in raw]
        total = sum(weights) or 1.0
        cum, acc = [], 0.0
        for w in weights:
            acc += w
            cum.append(acc)
        states = []
        gone = 0
        for stage in range(STAGES):
            target = total * stage / (STAGES - 1)
            want = sum(1 for c in cum if c <= target + 1e-9)
            if want < gone:
                want = gone
            drop([n for u in units[gone:want] for n in u])
            gone = want
            states.append(render(props, f"cl_{key}_{stage}"))
        drop(carcass)
        if not merged:
            merged = dict(states[0])
        tile = dict(base, CustomName=cname, ContainerCapacity=cap)
        for facing in ("S", "E", "N", "W"):
            for st in states:
                for cell in st["cells"]:
                    if cell["facing"] == facing:
                        cells.append(dict(cell, group=group,
                                          tile_props=dict(tile, Facing=facing)))
        for st in states:
            elements.update(st.get("elements", {}))
        print(f"== {key}: {len(items)} content parts over {STAGES} stages")

    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2),
                                       encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
