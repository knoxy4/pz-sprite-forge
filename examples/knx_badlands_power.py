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

    bank = load("knx_battery_bank")
    gensets = load("knx_gensets")

    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = SHEET
    props.output_dir = str(OUT)
    props.footprint_x = props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False

    F.build_rig(bpy.context)
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True

    order = [
        ("bp_bank", lambda: bank.build()),
        ("bp_propane", lambda: gensets.build("propane")),
        ("bp_wasteoil", lambda: gensets.build("wasteoil")),
        ("bp_scrap", lambda: gensets.build("scrap")),
        ("bp_diesel", lambda: gensets.build("diesel")),
    ]

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
    for _, manifest in manifests:
        elements.update(manifest.get("elements", {}))
        cells.extend(manifest["cells"])
    merged["elements"] = elements
    merged["cells"] = cells

    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2),
                                       encoding="utf-8")
    print(f"merged {len(cells)} cell(s) into {SHEET} at {OUT}")
    for index, (sheet, manifest) in enumerate(manifests):
        print(f"   {SHEET}_{index * 4}: {sheet}")


if __name__ == "__main__":
    main()
