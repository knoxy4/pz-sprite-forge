"""BADLANDS medical table: a trestle table under a tarp, loaded with supplies.

Built from the operator's photo -- a folding table with a brown tarp thrown over
it, glove cartons and folded towels at one end, bottles and tape in the middle,
saline bags and the small valuable things at the other, cardboard boxes stacked
underneath.

Ten fill stages, fullest first, in the sheet layout KNXBookcase.lua reads:
index = piece * 40 + facing * 10 + stage. The removal order is what a scavenger
would actually take first -- syringes, vials and blister packs long before
anybody carries off a carton of towels.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_medical.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "medical_cells"
SHEET = "badlands_medical_01"
GRAIN_PATH = ROOT / "build" / "medical_tarp_grain.png"
METAL_PATH = ROOT / "build" / "medical_steel.png"
STAGES = 10

# A table stands in the middle of its tile, unlike the wall pieces, so no
# back-hugging offset here -- only the 2 px of painted contact the rig has no
# pass for.
OFFSET_Y = 0.0
OFFSET_Z = -2.0 / 77.2

TARP = (0.355, 0.290, 0.205)   # canvas, not timber
STEEL = (0.300, 0.305, 0.300)

# Cloned from vanilla's bathroom medicine cabinet (container = medicine) for the
# loot type, with the table keys off vanilla's own folding table: it is a
# surface you can craft on and set things down on.
TABLE_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "",
    "ContainerPutSound": "ShelfWoodTransferItem",
    "ContainerTakeSound": "ShelfWoodTransferItem",
    "GenericCraftingSurface": "", "GroupName": "Badlands Medical",
    "IsMoveAble": "", "IsTable": "", "IsTableTop": "",
    "Material": "Wood", "Material2": "SmallMetalPlates", "MaterialType": "Wood",
    "PickUpWeight": "120", "ScrapSize": "Medium", "Surface": "60",
    "container": "medicine", "solidtrans": "",
}
OBJECTS = [
    ("medtable", "Medical Table", "60", TABLE_PROPS),
]


class Builder:
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

    # Canvas tarp: weave, not wood grain, so the strokes run both ways and stay
    # shallow. A coarse spec here reads as burlap sacking.
    spec = material_spec("wood", seed=71)
    spec = dataclasses.replace(
        spec,
        octaves=[(size, amplitude * 0.09) for size, amplitude in spec.octaves],
        contrast=1.06, stroke_count=120, stroke_amplitude=0.035,
        knot_count=0, knot_depth=0.0,
    )
    write_surface_map(GRAIN_PATH, 512, 512, spec)
    mspec = material_spec("metal", seed=21)
    mspec = dataclasses.replace(
        mspec,
        octaves=[(size, amplitude * 0.35) for size, amplitude in mspec.octaves],
    )
    write_surface_map(METAL_PATH, 512, 512, mspec)


def materials() -> dict:
    t = F.toon_material
    return {
        "tarp": t("md_tarp", TARP),
        "tarp_dark": t("md_tarp_dark", tuple(c * 0.74 for c in TARP)),
        "tarp_fold": t("md_tarp_fold", tuple(c * 0.88 for c in TARP)),
        "steel": F.forge_material("md_steel", "metal", STEEL, texture_path=str(METAL_PATH)),
        # Everything on the table is packaging: flat toon paint, no grain.
        "white": t("md_white", (0.780, 0.780, 0.765)),
        "paper": t("md_paper", (0.720, 0.710, 0.680)),
        "card": t("md_card", (0.560, 0.410, 0.230)),
        "card_dark": t("md_card_dark", (0.430, 0.310, 0.170)),
        "blue": t("md_blue", (0.180, 0.330, 0.580)),
        "teal": t("md_teal", (0.130, 0.450, 0.440)),
        "violet": t("md_violet", (0.380, 0.260, 0.480)),
        "green": t("md_green", (0.330, 0.560, 0.330)),
        "saline": t("md_saline", (0.620, 0.740, 0.640)),
        "amber": t("md_amber", (0.620, 0.420, 0.120)),
        "red": t("md_red", (0.600, 0.180, 0.150)),
        "grey": t("md_grey", (0.440, 0.440, 0.430)),
        "black": t("md_black", (0.095, 0.095, 0.105)),
        "towel": [t("md_towel_%d" % i, p) for i, p in enumerate([
            (0.520, 0.620, 0.560), (0.640, 0.560, 0.470), (0.480, 0.560, 0.640),
            (0.660, 0.620, 0.520)])],
    }


TOP = 0.760          # tarp surface: what everything stands on


def build_table(b, m) -> None:
    """The carcass: folding table, tarp over it, and nothing else. Every stage
    keeps this, so it is what a stripped table looks like."""
    W, D, H = 0.960, 0.560, 0.720
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.cyl(f"leg_{sx}_{sy}", (sx * (W / 2 - 0.06), sy * (D / 2 - 0.06), H / 2),
                  0.018, H, m["steel"], vertices=10)
        b.box(f"brace_{sx}", (sx * (W / 2 - 0.06), 0.0, 0.18), (0.024, D - 0.12, 0.024),
              m["steel"])
    b.box("top", (0.0, 0.0, H + 0.018), (W, D, 0.036), m["paper"])
    # the tarp: over the top, down the front, a fold at each end
    b.box("tarp_top", (0.0, 0.0, H + 0.041), (W + 0.02, D + 0.02, 0.014), m["tarp"])
    b.box("tarp_front", (0.0, -D / 2 - 0.012, H - 0.12), (W + 0.02, 0.016, 0.280),
          m["tarp_dark"])
    for sx in (-1, 1):
        b.box(f"tarp_side_{sx}", (sx * (W / 2 + 0.006), 0.0, H + 0.005),
              (0.012, D, 0.075), m["tarp_dark"])
    for i, x in enumerate((-0.26, 0.10, 0.34)):
        b.box(f"tarp_fold_{i}", (x, 0.0, H + 0.049), (0.020, D + 0.01, 0.006),
              m["tarp_fold"], rot=(0.0, 0.0, 0.05 if i % 2 else -0.04))
    b.box("tarp_hem", (0.0, -D / 2 - 0.016, H - 0.255), (W + 0.02, 0.020, 0.030),
          m["tarp"])


def stack_boxes(b, m, tag, x, y, z, count, size, colours, band=None):
    """A stack of cartons, each turned a little off square."""
    w, d, h = size
    for i in range(count):
        yaw = (0.05 if i % 2 else -0.04) * (i + 1) * 0.5
        zz = z + h / 2 + i * h
        b.box(f"item_{tag}_{i}", (x, y, zz), (w, d, h), m[colours[i % len(colours)]],
              rot=(0.0, 0.0, yaw))
        if band:
            b.box(f"item_{tag}_{i}_band", (x, y - d / 2 - 0.002, zz),
                  (w * 0.72, 0.004, h * 0.34), m[band], rot=(0.0, 0.0, yaw))


def build_contents(b, m) -> None:
    """The spread, laid out like the photo: cartons and linen at the left,
    bottles and tape through the middle, the small valuable things at the right,
    boxes stacked under the table."""
    z = TOP

    # -- left: glove cartons and folded towels
    stack_boxes(b, m, "gloves0", -0.400, 0.105, z, 3, (0.150, 0.100, 0.052),
                ["blue", "violet", "white"], band="white")
    stack_boxes(b, m, "gloves1", -0.395, -0.095, z, 3, (0.150, 0.100, 0.052),
                ["teal", "white", "blue"], band="white")
    for i in range(4):
        b.box(f"item_towel_{i}", (-0.215, 0.090, z + 0.013 + i * 0.026),
              (0.170, 0.120, 0.026), m["towel"][i % 4],
              rot=(0.0, 0.0, 0.04 if i % 2 else -0.03))

    # -- middle: bottles, tape rolls, a stack of kidney trays
    for i in range(6):
        x = -0.115 + (i % 3) * 0.076
        y = 0.090 - (i // 3) * 0.105
        b.cyl(f"item_bottle_{i}", (x, y, z + 0.065), 0.028, 0.130, m["white"], vertices=12)
        b.cyl(f"item_bottle_{i}_cap", (x, y, z + 0.138), 0.020, 0.018,
              m[("blue", "red", "teal")[i % 3]], vertices=12)
    for i in range(3):
        b.cyl(f"item_tape_{i}", (-0.070 + i * 0.012, -0.170, z + 0.020 + i * 0.038),
              0.042, 0.036, m["white"], rot=(0.0, 0.0, 0.0), vertices=16)
        b.cyl(f"item_tape_{i}_core", (-0.070 + i * 0.012, -0.170, z + 0.020 + i * 0.038),
              0.018, 0.038, m["card"], vertices=12)

    # -- right: saline bags leaning against a carton, syringes, vials, blisters
    for i in range(3):
        b.box(f"item_saline_{i}", (0.255 + i * 0.050, 0.120, z + 0.100),
              (0.130, 0.030, 0.200), m["saline"], rot=(0.22, 0.0, 0.04 * i))
        b.box(f"item_saline_{i}_label", (0.255 + i * 0.050, 0.102, z + 0.150),
              (0.090, 0.004, 0.050), m["green"], rot=(0.22, 0.0, 0.04 * i))
    for i in range(6):
        b.cyl(f"item_syringe_{i}", (0.190, -0.130 + i * 0.016, z + 0.010),
              0.008, 0.115, m["white"], rot=(0.0, 1.5708, 0.06 * i), vertices=8)
    for i in range(6):
        b.cyl(f"item_vial_{i}", (0.330 + (i % 3) * 0.028, -0.055 - (i // 3) * 0.032,
                                 z + 0.020), 0.012, 0.040, m["amber"], vertices=10)
    for i in range(5):
        b.box(f"item_blister_{i}", (0.060 + (i % 3) * 0.052, -0.090 - (i // 3) * 0.040,
                                    z + 0.004), (0.048, 0.032, 0.008),
              m[("red", "teal", "blue", "green", "violet")[i]],
              rot=(0.0, 0.0, 0.10 * i))

    for i in range(3):
        b.box(f"item_towelr_{i}", (0.430, 0.115, z + 0.013 + i * 0.026),
              (0.150, 0.110, 0.026), m["towel"][(i + 2) % 4],
              rot=(0.0, 0.0, -0.05 if i % 2 else 0.04))

    # -- the kit at the front edge: cuff and stethoscope, like the photo
    b.box("item_cuff_0", (-0.030, -0.190, z + 0.018), (0.110, 0.070, 0.036), m["black"])
    b.cyl("item_cuff_0_bulb", (0.040, -0.200, z + 0.020), 0.018, 0.045, m["black"],
          rot=(0.0, 1.5708, 0.0), vertices=10)
    b.torus("item_steth_0", (-0.170, -0.195, z + 0.012), 0.055, 0.007, m["black"])
    b.cyl("item_steth_0_head", (-0.170, -0.255, z + 0.012), 0.022, 0.012, m["steel"],
          vertices=12)

    # -- cartons on the table and boxes under it
    stack_boxes(b, m, "carton0", 0.420, -0.135, z, 2, (0.170, 0.130, 0.095),
                ["card", "card_dark"], band="white")
    stack_boxes(b, m, "floor0", -0.300, -0.010, 0.0, 2, (0.230, 0.180, 0.150),
                ["card", "card_dark"], band="paper")
    stack_boxes(b, m, "floor1", 0.010, 0.060, 0.0, 3, (0.200, 0.160, 0.120),
                ["card_dark", "card", "card"], band="paper")
    stack_boxes(b, m, "floor2", 0.310, -0.040, 0.0, 2, (0.210, 0.170, 0.135),
                ["card", "card_dark"], band="paper")


def build_medtable(b, m) -> None:
    build_table(b, m)
    build_contents(b, m)


def unit_of(name):
    """The physical thing a part belongs to. Parts are named
    item_<tag>_<index>[_<part>], so the first three tokens are the unit: a
    carton and its tape band share one, and the cut can never separate them."""
    return "_".join(name.split("_")[:3])


def in_group(name, group):
    """A group token matches a tag exactly, or exactly plus a number -- so
    "bag" still catches bag0, but "towel" no longer swallows towelr."""
    tag = name.split("_")[1] if name.count("_") >= 2 else ""
    return tag == group or (tag.startswith(group) and tag[len(group):].isdigit())


def order_medical(names):
    """What a scavenger clears first: drugs and sharps, then fluids, then
    consumables, then the heavy cardboard nobody wants to carry."""
    groups = ("vial", "blister", "syringe", "saline", "bottle", "tape",
              "cuff", "steth", "gloves0", "gloves1", "towelr", "towel", "carton0",
              "floor2", "floor0", "floor1")
    out = []
    for g in groups:
        picked = sorted(n for n in names if in_group(n, g))
        out += picked
    return out


BUILDERS = [(build_medtable, order_medical)]


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
    for group, ((key, cname, cap, base), (build, order)) in enumerate(zip(OBJECTS, BUILDERS)):
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

        states = []
        # Space the stages by visual mass, not part count: the narrative order
        # clears sharps and vials first, and a dozen of those weigh less on
        # screen than one carton. Cut where the cumulative silhouette says to.
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
        gone = 0
        for stage in range(STAGES):
            target = total * stage / (STAGES - 1)
            want = sum(1 for c in cum if c <= target + 1e-9)
            if want < gone:
                want = gone
            drop([n for u in units[gone:want] for n in u])
            gone = want
            states.append(render(props, f"md_{key}_{stage}"))
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
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
