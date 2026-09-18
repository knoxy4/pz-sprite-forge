"""Render an original, book-filled oak bookcase for Project Zomboid.

The piece is a one-tile, four-facing bookcase.  Books are deliberately packed
tight with varied muted bindings so that, at gameplay scale, the shelves read
as stocked rather than as bare furniture with a few decorative objects.

Run headlessly:
    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/bookcase_full.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "bookcase_full_cells"
# One sheet carries three states of the same carcass -- stocked, picked over,
# stripped -- rendered from one model by deleting books between passes, so shelf
# count, silhouette and wood are identical across all of them by construction.
# Vanilla has no equivalent: all 60 tiles of furniture_shelving_01 are
# CustomName = Shelves differing only by GroupName and capacity, and no vanilla
# Lua swaps a container's sprite from its contents.
#
# "Picked over" is whole missing runs, not uniformly shorter books.  A shelf
# somebody has been through has gaps and a gutted bay; a shelf of short books
# just reads as a different bookcase.
SHEET = "badlands_bookcase_01"
GRAIN_PATH = ROOT / "build" / "bookcase_oak_grain.png"

# Solved against vanilla furniture_shelving_01_40, whose 2x trim box is
# 92x204 px at (31,38).  Fitted from a render of this recipe, the projection is
#   width_px  = 63.0 * (WIDTH + cap_depth) + 2
#   height_px = 32.0 * (WIDTH + cap_depth) + 77.2 * HEIGHT + 2
# with cap_depth = DEPTH + 0.030.  WIDTH is pinned at one full tile because the
# spec puts vanilla at 1.016 tiles across.
WIDTH = 1.00
DEPTH = 0.40
HEIGHT = 2.02
SIDE = 0.060
SHELF = 0.046
BACK = 0.026
BOOK_DEPTH = DEPTH - 0.080
BOOK_Y = -DEPTH / 2 + 0.0125 + BOOK_DEPTH / 2
# Vanilla's bookcase is a wall object: its 92 px trim box sits at x=31, i.e. 13 px
# right of the cell centre, because the case hugs the back of its tile rather than
# standing in the middle of it.  Applied inside box() so it rotates with the facing.
OFFSET_Y = 0.206
# Registration: with the case grounded at z=0 the silhouette lands 2 px above
# vanilla's on all four facings (top 36 vs 38, bottom 240 vs 242).  Vanilla's
# base carries ~2 px of painted contact alpha that this rig has no pass for, so
# the model registers 2 px lower instead: 2 px / 77.2 px-per-metre.
OFFSET_Z = -2.0 / 77.2


def make_grain() -> Path:
    """Write a restrained, directional oak texture for the case itself."""
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    spec = material_spec("wood", seed=48)
    spec = dataclasses.replace(
        spec,
        octaves=[(size, amplitude * 0.11) for size, amplitude in spec.octaves],
        contrast=1.10,
        stroke_count=70,
        stroke_amplitude=0.05,
        knot_count=1,
        knot_depth=0.06,
    )
    return write_surface_map(GRAIN_PATH, 512, 512, spec, grain_axis="v")


def build_bookcase() -> list[bpy.types.Object]:
    grain = str(GRAIN_PATH)
    # pzforge spec furniture_shelving_01_40 --sprite inverts the rig's measured
    # lighting response on vanilla's own paint colour (120, 64, 24) and recovers
    # a south-facing base colour of (0.508, 0.139, 0.025).  The trim and the
    # recess keep their old value ladder as plain multipliers of it, so the whole
    # case carries vanilla's hue and saturation instead of a guess.
    OAK = (0.508, 0.139, 0.025)
    oak = F.forge_material("oak", "wood", OAK, texture_path=grain)
    oak_trim = F.forge_material("oak_trim", "wood",
                                tuple(c * 0.70 for c in OAK),
                                texture_path=grain)
    # The boards get their own grain-free oak.  The surface map is generated
    # with grain_axis="v", which streaks a shelf across its length instead of
    # along it, and on five lit horizontal faces that read as a louvre rather
    # than a bookcase.  Vanilla paints its shelves flat, so these are flat.
    oak_shelf = F.forge_material("oak_shelf", "wood",
                                 tuple(c * 0.78 for c in OAK))
    # The backboard is what sells depth on an empty shelf, so it goes deeper
    # than a plain shading step would.
    interior = F.forge_material("shadowed_oak", "wood",
                                tuple(c * 0.28 for c in OAK))
    book_paints = [
        (0.620, 0.100, 0.055), # deep red
        (0.170, 0.310, 0.075), # moss green
        (0.075, 0.220, 0.440), # slate blue
        (0.600, 0.360, 0.055), # ochre
        (0.360, 0.075, 0.045), # oxblood
        (0.260, 0.165, 0.055), # worn brown
        (0.500, 0.460, 0.270), # old canvas
        (0.065, 0.270, 0.235), # dark teal
    ]
    book_mats = [F.toon_material(f"book_{index}", paint)
                 for index, paint in enumerate(book_paints)]
    page_mat = F.toon_material("book_pages", (0.51, 0.44, 0.29))

    parts: list[bpy.types.Object] = []

    def box(name: str, centre: tuple[float, float, float],
            size: tuple[float, float, float], material) -> bpy.types.Object:
        centre = (centre[0], centre[1] + OFFSET_Y, centre[2] + OFFSET_Z)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = size
        obj.data.materials.append(material)
        parts.append(obj)
        return obj

    # The backboard is dark enough to create the deep, filled-shelf recess that
    # survives when the sprite is reduced to game size.
    box("backboard", (0, DEPTH / 2 - BACK / 2, HEIGHT / 2),
        (WIDTH - 2 * SIDE, BACK, HEIGHT - 0.10), interior)
    box("left_stile", (-(WIDTH - SIDE) / 2, 0, HEIGHT / 2),
        (SIDE, DEPTH, HEIGHT), oak_trim)
    box("right_stile", ((WIDTH - SIDE) / 2, 0, HEIGHT / 2),
        (SIDE, DEPTH, HEIGHT), oak_trim)
    box("base_plinth", (0, 0, 0.100 / 2), (WIDTH, DEPTH, 0.100), oak_trim)
    box("top_cap", (0, 0, HEIGHT - 0.062 / 2),
        (WIDTH, DEPTH + 0.030, 0.062), oak_trim)

    # Five boards at a 0.365 m pitch; the top cap closes the fifth bay, so every
    # board carries books instead of leaving a dead gap under the lid.
    # Four boards, not five: vanilla runs three at a 0.65 m pitch, which no
    # book stands up in, but five at 0.365 m stacks the front face with slats.
    # Four at 0.465 m keeps a book-sized bay and a front edge you can read.
    shelf_levels = tuple(round(0.100 + index * 0.465, 3) for index in range(4))
    for index, level in enumerate(shelf_levels):
        box(f"shelf_{index}", (0, -0.004, level),
            (WIDTH - 2 * SIDE, DEPTH - 0.012, 0.038), oak_shelf)

    # Binding widths and heights repeat with a small offset on each shelf. The
    # page strip on a few books gives light, readable interruptions in the mass
    # without resorting to unreadable title text.
    widths = (0.050, 0.041, 0.063, 0.036, 0.056, 0.045, 0.052, 0.038, 0.060,
              0.044)
    heights = (0.255, 0.284, 0.210, 0.290, 0.238, 0.270, 0.219, 0.277, 0.249,
               0.263)
    inner_left = -WIDTH / 2 + SIDE + 0.025
    # Two closely stacked volumes make each row feel used and genuinely full.
    stack_width = 0.165
    stack_x = WIDTH / 2 - SIDE - stack_width / 2 - 0.024
    # Books run up to the stack, not to the case wall, so widening the case adds
    # books rather than an empty strip.
    book_limit = stack_x - stack_width / 2 - 0.012
    for row, level in enumerate(shelf_levels):
        cursor = inner_left + 0.004 * (row % 2)
        column = 0
        while True:
            book_width = widths[column % len(widths)]
            book_height = heights[column % len(heights)]
            # Leave one intentional breathing gap per row, then fill it with a
            # short horizontal stack below. The overall silhouette remains full.
            if (row, column) in {(1, 4), (3, 7)}:
                cursor += 0.022
            actual_height = book_height - 0.010 * ((row + column) % 3)
            x = cursor + book_width / 2
            if x + book_width / 2 > book_limit:
                break
            book = box(f"book_{row}_{column}",
                       (x, BOOK_Y, level + SHELF / 2 + actual_height / 2),
                       (book_width, BOOK_DEPTH, actual_height),
                       book_mats[(row * 3 + column) % len(book_mats)])
            # A slight lean once per shelf avoids an artificial picket-fence row.
            if column % 8 == 7:
                book.rotation_euler = (0.0, 0.0, -0.075 if row % 2 else 0.065)
            if column % 6 in {2, 5}:
                box(f"pages_{row}_{column}",
                    (x + book_width / 2 + 0.001, BOOK_Y,
                     level + SHELF / 2 + actual_height / 2),
                    (0.006, BOOK_DEPTH + 0.001, actual_height - 0.025), page_mat)
            cursor += book_width + 0.006
            column += 1

        for layer in range(2):
            box(f"stack_{row}_{layer}",
                (stack_x, BOOK_Y,
                 level + SHELF / 2 + 0.030 + layer * 0.058),
                (stack_width, BOOK_DEPTH, 0.048),
                book_mats[(row + layer + 5) % len(book_mats)])

    books = [o for o in parts
             if o.name.startswith(("book_", "pages_", "stack_"))]
    carcass = [o for o in parts if o not in books]
    return carcass, books


def looted(name: str) -> bool:
    """True for the volumes a passing survivor would have taken first.

    Bay 1 is emptied outright and bay 3 thinned to alternate spines; the two
    remaining bays lose their right-hand end, where a hand reaches first.  The
    horizontal stacks go with the bays they sit in.
    """
    fields = name.split("_")
    if name.startswith("stack_"):
        return int(fields[1]) in (1, 3)
    if name.startswith(("book_", "pages_")):
        row, column = int(fields[1]), int(fields[2])
        if row == 1:
            return True
        if row == 3 and column % 2 == 0:
            return True
        if row == 0 and column >= 6:
            return True
        if row == 2 and column >= 8:
            return True
    return False


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    make_grain()
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = "fullbookcase_01"
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
    carcass, books = build_bookcase()
    for part in carcass + books:
        part.parent = subject

    props.sheet_name = "fullbookcase_01"
    filled = F.render_cells(bpy.context)

    taken = [o for o in books if looted(o.name)]
    for obj in taken:
        bpy.data.objects.remove(obj, do_unlink=True)
    props.sheet_name = "halfbookcase_01"
    half = F.render_cells(bpy.context)

    for obj in [o for o in books if o not in taken]:
        bpy.data.objects.remove(obj, do_unlink=True)
    props.sheet_name = "emptybookcase_01"
    empty = F.render_cells(bpy.context)

    merged = dict(filled)
    merged["sheet"] = SHEET
    # Each cell styles alone: three cells share every facing here, and without
    # this the packer composes same-facing cells onto one canvas as though
    # they were tiles of one wide object.
    merged["isolate_tiles"] = True
    merged["elements"] = {**empty.get("elements", {}),
                          **half.get("elements", {}),
                          **filled.get("elements", {})}
    merged["cells"] = (list(filled["cells"]) + list(half["cells"])
                       + list(empty["cells"]))
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2),
                                       encoding="utf-8")
    print(f"rendered {len(merged['cells'])} cell(s) to {OUT}: "
          f"{len(filled['cells'])} stocked, {len(half['cells'])} picked over "
          f"({len(taken)} volumes removed), {len(empty['cells'])} stripped")


if __name__ == "__main__":
    main()
