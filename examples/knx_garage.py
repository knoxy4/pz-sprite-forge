"""Garage workshop set for Tokin's garage mod: engine stand, tire changer,
air compressor (1x1 each) and a diagnostic bench (2x1).

After the operator's concept sheet "BADLANDS GARAGE - workshop equipment concepts":
red square-tube engine stand with a four-cylinder on its head plate, red tire
changer with a tire on the turntable, yellow twin-wheel compressor with the pump
on the tank, blue steel bench with a scope, a meter and a parts cabinet on top.
The concept is reference only; the pieces are built from primitives on the
Kit part builders and the genset material set, same rig as every BADLANDS tile.

Sheets (four facings each, S E N W, subject-major like knx_badlands_power):
    ikag_garage_01   0-3 engine stand, 4-7 tire changer, 8-11 air compressor
    ikag_garage_02   bench, 2x1: 8 cells, two per facing (SpriteGridPos in the manifest)

Run headlessly from the repo root:
    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \\
        -P examples/knx_garage.py -- [--bench] [--only stand,tire,comp] [--samples N]

To add a piece: write build_<name>(k, m) in tile units (1 m = 1 tile, S front
faces -Y, floor at z = 0), add it to PIECES, re-run. See the kit README.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import pz_sprite_forge as F  # noqa: E402

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BENCH = "--bench" in ARGV
SHEET = "ikag_garage_02" if BENCH else "ikag_garage_01"
OUT = ROOT / "build" / ("garage_bench_cells" if BENCH else "garage_cells")


def arg(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


def load(name: str):
    path = ROOT / "examples" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


G = load("knx_gensets")


def materials() -> dict:
    m = G.materials()
    t = G.TEXTURE_PATH
    rust = (0.330, 0.160, 0.075)

    def worn(name, colour, accent=None, pos=None):
        return F.forge_material(name, "metal", colour, texture_path=t, hue=G.KEEP_HUE,
                                accent=accent, accent_position=pos)

    def flat(name, colour):
        return F.forge_material(name, "metal", colour, hue=G.KEEP_HUE)

    def glow(name, colour, strength=1.0):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        nodes.clear()
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*colour, 1.0)
        emit.inputs["Strength"].default_value = strength
        out = nodes.new("ShaderNodeOutputMaterial")
        links.new(emit.outputs["Emission"], out.inputs["Surface"])
        return mat

    m.update({
        # Shop red: deeper than vanilla's Generator orange-red, same call as the crimson genset.
        "shop_red": worn("gr_red", (0.600, 0.080, 0.060), accent=rust, pos=0.14),
        "shop_red_d": flat("gr_red_d", (0.330, 0.045, 0.040)),
        "bench_blue": worn("gr_blue", (0.200, 0.300, 0.400), accent=rust, pos=0.12),
        "bench_blue_d": flat("gr_blue_d", (0.110, 0.165, 0.225)),
        "bench_top": worn("gr_top", (0.330, 0.320, 0.300), accent=rust, pos=0.20),
        "tank_yellow": worn("gr_yellow", (0.880, 0.640, 0.080)),
        "tank_yellow_d": flat("gr_yellow_d", (0.560, 0.390, 0.040)),
        "iron": worn("gr_iron", (0.150, 0.147, 0.142), accent=rust, pos=0.22),
        "iron_d": flat("gr_iron_d", (0.090, 0.088, 0.085)),
        "cream": worn("gr_cream", (0.720, 0.690, 0.600)),
        "rag": flat("gr_rag", (0.780, 0.760, 0.700)),
        "screen": glow("gr_screen", (0.050, 0.420, 0.180)),
        "trace": glow("gr_trace", (0.350, 1.000, 0.450)),
        "gauge_face": flat("gr_gauge_face", (0.930, 0.920, 0.880)),
    })
    return m


# ---------------------------------------------------------------- engine stand

def build_stand(k, m) -> None:
    red, red_d = m["shop_red"], m["shop_red_d"]
    # Base: two legs running forward, crossbar at the back, casters under all four ends.
    for sx in (-1, 1):
        k.box(f"es_leg_{sx}", (0.28 * sx, 0.0, 0.105), (0.070, 0.80, 0.060), red, bevel=0.006)
        for y in (-0.36, 0.34):
            k.box(f"es_fork_{sx}_{y}", (0.28 * sx, y, 0.062), (0.040, 0.040, 0.030), m["iron_d"])
            k.cyl(f"es_caster_{sx}_{y}", (0.28 * sx, y, 0.036), 0.034, 0.026, m["rubber"],
                  axis="X", verts=16)
    k.box("es_cross", (0.0, 0.34, 0.105), (0.63, 0.070, 0.060), red, bevel=0.006)
    # Post, gusset, head.
    k.box("es_post", (0.0, 0.34, 0.415), (0.080, 0.080, 0.560), red, bevel=0.006)
    k.rod("es_gusset", (0.0, 0.10, 0.14), (0.0, 0.31, 0.40), 0.018, red)
    k.box("es_head", (0.0, 0.25, 0.620), (0.070, 0.12, 0.070), red_d)
    k.cyl("es_plate", (0.0, 0.18, 0.600), 0.105, 0.020, red_d, axis="Y", verts=24)
    # Crank handle out the +X side of the head.
    k.rod("es_crank_shaft", (0.04, 0.26, 0.64), (0.15, 0.26, 0.64), 0.010, m["iron_d"])
    k.rod("es_crank_arm", (0.15, 0.26, 0.64), (0.15, 0.26, 0.74), 0.010, m["iron_d"])
    k.cyl("es_crank_knob", (0.15, 0.26, 0.78), 0.016, 0.060, m["rubber"], verts=12)
    # Mount arms from the plate into the back of the block.
    for dx, dz in ((-0.07, 0.53), (0.07, 0.53), (-0.07, 0.67), (0.07, 0.67)):
        k.rod(f"es_arm_{dx}_{dz}", (dx * 0.6, 0.17, 0.60 + (dz - 0.60) * 0.6),
              (dx * 1.4, 0.13, dz), 0.010, m["iron_d"])
    # Engine: inline four, crank axis along Y, timing end facing the front.
    iron, alu = m["iron"], m["alu"]
    k.box("en_block", (0.0, -0.08, 0.580), (0.300, 0.420, 0.240), iron, bevel=0.008)
    k.box("en_pan", (0.0, -0.08, 0.425), (0.230, 0.360, 0.080), m["iron_d"], bevel=0.006)
    k.box("en_head", (0.0, -0.08, 0.735), (0.280, 0.400, 0.070), iron, bevel=0.006)
    k.box("en_cover", (0.0, -0.08, 0.800), (0.230, 0.370, 0.060), alu, bevel=0.010)
    k.cyl("en_cap", (0.04, -0.18, 0.840), 0.028, 0.020, m["black_plastic"], verts=16)
    k.box("en_timing", (0.0, -0.305, 0.600), (0.250, 0.030, 0.260), m["iron_d"], bevel=0.006)
    k.cyl("en_crank_pulley", (0.0, -0.335, 0.500), 0.068, 0.030, alu, axis="Y", verts=28)
    k.cyl("en_cam_pulley", (0.0, -0.330, 0.700), 0.058, 0.026, alu, axis="Y", verts=28)
    k.cyl("en_alt", (-0.12, -0.290, 0.640), 0.045, 0.080, alu, axis="Y", verts=20)
    k.cyl("en_pump", (0.11, -0.325, 0.600), 0.036, 0.024, alu, axis="Y", verts=20)
    # Exhaust manifold down the +X flank, four runners into a collector.
    for i in range(4):
        y = 0.06 - i * 0.095
        k.rod(f"en_ex_{i}", (0.15, y, 0.690), (0.205, y, 0.620), 0.020, m["rusty"])
    k.rod("en_ex_coll", (0.205, 0.08, 0.605), (0.205, -0.25, 0.605), 0.024, m["rusty"])
    # Intake along the -X flank.
    for i in range(4):
        y = 0.06 - i * 0.095
        k.rod(f"en_in_{i}", (-0.15, y, 0.700), (-0.19, y, 0.720), 0.016, alu)
    k.box("en_plenum", (-0.200, -0.08, 0.730), (0.050, 0.380, 0.060), alu, bevel=0.008)
    for i, y in enumerate((0.05, -0.05, -0.15, -0.25)):
        k.cyl(f"en_plug_{i}", (0.10, y, 0.775), 0.010, 0.050, m["rubber"], verts=8)


# ---------------------------------------------------------------- tire changer

def build_tire(k, m) -> None:
    red, red_d = m["shop_red"], m["shop_red_d"]
    k.box("tc_foot", (0.0, 0.02, 0.015), (0.580, 0.620, 0.030), m["iron_d"])
    k.box("tc_cab", (0.0, 0.02, 0.310), (0.520, 0.560, 0.560), red, bevel=0.010)
    k.box("tc_door", (0.0, -0.262, 0.300), (0.320, 0.006, 0.340), red_d)
    k.box("tc_door_handle", (0.12, -0.268, 0.300), (0.020, 0.010, 0.080), m["chrome"])
    k.box("tc_label", (-0.19, -0.262, 0.500), (0.080, 0.006, 0.060), m["sticker_yellow"])
    # Pedals low at the front.
    for i, x in enumerate((-0.11, 0.0, 0.11)):
        k.box(f"tc_pedal_{i}", (x, -0.320, 0.045), (0.075, 0.110, 0.022), m["iron_d"], bevel=0.004)
        k.box(f"tc_pedal_pad_{i}", (x, -0.335, 0.058), (0.065, 0.070, 0.006), m["rubber"])
    # Turntable, jaws, tire on the rim.
    k.cyl("tc_table", (0.0, -0.02, 0.610), 0.250, 0.040, m["steel"], verts=40)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        k.box(f"tc_jaw_{i}", (0.17 * math.cos(a), -0.02 + 0.17 * math.sin(a), 0.645),
              (0.060, 0.030, 0.030), m["iron_d"], rot=(0, 0, a))
    k.torus("tc_tire", (0.0, -0.02, 0.720), 0.190, 0.075, m["rubber"])
    k.cyl("tc_tread", (0.0, -0.02, 0.720), 0.262, 0.100, m["rubber"], verts=40)
    k.cyl("tc_rim", (0.0, -0.02, 0.725), 0.140, 0.140, m["steel"], verts=32)
    k.cyl("tc_hub", (0.0, -0.02, 0.800), 0.050, 0.020, m["iron_d"], verts=16)
    # Tower at the back, horizontal arm, mount column down onto the rim.
    k.box("tc_tower", (0.0, 0.25, 0.960), (0.120, 0.120, 0.740), red, bevel=0.008)
    k.box("tc_tower_cap", (0.0, 0.25, 1.340), (0.140, 0.140, 0.020), red_d)
    k.box("tc_warn", (0.0, 0.188, 1.100), (0.070, 0.004, 0.090), m["sticker_yellow"])
    k.box("tc_arm", (0.0, 0.11, 1.280), (0.080, 0.300, 0.080), m["iron_d"], bevel=0.006)
    k.box("tc_column", (0.0, -0.02, 1.060), (0.045, 0.045, 0.440), m["chrome"])
    k.cyl("tc_spring", (0.0, -0.02, 1.380), 0.028, 0.120, m["rubber"], verts=16)
    k.box("tc_mount_head", (0.0, -0.02, 0.855), (0.070, 0.070, 0.060), m["iron_d"], bevel=0.006)
    # Bead breaker on the +X flank: air cylinder, arm, paddle.
    k.cyl("tc_bead_cyl", (0.300, 0.140, 0.330), 0.040, 0.220, m["chrome"], axis="Y", verts=16)
    k.rod("tc_bead_arm", (0.300, 0.24, 0.40), (0.330, -0.12, 0.30), 0.016, m["iron_d"])
    k.box("tc_bead_paddle", (0.330, -0.14, 0.300), (0.020, 0.060, 0.100), m["iron_d"])
    # Lube bucket and brush on a bracket, -X front corner.
    k.box("tc_bracket", (-0.285, -0.16, 0.500), (0.050, 0.040, 0.010), m["iron_d"])
    k.cyl("tc_bucket", (-0.310, -0.16, 0.550), 0.042, 0.090, m["steel"], verts=16)
    k.rod("tc_brush", (-0.310, -0.16, 0.550), (-0.300, -0.13, 0.680), 0.007, m["wood"])
    # Air line up the back of the tower.
    k.path("tc_air", [(0.06, 0.31, 1.20), (0.06, 0.33, 0.60), (0.20, 0.30, 0.25)], 0.010, m["hose"])


# ---------------------------------------------------------------- air compressor

def build_comp(k, m) -> None:
    yel, yel_d = m["tank_yellow"], m["tank_yellow_d"]
    k.cyl("ac_tank", (0.0, 0.0, 0.280), 0.170, 0.640, yel, axis="X", verts=40)
    for sx in (-1, 1):
        k.sphere(f"ac_end_{sx}", (0.320 * sx, 0.0, 0.280), 0.170, yel, scale=(0.35, 1, 1))
    # Wheels at -X, rubber feet at +X, drain cock underneath.
    k.rod("ac_axle", (-0.27, -0.21, 0.110), (-0.27, 0.21, 0.110), 0.012, m["iron_d"])
    for sy in (-1, 1):
        k.cyl(f"ac_wheel_{sy}", (-0.27, 0.205 * sy, 0.110), 0.110, 0.050, m["rubber"], axis="Y", verts=28)
        k.cyl(f"ac_hub_{sy}", (-0.27, 0.232 * sy, 0.110), 0.050, 0.010, m["steel"], axis="Y", verts=16)
        k.box(f"ac_foot_{sy}", (0.270, 0.110 * sy, 0.075), (0.040, 0.060, 0.150), yel_d)
        k.box(f"ac_pad_{sy}", (0.270, 0.110 * sy, 0.008), (0.060, 0.070, 0.016), m["rubber"])
    k.cyl("ac_drain", (0.0, 0.0, 0.100), 0.012, 0.030, m["brass"], verts=10)
    # Handle up and over the +X end.
    for sy in (-1, 1):
        k.path(f"ac_handle_{sy}", [(0.300, 0.130 * sy, 0.380), (0.420, 0.130 * sy, 0.460),
                                   (0.420, 0.130 * sy, 0.600)], 0.016, yel_d)
    k.rod("ac_handle_bar", (0.420, -0.13, 0.600), (0.420, 0.13, 0.600), 0.020, m["rubber"])
    # Saddle plate, motor, pump with finned heads, belt guard behind.
    k.box("ac_saddle", (0.0, 0.0, 0.460), (0.440, 0.240, 0.020), yel_d)
    k.cyl("ac_motor", (0.110, -0.030, 0.560), 0.085, 0.200, m["alt_grey"], axis="X", verts=28)
    k.cyl("ac_fan", (0.220, -0.030, 0.560), 0.080, 0.030, m["black_plastic"], axis="X", verts=28)
    k.box("ac_pump", (-0.120, -0.030, 0.530), (0.150, 0.140, 0.120), m["iron_d"], bevel=0.008)
    for i in range(6):
        k.box(f"ac_fin_{i}", (-0.120, -0.030, 0.605 + i * 0.016),
              (0.130 - i * 0.006, 0.130 - i * 0.006, 0.008), m["alu"])
    k.box("ac_guard", (-0.020, 0.110, 0.560), (0.380, 0.030, 0.170), m["mesh"], bevel=0.010)
    # Pressure switch, two gauges, red safety valve, brass manifold.
    k.box("ac_switch", (0.280, -0.090, 0.530), (0.070, 0.060, 0.080), m["alt_grey"], bevel=0.006)
    k.cyl("ac_valve", (0.280, -0.090, 0.600), 0.020, 0.040, m["estop"], verts=12)
    k.rod("ac_manifold", (0.200, -0.150, 0.500), (0.340, -0.150, 0.500), 0.014, m["brass"])
    for i, x in enumerate((0.220, 0.315)):
        k.cyl(f"ac_gauge_{i}", (x, -0.165, 0.555), 0.036, 0.020, m["steel"], axis="Y", verts=20)
        k.cyl(f"ac_gauge_face_{i}", (x, -0.177, 0.555), 0.030, 0.004, m["gauge_face"], axis="Y", verts=20)
        k.rod(f"ac_gauge_stem_{i}", (x, -0.155, 0.500), (x, -0.160, 0.525), 0.008, m["brass"])
    # Coiled hose hung on the front of the tank.
    k.torus("ac_hose", (0.130, -0.185, 0.270), 0.095, 0.014, m["hose"], axis="Y")
    k.torus("ac_hose_b", (0.130, -0.195, 0.260), 0.085, 0.014, m["hose"], axis="Y")
    k.rod("ac_coupler", (0.225, -0.190, 0.290), (0.225, -0.190, 0.340), 0.012, m["brass"])


# ---------------------------------------------------------------- diagnostic bench (2x1)

def build_bench(k, m) -> None:
    """Spans x -0.40..1.40: tile (0,0) is centred on the origin, tile (1,0) on x = 1."""
    blue, blue_d = m["bench_blue"], m["bench_blue_d"]
    k.box("db_top", (0.50, 0.0, 0.845), (1.800, 0.660, 0.050), m["bench_top"], bevel=0.006)
    k.box("db_ped_l", (-0.10, 0.02, 0.410), (0.600, 0.600, 0.780), blue, bevel=0.008)
    k.box("db_ped_r", (1.10, 0.02, 0.410), (0.560, 0.600, 0.780), blue, bevel=0.008)
    k.box("db_back", (0.50, 0.29, 0.480), (0.620, 0.030, 0.640), blue_d)
    k.box("db_mid", (0.50, 0.02, 0.745), (0.620, 0.580, 0.130), blue, bevel=0.006)
    k.box("db_kick_l", (-0.10, 0.0, 0.025), (0.580, 0.560, 0.050), m["iron_d"])
    k.box("db_kick_r", (1.10, 0.0, 0.025), (0.540, 0.560, 0.050), m["iron_d"])
    y_face = -0.283
    for i, (z, h) in enumerate(((0.640, 0.180), (0.430, 0.200), (0.200, 0.220))):
        k.box(f"db_drawer_{i}", (-0.10, y_face, z), (0.540, 0.006, h), blue_d)
        k.rod(f"db_pull_{i}", (-0.20, y_face - 0.018, z + h * 0.25), (0.00, y_face - 0.018, z + h * 0.25),
              0.009, m["chrome"])
    k.box("db_mid_face", (0.50, y_face, 0.745), (0.560, 0.006, 0.100), blue_d)
    k.rod("db_mid_pull", (0.40, y_face - 0.018, 0.755), (0.60, y_face - 0.018, 0.755), 0.009, m["chrome"])
    k.box("db_door", (1.10, y_face, 0.390), (0.500, 0.006, 0.620), blue_d)
    k.box("db_door_handle", (0.90, y_face - 0.012, 0.460), (0.020, 0.014, 0.100), m["chrome"])
    # Riser shelf at the back of the top.
    k.box("db_riser", (0.30, 0.200, 0.990), (1.100, 0.220, 0.025), m["wood"])
    for x in (-0.22, 0.82):
        k.box(f"db_riser_leg_{x}", (x, 0.200, 0.920), (0.030, 0.200, 0.120), m["wood"])
    # Scope: cream case, green screen with a trace, knob row.
    k.box("db_scope", (0.40, 0.190, 1.130), (0.300, 0.230, 0.250), m["cream"], bevel=0.012)
    k.box("db_scope_bezel", (0.36, 0.072, 1.140), (0.180, 0.008, 0.150), m["gap"])
    k.box("db_scope_screen", (0.36, 0.066, 1.140), (0.150, 0.006, 0.120), m["screen"])
    for i in range(5):
        x = 0.30 + i * 0.030
        z = 1.140 + 0.030 * math.sin(i * 1.7)
        k.box(f"db_trace_{i}", (x, 0.062, z), (0.030, 0.004, 0.008), m["trace"])
    for i in range(3):
        k.cyl(f"db_knob_{i}", (0.500, 0.070, 1.200 - i * 0.050), 0.014, 0.014, m["black_plastic"],
              axis="Y", verts=12)
    # Analog meter: grey box with two dial faces.
    k.box("db_meter", (0.07, 0.190, 1.100), (0.240, 0.200, 0.190), m["alt_grey"], bevel=0.010)
    for i, x in enumerate((0.01, 0.13)):
        k.box(f"db_dial_{i}", (x, 0.087, 1.120), (0.090, 0.006, 0.080), m["gauge_face"])
        k.rod(f"db_needle_{i}", (x, 0.082, 1.090), (x + 0.025, 0.082, 1.140), 0.003, m["estop"])
    k.cyl("db_meter_jack", (0.07, 0.087, 1.040), 0.012, 0.010, m["estop"], axis="Y", verts=10)
    # Parts cabinet and a red toolbox on it, right end of the top.
    k.box("db_cabinet", (1.05, 0.170, 0.985), (0.320, 0.200, 0.230), blue, bevel=0.006)
    for r in range(3):
        for c in range(3):
            k.box(f"db_bin_{r}_{c}", (0.955 + c * 0.095, 0.068, 1.055 - r * 0.070),
                  (0.080, 0.006, 0.055), blue_d)
    k.box("db_toolbox", (1.05, 0.170, 1.145), (0.230, 0.110, 0.090), m["shop_red"], bevel=0.008)
    k.rod("db_toolbox_handle", (1.00, 0.170, 1.200), (1.10, 0.170, 1.200), 0.008, m["iron_d"])
    # Vise on the front-left corner.
    k.box("db_vise_base", (-0.25, -0.200, 0.885), (0.120, 0.120, 0.030), blue_d)
    k.box("db_vise_body", (-0.25, -0.200, 0.935), (0.080, 0.200, 0.070), blue, bevel=0.006)
    k.box("db_vise_jaw", (-0.25, -0.300, 0.960), (0.140, 0.030, 0.060), m["iron_d"])
    k.rod("db_vise_bar", (-0.33, -0.320, 0.930), (-0.17, -0.320, 0.930), 0.008, m["chrome"])
    # Clutter on the top: test leads, a rag, a spray can.
    k.path("db_lead_r", [(0.05, 0.02, 1.00), (0.10, -0.10, 0.875), (0.40, -0.18, 0.875),
                         (0.55, -0.08, 0.875)], 0.008, m["cable_red"])
    k.path("db_lead_k", [(0.11, 0.02, 1.00), (0.20, -0.06, 0.875), (0.48, -0.12, 0.875)],
           0.008, m["hose"])
    k.box("db_rag", (0.72, -0.130, 0.874), (0.180, 0.140, 0.008), m["rag"], rot=(0, 0, 0.35))
    k.cyl("db_can", (-0.33, 0.150, 0.930), 0.030, 0.120, m["jerry_red"], verts=16)
    # Cable coil hung on the right end.
    k.torus("db_coil", (1.395, 0.0, 0.450), 0.100, 0.012, m["cable_red"], axis="X")
    k.torus("db_coil_b", (1.400, 0.02, 0.440), 0.090, 0.012, m["cable_red"], axis="X")


#: Vanilla crafted_04_96 (Branch Workbench) is the model: toolcabinet container,
#: GenericCraftingSurface, IsTable/IsLow, Surface 36 (VERIFY flush in game).
BENCH_PROPS = {
    "BlocksPlacement": "", "solidtrans": "", "IsMoveAble": "", "CanScrap": "",
    "ScrapSize": "Large", "GroupName": "Garage", "CustomName": "Diagnostic Bench",
    "container": "toolcabinet", "ContainerCapacity": "30", "GenericCraftingSurface": "true",
    "IsTable": "", "IsLow": "", "Surface": "36", "Material": "MetalScrap",
    "Material2": "Electric", "PickUpWeight": "400",
}

PIECES = {
    "stand": ("Engine Stand", build_stand),
    "tire": ("Tire Changer", build_tire),
    "comp": ("Air Compressor", build_comp),
}


def render_subject(props, sheet: str, build_fn) -> dict:
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
    G.make_texture()
    mats = materials()

    F.register()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    props = scene.pz_forge
    props.sheet_name = SHEET
    props.output_dir = str(OUT)
    props.footprint_x = 2 if BENCH else 1
    props.footprint_y = 1
    props.facings = "4"
    props.show_guide = False
    props.contrast_boost = 1.0
    props.toon_shading = True
    F.build_rig(bpy.context)
    scene.cycles.samples = int(arg("--samples", "512"))
    scene.cycles.use_denoising = True

    if BENCH:
        order = [("gb_bench", "Diagnostic Bench", lambda: build_bench(G.Kit(), mats))]
    else:
        keys = arg("--only", ",".join(PIECES)).split(",")
        order = [(f"gg_{key}", PIECES[key][0], (lambda fn=PIECES[key][1]: fn(G.Kit(), mats)))
                 for key in keys]
    manifests = [(s, name, render_subject(props, s, fn)) for s, name, fn in order]

    merged = dict(manifests[0][2])
    merged["sheet"] = SHEET
    merged["isolate_tiles"] = True
    elements: dict = {}
    cells: list = []
    for group, (_, name, manifest) in enumerate(manifests):
        elements.update(manifest.get("elements", {}))
        for cell in manifest["cells"]:
            extra = {"group": group, "piece": name}
            if BENCH:
                # A cell's tile_props REPLACE the props file for that cell (bbq_s10 does the
                # same), so the whole bench block rides here, not in knx_garage_bench_props.json.
                extra["tile_props"] = dict(BENCH_PROPS, Facing=cell["facing"],
                                           SpriteGridPos=f"{cell['x']},{cell['y']}")
            cells.append(dict(cell, **extra))
    merged["elements"] = elements
    merged["cells"] = cells
    (OUT / "manifest.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"merged {len(cells)} cell(s) into {SHEET} at {OUT}")


if __name__ == "__main__":
    main()
