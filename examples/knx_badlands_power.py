"""Badlands Power: every object in the mod onto one tilesheet.

Each shipping tile mod on disk carries exactly one ``tiledef`` and one ``pack``
line in mod.info -- Simon-MDs-Tiles fits 1.2 MB of tiles into a single tileset,
and nothing ships two. So the battery bank and the four gensets go onto one
sheet rather than five, the way bookcase_full.py puts three bookcase states on
one: render each subject under its own sheet name into a shared directory, then
concatenate the manifests under the real sheet with ``isolate_tiles`` set.

Cell order is deliberate. It lands each object on a multiple of four, which is
vanilla's own generator convention (appliances_misc_01 puts its four generators
at _0, _4, _8 and _12):

     0-3    battery bank      badlands_power_01_0
     4-7    propane genset    badlands_power_01_4
     8-11   waste-oil genset  badlands_power_01_8
    12-15   scrap jury-rig    badlands_power_01_12
    16-19   industrial diesel badlands_power_01_16
    20-39   bank overlays: 20 + (batteries - 1) * 4 + facing, batteries 1..5

The bank tile (0-3) is the empty rack. The Lua sets one overlay sprite on top
of it to show however many batteries are in the rack (BP.updateRackOverlay).

Run headlessly:
    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_badlands_power.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "badlands_power_cells"
SHEET = "badlands_power_01"


def load(name: str):
    """Import a sibling recipe without running its main()."""
    path = ROOT / "examples" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def render_subject(props, sheet: str, build_fn) -> dict:
    """Build, parent, render, then remove -- so the next subject starts clean.

    Tracking objects by identity rather than by name matters: the genset recipe
    reuses part names across variants, and a name-based sweep would leave the
    previous machine standing inside the next one.
    """
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

    gensets = load("knx_gensets")
    gensets.make_texture()
    mats = gensets.materials()

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
        ("bp_bank", lambda: gensets.build("bank", mats, count=0)),
        ("bp_propane", lambda: gensets.build("propane", mats)),
        ("bp_wasteoil", lambda: gensets.build("wasteoil", mats)),
        ("bp_scrap", lambda: gensets.build("scrap", mats)),
        ("bp_diesel", lambda: gensets.build("diesel", mats)),
    ]
    # Battery-count overlays for the bank: 1..5 batteries, groups 5..9.
    for n in range(1, 6):
        order.append((f"bp_bank_n{n}",
                      lambda n=n: gensets.build("bank", mats, count=n,
                                                overlay=True)))
    overlay_groups = set(range(5, 10))

    manifests = []
    for sheet, build_fn in order:
        manifest = render_subject(props, sheet, build_fn)
        manifests.append((sheet, manifest))
        print(f"   {sheet}: {len(manifest['cells'])} cell(s)")

    merged = dict(manifests[0][1])
    merged["sheet"] = SHEET
    # Without this the packer composes same-facing cells onto one canvas as
    # though five different machines were tiles of a single wide object.
    merged["isolate_tiles"] = True
    elements: dict = {}
    cells: list = []
    for group, (_, manifest) in enumerate(manifests):
        elements.update(manifest.get("elements", {}))
        # The group stamp is what keeps each machine's four facings together
        # on the sheet; without it pzforge sorts facing-major and the sheet
        # cycles bank/propane/... inside each facing (the 2026-09-18 bug).
        extra = {"group": group}
        if group in overlay_groups:
            # Overlay sprites carry no tile properties, as vanilla's do.
            extra["tile_props"] = {}
        cells.extend(dict(cell, **extra) for cell in manifest["cells"])
    merged["elements"] = elements
    merged["cells"] = cells

    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2),
                                       encoding="utf-8")
    print(f"merged {len(cells)} cell(s) into {SHEET} at {OUT}")
    for index, (sheet, manifest) in enumerate(manifests):
        print(f"   {SHEET}_{index * 4}: {sheet}")


if __name__ == "__main__":
    main()
