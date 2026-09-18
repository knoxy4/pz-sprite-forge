"""Badlands Power: a wood pallet carrying six car batteries and an inverter box.

Measured against the vanilla generator it has to sit beside
(``appliances_misc_01_0``, via tools/show_sprite.py):

* vanilla footprint 0.492 tiles, 0.625 m tall, bottom raised 16 px off the cell floor;
* its silhouette is a 60 px body under a 6 px fuel-cap spike, wrapped in a dark
  tubular roll cage that is 24% of the sprite's pixels.

This deliberately breaks that language. A pallet is wider (0.86 x 0.78 of a tile),
shorter in the body, has no cage, and carries one tall asymmetric element -- the
inverter -- so all four facings differ and it never reads as a genset.

Run with:
    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" -b \
        -P examples/knx_battery_bank.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "battery_bank_cells"

PALLET_W = 0.98
PALLET_D = 0.90
BLOCK_H = 0.055
DECK_H = 0.024
DECK_Z = BLOCK_H + DECK_H / 2

BATT_W = 0.235
BATT_D = 0.165
BATT_H = 0.205
CAP_H = 0.034
TERM_H = 0.034


def mat(name: str, colour, rough: float = 0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.1
    return m


def box(name: str, centre, size, material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    obj.data.materials.append(material)
    return obj


def build_pallet(wood_pale, wood_dark) -> list[bpy.types.Object]:
    """Three bottom blocks under seven deck boards, gaps left open.

    The gaps are the whole point -- a solid slab reads as a crate lid. At this
    pixel size the eye only needs three or four visible dark lines to call it a
    pallet.
    """
    parts = []
    for i, sy in enumerate((-1, 0, 1)):
        parts.append(box(f"pallet_block_{i}",
                         (0, sy * (PALLET_D / 2 - 0.09), BLOCK_H / 2),
                         (PALLET_W * 0.98, 0.115, BLOCK_H), wood_dark))

    boards = 6
    pitch = PALLET_D / boards
    for i in range(boards):
        y = -PALLET_D / 2 + pitch * (i + 0.5)
        parts.append(box(f"deck_board_{i}", (0, y, DECK_Z),
                         (PALLET_W, pitch * 0.70, DECK_H), wood_pale))
    return parts


def build_batteries(case, cap_red, lead) -> list[bpy.types.Object]:
    """Two rows of three. Six discrete blocks still resolve at 32 px."""
    parts = []
    top = BLOCK_H + DECK_H
    xs = (-0.290, 0.0, 0.290)
    ys = (-0.205, 0.205)
    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            if r == 1 and c == 2:
                continue
            base = f"batt_{r}{c}"
            parts.append(box(base, (x, y, top + BATT_H / 2),
                             (BATT_W, BATT_D, BATT_H), case))
            parts.append(box(base + "_cap", (x, y, top + BATT_H + CAP_H / 2),
                             (BATT_W * 0.97, BATT_D * 0.97, CAP_H), cap_red))
            for sx in (-1, 1):
                parts.append(box(f"{base}_term_{sx}",
                                 (x + sx * BATT_W * 0.31, y,
                                  top + BATT_H + CAP_H + TERM_H / 2),
                                 (0.042, 0.042, TERM_H), lead))
    return parts


def build_inverter(shell, vent) -> list[bpy.types.Object]:
    """The tall asymmetric element. Occupies the gap left in the battery grid so
    every facing gets a different profile, which is what stops four renders of a
    symmetric box looking like one sprite repeated."""
    top = BLOCK_H + DECK_H
    h = 0.44
    x, y = 0.290, 0.205
    parts = [box("inverter", (x, y, top + h / 2), (0.235, 0.185, h), shell)]
    for i in range(3):
        parts.append(box(f"inverter_vent_{i}",
                         (x - 0.075, y - 0.088, top + 0.09 + i * 0.045),
                         (0.055, 0.012, 0.022), vent))
    parts.append(box("inverter_lid", (x, y, top + h + 0.012),
                     (0.235, 0.185, 0.024), vent))
    return parts


def build_strap(strap) -> list[bpy.types.Object]:
    """One ratchet strap over the battery rows. Reads as 'somebody rigged this',
    and gives a horizontal line that separates the cases from the caps."""
    top = BLOCK_H + DECK_H
    z = top + BATT_H * 0.72
    parts = []
    for i, y in enumerate((-0.205, 0.205)):
        parts.append(box(f"strap_{i}", (0, y, z),
                         (PALLET_W * 0.99, 0.040, 0.026), strap))
    return parts


def build() -> list[bpy.types.Object]:
    wood_pale = mat("bank_wood_pale", (0.849, 0.583, 0.264))
    wood_dark = mat("bank_wood_dark", (0.355, 0.238, 0.104))
    case = mat("bank_case", (0.165, 0.165, 0.180), rough=0.55)
    cap_red = mat("bank_cap", (1.000, 0.316, 0.264), rough=0.6)
    lead = mat("bank_lead", (0.62, 0.62, 0.66), rough=0.35)
    shell = mat("bank_shell", (0.275, 0.330, 0.405), rough=0.5)
    vent = mat("bank_vent", (0.105, 0.105, 0.115), rough=0.7)
    strap = mat("bank_strap", (0.115, 0.115, 0.125), rough=0.9)

    parts = []
    parts += build_pallet(wood_pale, wood_dark)
    parts += build_batteries(case, cap_red, lead)
    parts += build_inverter(shell, vent)
    parts += build_strap(strap)
    return parts


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = "badlands_power_01"
    props.output_dir = str(OUT)
    props.footprint_x = props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False

    F.build_rig(bpy.context)
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True

    subject = bpy.data.objects[F.SUBJECT_NAME]
    for part in build():
        part.parent = subject

    total_h = BLOCK_H + DECK_H + 0.30 + 0.024
    print(f"battery bank stands {total_h:.3f} m "
          f"(vanilla generator is 0.625 m) in a cell clearing "
          f"{F.clear_height(*F.cell_size(props.scale_2x)):.2f} m")
    manifest = F.render_cells(bpy.context)
    print(f"rendered {len(manifest['cells'])} cells to {OUT}")
    for cell in manifest["cells"]:
        print(f"   {cell['file']}  facing={cell['facing']}")


if __name__ == "__main__":
    main()
