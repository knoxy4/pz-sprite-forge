"""BADLANDS theater: the VCR Stack and the Wall Tape Rack.

Both are storage that shows its stock, the bookcase pattern: one carcass, three
appearances (stocked / picked over / stripped), rendered as one model with the
tapes deleted between passes so the silhouette never moves. Sheet layout is the
mod's usual twelve per piece, facing-major and stock-descending inside a facing,
which is what `KNXBookcase.lua` already reads:

    0..11   VCR Stack        S F H E  E F H E  N F H E  W F H E
    12..23  Wall Tape Rack   same

The stack is also the theater's patch bay (KNXVCR.lua): it holds the tapes and
loads them into the TVs in the room. The art therefore has to read as decks plus
a library, not as a cabinet.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_theater.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "theater_cells"
#: Fill stages per piece, fullest first. The mod's older sheets use three;
#: ten is what the operator asked for here, and the Lua reads the count off
#: the sheet table rather than assuming.
STAGES = 10
SHEET = "badlands_theater_01"
GRAIN_PATH = ROOT / "build" / "theater_laminate_grain.png"
METAL_PATH = ROOT / "build" / "theater_steel.png"

# Registration is the bookcase's, so every Badlands storage piece lines up.
OFFSET_Y = 0.206
OFFSET_Z = -2.0 / 77.2

LAMINATE = (0.165, 0.092, 0.052)    # dark walnut veneer, the 80s AV cabinet
PINE = (0.600, 0.430, 0.235)        # weathered plank: the bright pine read as fresh sawn
STEEL = (0.300, 0.305, 0.300)

# A VHS cassette is 187 x 103 x 25 mm. Standing spine-out on a shelf that is
# 25 mm of width and 103 mm of height, which is what the sprite shows.
TAPE_W, TAPE_D, TAPE_H = 0.025, 0.187, 0.103

WOOD_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "",
    "ContainerPutSound": "ShelfWoodTransferItem",
    "ContainerTakeSound": "ShelfWoodTransferItem",
    "GroupName": "Badlands Theater", "IsMoveAble": "",
    "Material": "Wood", "Material2": "Screws", "MaterialType": "Wood",
    "PickUpTool": "Hammer", "PickUpWeight": "200", "PlaceTool": "Hammer",
    "ScrapSize": "Large", "Surface": "80", "container": "shelves", "solid": "",
}
# The wall rack hangs: no floor footprint to stand on, so no solid and no
# Surface (nothing can be set down on a rack of spines).
RACK_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "",
    "ContainerPutSound": "ShelfWoodTransferItem",
    "ContainerTakeSound": "ShelfWoodTransferItem",
    "GroupName": "Badlands Theater", "IsMoveAble": "",
    "Material": "Wood", "Material2": "Screws", "MaterialType": "Wood",
    "PickUpTool": "Hammer", "PickUpWeight": "60", "PlaceTool": "Hammer",
    "ScrapSize": "Small", "container": "shelves",
}
# Cloned from vanilla desk electronics -- appliances_television_01_4 (TvBlack)
# and appliances_com_01_0 (ham radio). IsTableTop is what makes it a thing that
# lives on a table, IsSurfaceOffset lifts the sprite to that table's Surface
# height, IsMoveAble + PickUpWeight is what lets you carry it there, and no
# PickUpTool because a television does not ask for a hammer either. No Surface
# of its own: nothing balances on a pile of cassettes.
STACK_PROPS = {
    "BlocksPlacement": "",
    "CanScrap": "",
    "ContainerPutSound": "ShelfWoodTransferItem",
    "ContainerTakeSound": "ShelfWoodTransferItem",
    "GroupName": "Badlands Theater",
    "IsMoveAble": "",
    "IsSurfaceOffset": "",
    "IsTableTop": "",
    "Material": "Electric",
    "MaterialType": "Metal_Light",
    "PickUpWeight": "90",
    "ScrapSize": "Medium",
    "container": "shelves",
    "solidtrans": "",
}
OBJECTS = [
    # key, CustomName, capacity, base props
    ("vcr", "VCR Stack", "50", STACK_PROPS),
    ("taperack", "Wall Tape Rack", "20", RACK_PROPS),
]


class Builder:
    """Collects the parts of one object, offset to hug the back of its tile."""

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
                                         major_segments=24, minor_segments=8,
                                         location=loc)
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)


def make_textures() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    # Veneer, not barn board. The first render read as a shipping crate: the
    # bookcase's grain settings are still too coarse for a laminate panel, so
    # every amplitude here is roughly half of those, with no knot at all.
    spec = material_spec("wood", seed=57)
    spec = dataclasses.replace(
        spec,
        octaves=[(size, amplitude * 0.055) for size, amplitude in spec.octaves],
        contrast=1.04, stroke_count=40, stroke_amplitude=0.028,
        knot_count=0, knot_depth=0.0,
    )
    write_surface_map(GRAIN_PATH, 512, 512, spec, grain_axis="v")
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
        "laminate": F.forge_material("th_lam", "wood", LAMINATE, texture_path=grain),
        "laminate_trim": F.forge_material("th_lam_trim", "wood",
                                          tuple(c * 0.72 for c in LAMINATE),
                                          texture_path=grain),
        "laminate_back": F.forge_material("th_lam_back", "wood",
                                          tuple(c * 0.30 for c in LAMINATE)),
        "pine": F.forge_material("th_pine", "wood", PINE, texture_path=grain),
        "pine_trim": F.forge_material("th_pine_trim", "wood",
                                      tuple(c * 0.80 for c in PINE), texture_path=grain),
        "steel": F.forge_material("th_steel", "metal", STEEL, texture_path=steel),
        # Consumer electronics are flat moulded plastic: toon paint, no grain.
        "deck": t("th_deck", (0.085, 0.085, 0.095)),
        # The faceplate has to out-read the cabinet at 128 px, so it sits well
        # above the body in value instead of a shade off it.
        "deck_face": t("th_deck_face", (0.255, 0.255, 0.275)),
        # One of the six is the silver one somebody scavenged from a different
        # house. No wood finishes: the operator wants machines, not furniture.
        "deck_silver": t("th_deck_silver", (0.300, 0.300, 0.295)),
        "slot": t("th_slot", (0.030, 0.030, 0.035)),
        "dial": t("th_dial", (0.165, 0.165, 0.175)),
        "display": t("th_display", (0.100, 0.320, 0.300)),
        "led_red": t("th_led_red", (0.720, 0.090, 0.070)),
        "led_green": t("th_led_green", (0.180, 0.620, 0.200)),
        "silver": t("th_silver", (0.480, 0.480, 0.470)),
        "cable": t("th_cable", (0.060, 0.060, 0.065)),
        "shell": t("th_shell", (0.070, 0.070, 0.080)),
        # Spine labels. Muted print colours so a row of them reads as a library
        # at 128 px instead of a fruit salad.
        "label": [t("th_label_%d" % i, p) for i, p in enumerate([
            (0.760, 0.720, 0.620), (0.560, 0.130, 0.110), (0.150, 0.260, 0.450),
            (0.620, 0.470, 0.120), (0.200, 0.330, 0.200), (0.400, 0.220, 0.380),
        ])],
    }


def tape_tower(b, m, tag, x, y, z0, count, pitch=0.0265):
    """Cassettes lying flat in a column, label edge to the front.

    This is the operator's reference photo: two towers of tapes flanking the
    machines, every one of them showing the white strip on its 187 x 25 front
    edge. Spine-out (render one) read as pistol magazines; face-out (render
    four) read as colour swatches. The flat edge with a label is the shape a
    person recognises as a video tape.
    """
    for i in range(count):
        jog = 0.008 if i % 3 == 1 else (-0.006 if i % 3 == 2 else 0.0)
        yaw = 0.02 if i % 4 == 1 else (-0.015 if i % 4 == 3 else 0.0)
        z = z0 + TAPE_W / 2 + i * pitch
        b.box(f"item_{tag}_{i}", (x + jog, y, z), (TAPE_D, TAPE_H, TAPE_W),
              m["shell"], rot=(0.0, 0.0, yaw))
        # The label: a strip on the front edge, inset from both ends the way a
        # stuck-on label sits, in cream with the odd coloured sleeve.
        b.box(f"item_{tag}label_{i}", (x + jog, y - TAPE_H / 2 - 0.002, z),
              (TAPE_D * 0.72, 0.004, TAPE_W * 0.58),
              m["label"][0] if i % 5 else m["label"][(i // 5) % len(m["label"])],
              rot=(0.0, 0.0, yaw))


def deck(b, m, tag, x, y, z, yaw=0.0, body="deck", face="deck_face"):
    """One VCR, 430 x 300 x 98 mm: black box, long tape slot, a big jog dial on
    the right and a row of small buttons. The dial is the tell -- at tile scale
    it is the one detail that says video recorder rather than shelf."""
    W, D, H = 0.430, 0.300, 0.098
    b.box(f"{tag}_body", (x, y, z + H / 2), (W, D, H), m[body], rot=(0.0, 0.0, yaw))
    b.box(f"{tag}_face", (x, y - D / 2 + 0.006, z + H / 2), (W, 0.012, H * 0.88),
          m[face], rot=(0.0, 0.0, yaw))
    # a seam under each machine, so a column of six does not fuse into a brick
    b.box(f"{tag}_seam", (x, y, z - 0.006), (W * 0.98, D * 0.98, 0.012), m["slot"],
          rot=(0.0, 0.0, yaw))
    b.box(f"{tag}_slot", (x - 0.045, y - D / 2 + 0.000, z + H * 0.60),
          (0.230, 0.008, 0.015), m["slot"], rot=(0.0, 0.0, yaw))
    b.box(f"{tag}_band", (x - 0.045, y - D / 2 - 0.001, z + H * 0.36),
          (0.230, 0.005, 0.005), m["silver"], rot=(0.0, 0.0, yaw))
    b.cyl(f"{tag}_dial", (x + 0.158, y - D / 2 - 0.002, z + H * 0.46), 0.030, 0.014,
          m["dial"], rot=(1.5708, 0.0, yaw), vertices=18)
    b.cyl(f"{tag}_dialcap", (x + 0.158, y - D / 2 - 0.009, z + H * 0.46), 0.012, 0.006,
          m["deck_face"], rot=(1.5708, 0.0, yaw), vertices=14)
    for j in range(4):
        b.box(f"{tag}_btn_{j}", (x - 0.185 + j * 0.026, y - D / 2 - 0.001, z + H * 0.30),
              (0.016, 0.005, 0.009), m["silver"], rot=(0.0, 0.0, yaw))
    b.cyl(f"{tag}_led", (x + 0.070, y - D / 2 - 0.001, z + H * 0.30), 0.005, 0.005,
          m["led_green"] if tag.endswith("0") else m["led_red"],
          rot=(1.5708, 0.0, yaw), vertices=10)


def build_vcr(b, m) -> None:
    """Six machines in a column with a tower of tapes stacked either side, the
    way the operator's photo has it. No pallet and no wood: it stands on the
    floor or, picked up and placed like any moveable, on a table."""
    DH = 0.098
    for k in range(6):
        yaw = (0.0, 0.022, -0.016, 0.028, -0.012, 0.018)[k]
        jog = (0.0, 0.014, -0.010, 0.016, -0.008, 0.006)[k]
        body = "deck_silver" if k == 3 else "deck"
        deck(b, m, f"deckA{k}", jog, 0.0, k * DH, yaw=yaw, body=body)

    # Cabling: a loom out of the back of the pile, a lead dropping down the
    # right side and one dumped in front, which is what the photo shows.
    b.cyl("loom", (0.05, 0.150, 0.30), 0.016, 0.58, m["cable"], rot=(0.10, 0.0, 0.0))
    b.cyl("lead_r", (0.235, 0.120, 0.22), 0.013, 0.46, m["cable"], rot=(-0.22, 0.0, 0.0))
    b.cyl("lead_f", (0.155, -0.145, 0.045), 0.012, 0.30, m["cable"], rot=(0.0, 1.5708, 0.35))
    b.torus("coil", (-0.30, -0.115, 0.014), 0.060, 0.012, m["cable"])
    b.cyl("aerial", (0.300, 0.120, 0.62), 0.005, 0.52, m["silver"], rot=(0.14, 0.0, 0.0))

    # the two towers, tall enough to top the machines like the photo
    tape_tower(b, m, "left", -0.318, -0.005, 0.0, 22)
    tape_tower(b, m, "right", 0.318, -0.005, 0.0, 22)
    # and the pile somebody left on top
    tape_tower(b, m, "crown", -0.02, -0.055, 6 * DH, 4)


def build_taperack(b, m) -> None:
    """Two planks on cleats at eye level: four short stacks of tapes to a
    plank, label edges out, same read as the towers on the stack."""
    W = 0.86
    for z in (1.16, 1.50):
        b.box(f"plank_{int(z * 100)}", (0.0, 0.0, z), (W, 0.16, 0.024), m["pine"])
        b.box(f"lip_{int(z * 100)}", (0.0, -0.075, z + 0.022), (W, 0.012, 0.022),
              m["pine_trim"])
        for sx in (-1, 1):
            b.box(f"cleat_{int(z * 100)}_{sx}", (sx * (W / 2 - 0.02), 0.055, z - 0.045),
                  (0.030, 0.050, 0.110), m["pine_trim"])
            b.cyl(f"screw_{int(z * 100)}_{sx}", (sx * (W / 2 - 0.02), 0.020, z - 0.020),
                  0.006, 0.014, m["steel"], rot=(1.5708, 0.0, 0.0))
    for k, x in enumerate((-0.300, -0.100, 0.100, 0.300)):
        tape_tower(b, m, f"top{k}", x, -0.005, 1.512, 4)
        tape_tower(b, m, f"bot{k}", x, -0.005, 1.172, 4)


def _tower_order(names, tag, reverse=True):
    """One tower's tapes, top first: a hand takes what it can reach."""
    picked = [n for n in names if n.startswith(f"item_{tag}_")]
    picked.sort(key=lambda n: int(n.rsplit("_", 1)[-1]), reverse=reverse)
    return picked


def order_vcr(names):
    """The loose pile off the top, then the two towers taken down in turns,
    alternating so the stack empties unevenly the way a real one does."""
    out = _tower_order(names, "crown")
    left = _tower_order(names, "left")
    right = _tower_order(names, "right")
    for i in range(max(len(left), len(right))):
        if i < len(right):
            out.append(right[i])
        if i < len(left):
            out.append(left[i])
    return out


def order_rack(names):
    """Eye level goes first, then the top shelf, then the bottom."""
    out = []
    for tag in ("top1", "top2", "top0", "top3", "bot1", "bot2", "bot0", "bot3"):
        out += _tower_order(names, tag)
    return out


BUILDERS = [(build_vcr, order_vcr), (build_taperack, order_rack)]


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
    for group, ((key, cname, cap, base), (build, order)) in enumerate(zip(OBJECTS, BUILDERS)):
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
        # Labels follow their tape: they are separate objects, so the order has
        # to carry both or a stripped shelf keeps its floating stickers.
        seq = []
        for n in order(items):
            seq.append(n)
            label = n.replace("item_", "item_", 1)
            label = label.rsplit("_", 1)
            label = f"{label[0]}label_{label[1]}"
            if label in items:
                seq.append(label)
        seq += [n for n in items if n not in seq]

        def drop(names):
            for n in names:
                obj = bpy.data.objects.get(n)
                if obj is not None:
                    bpy.data.objects.remove(obj, do_unlink=True)

        states = []
        gone = 0
        for stage in range(STAGES):
            # stage 0 is full, stage STAGES-1 is bare; everything between is an
            # even slice of the removal order.
            want = round(len(seq) * stage / (STAGES - 1))
            drop(seq[gone:want])
            gone = want
            states.append(render(props, f"th_{key}_{stage}"))
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
