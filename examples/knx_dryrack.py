"""BADLANDS jerky and fish drying rack: an A-frame of lashed poles, a ridge pole
and two crossbars, strips hung from the bars.

1x1, two facings (S, E) like vanilla's herb rack -- the rack is symmetric, so N/W
would repeat S/E.  Cells, index = group*2 + facing:
    0-1   bare rack                          (SpriteConfig)
    then per style Beef, Pork, Poultry, Game, Fish: progress 0/50/100, S+E
    (SpriteOverlayConfig style <name>), i.e. style k starts at 2 + 6*k.
Overlays render with the rack as holdout so the poles occlude correctly.
Strips darken and shrink as they dry: raw red -> jerky brown; fish pale -> golden.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_dryrack.py -- [--samples N]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

SHEET = "badlands_dryrack_01"
OUT = ROOT / "build" / "dryrack_cells"
GRAIN = ROOT / "build" / "dryrack_grain.png"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OFFSET_Z = -2.0 / 77.2

SPAN = 0.84          # ridge length along x
FOOT = 0.30          # half-spread of the A-frame legs along y
RIDGE_Z = 1.30
#: (y, z) of the two crossbars, where they meet the legs: a leg runs from
#: y=+-FOOT at the ground to y=-+0.05 at RIDGE_Z+0.10, so at z=0.80 it sits at
#: y=+-(0.30 - 0.35*0.80/1.40) = +-0.10.
BARS = [(-0.10, 0.80), (0.10, 0.80)]

#: style -> progress -> (colour, length scale, width scale).  Each style is a
#: family of raw meats with its own cut: see hang().
STYLES = {
    "Beef": {0: ((0.55, 0.10, 0.09), 1.00, 1.00), 50: ((0.42, 0.13, 0.08), 0.94, 0.92),
             100: ((0.28, 0.14, 0.08), 0.88, 0.85)},
    "Pork": {0: ((0.78, 0.40, 0.38), 1.00, 1.00), 50: ((0.62, 0.30, 0.22), 0.94, 0.93),
             100: ((0.46, 0.24, 0.14), 0.90, 0.88)},
    "Poultry": {0: ((0.88, 0.66, 0.60), 1.00, 1.00), 50: ((0.80, 0.58, 0.40), 0.95, 0.94),
                100: ((0.68, 0.48, 0.28), 0.90, 0.90)},
    "Game": {0: ((0.40, 0.07, 0.08), 1.00, 1.00), 50: ((0.30, 0.08, 0.07), 0.93, 0.92),
             100: ((0.20, 0.08, 0.06), 0.87, 0.86)},
    "Fish": {0: ((0.78, 0.70, 0.62), 1.00, 1.00), 50: ((0.72, 0.56, 0.36), 0.95, 0.93),
             100: ((0.60, 0.42, 0.20), 0.90, 0.88)},
}
FAT = (0.86, 0.80, 0.68)

def rod(name, a, b, r, mat, parts, verts=10):
    d = Vector(b) - Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length,
                                        location=(Vector(a) + Vector(b)) / 2 + Vector((0, 0, OFFSET_Z)))
    o = bpy.context.active_object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.name = name
    o.data.materials.append(mat)
    parts.append(o)
    return o


def make_grain() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses
    from pzforge.texture import material_spec, write_surface_map
    spec = material_spec("wood", seed=31)
    spec = dataclasses.replace(spec, octaves=[(s, a * 0.2) for s, a in spec.octaves],
                               stroke_count=70, stroke_amplitude=0.07, knot_count=2)
    write_surface_map(GRAIN, 512, 512, spec, grain_axis="v")


def rack(subject) -> list:
    pole = F.forge_material("dr_pole", "wood", (0.46, 0.34, 0.21), texture_path=GRAIN, swing=(0.8, 1.15))
    bark = F.forge_material("dr_bark", "wood", (0.30, 0.22, 0.14), texture_path=GRAIN, swing=(0.8, 1.15))
    twine = F.toon_material("dr_twine", (0.62, 0.55, 0.38))
    parts: list = []
    for sx in (-1, 1):
        x = sx * SPAN / 2
        for sy in (-1, 1):
            rod(f"leg_{sx}_{sy}", (x, sy * FOOT, 0.0), (x, -sy * 0.05, RIDGE_Z + 0.10), 0.022, bark, parts)
        rod(f"lash_{sx}", (x - 0.03, 0, RIDGE_Z - 0.01), (x + 0.03, 0, RIDGE_Z + 0.01), 0.032, twine, parts)
    rod("ridge", (-SPAN / 2 - 0.06, 0, RIDGE_Z), (SPAN / 2 + 0.06, 0, RIDGE_Z), 0.020, pole, parts)
    for i, (y, z) in enumerate(BARS):
        rod(f"bar_{i}", (-SPAN / 2 + 0.01, y, z), (SPAN / 2 - 0.01, y, z), 0.014, pole, parts)
    for p in parts:
        p.parent = subject
    return parts


def _r(*k) -> float:
    """Deterministic 0..1 per strip, so every render and facing agrees."""
    h = 0
    for v in k:
        h = (h * 1103515245 + int(v) * 2654435761 + 12345) & 0x7FFFFFFF
    return (h % 10007) / 10007.0


def hang(style, progress, subject) -> list:
    """One style's cuts over the ridge and both bars.  Nothing uniform: length,
    width, twist, sway, spacing and shade vary per piece (deterministic)."""
    rgb, ls, ws = STYLES[style][progress]
    twine = F.toon_material("dr_twine2", (0.62, 0.55, 0.38))
    shades = [F.toon_material(f"dr_{style}_{progress}_{j}", tuple(min(1.0, c * f) for c in rgb))
              for j, f in enumerate((0.82, 0.92, 1.0, 1.10))]
    fat_rgb = tuple(c * (1.0 - 0.25 * progress / 100) for c in FAT)
    fat = F.toon_material(f"dr_fat_{progress}", fat_rgb)
    parts: list = []

    def piece(loc, size, rot, mat):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
        o = bpy.context.active_object
        o.scale = size
        o.rotation_euler = rot
        o.location = Vector(loc) + Vector((0, 0, OFFSET_Z))
        o.data.materials.append(mat)
        o.parent = subject
        parts.append(o)
        return o

    def loop(x, y, z, top):
        rod("loop", (x, y, z + 0.012), (x, y, top), 0.004, twine, parts, verts=5)
        parts[-1].parent = subject

    lines = [(0.0, RIDGE_Z - 0.02, 7)] + [(y, z, 6) for y, z in BARS]
    for li, (y, z, n) in enumerate(lines):
        if style == "Game":
            n = n - 2
        for i in range(n):
            r1, r2, r3, r4, r5 = (_r(li, i, k, len(style)) for k in range(5))
            x = -SPAN / 2 + 0.09 + i * (SPAN - 0.18) / (n - 1) + (r1 - 0.5) * 0.045
            mat = shades[int(r5 * 4) % 4]
            sway = math.radians((r1 - 0.5) * 16)
            twist = math.radians((r4 - 0.5) * 44)
            top = z - 0.018
            if style == "Beef":
                length, width, thick = (0.13 + 0.18 * r2) * ls, (0.020 + 0.022 * r3) * ws, 0.005 + 0.004 * r4
                piece((x, y, top - length / 2), (width, thick, length), (sway, 0, twist), mat)
                loop(x, y, z, top)
            elif style == "Pork":
                length, width = (0.12 + 0.12 * r2) * ls, (0.040 + 0.020 * r3) * ws
                piece((x, y, top - length / 2), (width, 0.007, length), (sway, 0, twist), mat)
                edge = width / 2 - 0.006
                dx, dy = edge * math.cos(twist), edge * math.sin(twist)
                piece((x + dx, y + dy, top - length / 2), (0.011, 0.0085, length * 0.97), (sway, 0, twist), fat)
                loop(x, y, z, top)
            elif style == "Poultry":
                length, width = (0.09 + 0.07 * r2) * ls, (0.030 + 0.016 * r3) * ws
                piece((x, y, top - length / 2), (width, 0.011, length), (sway, 0, twist), mat)
                curl = math.radians(35 + 30 * r4) * (1 if r5 > 0.5 else -1)
                tip = 0.035 + 0.02 * r2
                piece((x, y + math.sin(curl) * tip / 2, top - length - math.cos(curl) * tip / 2 + 0.004),
                      (width * 0.9, 0.011, tip), (curl, 0, twist), mat)
                loop(x, y, z, top)
            elif style == "Game":
                count = 4 + int(r2 * 3)
                zc = top
                loop(x, y, z, top)
                for k in range(count):
                    c = (0.022 + 0.012 * _r(li, i, k, 9)) * ws
                    zc -= c * 0.95 + 0.004
                    piece((x + (_r(li, i, k, 7) - 0.5) * 0.008, y, zc), (c, c * 0.8, c),
                          (0.3 * _r(li, i, k, 5), 0.4 * _r(li, i, k, 6), 0.6 * _r(li, i, k, 8)),
                          shades[(k + i) % 4])
                    zc -= c * 0.05
                rod("string", (x, y, top), (x, y, zc - 0.01), 0.0025, twine, parts, verts=4)
                parts[-1].parent = subject
            else:
                length, width = (0.14 + 0.06 * r2) * ls, (0.064 + 0.02 * r3) * ws
                piece((x, y, top - length / 2), (width, 0.008, length),
                      (math.radians((r1 - 0.5) * 8), 0, math.radians((r4 - 0.5) * 16)), mat)
                loop(x, y, z, top)
    return parts

def setup():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    make_grain()
    F.register()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    p = sc.pz_forge
    p.sheet_name = SHEET
    p.output_dir = str(OUT)
    p.footprint_x = p.footprint_y = 1
    p.facings = "2"
    p.show_guide = False
    p.contrast_boost = 1.0
    p.toon_shading = True
    F.build_rig(bpy.context)
    sc.cycles.samples = int(ARGV[ARGV.index("--samples") + 1]) if "--samples" in ARGV else 512
    sc.cycles.use_denoising = True
    return bpy.data.objects[F.SUBJECT_NAME]


def main() -> None:
    subject = setup()
    frame = rack(subject)
    props = bpy.context.scene.pz_forge
    groups = [("base", None, None)] + [(st, st, p) for st in STYLES for p in (0, 50, 100)]
    merged, cells = None, []
    for g, (label, kind, prog) in enumerate(groups):
        for o in frame:
            o.is_holdout = kind is not None
        parts = hang(kind, prog, subject) if kind else []
        props.sheet_name = SHEET if kind is None else f"{SHEET}_{kind.lower()}{prog}"
        manifest = F.render_cells(bpy.context)
        merged = merged or dict(manifest)
        for c in manifest["cells"]:
            props_ = {} if kind else {
                "BlocksPlacement": "", "CustomName": "Drying Rack", "GroupName": "Badlands Jerky",
                "ForceSingleItem": "", "IsMoveAble": "", "PickUpWeight": "60", "solidtrans": "",
                "Facing": c["facing"]}
            cells.append(dict(c, group=g, stage=f"{kind}{prog}" if kind else None, style=kind, tile_props=props_))
        for p in parts:
            bpy.data.objects.remove(p, do_unlink=True)
    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
