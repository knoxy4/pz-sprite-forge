"""Badlands Power: the bank and four generators, each modelled on a real machine class.

v1 of this recipe was four boxes in four paints under a shared roll cage, and
it rendered through plain Principled BSDF -- which skips the forge's measured
material classes entirely, so the sprites came out as clean CAD instead of
vanilla paint. v2 fixes both halves:

* every part takes a ``F.forge_material`` metal-class paint over a generated
  wear map, rendered with ``toon_shading`` like metal_still.py;
* every variant is a recognisable real-world machine, with its own silhouette
  on all four faces rather than one dressed face and three blank ones.

    propane   dual-fuel open-frame portable (~4 kW class, operator
              reference): green tube frame, black tank shroud and control
              face, bare engine low, 20 lb bottle alongside on a hose.
    wasteoil  slow-speed single-cylinder stationary diesel (the Lister CS
              pattern people run on filtered waste oil): green engine on a
              channel skid, twin spoked flywheels, belt-free coupled alternator
              head, stack muffler, feed drum and spin-on filter.
    scrap     a small suitcase portable (operator reference) that has had a
              hard life: dirty shroud, rusted recoil, duct tape, a wooden
              shim for a lost foot, bungee, jerry can alongside.
    diesel    the big slot, a 10 kW wheeled open-frame portable (operator
              reference): black tube frame, wheels and fold-out handles,
              crimson tank shroud, mesh side panels, outlet panel, round
              alternator grille, onboard starter battery.
    bank      five deep-cycle batteries on a block pallet, in series, main
              leads up to an inverter on an OSB backboard (operator photo).

Scale is measured, not eyeballed. Vanilla (tools/show_sprite.py):

    appliances_misc_01_0   Generator          0.492 tiles, 0.625 m
    appliances_misc_01_4   Generator_Old      0.648 tiles, 0.804 m

The scrap suitcase portable is deliberately SMALLER than vanilla's 0.625 m
(the real class is ~0.38 m tall); the stationary diesel is the one set allowed to fill
most of a tile, because a 10 kW frame set is a big object.
Coordinates are metres, tile = 1 m; -Y is the face the S camera sees
(with +X), so each machine puts its busiest face on -Y.

Run one variant:
    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" -b \
        -P examples/knx_gensets.py -- propane
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

TEXTURE_PATH = ROOT / "build" / "genset_surface.png"
VARIANTS = ("bank", "propane", "wasteoil", "scrap", "diesel")
KEEP_HUE = (lambda p: p)


def make_texture() -> Path:
    sys.path.insert(0, str(ROOT))
    from pzforge.texture import material_spec, write_surface_map

    return write_surface_map(TEXTURE_PATH, 512, 256,
                             material_spec("metal", seed=31))


# ---------------------------------------------------------------- materials

def materials() -> dict:
    """Stage 1. Painted parts keep their own hue (the steel correction would
    grey out Lister green and canopy yellow); bare steel takes the class hue.
    Accent = the class's rust stop, confined to the darkest wear streaks."""
    t = TEXTURE_PATH
    rust = (0.330, 0.160, 0.075)

    def worn(name, colour, accent=None, pos=None):
        return F.forge_material(name, "metal", colour, texture_path=t,
                                hue=KEEP_HUE, accent=accent,
                                accent_position=pos)

    def flat(name, colour, hue=KEEP_HUE):
        return F.forge_material(name, "metal", colour, hue=hue)

    return {
        # shared
        "rubber": flat("g_rubber", (0.060, 0.058, 0.056)),
        "gap": flat("g_gap", (0.035, 0.034, 0.033)),
        "black_plastic": worn("g_black_plastic", (0.105, 0.103, 0.100)),
        "steel": F.forge_material("g_steel", "metal", texture_path=t,
                                  dark=(0.300, 0.295, 0.285),
                                  light=(0.690, 0.680, 0.660),
                                  accent=(0.320, 0.270, 0.230)),
        "chrome": flat("g_chrome", (0.820, 0.820, 0.800)),
        "rusty": worn("g_rusty", (0.300, 0.190, 0.120), accent=rust, pos=0.30),
        "outlet": flat("g_outlet", (0.620, 0.610, 0.585)),
        "lamp_green": flat("g_lamp_green", (0.300, 1.000, 0.260)),
        "estop": flat("g_estop", (0.900, 0.090, 0.060)),
        "sticker_white": flat("g_sticker_w", (0.880, 0.870, 0.820)),
        "sticker_yellow": flat("g_sticker_y", (0.980, 0.800, 0.100)),
        "wood": F.forge_material("g_wood", "wood", (0.640, 0.450, 0.240)),
        "hose": flat("g_hose", (0.080, 0.078, 0.075)),
        # propane dual-fuel
        "frame_green": worn("g_frame_green", (0.300, 0.440, 0.170)),
        "olive_label": flat("g_olive_label", (0.330, 0.380, 0.150)),
        "gold": flat("g_gold", (0.850, 0.680, 0.300)),
        "alu": worn("g_alu", (0.560, 0.560, 0.540)),
        "brass": flat("g_brass", (0.720, 0.540, 0.220)),
        # scrap suitcase portable
        "shroud_dirty": worn("g_shroud_dirty", (0.740, 0.720, 0.660),
                             accent=(0.330, 0.160, 0.075), pos=0.16),
        # Clean paint, no rust stop: at pos 0.10 the wear map still streaked
        # the whole bottle brown (contact sheet v2).
        "bottle": worn("g_bottle", (0.800, 0.795, 0.760)),
        # waste-oil stationary
        "lister_green": worn("g_lister_green", (0.150, 0.300, 0.190),
                             accent=rust, pos=0.14),
        "alt_grey": worn("g_alt_grey", (0.390, 0.420, 0.440)),
        # No rust stop on near-black paint: rust (0.33, 0.16, 0.075) is
        # BRIGHTER than the paint, so every dark streak turned brown and the
        # drum read as a wooden barrel. Weathering comes from the lid instead.
        "drum_black": worn("g_drum_black", (0.095, 0.092, 0.090)),
        "filter_blue": flat("g_filter_blue", (0.120, 0.240, 0.520)),
        # scrap
        "jerry_red": worn("g_jerry_red", (0.700, 0.150, 0.090), accent=rust,
                          pos=0.16),
        "bungee": flat("g_bungee", (0.950, 0.720, 0.080)),
        "tape": flat("g_tape", (0.560, 0.565, 0.570)),
        "cable_red": flat("g_cable_red", (0.780, 0.100, 0.070)),
        "base_grey": worn("g_base_grey", (0.200, 0.200, 0.205), accent=rust,
                          pos=0.20),
        # 10 kW portable -- a deep crimson, clear of vanilla's orange-red
        # Generator (1.000, 0.316, 0.264)
        # Same brighter-than-paint rust problem as the drum: browned the lid.
        "crimson": worn("g_crimson", (0.560, 0.045, 0.060)),
        "crimson_dark": flat("g_crimson_dark", (0.300, 0.030, 0.035)),
        "frame": worn("g_frame", (0.070, 0.068, 0.066)),
        "mesh": flat("g_mesh", (0.170, 0.168, 0.165)),
        "panel_grey": worn("g_panel_grey", (0.260, 0.265, 0.260)),
        "battery_white": worn("g_battery_white", (0.850, 0.850, 0.820)),
        # battery bank
        "pine": F.forge_material("g_pine", "wood", (0.820, 0.640, 0.380)),
        "pine_dark": F.forge_material("g_pine_dark", "wood",
                                      (0.620, 0.460, 0.250)),
        "osb": F.forge_material("g_osb", "wood", (0.720, 0.530, 0.290)),
        "batt_case": worn("g_batt_case", (0.075, 0.074, 0.072)),
        "label_purple": flat("g_label_purple", (0.330, 0.160, 0.420)),
        "lead": flat("g_lead", (0.560, 0.560, 0.560)),
    }


# ---------------------------------------------------------------- primitives

class Kit:
    """Part builders that record everything they make."""

    def __init__(self):
        self.parts: list[bpy.types.Object] = []

    def _add(self, obj, name, material, bevel=0.0):
        obj.name = name
        obj.data.materials.append(material)
        if bevel:
            mod = obj.modifiers.new("bevel", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = "ANGLE"
        self.parts.append(obj)
        return obj

    def box(self, name, centre, size, material, bevel=0.0, rot=None):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
        obj = bpy.context.active_object
        obj.scale = size
        if rot:
            obj.rotation_euler = rot
        if bevel:
            bpy.ops.object.transform_apply(location=False, rotation=False,
                                           scale=True)
        return self._add(obj, name, material, bevel)

    def cyl(self, name, centre, r, depth, material, axis="Z", verts=32,
            smooth=True):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r,
                                            depth=depth, location=centre)
        obj = bpy.context.active_object
        obj.rotation_euler = {"X": (0, math.pi / 2, 0),
                              "Y": (math.pi / 2, 0, 0),
                              "Z": (0, 0, 0)}[axis]
        if smooth:
            _smooth()
        return self._add(obj, name, material)

    def torus(self, name, centre, major, minor, material, axis="Z"):
        bpy.ops.mesh.primitive_torus_add(major_radius=major,
                                         minor_radius=minor,
                                         major_segments=40, minor_segments=8,
                                         location=centre)
        obj = bpy.context.active_object
        obj.rotation_euler = {"X": (0, math.pi / 2, 0),
                              "Y": (math.pi / 2, 0, 0),
                              "Z": (0, 0, 0)}[axis]
        _smooth()
        return self._add(obj, name, material)

    def sphere(self, name, centre, r, material, scale=(1, 1, 1)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12,
                                             radius=r, location=centre)
        obj = bpy.context.active_object
        obj.scale = scale
        _smooth()
        return self._add(obj, name, material)

    def rod(self, name, a, b, r, material, verts=12):
        """A straight tube between two points -- handles, pipes, hoses."""
        d = tuple(b[i] - a[i] for i in range(3))
        length = math.sqrt(sum(c * c for c in d))
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=verts, radius=r, depth=length,
            location=tuple((a[i] + b[i]) / 2 for i in range(3)))
        obj = bpy.context.active_object
        obj.rotation_euler = (0.0, math.acos(max(-1, min(1, d[2] / length))),
                              math.atan2(d[1], d[0]))
        _smooth()
        return self._add(obj, name, material)

    def path(self, name, points, r, material):
        for i in range(len(points) - 1):
            self.rod(f"{name}_{i}", points[i], points[i + 1], r, material)
        for i, p in enumerate(points[1:-1]):
            self.sphere(f"{name}_j{i}", p, r, material)


def _smooth():
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
    except (AttributeError, TypeError, RuntimeError):
        bpy.ops.object.shade_smooth()


# ---------------------------------------------------------------- shared

def build_bottle(k: Kit, m: dict, bx: float, by: float, hose_to) -> None:
    """A 20 lb propane bottle (0.31 m dia, 0.46 m tall): foot ring, welded
    body, domed top, collar with the carry cut-outs, valve, hose to ``hose_to``."""
    br, bh = 0.150, 0.330
    k.cyl("pb_foot", (bx, by, 0.030), br * 0.88, 0.060, m["steel"])
    k.cyl("pb_body", (bx, by, 0.060 + bh / 2), br, bh, m["bottle"], verts=40)
    k.sphere("pb_dome", (bx, by, 0.060 + bh), br, m["bottle"],
             scale=(1, 1, 0.38))
    k.torus("pb_weld", (bx, by, 0.060 + bh * 0.50), br, 0.005, m["gap"])
    top = 0.060 + bh + br * 0.38
    k.cyl("pb_collar", (bx, by, top + 0.045), 0.095, 0.100, m["bottle"])
    k.cyl("pb_collar_bore", (bx, by, top + 0.070), 0.080, 0.080, m["gap"])
    for i, a in enumerate((0.0, math.pi / 2, math.pi, 1.5 * math.pi)):
        k.box(f"pb_collar_cut_{i}", (bx + math.cos(a) * 0.093,
                                     by + math.sin(a) * 0.093, top + 0.070),
              (0.050, 0.050, 0.040), m["gap"], rot=(0, 0, a))
    k.cyl("pb_valve", (bx, by, top + 0.035), 0.022, 0.060, m["brass"])
    k.cyl("pb_valve_wheel", (bx, by, top + 0.075), 0.030, 0.012, m["brass"],
          verts=16)
    k.box("pb_tag", (bx + 0.050, by - br * 0.95, 0.060 + bh * 0.72),
          (0.070, 0.006, 0.045), m["sticker_yellow"], rot=(0, 0, 0.35))
    k.path("pb_hose", [(bx + 0.025, by - 0.010, top + 0.030),
                       (bx + 0.080, by - 0.030, top + 0.010),
                       (bx + 0.140, by - 0.050, hose_to[2] + 0.080),
                       hose_to], 0.012, m["hose"])


# ---------------------------------------------------------------- propane

def build_propane(k: Kit, m: dict) -> None:
    """Dual-fuel open-frame portable after the operator's reference (~4 kW
    class, ~0.58 x 0.44 x 0.44 m): green tubular frame as two end hoops tied
    by base rails, black fuel-tank shroud with a trim band, black control
    face with the olive fuel panel, red rocker, analog voltmeter, outlets and
    a twist-lock; bare aluminium engine low under the panel; the 20 lb bottle
    beside it on the hose."""
    gx = 0.110                # generator centre; bottle at -X
    L, W = 0.560, 0.420
    tube = 0.020
    top = 0.470
    fr = m["frame_green"]
    # End hoops: legs up, over the top along Y; base rails along X.
    for sx in (-1, 1):
        x = gx + sx * L / 2
        k.path(f"q_hoop_{sx}", [(x, -W / 2, 0.030), (x, -W / 2, top - 0.04),
                                (x, -W / 2 + 0.04, top),
                                (x, W / 2 - 0.04, top),
                                (x, W / 2, top - 0.04), (x, W / 2, 0.030)],
               tube, fr)
        for sy in (-1, 1):
            k.cyl(f"q_foot_{sx}{sy}", (x, sy * W / 2, 0.015), 0.026, 0.030,
                  m["rubber"], verts=16)
    for sy in (-1, 1):
        k.rod(f"q_rail_{sy}", (gx - L / 2, sy * W / 2, 0.060),
              (gx + L / 2, sy * W / 2, 0.060), tube, fr)
        k.rod(f"q_rail_top_{sy}", (gx - L / 2, sy * (W / 2 - 0.02), top - 0.02),
              (gx + L / 2, sy * (W / 2 - 0.02), top - 0.02), tube * 0.8, fr)
    k.box("q_cradle", (gx, 0, 0.075), (L - 0.04, W - 0.08, 0.020), fr)

    # Engine and alternator, low: aluminium crankcase right, alternator left.
    k.box("q_engine", (gx + 0.110, 0.010, 0.170), (0.240, 0.260, 0.170),
          m["alu"], bevel=0.016)
    k.box("q_engine_head", (gx + 0.150, 0.080, 0.270), (0.130, 0.130, 0.080),
          m["alu"], bevel=0.012, rot=(0, 0.3, 0))
    k.cyl("q_alternator", (gx - 0.140, 0.010, 0.175), 0.105, 0.170,
          m["black_plastic"], axis="X", verts=36)
    k.box("q_alt_sticker", (gx - 0.140, -0.100, 0.175), (0.060, 0.004, 0.070),
          m["sticker_white"])
    k.cyl("q_carb_bowl", (gx + 0.020, -0.100, 0.130), 0.018, 0.030,
          m["alu"], verts=12)
    k.cyl("q_recoil", (gx + 0.240, 0.010, 0.190), 0.090, 0.030,
          m["black_plastic"], axis="X", verts=32)
    k.box("q_recoil_grip", (gx + 0.265, -0.040, 0.250), (0.020, 0.070, 0.022),
          m["rubber"], bevel=0.005)
    k.cyl("q_muffler", (gx + 0.040, 0.150, 0.300), 0.050, 0.200,
          m["black_plastic"], axis="X", verts=24)
    k.box("q_muffler_guard", (gx + 0.040, 0.205, 0.300), (0.220, 0.008, 0.110),
          m["steel"], bevel=0.004)

    # Fuel-tank shroud across the top, with the trim band on -Y.
    k.box("q_tank", (gx, 0, 0.395), (L - 0.050, W - 0.030, 0.120),
          m["black_plastic"], bevel=0.024)
    k.box("q_tank_band", (gx, -(W - 0.030) / 2 - 0.002, 0.400),
          (L * 0.72, 0.004, 0.036), m["gap"])
    k.box("q_tank_trim", (gx - 0.030, -(W - 0.030) / 2 - 0.004, 0.400),
          (L * 0.44, 0.004, 0.012), m["gold"])
    k.cyl("q_fuel_cap", (gx + 0.140, 0.060, 0.462), 0.030, 0.020,
          m["black_plastic"], verts=20)
    k.cyl("q_fuel_gauge", (gx - 0.100, 0.060, 0.458), 0.022, 0.010,
          m["sticker_white"], verts=16)

    # Control face on -Y: black panel, olive fuel block, rocker, meter,
    # outlets, twist-lock.
    fy = -W / 2 + 0.030
    k.box("q_face", (gx, fy, 0.285), (L - 0.070, 0.020, 0.130),
          m["black_plastic"], bevel=0.010)
    k.box("q_fuel_block", (gx - 0.090, fy - 0.012, 0.285),
          (0.150, 0.004, 0.100), m["olive_label"])
    k.box("q_fuel_block_band", (gx - 0.090, fy - 0.015, 0.310),
          (0.140, 0.003, 0.018), m["sticker_yellow"])
    k.box("q_rocker", (gx - 0.195, fy - 0.014, 0.290), (0.024, 0.010, 0.030),
          m["estop"], bevel=0.003)
    k.box("q_meter", (gx + 0.060, fy - 0.014, 0.315), (0.050, 0.006, 0.040),
          m["sticker_white"])
    k.box("q_meter_needle", (gx + 0.060, fy - 0.018, 0.318),
          (0.030, 0.002, 0.004), m["estop"], rot=(0, 0.5, 0))
    for i, (dx, dz) in enumerate(((0.030, 0.265), (0.080, 0.265),
                                  (0.030, 0.230), (0.080, 0.230))):
        k.box(f"q_outlet_{i}", (gx + dx, fy - 0.013, dz),
              (0.034, 0.006, 0.026), m["outlet"])
        k.box(f"q_outlet_slot_{i}", (gx + dx, fy - 0.017, dz),
              (0.018, 0.002, 0.010), m["gap"])
    k.cyl("q_twistlock", (gx + 0.160, fy - 0.014, 0.255), 0.028, 0.010,
          m["outlet"], axis="Y", verts=20)
    for dx in (-0.230, 0.225):
        for dz in (0.235, 0.335):
            k.cyl(f"q_bolt_{dx}_{dz}", (gx + dx, fy - 0.013, dz), 0.008,
                  0.006, m["steel"], axis="Y", verts=10)

    # Regulator on the -X end, where the hose lands.
    rx = gx - L / 2 + 0.030
    k.box("q_regulator", (rx, -0.080, 0.300), (0.040, 0.050, 0.050),
          m["brass"], bevel=0.008)
    build_bottle(k, m, -0.330, -0.020, (rx - 0.020, -0.080, 0.300))


# ---------------------------------------------------------------- waste oil

def build_wasteoil(k: Kit, m: dict) -> None:
    """Slow-speed single-cylinder stationary diesel on a channel skid.
    Engine left, direct-coupled alternator head right, flywheels either side
    of the crank, stack muffler off the head. Drum + spin-on filter behind."""
    skid_l, skid_w, skid_h = 0.74, 0.40, 0.055
    for sy in (-1, 1):
        k.box(f"w_skid_{sy}", (0.02, sy * skid_w / 2, skid_h / 2),
              (skid_l, 0.055, skid_h), m["base_grey"], bevel=0.004)
    for sx in (-1, 1):
        k.box(f"w_crossmember_{sx}", (0.02 + sx * skid_l * 0.40, 0, skid_h),
              (0.050, skid_w + 0.05, 0.020), m["base_grey"])

    # Engine: crankcase, finned barrel, head, rocker cover.
    ex = -0.13
    cz = skid_h + 0.020
    k.box("w_crankcase", (ex, 0, cz + 0.125), (0.240, 0.220, 0.250),
          m["lister_green"], bevel=0.018)
    k.box("w_sump", (ex, 0, cz + 0.020), (0.270, 0.240, 0.040),
          m["lister_green"], bevel=0.008)
    barrel_z = cz + 0.250
    k.box("w_barrel", (ex, 0, barrel_z + 0.100), (0.170, 0.170, 0.200),
          m["lister_green"], bevel=0.010)
    for i in range(6):
        k.box(f"w_fin_{i}", (ex, 0, barrel_z + 0.030 + i * 0.028),
              (0.200, 0.200, 0.010), m["lister_green"])
    k.box("w_head", (ex, 0, barrel_z + 0.225), (0.190, 0.190, 0.050),
          m["lister_green"], bevel=0.010)
    k.box("w_rocker", (ex, 0.010, barrel_z + 0.268), (0.130, 0.120, 0.040),
          m["black_plastic"], bevel=0.012)
    k.cyl("w_injector", (ex + 0.050, -0.050, barrel_z + 0.300), 0.012, 0.050,
          m["steel"], verts=12)
    # Nameplate on the crankcase door (blank -- no maker's mark).
    k.box("w_door", (ex, -0.112, cz + 0.130), (0.130, 0.008, 0.120),
          m["lister_green"], bevel=0.010)
    k.box("w_plate", (ex, -0.118, cz + 0.160), (0.070, 0.004, 0.030),
          m["chrome"])

    # Twin spoked flywheels on the crank, either side of the crankcase.
    crank_z = cz + 0.180
    for sy in (-1, 1):
        y = sy * 0.160
        k.torus(f"w_fly_rim_{sy}", (ex, y, crank_z), 0.175, 0.024,
                m["lister_green"], axis="Y")
        k.cyl(f"w_fly_face_{sy}", (ex, y, crank_z), 0.160, 0.020,
              m["lister_green"], axis="Y", verts=40)
        k.cyl(f"w_fly_hub_{sy}", (ex, y + sy * 0.010, crank_z), 0.040, 0.050,
              m["steel"], axis="Y")
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            k.box(f"w_fly_window_{sy}_{i}",
                  (ex + math.cos(a) * 0.095, y + sy * 0.011,
                   crank_z + math.sin(a) * 0.095),
                  (0.070, 0.004, 0.070), m["gap"], rot=(0, a, 0))
    # Keep the flywheels off the skid: they sit in a slot, drawn as a shadow.
    k.box("w_fly_slot", (ex, 0, skid_h + 0.002), (0.090, skid_w + 0.10, 0.006),
          m["gap"])

    # Coupling and alternator head.
    ax = 0.200
    k.cyl("w_coupling", (0.035, 0, crank_z), 0.050, 0.080, m["steel"],
          axis="X")
    k.cyl("w_alternator", (ax, 0, crank_z), 0.120, 0.230, m["alt_grey"],
          axis="X", verts=40)
    for i in range(5):
        k.box(f"w_alt_vent_{i}", (ax + 0.070, -0.121, crank_z - 0.05
                                  + i * 0.025),
              (0.060, 0.006, 0.010), m["gap"])
    k.cyl("w_alt_endbell", (ax + 0.125, 0, crank_z), 0.100, 0.030,
          m["alt_grey"], axis="X")
    k.box("w_alt_foot", (ax, 0, skid_h + 0.040), (0.200, 0.180, 0.060),
          m["base_grey"], bevel=0.006)
    k.box("w_junction", (ax + 0.010, 0, crank_z + 0.150),
          (0.140, 0.110, 0.080), m["alt_grey"], bevel=0.008)
    k.cyl("w_gland", (ax + 0.050, -0.058, crank_z + 0.140), 0.014, 0.020,
          m["black_plastic"], axis="Y", verts=12)
    k.box("w_breaker", (ax - 0.030, -0.057, crank_z + 0.150),
          (0.030, 0.006, 0.040), m["black_plastic"])

    # Exhaust: out of the head, up, into a rusty stack muffler.
    head_top = barrel_z + 0.250
    k.path("w_exhaust", [
        (ex + 0.095, 0.050, barrel_z + 0.200),
        (ex + 0.140, 0.080, barrel_z + 0.200),
        (ex + 0.140, 0.080, head_top + 0.100),
    ], 0.022, m["rusty"])
    k.cyl("w_muffler", (ex + 0.140, 0.080, head_top + 0.190), 0.050, 0.170,
          m["rusty"])
    k.cyl("w_stack", (ex + 0.140, 0.080, head_top + 0.300), 0.020, 0.060,
          m["rusty"], verts=12)

    # Fuel: a waste-oil drum behind-left, spin-on filter on a bracket, line.
    dx, dy = -0.310, 0.170
    k.cyl("w_drum", (dx, dy, 0.230), 0.150, 0.460, m["drum_black"], verts=40)
    for z in (0.080, 0.380):
        k.torus(f"w_drum_hoop_{z}", (dx, dy, z), 0.150, 0.008, m["drum_black"])
    k.cyl("w_drum_bung", (dx + 0.060, dy - 0.050, 0.465), 0.022, 0.012,
          m["steel"], verts=12)
    k.cyl("w_drum_lid", (dx, dy, 0.462), 0.145, 0.006, m["rusty"])
    k.box("w_filter_bracket", (ex - 0.140, -0.080, cz + 0.200),
          (0.020, 0.060, 0.080), m["steel"])
    k.cyl("w_filter", (ex - 0.175, -0.080, cz + 0.190), 0.040, 0.110,
          m["filter_blue"])
    k.path("w_feed", [
        (dx + 0.060, dy - 0.050, 0.475),
        (dx + 0.090, dy - 0.090, 0.540),
        (ex - 0.175, -0.080, cz + 0.260),
    ], 0.009, m["hose"])
    k.path("w_feed_2", [
        (ex - 0.175, -0.080, cz + 0.130),
        (ex - 0.130, -0.100, cz + 0.100),
        (ex + 0.050, -0.090, barrel_z + 0.150),
    ], 0.007, m["hose"])


# ---------------------------------------------------------------- scrap

def build_scrap(k: Kit, m: dict) -> None:
    """The scrap slot: a small suitcase portable (1-2 kW, ~0.46 x 0.34 x
    0.38 m, after the operator's reference photo) that has had a hard life --
    dirty shroud, rusted recoil, a duct-taped panel cover, and a red jerry can
    lashed alongside instead of a propane bottle."""
    gx = 0.13                 # generator centre; the bottle sits at -X
    L, W = 0.46, 0.33
    foot_h = 0.040
    z0 = foot_h
    body_h = 0.235
    shroud_h = 0.085

    for sx in (-1, 1):
        for sy in (-1, 1):
            k.cyl(f"s_foot_{sx}{sy}", (gx + sx * L * 0.40, sy * W * 0.38,
                                       foot_h / 2), 0.030, foot_h,
                  m["rubber"], verts=16)

    # Black lower housing, with a slightly proud front frame.
    k.box("s_housing", (gx, 0, z0 + body_h / 2), (L, W, body_h),
          m["black_plastic"], bevel=0.010)
    # White fuel-tank shroud on top, a touch wider, rounded.
    k.box("s_shroud", (gx, 0, z0 + body_h + shroud_h / 2),
          (L + 0.012, W + 0.012, shroud_h), m["shroud_dirty"], bevel=0.022)
    k.box("s_shroud_seam", (gx, 0, z0 + body_h + 0.004),
          (L + 0.016, W + 0.016, 0.008), m["gap"])
    # Fuel cap / filler neck, silver, dead centre of the shroud.
    top = z0 + body_h + shroud_h
    k.cyl("s_fuel_cap", (gx - 0.02, 0.0, top + 0.012), 0.042, 0.024,
          m["chrome"])
    k.cyl("s_fuel_cap_grip", (gx - 0.02, 0.0, top + 0.027), 0.030, 0.008,
          m["steel"])

    # Carry handle: black tube, uprights at the X ends, bar along X.
    hz = top + 0.085
    for sx in (-1, 1):
        k.rod(f"s_handle_up_{sx}", (gx + sx * L * 0.30, 0, top - 0.01),
              (gx + sx * L * 0.30, 0, hz), 0.017, m["black_plastic"])
        k.sphere(f"s_handle_knee_{sx}", (gx + sx * L * 0.30, 0, hz), 0.017,
                 m["black_plastic"])
    k.rod("s_handle_bar", (gx - L * 0.30, 0, hz), (gx + L * 0.30, 0, hz),
          0.019, m["black_plastic"])

    # -Y face: control panel (left) and louvred engine cover (right).
    fy = -W / 2 - 0.004
    pz = z0 + body_h * 0.52
    k.box("s_panel", (gx - L * 0.20, fy, pz), (L * 0.40, 0.010, body_h * 0.80),
          m["gap"], bevel=0.004)
    k.box("s_panel_face", (gx - L * 0.20, fy - 0.004, pz),
          (L * 0.36, 0.006, body_h * 0.72), m["black_plastic"])
    for i, dz in enumerate((-0.045, 0.020)):
        k.box(f"s_outlet_{i}", (gx - L * 0.28, fy - 0.009, pz + dz),
              (0.040, 0.008, 0.050), m["outlet"])
        k.box(f"s_outlet_slot_{i}", (gx - L * 0.28, fy - 0.014, pz + dz),
              (0.022, 0.004, 0.018), m["gap"])
    k.cyl("s_lamp", (gx - L * 0.12, fy - 0.010, pz + 0.070), 0.012, 0.012,
          m["lamp_green"], axis="Y", verts=12)
    k.box("s_switch", (gx - L * 0.12, fy - 0.010, pz + 0.005),
          (0.022, 0.010, 0.032), m["estop"])
    k.box("s_label", (gx + L * 0.20, fy - 0.004, pz + body_h * 0.28),
          (L * 0.34, 0.006, 0.040), m["sticker_white"])
    k.box("s_label_strip", (gx + L * 0.20, fy - 0.007, pz + body_h * 0.28),
          (L * 0.30, 0.004, 0.012), m["sticker_yellow"])
    k.box("s_engine_cover", (gx + L * 0.20, fy - 0.003, pz - 0.030),
          (L * 0.32, 0.008, body_h * 0.48), m["gap"], bevel=0.004)
    for i in range(4):
        k.box(f"s_louvre_{i}", (gx + L * 0.20, fy - 0.009,
                                pz - 0.075 + i * 0.030),
              (L * 0.26, 0.006, 0.012), m["black_plastic"])

    # +X end: the big silver recoil-start cover and its T-grip.
    ex = gx + L / 2 + 0.010
    k.cyl("s_recoil", (ex, -0.010, z0 + body_h * 0.50), 0.105, 0.030,
          m["rusty"], axis="X", verts=40)
    k.cyl("s_recoil_hub", (ex + 0.018, -0.010, z0 + body_h * 0.50), 0.035,
          0.012, m["chrome"], axis="X")
    for i in range(3):
        k.box(f"s_recoil_rib_{i}", (ex + 0.016, -0.010,
                                    z0 + body_h * 0.50 + (i - 1) * 0.045),
              (0.006, 0.150 - abs(i - 1) * 0.04, 0.010), m["gap"])
    k.rod("s_pull_cord", (ex + 0.02, W * 0.25, z0 + body_h * 0.62),
          (ex + 0.05, W * 0.30, z0 + body_h * 0.62), 0.006, m["gap"])
    k.box("s_pull_grip", (ex + 0.060, W * 0.30, z0 + body_h * 0.62),
          (0.024, 0.024, 0.075), m["rubber"], bevel=0.006)

    # -X end: muffler guard, and the propane conversion regulator.
    wx = gx - L / 2 - 0.006
    k.box("s_muffler_guard", (wx, 0.02, z0 + body_h * 0.55),
          (0.012, W * 0.62, body_h * 0.62), m["steel"], bevel=0.004)
    for i in range(5):
        k.box(f"s_muffler_slot_{i}", (wx - 0.007, 0.02 - W * 0.24 + i * 0.040,
                                      z0 + body_h * 0.55),
              (0.004, 0.012, body_h * 0.46), m["gap"])
    # Hard-life details: tape over a cracked engine cover, a missing foot
    # replaced by a block of wood, a bungee holding the shroud down.
    k.box("s_tape_cover", (gx + L * 0.20, fy - 0.012, pz - 0.020),
          (L * 0.36, 0.004, 0.030), m["tape"], rot=(0, 0.12, 0))
    k.box("s_tape_cover_2", (gx + L * 0.16, fy - 0.013, pz - 0.060),
          (L * 0.30, 0.004, 0.026), m["tape"], rot=(0, -0.08, 0))
    k.box("s_shim", (gx + L * 0.40, W * 0.38, 0.020), (0.070, 0.060, 0.040),
          m["wood"])
    k.box("s_bungee", (gx - L * 0.05, 0, z0 + body_h + shroud_h * 0.5),
          (0.018, W + 0.030, shroud_h + 0.012), m["bungee"])
    # Jerry can at -X, on its own.
    jx = -0.260
    k.box("s_jerry", (jx, 0.020, 0.140), (0.110, 0.230, 0.280),
          m["jerry_red"], bevel=0.016)
    for dz in (-0.06, 0.06):
        k.box(f"s_jerry_x_{dz}", (jx - 0.057, 0.020, 0.140 + dz),
              (0.006, 0.160, 0.012), m["jerry_red"], rot=(dz * 8, 0, 0))
    k.box("s_jerry_handle", (jx, -0.040, 0.300), (0.050, 0.090, 0.032),
          m["jerry_red"], bevel=0.008)
    k.cyl("s_jerry_spout", (jx, 0.100, 0.295), 0.020, 0.045,
          m["black_plastic"], verts=12)

# ---------------------------------------------------------------- 10 kW

def build_diesel(k: Kit, m: dict) -> None:
    """The big slot: a 10 kW wheeled open-frame portable after the operator's
    reference -- ~0.78 x 0.62 x 0.70 m, the one set allowed near a full tile.
    Wheels at -X, fold-out handles and legs at +X (the control end), crimson
    tank shroud on a black sheet-metal chassis with mesh side panels, and the
    electric-start battery riding in the -Y side."""
    L, W = 0.620, 0.480          # chassis
    fx0, fx1 = -0.370, 0.360     # frame extent in X
    fw = 0.300                   # frame half-width in Y
    rail = 0.018
    zb, zt = 0.105, 0.640        # bottom and top frame loops

    # Tubular frame: bottom loop, four uprights, top loop, cross bar over the
    # tank, fold-out handles off the +X end.
    fr = m["frame"]
    k.path("t_frame_bottom", [(fx0, -fw, zb), (fx1, -fw, zb), (fx1, fw, zb),
                              (fx0, fw, zb), (fx0, -fw, zb)], rail, fr)
    k.path("t_frame_top", [(fx0 + 0.02, -fw + 0.02, zt),
                           (fx1 - 0.02, -fw + 0.02, zt),
                           (fx1 - 0.02, fw - 0.02, zt),
                           (fx0 + 0.02, fw - 0.02, zt),
                           (fx0 + 0.02, -fw + 0.02, zt)], rail, fr)
    for x in (fx0, fx1):
        for sy in (-1, 1):
            k.path(f"t_upright_{x}_{sy}", [
                (x, sy * fw, zb),
                (x, sy * fw, zt - 0.06),
                (x + (0.02 if x < 0 else -0.02), sy * (fw - 0.02), zt),
            ], rail, fr)
    k.rod("t_frame_mid_x", (-0.05, -fw + 0.02, zt), (-0.05, fw - 0.02, zt),
          rail, fr)
    for sy in (-1, 1):
        k.path(f"t_handle_{sy}", [
            (fx1, sy * (fw - 0.04), zt - 0.10),
            (fx1 + 0.110, sy * (fw - 0.04), zt - 0.02),
            (fx1 + 0.130, sy * (fw - 0.04), zt + 0.02),
        ], rail * 0.9, fr)
        k.cyl(f"t_handle_grip_{sy}", (fx1 + 0.130, sy * (fw - 0.04),
                                      zt + 0.05), 0.022, 0.070, m["rubber"],
              verts=16)
        # Legs under the control end.
        k.box(f"t_leg_{sy}", (fx1 - 0.03, sy * (fw - 0.02), zb / 2),
              (0.070, 0.040, zb), fr, bevel=0.006)
        k.box(f"t_leg_foot_{sy}", (fx1 - 0.03, sy * (fw - 0.02), 0.008),
              (0.090, 0.050, 0.016), m["rubber"])

    # Wheels at -X.
    for sy in (-1, 1):
        y = sy * (fw + 0.050)
        k.cyl(f"t_tyre_{sy}", (fx0 + 0.020, y, 0.125), 0.125, 0.075,
              m["rubber"], axis="Y", verts=40)
        k.cyl(f"t_rim_{sy}", (fx0 + 0.020, y + sy * 0.006, 0.125), 0.075,
              0.068, m["steel"], axis="Y", verts=32)
        k.cyl(f"t_hub_{sy}", (fx0 + 0.020, y + sy * 0.040, 0.125), 0.022,
              0.012, m["chrome"], axis="Y", verts=16)
        for i in range(8):
            a = i * math.pi / 4
            k.box(f"t_tread_{sy}_{i}", (fx0 + 0.020 + math.cos(a) * 0.124, y,
                                        0.125 + math.sin(a) * 0.124),
                  (0.018, 0.080, 0.018), m["gap"], rot=(0, -a, 0))
    k.rod("t_axle", (fx0 + 0.020, -fw - 0.05, 0.125),
          (fx0 + 0.020, fw + 0.05, 0.125), 0.012, m["steel"])

    # Chassis: black sheet-metal box with mesh side panels.
    cz0, cz1 = 0.140, 0.505
    k.box("t_chassis", (-0.010, 0, (cz0 + cz1) / 2), (L, W, cz1 - cz0),
          m["black_plastic"], bevel=0.008)
    for sy in (-1, 1):
        fy = sy * (W / 2 + 0.002)
        for i, (cx, pw) in enumerate(((-0.170, 0.200), (0.080, 0.230))):
            k.box(f"t_mesh_{sy}_{i}", (cx, fy, 0.345), (pw, 0.004, 0.260),
                  m["gap"])
            for j in range(6):
                k.box(f"t_mesh_v_{sy}_{i}_{j}",
                      (cx - pw / 2 + (j + 0.5) * pw / 6, fy + sy * 0.004,
                       0.345), (0.005, 0.004, 0.250), m["mesh"])
            for j in range(7):
                k.box(f"t_mesh_h_{sy}_{i}_{j}",
                      (cx, fy + sy * 0.004, 0.225 + j * 0.040),
                      (pw - 0.008, 0.004, 0.005), m["mesh"])
            k.box(f"t_mesh_frame_{sy}_{i}", (cx, fy, 0.345),
                  (pw + 0.016, 0.002, 0.276), m["black_plastic"])
        # Stripe panel under the shroud (the badge band, left blank).
        k.box(f"t_band_{sy}", (-0.010, fy + sy * 0.003, 0.482),
              (L * 0.92, 0.004, 0.030), m["crimson_dark"])

    # Starter battery in a cut-out on the -Y side, low, by the wheels.
    bx = -0.220
    k.box("t_battery_bay", (bx, -W / 2 + 0.035, 0.225), (0.170, 0.080, 0.150),
          m["gap"])
    k.box("t_battery", (bx, -W / 2 - 0.005, 0.225), (0.150, 0.090, 0.140),
          m["battery_white"], bevel=0.006)
    k.box("t_battery_lid", (bx, -W / 2 - 0.005, 0.300),
          (0.152, 0.092, 0.012), m["black_plastic"])
    k.box("t_battery_term_r", (bx - 0.045, -W / 2 - 0.030, 0.312),
          (0.022, 0.022, 0.014), m["cable_red"])
    k.box("t_battery_term_b", (bx + 0.045, -W / 2 - 0.030, 0.312),
          (0.022, 0.022, 0.014), m["filter_blue"])

    # Crimson tank shroud with raised ribs, fuel cap and the lift eye.
    sz0 = cz1
    k.box("t_shroud", (-0.010, 0, sz0 + 0.060), (L + 0.010, W - 0.020, 0.120),
          m["crimson"], bevel=0.030)
    for i in range(5):
        k.box(f"t_rib_{i}", (0.080 + i * 0.036, 0.0, sz0 + 0.124),
              (0.014, W * 0.60, 0.012), m["crimson_dark"], bevel=0.004)
    k.box("t_tank_lid", (-0.160, -0.030, sz0 + 0.124), (0.180, 0.220, 0.014),
          m["crimson"], bevel=0.008)
    k.cyl("t_fuel_cap", (-0.200, 0.110, sz0 + 0.132), 0.034, 0.020,
          m["black_plastic"], verts=20)
    k.torus("t_lift_eye", (-0.050, 0.0, zt + 0.070), 0.050, 0.010, fr,
            axis="X")
    k.box("t_lift_plate", (-0.050, 0.0, zt + 0.012), (0.040, 0.100, 0.020),
          fr, bevel=0.004)

    # +X end: control panel, outlets, silver hinge brackets, alternator grille.
    px = L / 2 - 0.010 + 0.006
    k.box("t_panel", (px, 0, 0.410), (0.012, W * 0.86, 0.180),
          m["panel_grey"], bevel=0.004)
    for i in range(5):
        y = -0.150 + i * 0.075
        k.box(f"t_outlet_{i}", (px + 0.010, y, 0.370), (0.012, 0.055, 0.070),
              m["black_plastic"], bevel=0.004)
        k.box(f"t_outlet_face_{i}", (px + 0.018, y, 0.370),
              (0.004, 0.040, 0.050), m["gap"])
    k.cyl("t_twistlock", (px + 0.020, -0.215, 0.370), 0.034, 0.030,
          m["black_plastic"], axis="X", verts=24)
    k.cyl("t_key", (px + 0.016, -0.150, 0.455), 0.020, 0.018,
          m["black_plastic"], axis="X", verts=16)
    k.cyl("t_lamp", (px + 0.010, -0.090, 0.465), 0.008, 0.008,
          m["lamp_green"], axis="X", verts=12)
    for i in range(4):
        k.box(f"t_breaker_{i}", (px + 0.012, -0.030 + i * 0.055, 0.465),
              (0.012, 0.020, 0.024), m["black_plastic"])
    k.box("t_panel_hood", (px + 0.010, 0, 0.508), (0.040, W * 0.88, 0.018),
          m["black_plastic"], bevel=0.004)
    for sy in (-1, 1):
        k.box(f"t_hinge_{sy}", (px + 0.020, sy * W * 0.46, 0.420),
              (0.030, 0.040, 0.140), m["chrome"], bevel=0.008)
    k.cyl("t_alt_grille", (px + 0.004, 0.030, 0.230), 0.105, 0.012,
          m["gap"], axis="X", verts=40)
    for r in (0.060, 0.090):
        k.torus(f"t_alt_ring_{r}", (px + 0.010, 0.030, 0.230), r, 0.004,
                m["mesh"], axis="X")
    k.rod("t_panel_bar", (fx1, -fw, 0.300), (fx1, fw, 0.300), rail, fr)

    # -X end: muffler and exhaust outlet behind the wheels.
    k.cyl("t_muffler", (-L / 2 - 0.010, 0.120, 0.380), 0.060, 0.200,
          m["black_plastic"], axis="Y")
    k.cyl("t_exhaust", (-L / 2 - 0.030, 0.230, 0.380), 0.020, 0.040,
          m["rusty"], axis="Y", verts=12)


# ---------------------------------------------------------------- battery bank

def build_bank(k: Kit, m: dict) -> None:
    """After the operator's photo: a block pallet carrying five deep-cycle
    batteries in a row, wired in series, a red main lead up to a black
    inverter on an OSB backboard screwed to two posts at the back edge."""
    PL, PW = 0.980, 0.520
    # Pallet: three rows of block feet, three stringers, deck boards.
    for ix in (-1, 0, 1):
        for iy in (-1, 1):
            k.box(f"b_block_{ix}_{iy}", (ix * 0.410, iy * 0.200, 0.045),
                  (0.100, 0.090, 0.090), m["pine"], bevel=0.004)
    for iy in (-1, 0, 1):
        k.box(f"b_stringer_{iy}", (0, iy * 0.200, 0.105), (PL, 0.090, 0.030),
              m["pine_dark"])
    for i in range(6):
        k.box(f"b_deck_{i}", (-PL / 2 + 0.085 + i * 0.162, 0, 0.138),
              (0.140, PW, 0.036), m["pine"], bevel=0.004)
    deck = 0.156

    # Five group-31 batteries across the pallet, long side along Y.
    bw, bd, bh = 0.172, 0.300, 0.230
    xs = [-0.360 + i * 0.180 for i in range(5)]
    by = -0.060
    for i, x in enumerate(xs):
        k.box(f"b_batt_{i}", (x, by, deck + bh / 2), (bw, bd, bh),
              m["batt_case"], bevel=0.010)
        for j in range(4):
            k.box(f"b_rib_{i}_{j}", (x, by - bd / 2 - 0.002,
                                     deck + 0.040 + j * 0.045),
                  (bw * 0.86, 0.004, 0.010), m["gap"])
        k.box(f"b_lid_{i}", (x, by, deck + bh + 0.008), (bw, bd, 0.016),
              m["batt_case"], bevel=0.004)
        k.box(f"b_label_{i}", (x, by - bd * 0.28, deck + bh + 0.017),
              (bw * 0.80, 0.070, 0.004), m["sticker_white"])
        k.box(f"b_label_stripe_{i}", (x, by - bd * 0.28, deck + bh + 0.020),
              (bw * 0.80, 0.018, 0.003), m["label_purple"])
        # Rope handle as a low arch.
        k.path(f"b_handle_{i}", [(x - 0.050, by + 0.030, deck + bh + 0.016),
                                 (x - 0.030, by + 0.030, deck + bh + 0.050),
                                 (x + 0.030, by + 0.030, deck + bh + 0.050),
                                 (x + 0.050, by + 0.030, deck + bh + 0.016)],
               0.006, m["rubber"])
        for sx, cap in ((-1, "cable_red"), (1, "rubber")):
            k.cyl(f"b_post_{i}_{sx}", (x + sx * 0.055, by + 0.100,
                                       deck + bh + 0.030), 0.012, 0.028,
                  m["lead"], verts=12)
            k.cyl(f"b_boot_{i}_{sx}", (x + sx * 0.055, by + 0.100,
                                       deck + bh + 0.046), 0.016, 0.010,
                  m[cap], verts=12)
    # Series links: + of one to - of the next.
    top = deck + bh + 0.050
    for i in range(4):
        k.path(f"b_link_{i}", [(xs[i] + 0.055, by + 0.100, top),
                               (xs[i] + 0.090, by + 0.130, top + 0.020),
                               (xs[i + 1] - 0.055, by + 0.100, top)],
               0.007, m["rubber"])

    # OSB backboard on two posts at the back edge, inverter on it.
    oy = PW / 2 - 0.030
    for sx in (-1, 1):
        k.box(f"b_post_{sx}", (sx * 0.300, oy + 0.020, deck + 0.270),
              (0.060, 0.040, 0.540), m["pine_dark"])
    # Board kept low enough that the back facings still show the batteries.
    k.box("b_osb", (0, oy, deck + 0.360), (0.760, 0.020, 0.340), m["osb"])
    iz = deck + 0.400
    k.box("b_inverter", (0.060, oy - 0.070, iz), (0.380, 0.120, 0.200),
          m["batt_case"], bevel=0.018)
    k.box("b_inverter_face", (0.060, oy - 0.132, iz), (0.330, 0.004, 0.150),
          m["gap"])
    k.box("b_inverter_wave", (0.030, oy - 0.135, iz + 0.010),
          (0.160, 0.004, 0.020), m["sticker_white"])
    k.box("b_inverter_stripe", (0.160, oy - 0.135, iz - 0.040),
          (0.080, 0.004, 0.016), m["lamp_green"])
    for sx in (-1, 1):
        k.box(f"b_inverter_fin_{sx}", (0.060 + sx * 0.195, oy - 0.070, iz),
              (0.012, 0.130, 0.190), m["steel"])
    k.cyl("b_inverter_lamp", (-0.090, oy - 0.135, iz - 0.050), 0.008, 0.006,
          m["lamp_green"], axis="Y", verts=12)
    # Main leads: + (red) and - (black) from the end batteries up to the box.
    k.path("b_main_red", [(xs[4] + 0.055, by + 0.100, top),
                          (xs[4] + 0.020, by + 0.180, top + 0.080),
                          (0.180, oy - 0.080, iz - 0.200),
                          (0.180, oy - 0.080, iz - 0.100)], 0.012,
           m["cable_red"])
    k.path("b_main_black", [(xs[0] - 0.055, by + 0.100, top),
                            (xs[0] - 0.020, by + 0.200, top + 0.120),
                            (-0.080, oy - 0.080, iz - 0.200),
                            (-0.060, oy - 0.080, iz - 0.100)], 0.012,
           m["rubber"])
    k.path("b_ac_out", [(-0.130, oy - 0.070, iz + 0.100),
                        (-0.200, oy - 0.070, iz + 0.180),
                        (-0.330, oy - 0.060, iz + 0.150),
                        (-0.360, oy - 0.060, deck + 0.050)], 0.008,
           m["rubber"])


BUILDERS = {
    "propane": build_propane,
    "wasteoil": build_wasteoil,
    "scrap": build_scrap,
    "diesel": build_diesel,
    "bank": build_bank,
}


def build(name: str, mats: dict | None = None) -> list[bpy.types.Object]:
    if not TEXTURE_PATH.exists():
        make_texture()
    k = Kit()
    BUILDERS[name](k, mats or materials())
    return k.parts


def main() -> None:
    argv = sys.argv
    name = argv[argv.index("--") + 1] if "--" in argv else "propane"
    if name not in BUILDERS:
        raise SystemExit(f"unknown variant {name!r}; pick from {VARIANTS}")

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    make_texture()
    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = f"bp_genset_{name}"
    props.output_dir = str(ROOT / "build" / f"genset_{name}_cells")
    props.footprint_x = props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True

    F.build_rig(bpy.context)
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True

    subject = bpy.data.objects[F.SUBJECT_NAME]
    for part in build(name):
        if part.parent is None:
            part.parent = subject
    manifest = F.render_cells(bpy.context)
    print(f"rendered {len(manifest['cells'])} cells for {name}")


if __name__ == "__main__":
    main()
