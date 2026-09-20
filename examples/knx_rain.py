"""BADLANDS rain collection: four rain barrels that work exactly like vanilla's (entity
FluidContainer + RainFactor, tile prop IsWaterCollector), from the operator's photos:

    group 0  Drum Rain Barrel    blue 55-gal drum on cinder blocks, PVC downspout elbow,
                                 yellow hose spigot                          (S only, round)
    group 1  Barrel Stand        grey ribbed lidded barrel on a 4x4 stand, hose coil (S only)
    group 2  Twin Can Collector  two lidded trash cans on a slatted bench, PVC link,
                                 screened inlet, hose bib                     (S,E,N,W)
    group 3  Drum Rack           three blue drums lying in a treated-lumber rack, PVC
                                 manifold and inlet funnel                    (S,E,N,W, wall)

All four are closed, like every photo: water is never visible, so no fill-state sprite
and no Lua -- the vanilla engine does all of it.  Sheet badlands_rain_01; with the group
stamp the order is 0 drum, 1 stand, 2-5 twin S/E/N/W, 6-9 rack S/E/N/W.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b -P examples/knx_rain.py
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

OUT = ROOT / "build" / "rain_cells"
SHEET = "badlands_rain_01"
GRAIN_PATH = ROOT / "build" / "rain_lumber_grain.png"
OFFSET_Z = -2.0 / 77.2

# Cloned from vanilla carpentry_02_122 (the round rain collector barrel).
RAIN_PROPS = {
    "BlocksPlacement": "", "CanScrap": "", "IsMoveAble": "", "IsWaterCollector": "",
    "Material": "Wood", "Material2": "PlasticBag", "PickUpWeight": "75", "solidtrans": "",
}
PIECES = [
    # key, CustomName, facings kept, wall offset (m toward the back of the tile)
    ("drum", "Drum Rain Barrel", ("S",), 0.0),
    ("stand", "Barrel Stand", ("S",), 0.0),
    ("twin", "Twin Can Collector", ("S", "E", "N", "W"), 0.0),
    ("rack", "Drum Rack", ("S", "E", "N", "W"), 0.17),
]


class Builder:
    def __init__(self, offset_y: float = 0.0) -> None:
        self.parts: list[bpy.types.Object] = []
        self.oy = offset_y

    def _loc(self, c):
        return (c[0], c[1] + self.oy, c[2] + OFFSET_Z)

    def _place(self, obj, name, material):
        obj.name = name
        obj.data.materials.append(material)
        self.parts.append(obj)
        return obj

    def box(self, name, centre, size, material, rot=(0.0, 0.0, 0.0)):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=self._loc(centre))
        obj = bpy.context.active_object
        obj.scale = size
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def cyl(self, name, centre, radius, length, material, rot=(0.0, 0.0, 0.0), vertices=24):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=vertices,
                                            location=self._loc(centre))
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def cone(self, name, centre, r1, r2, length, material, rot=(0.0, 0.0, 0.0), vertices=24):
        bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=length, vertices=vertices,
                                        location=self._loc(centre))
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)

    def torus(self, name, centre, major, minor, material, rot=(0.0, 0.0, 0.0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                         major_segments=32, minor_segments=8,
                                         location=self._loc(centre))
        obj = bpy.context.active_object
        obj.rotation_euler = rot
        return self._place(obj, name, material)


def make_textures() -> None:
    sys.path.insert(0, str(ROOT))
    import dataclasses

    from pzforge.texture import material_spec, write_surface_map

    spec = material_spec("wood", seed=31)
    spec = dataclasses.replace(
        spec, octaves=[(s, a * 0.13) for s, a in spec.octaves],
        stroke_count=90, stroke_amplitude=0.06, knot_count=1, knot_depth=0.06)
    write_surface_map(GRAIN_PATH, 512, 512, spec, grain_axis="v")


def materials() -> dict:
    grain = str(GRAIN_PATH)
    t = F.toon_material
    # Pressure-treated lumber: pale with a green cast.  Narrow swing -- the wood
    # class default (0.40-1.60) turns pale stock into camo (seating lesson).
    LUMBER = (0.700, 0.610, 0.400)
    wood = lambda n, c: F.forge_material(n, "wood", c, texture_path=grain, swing=(0.84, 1.10))
    return {
        "lumber": wood("rn_lumber", LUMBER),
        "lumber_dark": wood("rn_lumber_dark", tuple(c * 0.72 for c in LUMBER)),
        # Plastics are flat toon paint: the metal class's steel hue correction
        # would drag blue HDPE toward grey.
        "hdpe_blue": t("rn_hdpe_blue", (0.040, 0.260, 0.640)),
        "hdpe_blue_dark": t("rn_hdpe_blue_dark", (0.025, 0.160, 0.420)),
        "hdpe_grime": t("rn_hdpe_grime", (0.050, 0.140, 0.260)),
        "grey_barrel": t("rn_grey_barrel", (0.200, 0.210, 0.215)),
        "grey_barrel_dark": t("rn_grey_barrel_dark", (0.110, 0.115, 0.120)),
        "can_grey": t("rn_can_grey", (0.380, 0.390, 0.395)),
        "can_grey_dark": t("rn_can_grey_dark", (0.250, 0.255, 0.260)),
        "pvc": t("rn_pvc", (0.820, 0.820, 0.790)),
        "pvc_shade": t("rn_pvc_shade", (0.640, 0.640, 0.610)),
        "brass": t("rn_brass", (0.620, 0.480, 0.160)),
        "yellow": t("rn_yellow", (0.880, 0.700, 0.060)),
        "valve_blue": t("rn_valve_blue", (0.080, 0.220, 0.700)),
        "cinder": t("rn_cinder", (0.500, 0.490, 0.460)),
        "cinder_hole": t("rn_cinder_hole", (0.200, 0.195, 0.180)),
        "hose": t("rn_hose", (0.080, 0.360, 0.220)),
        "screen": t("rn_screen", (0.700, 0.720, 0.700)),
        "black": t("rn_black", (0.060, 0.060, 0.065)),
    }


def build_drum(b: Builder, m: dict) -> None:
    # two cinder blocks side by side, cores showing on the front
    for k, x in enumerate((-0.20, 0.20)):
        b.box(f"block_{k}", (x, 0.0, 0.10), (0.39, 0.40, 0.20), m["cinder"])
        for j, dx in enumerate((-0.09, 0.09)):
            b.box(f"core_{k}_{j}", (x + dx, -0.201, 0.10), (0.12, 0.004, 0.12), m["cinder_hole"])
    r, z0, h = 0.29, 0.20, 0.88
    b.cyl("drum", (0, 0, z0 + h / 2), r, h, m["hdpe_blue"])
    for k, zz in enumerate((z0 + h * 0.34, z0 + h * 0.67)):   # rolling hoops
        b.cyl(f"hoop_{k}", (0, 0, zz), r + 0.008, 0.035, m["hdpe_blue_dark"])
    b.torus("chime", (0, 0, z0 + h), r - 0.012, 0.016, m["hdpe_blue_dark"])
    b.cyl("top", (0, 0, z0 + h - 0.012), r - 0.02, 0.012, m["hdpe_blue_dark"])
    b.cyl("bung", (-0.15, -0.10, z0 + h + 0.005), 0.035, 0.02, m["brass"])
    # the downspout elbow: up from the far bung, over and back toward the wall
    b.cyl("inlet_bush", (0.12, 0.08, z0 + h + 0.01), 0.048, 0.03, m["pvc_shade"])
    b.cyl("inlet_riser", (0.12, 0.08, z0 + h + 0.15), 0.036, 0.28, m["pvc"])
    b.cyl("inlet_elbow", (0.12, 0.12, z0 + h + 0.30), 0.042, 0.10, m["pvc_shade"],
          rot=(math.pi / 2, 0, 0))
    b.cyl("inlet_run", (0.12, 0.30, z0 + h + 0.30), 0.036, 0.30, m["pvc"],
          rot=(math.pi / 2, 0, 0))
    # hose spigot low on the front, yellow wheel handle
    b.cyl("spigot", (0.0, -r - 0.03, z0 + 0.12), 0.016, 0.07, m["brass"], rot=(math.pi / 2, 0, 0))
    b.cyl("spigot_wheel", (0.0, -r - 0.07, z0 + 0.12), 0.040, 0.014, m["yellow"],
          rot=(math.pi / 2, 0, 0), vertices=8)
    # two drip stains down the front-left, like the photo
    for k, (ang, top, ln) in enumerate(((-0.55, 0.78, 0.55), (-0.30, 0.70, 0.35))):
        x, y = r * math.sin(ang), -r * math.cos(ang)
        b.box(f"stain_{k}", (x * 1.012, y * 1.012, z0 + top - ln / 2), (0.028, 0.004, ln),
              m["hdpe_grime"], rot=(0, 0, ang))


def ribbed_barrel(b, tag, m, x, y, z0, r=0.27, h=0.88, body="grey_barrel", rib="grey_barrel_dark",
                  lid="black"):
    """Grey tight-head plastic barrel: ribs, a moulded handle pocket, screw lid."""
    b.cyl(f"{tag}_body", (x, y, z0 + h / 2), r, h, m[body])
    for k, f in enumerate((0.18, 0.40, 0.62, 0.82)):
        b.cyl(f"{tag}_rib_{k}", (x, y, z0 + h * f), r + 0.010, 0.030, m[rib])
    b.box(f"{tag}_pocket", (x, y - r + 0.01, z0 + h * 0.90), (0.16, 0.02, 0.06), m[rib])
    b.cyl(f"{tag}_lid", (x, y, z0 + h + 0.03), r + 0.012, 0.06, m[lid])
    b.cyl(f"{tag}_knob", (x + 0.06, y - 0.08, z0 + h + 0.075), 0.022, 0.03, m[lid])


def build_stand(b: Builder, m: dict) -> None:
    top = 0.42
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}", (sx * 0.30, sy * 0.30, top / 2), (0.09, 0.09, top), m["lumber"])
    for k in range(4):
        b.box(f"deck_{k}", (0, -0.27 + k * 0.18, top + 0.02), (0.72, 0.16, 0.04), m["lumber"])
    b.box("apron", (0, -0.35, top - 0.05), (0.70, 0.03, 0.10), m["lumber_dark"])
    ribbed_barrel(b, "barrel", m, 0.0, 0.02, top + 0.04)
    b.cyl("tap", (0.10, -0.28, top + 0.14), 0.014, 0.06, m["black"], rot=(math.pi / 2, 0, 0))
    # garden hose coiled and hung on the front-left post
    for k in range(2):
        b.torus(f"hose_{k}", (-0.34, -0.37 - k * 0.012, 0.24), 0.10, 0.014, m["hose"],
                rot=(math.pi / 2, 0, 0))


def build_twin(b: Builder, m: dict) -> None:
    top = 0.44
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"leg_{sx}_{sy}", (sx * 0.42, sy * 0.24, top / 2), (0.07, 0.07, top), m["lumber"])
        b.box(f"stretch_{sx}", (sx * 0.42, 0, 0.12), (0.06, 0.48, 0.06), m["lumber_dark"])
    for k in range(5):
        b.box(f"slat_{k}", (0, -0.24 + k * 0.12, top + 0.02), (0.94, 0.10, 0.04), m["lumber"])
    for k, x in enumerate((-0.235, 0.235)):
        b.cone(f"can_{k}", (x, 0.02, top + 0.04 + 0.34), 0.19, 0.225, 0.68, m["can_grey"])
        b.torus(f"can_rim_{k}", (x, 0.02, top + 0.73), 0.225, 0.016, m["can_grey_dark"])
        b.cyl(f"can_lid_{k}", (x, 0.02, top + 0.75), 0.238, 0.04, m["can_grey"])
        for sx in (-1, 1):
            b.box(f"can_handle_{k}_{sx}", (x + sx * 0.235, 0.02, top + 0.64), (0.03, 0.10, 0.04),
                  m["can_grey_dark"])
    b.cyl("screen", (-0.235, 0.02, top + 0.773), 0.10, 0.006, m["screen"])
    # PVC under the bench: a drop from each can, a run between them, tee to the front bib
    for k, x in enumerate((-0.235, 0.235)):
        b.cyl(f"drop_{k}", (x, 0.02, top - 0.10), 0.026, 0.20, m["pvc"])
    b.cyl("run", (0, 0.02, top - 0.20), 0.026, 0.50, m["pvc"], rot=(0, math.pi / 2, 0))
    b.cyl("tee_out", (0, -0.14, top - 0.20), 0.024, 0.32, m["pvc"], rot=(math.pi / 2, 0, 0))
    b.cyl("valve", (0, -0.28, top - 0.20), 0.034, 0.06, m["pvc_shade"], rot=(math.pi / 2, 0, 0))
    b.box("valve_lever", (0.04, -0.28, top - 0.155), (0.09, 0.02, 0.015), m["yellow"])
    b.cyl("bib", (0, -0.32, top - 0.22), 0.018, 0.05, m["brass"])


def build_rack(b: Builder, m: dict) -> None:
    H, D = 2.00, 0.62
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}", (sx * 0.465, sy * (D / 2 - 0.035), H / 2), (0.07, 0.07, H),
                  m["lumber"])
    r, ln = 0.285, 0.80
    centres = (0.37, 1.03, 1.69)
    for k, zc in enumerate(centres):
        for sy in (-1, 1):   # 2x4 rails the drum sits in, front and back
            b.box(f"rail_{k}_{sy}", (0, sy * (D / 2 - 0.035), zc - r - 0.03), (0.86, 0.05, 0.09),
                  m["lumber"])
        b.cyl(f"drum_{k}", (0, 0, zc), r, ln, m["hdpe_blue"], rot=(0, math.pi / 2, 0))
        for j, x in enumerate((-0.22, 0.22)):
            b.cyl(f"hoop_{k}_{j}", (x, 0, zc), r + 0.008, 0.03, m["hdpe_blue_dark"],
                  rot=(0, math.pi / 2, 0))
        b.torus(f"chime_{k}", (ln / 2, 0, zc), r - 0.012, 0.014, m["hdpe_blue_dark"],
                rot=(0, math.pi / 2, 0))
        b.cyl(f"bung_top_{k}", (ln / 2 + 0.006, 0.0, zc + 0.19), 0.032, 0.02, m["pvc"],
              rot=(0, math.pi / 2, 0))
        # lower bung teed into the manifold
        b.cyl(f"tie_{k}", (ln / 2 + 0.04, 0.0, zc - 0.17), 0.026, 0.09, m["pvc"],
              rot=(0, math.pi / 2, 0))
        b.cyl(f"tee_{k}", (0.455, 0.0, zc - 0.17), 0.034, 0.07, m["pvc_shade"])
    b.box("cap", (0, 0, H - 0.02), (1.0, D, 0.04), m["lumber"])
    for k, z0 in enumerate((0.06, 0.72)):   # braces on the far end, out of the S view
        b.box(f"brace_{k}", (-0.465, 0, z0 + 0.33), (0.04, 0.05, 0.78), m["lumber_dark"],
              rot=(0.72, 0, 0))
    # manifold: vertical run on the near end, inlet funnel on top, drain valve low
    b.cyl("manifold", (0.455, 0.0, 1.02), 0.028, 1.80, m["pvc"])
    b.cone("funnel", (0.455, 0.0, 2.02), 0.030, 0.075, 0.10, m["pvc"])
    b.cyl("overflow", (0.455, 0.12, 1.25), 0.024, 1.40, m["pvc_shade"])
    b.cyl("drain_valve", (0.455, -0.06, 0.10), 0.032, 0.08, m["pvc_shade"], rot=(math.pi / 2, 0, 0))
    b.box("drain_lever", (0.455, -0.10, 0.14), (0.02, 0.02, 0.06), m["valve_blue"])


def build_wash(b: Builder, m: dict) -> None:
    """Tall gravity wash station: a drum up top, a basin at hip height under it."""
    # Platform at 1.52, not 1.30: the game camera (~30 deg) looks up under the platform,
    # and at 1.30 its front edge hid the whole faucet.  Faucet also sits forward.
    H = 1.52          # drum platform
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}", (sx * 0.43, sy * 0.25, H / 2), (0.08, 0.08, H), m["lumber"])
    for k in range(4):
        b.box(f"plat_{k}", (0, -0.23 + k * 0.155, H + 0.02), (0.94, 0.14, 0.04), m["lumber"])
    b.box("plat_apron", (0, -0.30, H - 0.05), (0.92, 0.03, 0.10), m["lumber_dark"])
    r, h = 0.28, 0.66
    b.cyl("drum", (0, 0.03, H + 0.04 + h / 2), r, h, m["hdpe_blue"])
    for k, f in enumerate((0.35, 0.68)):
        b.cyl(f"hoop_{k}", (0, 0.03, H + 0.04 + h * f), r + 0.008, 0.03, m["hdpe_blue_dark"])
    b.torus("chime", (0, 0.03, H + 0.04 + h), r - 0.012, 0.016, m["hdpe_blue_dark"])
    b.cyl("screen", (0, 0.03, H + 0.04 + h - 0.004), 0.20, 0.008, m["screen"])
    # counter + basin
    C = 0.82
    b.box("counter", (0, -0.02, C), (0.94, 0.50, 0.05), m["lumber"])
    b.box("counter_apron", (0, -0.27, C - 0.06), (0.92, 0.03, 0.10), m["lumber_dark"])
    b.box("basin", (0, -0.03, C + 0.035), (0.46, 0.36, 0.12), m["can_grey"])
    b.box("basin_well", (0, -0.03, C + 0.066), (0.40, 0.30, 0.06), m["can_grey_dark"])
    b.cyl("drain", (0, -0.03, C + 0.037), 0.025, 0.004, m["black"])
    # gravity feed: out of the drum's belly, down the back, gooseneck over the basin
    b.cyl("feed_out", (0.12, 0.20, H - 0.02), 0.024, 0.12, m["pvc"])
    b.cyl("feed_down", (0.12, 0.20, (H + C) / 2 + 0.06), 0.024, H - C - 0.06, m["pvc"])
    b.cyl("faucet_riser", (0.12, 0.13, C + 0.17), 0.020, 0.28, m["brass"])
    b.cyl("faucet_arm", (0.12, 0.02, C + 0.31), 0.018, 0.24, m["brass"], rot=(math.pi / 2, 0, 0))
    b.cyl("faucet_spout", (0.12, -0.10, C + 0.26), 0.018, 0.10, m["brass"])
    b.cyl("faucet_handle", (0.12, 0.13, C + 0.33), 0.042, 0.016, m["yellow"], vertices=8)
    # drain pipe down into a bucket
    b.cyl("tail", (0.0, -0.03, C - 0.12), 0.022, 0.20, m["pvc"])
    b.cone("bucket", (0.0, -0.03, 0.14), 0.13, 0.16, 0.28, m["valve_blue"])
    b.torus("bucket_rim", (0.0, -0.03, 0.28), 0.16, 0.012, m["valve_blue"])
    # shelf rail low between the legs, a bar of soap and a rag on the counter edge
    b.box("low_rail", (0, 0.25, 0.20), (0.86, 0.05, 0.06), m["lumber_dark"])
    b.box("soap", (0.33, -0.10, C + 0.045), (0.07, 0.045, 0.03), m["screen"])
    b.box("rag", (-0.33, -0.12, C + 0.03), (0.14, 0.12, 0.012), m["hose"])


def build_shower(b: Builder, m: dict, closed: bool = False) -> None:
    """Makeshift shower: a black drum up top (sun-warmed), gravity down to a pull-chain
    head, pallet floor, tarp on the back and far side, a curtain half drawn on the front."""
    H = 1.82
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}", (sx * 0.44, sy * 0.44, H / 2), (0.07, 0.07, H), m["lumber"])
    for k in range(4):
        b.box(f"plat_{k}", (0, -0.36 + k * 0.24, H + 0.02), (0.95, 0.20, 0.04), m["lumber"])
    r, h = 0.26, 0.56
    b.cyl("drum", (0, 0.06, H + 0.04 + h / 2), r, h, m["black"])
    for k, f in enumerate((0.35, 0.68)):
        b.cyl(f"hoop_{k}", (0, 0.06, H + 0.04 + h * f), r + 0.008, 0.03, m["grey_barrel_dark"])
    b.torus("chime", (0, 0.06, H + 0.04 + h), r - 0.012, 0.014, m["grey_barrel_dark"])
    # pallet floor
    for k in range(5):
        b.box(f"floor_{k}", (0, -0.38 + k * 0.19, 0.07), (0.86, 0.15, 0.03), m["lumber"])
    for k, x in enumerate((-0.38, 0.0, 0.38)):
        b.box(f"floor_str_{k}", (x, 0, 0.03), (0.07, 0.86, 0.05), m["lumber_dark"])
    # tarp walls: back (+Y) and the far side (-X), hung from a top rail, sagging a little
    b.box("rail_back", (0, 0.44, H - 0.06), (0.88, 0.05, 0.05), m["lumber_dark"])
    b.box("rail_side", (-0.44, 0, H - 0.06), (0.05, 0.88, 0.05), m["lumber_dark"])
    b.box("tarp_back", (0, 0.425, (H - 0.08 + 0.25) / 2), (0.86, 0.012, H - 0.33), m["valve_blue"])
    b.box("tarp_side", (-0.425, 0, (H - 0.08 + 0.25) / 2), (0.012, 0.86, H - 0.33), m["valve_blue"])
    for k, zz in enumerate((0.55, 1.05)):   # tie-downs
        b.box(f"tie_b_{k}", (0.43, 0.43, zz), (0.03, 0.03, 0.03), m["hose"])
    # front curtain on a rod.  Open: bunched to the near-left (stripes read as folds).
    # Closed: drawn right across the front -- the KNX_ShowerClosed entity's sprite.
    b.cyl("rod", (0, -0.44, H - 0.10), 0.012, 0.90, m["brass"], rot=(0, math.pi / 2, 0))
    if closed:
        n = 16
        for k in range(n):
            x = -0.42 + k * (0.84 / (n - 1))
            b.box(f"curtain_{k}", (x, -0.445 + (k % 2) * 0.018, (H - 0.12 + 0.30) / 2),
                  (0.058, 0.02, H - 0.42), m["valve_blue"] if k % 2 else m["hdpe_blue_dark"])
    else:
        for k in range(4):
            b.box(f"curtain_{k}", (-0.40 + k * 0.05, -0.445 + (k % 2) * 0.02, (H - 0.12 + 0.35) / 2),
                  (0.05, 0.02, H - 0.47), m["valve_blue"] if k % 2 else m["hdpe_blue_dark"])
    # feed: out of the drum floor, down the back post, over to a head in the middle
    # The head hangs toward the open front-right corner: centred, the platform edge hid
    # it from the game camera.  Feed runs down the near-right post, then inward.
    b.cyl("feed_down", (0.38, 0.30, H - 0.16), 0.022, 0.34, m["pvc"])
    b.cyl("feed_elbow", (0.38, 0.12, H - 0.33), 0.022, 0.38, m["pvc"], rot=(math.pi / 2, 0, 0))
    b.cyl("feed_drop", (0.38, -0.07, H - 0.40), 0.022, 0.14, m["pvc"])
    b.cone("head", (0.38, -0.07, H - 0.50), 0.03, 0.10, 0.07, m["brass"], rot=(math.pi, 0, 0))
    b.cyl("chain", (0.30, -0.07, H - 0.68), 0.005, 0.34, m["brass"], vertices=6)
    b.box("chain_pull", (0.30, -0.07, H - 0.86), (0.035, 0.035, 0.05), m["yellow"])
    # soap shelf on the near-right post
    b.box("shelf", (0.38, 0.38, 1.05), (0.14, 0.10, 0.02), m["lumber_dark"])
    b.box("soap", (0.38, 0.38, 1.075), (0.07, 0.045, 0.03), m["screen"])


BUILDERS = {"drum": build_drum, "stand": build_stand, "twin": build_twin,
            "rack": build_rack, "wash": build_wash, "shower": build_shower,
            "showerc": lambda b, m: build_shower(b, m, closed=True)}
PIECES += [
    ("wash", "Wash Station", ("S", "E", "N", "W"), 0.0),
    ("shower", "Makeshift Shower", ("S", "E", "N", "W"), 0.0),
    # group 6, sheet 18-21: the same stall with the curtain drawn (KNX_ShowerClosed)
    ("showerc", "Makeshift Shower", ("S", "E", "N", "W"), 0.0),
]


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
    for group, (key, cname, facings, offset) in enumerate(PIECES):
        if only and key != only:
            continue
        b = Builder(offset)
        BUILDERS[key](b, m)
        names = [o.name for o in b.parts]
        for part in b.parts:
            part.parent = subject
        props.sheet_name = f"rn_{key}"
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
            if f not in facings:
                continue
            tile = dict(RAIN_PROPS, CustomName=cname)
            if len(facings) > 1:
                tile["Facing"] = f
            if key == "rack":
                tile.pop("solidtrans", None)
                tile["solid"] = ""
            elif key in ("shower", "showerc"):
                # walk-in: no solid/solidtrans, so a player can stand in the stall
                tile.pop("solidtrans", None)
            cells.append(dict(cell, group=group, tile_props=tile))
        print(f"== {key}: {len(names)} parts, {len(facings)} facing(s)")

    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"rendered {len(cells)} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
