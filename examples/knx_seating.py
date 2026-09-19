"""BADLANDS makeshift seating: three post-collapse recliners for the Badlands furniture mod.

    group 0  Pallet Recliner     salvaged car seat bolted to stacked pallets, crate footrest,
                                 duct-taped vinyl, blanket over the arm
    group 1  Tire Chair          two stacked tires, sewn denim cushion, lashed plank backrest
    group 2  Patchwork Armchair  plank frame upholstered in tarp and leather scraps

Sheet badlands_seating_01, subject-major via the group stamp: index // 4 is the
chair, index % 4 the facing S,E,N,W.  Seats have no fill state, so one render
each.  Size and placement are vanilla's own recliner, furniture_seating_indoor_02_44
("Brown Lazy"): centred in the tile, trim box ~121x122 at the 2x cell bottom.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_seating.py
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

OUT = ROOT / "build" / "seating_cells"
SHEET = "badlands_seating_01"
GRAIN_PATH = ROOT / "build" / "seating_pallet_grain.png"
FABRIC_PATH = ROOT / "build" / "seating_fabric.png"
OFFSET_Z = -2.0 / 77.2

# Cloned from vanilla furniture_seating_indoor_02_44 (Brown Lazy), less the
# livingRoom room tag.  The chair<Facing> key is added per cell.
SEAT_PROPS = {
    "BlocksPlacement": "", "CanBreak": "", "CanScrap": "", "IsLow": "",
    "IsMoveAble": "", "Material": "Wood", "Material2": "Nails",
    "Material3": "Fabric", "MaterialType": "Fabric", "PickUpWeight": "75",
    "ScrapSize": "Small", "Surface": "17", "bed": "", "solidtrans": "",
    "GroupName": "Badlands Makeshift",
}
CHAIRS = [
    ("recliner", "Pallet Recliner", "averageBed"),
    ("tire", "Tire Chair", "badBed"),
    ("patchwork", "Patchwork Armchair", "averageBed"),
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

    def torus(self, name, centre, major, minor, material):
        bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                         major_segments=28, minor_segments=10,
                                         location=(centre[0], centre[1], centre[2] + OFFSET_Z))
        return self._place(bpy.context.active_object, name, material)


def make_textures() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    # weathered pallet stock: a touch louder than the bookcase oak.  The first cut
    # (octaves x0.30, strokes 0.10, 2 knots) blotched into camo at tile scale.
    spec = material_spec("wood", seed=77)
    spec = dataclasses.replace(
        spec, octaves=[(s, a * 0.13) for s, a in spec.octaves],
        stroke_count=90, stroke_amplitude=0.06, knot_count=1, knot_depth=0.06)
    write_surface_map(GRAIN_PATH, 512, 512, spec, grain_axis="v")
    write_surface_map(FABRIC_PATH, 512, 512, material_spec("fabric", seed=5))


def materials() -> dict:
    grain, cloth = str(GRAIN_PATH), str(FABRIC_PATH)
    fab = lambda n, c: F.forge_material(n, "fabric", c, texture_path=cloth)
    t = F.toon_material
    PALLET = (0.600, 0.450, 0.270)
    return {
        # The wood class swings paint 0.40-1.60x across the grain map: right for dark
        # oak, camo on pale pallet pine.  Narrowed to a planed-lumber swing here.
        "pallet": F.forge_material("st_pallet", "wood", PALLET, texture_path=grain,
                                   swing=(0.82, 1.12)),
        "pallet_dark": F.forge_material("st_pallet_dark", "wood",
                                        tuple(c * 0.62 for c in PALLET), texture_path=grain,
                                        swing=(0.82, 1.12)),
        "plank": F.forge_material("st_plank", "wood", (0.66, 0.50, 0.30), texture_path=grain,
                                  swing=(0.82, 1.12)),
        "vinyl": fab("st_vinyl", (0.17, 0.17, 0.19)),
        "vinyl_dark": t("st_vinyl_dark", (0.09, 0.09, 0.10)),
        "tape": t("st_tape", (0.58, 0.58, 0.56)),
        "blanket": fab("st_blanket", (0.58, 0.20, 0.07)),
        "blanket_stripe": t("st_blanket_stripe", (0.72, 0.62, 0.32)),
        "pillow": fab("st_pillow", (0.70, 0.66, 0.55)),
        "rubber": t("st_rubber", (0.085, 0.085, 0.090)),
        "rubber_tread": t("st_rubber_tread", (0.050, 0.050, 0.055)),
        "denim": fab("st_denim", (0.17, 0.25, 0.40)),
        "denim_dark": t("st_denim_dark", (0.10, 0.15, 0.25)),
        "rope": t("st_rope", (0.62, 0.52, 0.32)),
        "tarp": fab("st_tarp", (0.10, 0.24, 0.52)),
        "leather": fab("st_leather", (0.36, 0.17, 0.07)),
        "canvas": fab("st_canvas", (0.34, 0.36, 0.20)),
        "stitch": t("st_stitch", (0.80, 0.76, 0.62)),
        "steel": t("st_steel", (0.30, 0.30, 0.30)),
    }


def pallet(b: Builder, m: dict, tag: str, z: float, w: float = 0.88) -> None:
    """A standard pallet: three stringers, five top boards, three bottom boards."""
    h = 0.13
    for i, y in enumerate((-w / 2 + 0.05, 0.0, w / 2 - 0.05)):
        b.box(f"{tag}_bot_{i}", (0, y, z + 0.01), (w, 0.10, 0.02), m["pallet_dark"])
    for i, x in enumerate((-w / 2 + 0.035, 0.0, w / 2 - 0.035)):
        b.box(f"{tag}_str_{i}", (x, 0, z + 0.02 + 0.045), (0.07, w, 0.09), m["pallet_dark"])
    for i in range(5):
        y = -w / 2 + 0.05 + i * (w - 0.10) / 4
        b.box(f"{tag}_top_{i}", (0, y, z + h - 0.01), (w, 0.10, 0.02), m["pallet"])


def leaning(b, name, y0, z0, size, angle, material, x=0.0):
    """A slab hinged at its bottom edge (y0, z0) and leaned back by ``angle``."""
    h = size[2]
    centre = (x, y0 + h / 2 * math.sin(angle), z0 + h / 2 * math.cos(angle))
    return b.box(name, centre, size, material, rot=(-angle, 0.0, 0.0))


def build_recliner(b: Builder, m: dict) -> None:
    pallet(b, m, "p0", 0.0)
    pallet(b, m, "p1", 0.13)
    top = 0.26
    # the salvaged car seat, set on the back two-thirds of the pallets
    b.box("seat_base", (0, 0.10, top + 0.02), (0.56, 0.52, 0.04), m["steel"])  # seat rails
    b.box("seat", (0, 0.10, top + 0.11), (0.52, 0.50, 0.14), m["vinyl"])
    for sx in (-1, 1):
        b.box(f"bolster_{sx}", (sx * 0.23, 0.10, top + 0.19), (0.08, 0.48, 0.06), m["vinyl_dark"])
    recline = 0.42
    back = leaning(b, "backrest", 0.33, top + 0.16, (0.52, 0.13, 0.62), recline, m["vinyl"])
    for sx in (-1, 1):
        leaning(b, f"back_bolster_{sx}", 0.30, top + 0.16, (0.07, 0.10, 0.60), recline,
                m["vinyl_dark"], x=sx * 0.235)
    hz = top + 0.16 + 0.66 * math.cos(recline)
    hy = 0.33 + 0.66 * math.sin(recline)
    b.box("headrest", (0, hy + 0.02, hz + 0.08), (0.26, 0.11, 0.15), m["vinyl"],
          rot=(-recline, 0, 0))
    # duct tape: one strip across the seat, a cross patch on the back
    b.box("tape_seat", (0.04, 0.02, top + 0.185), (0.50, 0.05, 0.006), m["tape"])
    leaning(b, "tape_back_a", 0.262, top + 0.36, (0.20, 0.004, 0.05), recline, m["tape"], x=-0.08)
    leaning(b, "tape_back_b", 0.262, top + 0.30, (0.05, 0.004, 0.20), recline, m["tape"], x=-0.08)
    # 2x4 arms on posts
    for sx in (-1, 1):
        b.box(f"arm_{sx}", (sx * 0.34, 0.06, top + 0.30), (0.08, 0.60, 0.05), m["plank"])
        b.box(f"arm_post_{sx}", (sx * 0.34, -0.20, top + 0.14), (0.07, 0.07, 0.28), m["plank"])
    # blanket over the left arm
    b.box("blanket_top", (-0.34, 0.06, top + 0.335), (0.14, 0.46, 0.018), m["blanket"])
    b.box("blanket_fall", (-0.415, 0.06, top + 0.18), (0.018, 0.44, 0.32), m["blanket"])
    b.box("blanket_stripe", (-0.425, 0.06, top + 0.08), (0.004, 0.44, 0.03), m["blanket_stripe"])
    # crate footrest with a pillow on it
    b.box("crate", (0, -0.30, top + 0.09), (0.44, 0.24, 0.18), m["pallet"])
    b.box("crate_slot", (0, -0.421, top + 0.11), (0.30, 0.004, 0.05), m["pallet_dark"])
    b.box("footrest_pillow", (0, -0.30, top + 0.21), (0.40, 0.22, 0.07), m["pillow"])


def build_tire(b: Builder, m: dict) -> None:
    for i, z in enumerate((0.10, 0.30)):
        b.torus(f"tire_{i}", (0, 0, z), 0.30, 0.10, m["rubber"])
        b.cyl(f"tread_{i}", (0, 0, z), 0.405, 0.12, m["rubber_tread"], vertices=28)
    # tread cylinder sits just inside the torus bulge: it reads as the tread band
    b.cyl("ply", (0, 0, 0.415), 0.36, 0.025, m["plank"], vertices=28)
    b.cyl("cushion", (0, -0.02, 0.465), 0.33, 0.085, m["denim"], vertices=28)
    for k, (x, y) in enumerate(((-0.12, -0.10), (0.12, -0.10), (0.0, 0.08))):
        b.cyl(f"tuft_{k}", (x, y, 0.510), 0.018, 0.006, m["denim_dark"])
    lean = 0.18
    for sx in (-1, 1):
        leaning(b, f"upright_{sx}", 0.30, 0.40, (0.07, 0.05, 0.66), lean, m["plank"], x=sx * 0.22)
    for k, zz in enumerate((0.60, 0.95)):
        leaning(b, f"cross_{k}", 0.30, zz, (0.52, 0.04, 0.06), lean, m["plank"])
    leaning(b, "back_cushion", 0.26, 0.52, (0.46, 0.10, 0.42), lean, m["denim"])
    for k, zz in enumerate((0.60, 0.86)):
        leaning(b, f"lash_{k}", 0.205, zz, (0.50, 0.015, 0.025), lean, m["rope"])


def build_patchwork(b: Builder, m: dict) -> None:
    b.box("frame", (0, 0.02, 0.17), (0.84, 0.80, 0.30), m["plank"])
    for k in range(3):  # board seams on the front face
        b.box(f"seam_{k}", (0, -0.381, 0.07 + k * 0.10), (0.84, 0.004, 0.008), m["pallet_dark"])
    b.box("seat", (0, -0.02, 0.39), (0.60, 0.62, 0.14), m["tarp"])
    b.box("seat_patch", (0.12, -0.14, 0.462), (0.20, 0.18, 0.008), m["leather"])
    b.box("seat_stitch", (0.12, -0.232, 0.462), (0.20, 0.004, 0.009), m["stitch"])
    lean = 0.26
    patches = [("tarp", -0.155, 0.46), ("leather", 0.155, 0.46),
               ("canvas", -0.155, 0.74), ("denim", 0.155, 0.74)]
    for k, (mat, x, z0) in enumerate(patches):
        leaning(b, f"back_{k}", 0.30, z0, (0.30, 0.17, 0.28), lean, m[mat], x=x)
    leaning(b, "back_seam_v", 0.214, 0.46, (0.012, 0.004, 0.56), lean, m["stitch"])
    for sx in (-1, 1):
        b.box(f"arm_{sx}", (sx * 0.36, 0.02, 0.43), (0.12, 0.78, 0.26), m["leather"])
        b.box(f"arm_cap_{sx}", (sx * 0.36, 0.02, 0.565), (0.13, 0.78, 0.02), m["canvas"])


BUILDERS = {"recliner": build_recliner, "tire": build_tire, "patchwork": build_patchwork}


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
    for group, (key, cname, bed) in enumerate(CHAIRS):
        if only and key != only:
            continue
        b = Builder()
        BUILDERS[key](b, m)
        names = [o.name for o in b.parts]
        for part in b.parts:
            part.parent = subject
        props.sheet_name = f"st_{key}"
        manifest = F.render_cells(bpy.context)
        for n in names:
            obj = bpy.data.objects.get(n)
            if obj is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
        if not merged:
            merged = dict(manifest)
        elements.update(manifest.get("elements", {}))
        for cell in manifest["cells"]:
            f = cell["facing"]
            tile = dict(SEAT_PROPS, CustomName=cname, BedType=bed, Facing=f)
            tile["chair" + f] = ""
            cells.append(dict(cell, group=group, tile_props=tile))
        print(f"== {key}: {len(names)} parts")

    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
