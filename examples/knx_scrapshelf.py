"""BADLANDS scrap shelves: battery shelf and gas can shelf, each knocked together
from scrap wood and from scrap metal. Messy but organized, stacked full.

Rides the knx_shelving.py fill-state pipeline (three states: stocked, picked
over, stripped; index // 12 piece, (index % 12) // 3 facing S E N W, index % 3
state) by swapping its OBJECTS / PIECES / materials and reusing its main().

    group 0  Battery Shelf    scrap wood    car batteries two high, jumper cables
    group 1  Battery Shelf    scrap metal   same load on a welded junk rack
    group 2  Gas Can Shelf    scrap wood    red plastic gas cans, a coiled siphon hose
    group 3  Gas Can Shelf    scrap metal

Sheet badlands_scrapshelf_01 (tileset 12 in tiledef 2000).

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_scrapshelf.py -- [--samples N] [--only KEY]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import knx_shelving as S  # noqa: E402

F = S.F
ROOT = S.ROOT
S.SHEET = "badlands_scrapshelf_01"
S.OUT = ROOT / "build" / "scrapshelf_cells"

W, D, H = S.WIDTH, S.DEPTH, 1.98
LEVELS = (0.100, 0.575, 1.050, 1.525)


def _r(*k) -> float:
    h = 2166136261
    for v in k:
        for ch in str(v):
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def _j(scale, *k) -> float:
    return (_r(*k) - 0.5) * 2 * scale


_base_materials = S.materials


def materials() -> dict:
    m = _base_materials()
    t, fm = F.toon_material, F.forge_material
    grain, steel = str(S.GRAIN_PATH), str(S.METAL_PATH)
    m.update({
        "scrapwood": [fm(f"ss_wood_{i}", "wood", p, texture_path=grain) for i, p in enumerate([
            (0.46, 0.40, 0.33), (0.52, 0.33, 0.17), (0.66, 0.52, 0.32),
            (0.36, 0.25, 0.15), (0.42, 0.36, 0.30)])],
        "scrapmetal": [fm(f"ss_metal_{i}", "metal", p, texture_path=steel,
                          accent=(0.40, 0.20, 0.08)) for i, p in enumerate([
            (0.40, 0.41, 0.40), (0.42, 0.26, 0.14), (0.24, 0.32, 0.22),
            (0.50, 0.50, 0.46), (0.30, 0.20, 0.12)])],
        "bat_case": [t(f"ss_bat_{i}", p) for i, p in enumerate([
            (0.07, 0.07, 0.075), (0.10, 0.10, 0.11), (0.16, 0.16, 0.17)])],
        "bat_label": [t(f"ss_lab_{i}", p) for i, p in enumerate([
            (0.10, 0.25, 0.60), (0.70, 0.55, 0.08), (0.62, 0.10, 0.06),
            (0.55, 0.55, 0.52), (0.12, 0.38, 0.14)])],
        "term_pos": t("ss_term_pos", (0.70, 0.10, 0.06)),
        "term_neg": t("ss_term_neg", (0.05, 0.05, 0.05)),
        "lead": t("ss_lead", (0.55, 0.55, 0.52)),
        "cable_r": t("ss_cable_r", (0.62, 0.07, 0.05)),
        "cable_k": t("ss_cable_k", (0.06, 0.06, 0.06)),
        "clamp": t("ss_clamp", (0.70, 0.62, 0.20)),
        "gas": [t(f"ss_gas_{i}", p) for i, p in enumerate([
            (0.66, 0.08, 0.05), (0.58, 0.07, 0.05), (0.72, 0.20, 0.10), (0.52, 0.12, 0.08)])],
        "gas_cap": t("ss_gas_cap", (0.08, 0.08, 0.08)),
        "gas_spout": t("ss_gas_spout", (0.76, 0.62, 0.10)),
        "hose": t("ss_hose", (0.40, 0.48, 0.30)),
    })
    return m


# --------------------------------------------------------------- carcasses

def scrap_wood_frame(b, m, key):
    """Four 2x4 posts, decks of mismatched boards with ragged ends, side braces
    and a couple of back rails -- no two boards the same shade."""
    wood = m["scrapwood"]

    def pick(*k):
        return wood[int(_r(key, *k) * len(wood)) % len(wood)]

    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(f"post_{sx}_{sy}", (sx * (W / 2 - 0.03), sy * (D / 2 - 0.045), H / 2),
                  (0.045, 0.09, H + _j(0.03, key, "ph", sx, sy)), pick("post", sx, sy),
                  rot=(_j(0.010, key, "px", sx, sy), _j(0.010, key, "py", sx, sy), 0.0))
    for i, z in enumerate(LEVELS):
        y = -D / 2 + 0.01
        k = 0
        while y < D / 2 - 0.04:
            bw = min(0.09 + _r(key, "bw", i, k) * 0.07, D / 2 - y)
            over = _j(0.035, key, "ov", i, k)
            b.box(f"deck_{i}_{k}", (over, y + bw / 2, z + _j(0.004, key, "dz", i, k)),
                  (W + 0.02 + abs(over), bw - 0.008, 0.022), pick("deck", i, k),
                  rot=(0.0, _j(0.006, key, "dr", i, k), _j(0.012, key, "dy", i, k)))
            y += bw
            k += 1
        b.box(f"rail_{i}", (0, -D / 2 + 0.01, z - 0.045), (W - 0.02, 0.022, 0.07),
              pick("rail", i))
    ln = math.hypot(D, H * 0.45)
    ang = math.atan2(H * 0.45, D)
    for sx in (-1, 1):  # side X-brace boards
        for n, zc in enumerate((H * 0.30, H * 0.72)):
            b.box(f"brace_{sx}_{n}", (sx * (W / 2 + 0.012), 0, zc), (0.018, ln, 0.07),
                  pick("brace", sx, n), rot=((ang if n == 0 else -ang) * sx, 0.0, 0.0))
    for n, zc in enumerate((0.42, 1.30)):
        b.box(f"back_{n}", (_j(0.03, key, "bk", n), D / 2 - 0.02, zc), (W + 0.04, 0.02, 0.10),
              pick("back", n), rot=(0.0, _j(0.03, key, "bkr", n), 0.0))


def scrap_metal_frame(b, m, key):
    """Two pipes and two angle-iron uprights, decks of odd plate, a rebar X on
    the back and a welded patch -- a rack built from whatever was in the yard."""
    met = m["scrapmetal"]

    def pick(*k):
        return met[int(_r(key, *k) * len(met)) % len(met)]

    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x, y = sx * (W / 2 - 0.03), sy * (D / 2 - 0.03)
        if n in (0, 3):
            b.cyl(f"post_{n}", (x, y, H / 2), 0.024, H + _j(0.02, key, "ph", n), pick("post", n))
        else:
            b.box(f"post_{n}a", (x, y, H / 2), (0.045, 0.006, H), pick("post", n))
            b.box(f"post_{n}b", (x, y, H / 2), (0.006, 0.045, H), pick("post", n))
    for i, z in enumerate(LEVELS):
        split = 0.35 + _r(key, "split", i) * 0.30
        for k, (x0, x1) in enumerate(((-W / 2, -W / 2 + split * W), (-W / 2 + split * W, W / 2))):
            b.box(f"deck_{i}_{k}", ((x0 + x1) / 2 + _j(0.012, key, "dx", i, k),
                                    _j(0.012, key, "dy", i, k), z + 0.004 * k),
                  (x1 - x0 + 0.03, D + _j(0.02, key, "dd", i, k), 0.012), pick("deck", i, k),
                  rot=(0.0, 0.0, _j(0.02, key, "dr", i, k)))
        b.box(f"lip_{i}", (0, -D / 2 + 0.004, z - 0.02), (W - 0.01, 0.010, 0.045), pick("lip", i))
    span = math.hypot(W, H * 0.9)
    ang = math.atan2(H * 0.9, W)
    for n, a in enumerate((ang, -ang)):
        b.cyl(f"rebar_{n}", (0, D / 2 - 0.02, H / 2), 0.008, span, m["steel_dark"],
              rot=(0.0, math.pi / 2 - a, 0.0), vertices=8)
    b.box("patch", (W / 2 + 0.004, 0.02, 0.80), (0.008, 0.18, 0.22), pick("patch"))


# ---------------------------------------------------------------- contents

def battery(b, m, n, cx, cy, z0, yaw, key):
    L, Dp, Hh = 0.26, 0.175, 0.19
    c, s = math.cos(yaw), math.sin(yaw)

    def at(lx, ly, lz):
        return (cx + lx * c - ly * s, cy + lx * s + ly * c, z0 + lz)

    case = m["bat_case"][int(_r(key, n, "c") * 3) % 3]
    b.box(f"{n}_case", at(0, 0, Hh / 2), (L, Dp, Hh), case, rot=(0, 0, yaw))
    b.box(f"{n}_lid", at(0, 0, Hh + 0.008), (L - 0.01, Dp - 0.01, 0.016),
          m["bat_case"][0], rot=(0, 0, yaw))
    lab = m["bat_label"][int(_r(key, n, "l") * 5) % 5]
    b.box(f"{n}_label", at(0, -Dp / 2 - 0.002, Hh * 0.62), (L * 0.78, 0.004, 0.06), lab,
          rot=(0, 0, yaw))
    for sgn, mat in ((-1, m["term_pos"]), (1, m["term_neg"])):
        b.cyl(f"{n}_t{sgn}", at(sgn * 0.085, -0.045, Hh + 0.028), 0.013, 0.026, m["lead"],
              vertices=10)
        b.cyl(f"{n}_c{sgn}", at(sgn * 0.085, -0.045, Hh + 0.018), 0.022, 0.008, mat,
              vertices=10)


def torus(b, name, loc, major, minor, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=20, minor_segments=8,
                                     location=(loc[0], loc[1] + S.OFFSET_Y, loc[2] + S.OFFSET_Z))
    o = bpy.context.active_object
    o.rotation_euler = rot
    return b._place(o, name, mat)


def load_batteries(b, m, key):
    for row, z in enumerate(LEVELS):
        z0 = z + 0.013
        for col, x in enumerate((-0.29, 0.0, 0.29)):
            if row == 3 and col == 2:
                # jumper cables coiled where the third battery would sit
                n = f"item_{row}_{col}"
                torus(b, f"{n}_r", (x, -0.02, z0 + 0.015), 0.10, 0.011, m["cable_r"])
                torus(b, f"{n}_k", (x + 0.015, -0.03, z0 + 0.038), 0.095, 0.011, m["cable_k"],
                      rot=(0.05, 0.08, 0.3))
                for s, dx in ((0, -0.07), (1, 0.06)):
                    b.box(f"{n}_clamp{s}", (x + dx, -0.12, z0 + 0.05), (0.07, 0.03, 0.025),
                          m["clamp"], rot=(0, 0.3, 0.4 * (s - 0.5)))
                continue
            for k in range(1 if row == 3 else 2):
                n = f"item_{row}_{col}_{k}"
                turned = _r(key, n, "turn") < 0.12
                yaw = (math.pi / 2 if turned else 0.0) + _j(0.07, key, n, "yaw")
                battery(b, m, n, x + _j(0.015, key, n, "x"), -0.02 + _j(0.02, key, n, "y"),
                        z0 + k * 0.232, yaw, key)


def gas_can(b, m, n, cx, cy, z0, yaw, key, lying=False):
    """Red plastic can, long axis along its local y: body, carry handle, spout."""
    L, Wd, Hh = 0.30, 0.16, 0.25
    body = m["gas"][int(_r(key, n, "g") * 4) % 4]
    c, s = math.cos(yaw), math.sin(yaw)

    def at(lx, ly, lz):
        return (cx + lx * c - ly * s, cy + lx * s + ly * c, z0 + lz)

    if lying:
        b.box(f"{n}_body", at(0, 0, Wd / 2), (Hh, L, Wd), body, rot=(0, 0, yaw))
        b.box(f"{n}_handle", at(Hh / 2 + 0.02, 0.05, Wd / 2), (0.022, 0.15, 0.03), body,
              rot=(0, 0, yaw))
        return
    b.box(f"{n}_body", at(0, 0, Hh / 2), (Wd, L, Hh), body, rot=(0, 0, yaw))
    b.box(f"{n}_shoulder", at(0, 0.02, Hh + 0.012), (Wd - 0.03, L - 0.08, 0.024), body,
          rot=(0, 0, yaw))
    b.box(f"{n}_handle", at(0, 0.05, Hh + 0.058), (0.03, 0.15, 0.022), body, rot=(0, 0, yaw))
    for dy in (-0.02, 0.12):
        b.box(f"{n}_hp{int(dy * 100)}", at(0, dy, Hh + 0.035), (0.03, 0.02, 0.045), body,
              rot=(0, 0, yaw))
    b.cyl(f"{n}_neck", at(0, -L / 2 + 0.04, Hh + 0.03), 0.024, 0.05, m["gas_cap"])
    b.cyl(f"{n}_spout", at(0, -L / 2 + 0.005, Hh + 0.075), 0.012, 0.11, m["gas_spout"],
          rot=(0.9, 0, yaw))


def load_gas(b, m, key):
    for row, z in enumerate(LEVELS):
        z0 = z + 0.013
        for col, x in enumerate((-0.37, -0.185, 0.0, 0.185, 0.37)):
            n = f"item_{row}_{col}"
            if row == 3 and col >= 3:
                if col == 3:  # a coiled siphon hose where two cans would stand
                    torus(b, f"{n}_hose", (0.28, -0.02, z0 + 0.012), 0.12, 0.012, m["hose"])
                    torus(b, f"{n}_hose2", (0.29, -0.01, z0 + 0.034), 0.11, 0.012, m["hose"],
                          rot=(0.06, -0.05, 0))
                continue
            yaw = _j(0.10, key, n, "yaw") + (math.pi if _r(key, n, "flip") < 0.3 else 0.0)
            gas_can(b, m, n, x + _j(0.01, key, n, "x"), _j(0.02, key, n, "y"), z0, yaw, key)


def build_battery_wood(b, m):
    scrap_wood_frame(b, m, "bw")
    load_batteries(b, m, "bw")


def build_battery_metal(b, m):
    scrap_metal_frame(b, m, "bm")
    load_batteries(b, m, "bm")


def build_gas_wood(b, m):
    scrap_wood_frame(b, m, "gw")
    load_gas(b, m, "gw")


def build_gas_metal(b, m):
    scrap_metal_frame(b, m, "gm")
    load_gas(b, m, "gm")


def looted_batteries(name):
    """Row 1 gone, one stack short on rows 0 and 2, top layer thinned."""
    row, col = S._rc(name)
    top = name.split("_")[3].startswith("1")
    return row == 1 or (row == 0 and col == 2) or (row == 2 and col == 0) or (row == 0 and top)


def looted_gas(name):
    row, col = S._rc(name)
    return row == 1 or (row == 2 and col % 2 == 0) or (row == 0 and col >= 3)


WOOD = dict(S.WOOD_PROPS, GroupName="Badlands Scrap", Material2="Nails")
METAL = dict(S.STEEL_PROPS, GroupName="Badlands Scrap")
S.OBJECTS = [
    ("battery_wood", "Battery Shelf", "60", WOOD),
    ("battery_metal", "Battery Shelf", "60", METAL),
    ("gas_wood", "Gas Can Shelf", "60", WOOD),
    ("gas_metal", "Gas Can Shelf", "60", METAL),
]
S.PIECES = [
    (build_battery_wood, looted_batteries),
    (build_battery_metal, looted_batteries),
    (build_gas_wood, looted_gas),
    (build_gas_metal, looted_gas),
]
S.materials = materials

if __name__ == "__main__":
    S.main()
