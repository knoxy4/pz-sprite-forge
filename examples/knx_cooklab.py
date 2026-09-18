"""Three tabletop props for the Badlands cook-lab set.

Tabletop objects are drawn PRE-ELEVATED.  Measured on the shipped sprites, a
vanilla radio (IsSurfaceOffset + IsTableTop) trims to 76x62 at (32,111), bottom
173, and the table lamps bottom out at 153 -- against a floor-standing sprite's
242.  So the art carries the table height, the engine does not add it, and the
model is built starting at TABLE_H rather than at z=0.

One tile each, four facings, all on one sheet:
    glassware rig   -- ring stand, flask, condenser, receiving jar
    burner and pot  -- hotplate, dented pot, thermometer
    jug rack        -- jugs, jars, funnel, filter stack, coiled tubing

Run:
    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_cooklab.py
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

OUT = ROOT / "build" / "cooklab_cells"
TEXTURE_PATH = ROOT / "build" / "cooklab_surface.png"
SHEET = "knx_cooklab_01"

#: Counter height in this art's scale.  77.2 px per metre vertical, so 0.90 m
#: lifts the base 69 px -- the radio's measured offset off the floor line.
TABLE_H = 0.90


def make_texture() -> Path:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    spec = material_spec("metal", seed=61)
    spec = dataclasses.replace(
        spec,
        octaves=[(s, a * 0.45) for s, a in spec.octaves],
        stroke_amplitude=0.10,
    )
    return write_surface_map(TEXTURE_PATH, 512, 256, spec)


def materials() -> dict:
    return {
        "steel": F.forge_material("lab_steel", "metal",
                                  texture_path=TEXTURE_PATH,
                                  dark=(0.250, 0.248, 0.242),
                                  light=(0.560, 0.548, 0.530),
                                  accent=(0.300, 0.265, 0.235)),
        "iron": F.forge_material("lab_iron", "metal", (0.145, 0.148, 0.145)),
        # The first pass came out monochrome: against a vanilla prop shelf the
        # whole set read as one grey lump.  Each piece now carries one owned
        # hue so they are told apart at 1x.
        "enamel": F.forge_material("lab_enamel", "metal",
                                   (0.560, 0.545, 0.510)),
        "enamel_cream": F.forge_material("lab_enamel_cream", "metal",
                                         (0.620, 0.560, 0.400)),
        "enamel_teal": F.forge_material("lab_enamel_teal", "metal",
                                        (0.165, 0.300, 0.300)),
        "coil_hot": F.toon_material("lab_coil_hot", (0.560, 0.170, 0.070)),
        "plastic_amber": F.toon_material("lab_plastic_amber",
                                         (0.580, 0.400, 0.130)),
        "cap_blue": F.toon_material("lab_cap_blue", (0.150, 0.250, 0.420)),
        # Glass at tile scale is a pale cool plane with one bright edge; PZ
        # paints glass, it does not refract it.
        "glass": F.toon_material("lab_glass", (0.620, 0.680, 0.690)),
        "glass_dark": F.toon_material("lab_glass_dark", (0.300, 0.360, 0.380)),
        "fluid_amber": F.toon_material("lab_fluid_amber",
                                       (0.520, 0.330, 0.105)),
        "fluid_pale": F.toon_material("lab_fluid_pale", (0.660, 0.640, 0.520)),
        "plastic": F.toon_material("lab_plastic", (0.700, 0.690, 0.650)),
        "plastic_blue": F.toon_material("lab_plastic_blue",
                                        (0.230, 0.330, 0.440)),
        "cap_red": F.toon_material("lab_cap_red", (0.480, 0.115, 0.075)),
        "tube": F.toon_material("lab_tube", (0.560, 0.575, 0.560)),
        "paper": F.toon_material("lab_paper", (0.700, 0.680, 0.620)),
        "grime": F.toon_material("lab_grime", (0.180, 0.150, 0.110)),
    }


class Build:
    """Collects parts and lifts everything onto the table."""

    def __init__(self, mats):
        self.mats = mats
        self.parts = []

    def _add(self, obj, name, material):
        obj.name = name
        obj.data.materials.append(material)
        self.parts.append(obj)
        return obj

    def _smooth(self):
        try:
            bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
        except (AttributeError, TypeError, RuntimeError):
            bpy.ops.object.shade_smooth()

    def box(self, name, centre, size, mat):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, location=(centre[0], centre[1], centre[2] + TABLE_H))
        obj = bpy.context.active_object
        obj.scale = size
        return self._add(obj, name, self.mats[mat])

    def cyl(self, name, r, depth, loc, mat, verts=32, smooth=True, rot=None):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=verts, radius=r, depth=depth,
            location=(loc[0], loc[1], loc[2] + TABLE_H))
        obj = bpy.context.active_object
        if rot:
            obj.rotation_euler = rot
        if smooth:
            self._smooth()
        return self._add(obj, name, self.mats[mat])

    def cone(self, name, r1, r2, depth, loc, mat, verts=32):
        bpy.ops.mesh.primitive_cone_add(
            vertices=verts, radius1=r1, radius2=r2, depth=depth,
            location=(loc[0], loc[1], loc[2] + TABLE_H))
        self._smooth()
        return self._add(bpy.context.active_object, name, self.mats[mat])

    def ball(self, name, r, loc, mat, segments=24):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments, ring_count=14, radius=r,
            location=(loc[0], loc[1], loc[2] + TABLE_H))
        self._smooth()
        return self._add(bpy.context.active_object, name, self.mats[mat])

    def ring(self, name, major, minor, loc, mat, segs=28):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=major, minor_radius=minor,
            major_segments=segs, minor_segments=8,
            location=(loc[0], loc[1], loc[2] + TABLE_H))
        return self._add(bpy.context.active_object, name, self.mats[mat])

    def pipe(self, name, r, start, end, mat, verts=14):
        """A straight run between two points -- the still's lyne-arm trick."""
        d = tuple(e - s for s, e in zip(start, end))
        length = math.sqrt(sum(c * c for c in d))
        mid = tuple((s + e) / 2 for s, e in zip(start, end))
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=verts, radius=r, depth=length,
            location=(mid[0], mid[1], mid[2] + TABLE_H))
        obj = bpy.context.active_object
        obj.rotation_euler = (0.0, math.acos(d[2] / length),
                              math.atan2(d[1], d[0]))
        return self._add(obj, name, self.mats[mat])


def glassware_rig(mats) -> list:
    """Ring stand carrying a flask, a condenser running down to a jar."""
    b = Build(mats)
    sx, sy = -0.16, 0.10

    b.box("stand_base", (sx, sy, 0.012), (0.24, 0.17, 0.024), "iron")
    b.cyl("stand_rod", 0.012, 0.62, (sx, sy + 0.05, 0.31), "steel", verts=12)
    b.box("stand_clamp", (sx + 0.06, sy + 0.02, 0.30), (0.13, 0.02, 0.018),
          "iron")
    b.ring("stand_ring", 0.075, 0.008, (sx + 0.02, sy - 0.02, 0.30), "iron")

    # Flask: a sphere with a neck, filled a third of the way up.
    fz = 0.30
    b.ball("flask", 0.095, (sx + 0.02, sy - 0.02, fz), "glass")
    b.ball("flask_fluid", 0.074, (sx + 0.02, sy - 0.02, fz - 0.018),
           "fluid_amber")
    b.cyl("flask_neck", 0.026, 0.13, (sx + 0.02, sy - 0.02, fz + 0.14),
          "glass", verts=16)
    b.cyl("flask_lip", 0.033, 0.018, (sx + 0.02, sy - 0.02, fz + 0.20),
          "glass", verts=16)

    # Condenser sloping down to the receiving jar, with a jacket collar.
    jx, jy = 0.24, -0.16
    top = (sx + 0.02, sy - 0.02, fz + 0.21)
    inlet = (jx, jy, 0.30)
    b.pipe("condenser", 0.022, top, inlet, "glass")
    b.pipe("condenser_jacket", 0.036,
           (sx + 0.10, sy - 0.08, fz + 0.13), (jx - 0.06, jy + 0.05, 0.345),
           "glass_dark")

    # Receiving jar under the drip, a collar, and slack tubing on the table.
    b.cyl("jar", 0.070, 0.20, (jx, jy, 0.10), "glass", verts=28)
    b.cyl("jar_fluid", 0.058, 0.07, (jx, jy, 0.045), "fluid_pale", verts=28)
    b.cyl("jar_collar", 0.074, 0.020, (jx, jy, 0.205), "cap_red", verts=28)
    # The loose coil sat clear of everything and read as a detached grey ring,
    # so it now tucks against the jar's foot.
    b.ring("tubing", 0.062, 0.011, (jx - 0.10, jy - 0.04, 0.012), "tube")
    # No floor mat: a flat grime box at table level read as a placemat, not as
    # a stain.  Grime lives on the objects instead.
    b.cyl("jar_ring_stain", 0.072, 0.006, (jx, jy, 0.003), "grime", verts=24)
    return b.parts


def burner_and_pot(mats) -> list:
    """A hotplate with a dented pot and a thermometer standing in it."""
    b = Build(mats)
    px, py = -0.02, 0.04

    b.box("plate_body", (px, py, 0.035), (0.44, 0.36, 0.070), "enamel_cream")
    b.box("plate_top", (px, py - 0.02, 0.074), (0.40, 0.28, 0.010), "iron")
    b.ring("plate_coil", 0.105, 0.010, (px, py - 0.03, 0.080), "coil_hot")
    b.box("plate_panel", (px, py + 0.175, 0.052), (0.44, 0.02, 0.046),
          "enamel_teal")
    b.cyl("plate_knob", 0.024, 0.030, (px - 0.15, py + 0.19, 0.052), "cap_red",
          verts=16, rot=(math.radians(90), 0, 0))

    b.cyl("pot", 0.135, 0.19, (px, py - 0.03, 0.180), "steel", verts=36)
    b.ring("pot_rim", 0.137, 0.009, (px, py - 0.03, 0.272), "iron", segs=36)
    b.cyl("pot_lid", 0.130, 0.016, (px + 0.03, py - 0.05, 0.286), "steel",
          verts=36, rot=(math.radians(7), 0, 0))
    b.ball("lid_knob", 0.021, (px + 0.03, py - 0.05, 0.302), "iron")
    b.box("pot_scorch", (px, py - 0.03, 0.098), (0.26, 0.26, 0.030), "grime")

    b.pipe("thermometer", 0.010, (px + 0.09, py - 0.13, 0.20),
           (px + 0.13, py - 0.20, 0.40), "steel")
    b.box("thermo_face", (px + 0.135, py - 0.21, 0.415),
          (0.055, 0.016, 0.055), "enamel")
    return b.parts


def jug_rack(mats) -> list:
    """The supply end: jugs, jars, a funnel, filters, coiled tubing."""
    b = Build(mats)

    b.cyl("jug_a", 0.095, 0.30, (-0.22, 0.10, 0.150), "plastic", verts=20)
    b.cyl("jug_a_neck", 0.036, 0.06, (-0.22, 0.10, 0.325), "plastic", verts=16)
    b.cyl("jug_a_cap", 0.042, 0.030, (-0.22, 0.10, 0.368), "cap_red", verts=16)
    b.box("jug_a_label", (-0.22, 0.008, 0.16), (0.11, 0.004, 0.13), "paper")

    b.cyl("jug_b", 0.080, 0.24, (-0.03, 0.22, 0.120), "plastic_blue", verts=20)
    b.cyl("jug_b_cap", 0.038, 0.028, (-0.03, 0.22, 0.252), "cap_blue",
          verts=16)
    # A third jug in amber, short and forward, so the N facing does not hide
    # every jar behind the two tall ones.
    b.cyl("jug_c", 0.068, 0.17, (0.06, -0.02, 0.085), "plastic_amber",
          verts=20)
    b.cyl("jug_c_cap", 0.032, 0.026, (0.06, -0.02, 0.183), "cap_red", verts=16)

    for i, (x, y, r, h, fill) in enumerate((
            (0.19, 0.02, 0.058, 0.15, "fluid_pale"),
            (0.30, -0.14, 0.052, 0.13, "fluid_amber"),
            (0.14, -0.22, 0.055, 0.14, "fluid_pale"))):
        b.cyl(f"jar_{i}", r, h, (x, y, h / 2), "glass", verts=24)
        b.cyl(f"jar_{i}_fluid", r * 0.82, h * 0.55, (x, y, h * 0.32), fill,
              verts=24)
        b.cyl(f"jar_{i}_lid", r * 1.05, 0.016, (x, y, h + 0.006), "steel",
              verts=24)

    b.cone("funnel", 0.075, 0.016, 0.11, (-0.15, -0.20, 0.055), "plastic_blue")
    b.cyl("filters", 0.062, 0.035, (-0.04, -0.14, 0.018), "paper", verts=24)
    # Coils tucked under the tall jug rather than floating off on their own.
    b.ring("coil_a", 0.070, 0.012, (-0.26, -0.06, 0.013), "tube")
    b.ring("coil_b", 0.052, 0.011, (-0.24, -0.13, 0.013), "tube")
    return b.parts


PIECES = (
    ("glassware", glassware_rig),
    ("burner", burner_and_pot),
    ("jugs", jug_rack),
)


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    make_texture()
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
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
    mats = materials()
    merged = None
    cells, elements = [], {}

    for name, builder in PIECES:
        parts = builder(mats)
        for part in parts:
            part.parent = subject
        props.sheet_name = f"{SHEET}_{name}"
        manifest = F.render_cells(bpy.context)
        if merged is None:
            merged = dict(manifest)
        cells += list(manifest["cells"])
        elements.update(manifest.get("elements", {}))
        for part in parts:
            bpy.data.objects.remove(part, do_unlink=True)

    merged["sheet"] = SHEET
    # Three different objects share every facing, so each cell styles alone.
    merged["isolate_tiles"] = True
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2),
                                       encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT} "
          f"({len(PIECES)} pieces x 4 facings)")


if __name__ == "__main__":
    main()
