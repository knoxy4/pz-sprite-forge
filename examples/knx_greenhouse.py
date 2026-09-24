"""BADLANDS greenhouse: glass wall set + glass roof panel (Furniture tilesets 17, 18).

Farming reads "under cover" off the engine's own roof test: a plant whose square
has a rain-blocking tile (solidfloor or BlockRain) somewhere above it is not
exterior, so it skips every winter / bad-month kill (see ZOMBOID project
mods/greenhouse-farming-hook-recon.md). The ROOF panel is the mechanic; the walls
are for looks and security.

Walls -- wall grammar from brick_wall.py / knx_corrugated.py, 2x4 footprint,
isolate_tiles, and the same slot order as vanilla's jail set
(location_community_police_01), whose props they mirror:

    (0,0) WallW      (1,0) WallN
    (0,1) NW corner  (1,1) SE post (at its own tile's NW corner)
    (0,2) door W     (1,2) door N          closed, hinged at the NW end
    (0,3) door W op  (1,3) door N op       leaf swung 90 deg into the tile

Roof (--roof) -- a 1x1 FLOOR-aligned glazed panel, built on z+1 from the ground.

Glass renders OPAQUE here so the style pass shades it like any other paint; the
"glass_*" parts are then made translucent per pixel from the element pass by
build/_greenhouse_glass.py, before `pzforge build` (which preserves alpha).

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_greenhouse.py -- [--roof] [--samples N]
"""
from __future__ import annotations

import dataclasses
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(ROOT))

import pz_sprite_forge as F  # noqa: E402

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOF = "--roof" in ARGV
SHEET = "badlands_ghroof_01" if ROOF else "badlands_greenhouse_01"
OUT = ROOT / "build" / ("ghroof_cells" if ROOF else "greenhouse_cells")
GRAIN = ROOT / "build" / "greenhouse_grain.png"

H = 2.4497        # vanilla wall height (brick_wall.py)
D = 0.045         # frame depth
STILE = 0.045
KICK = 0.42       # painted kick board
SILL = 0.05
TRANSOM = 1.62
RAIL = 0.055
GLASS_T = 0.006


def maps() -> None:
    from pzforge.texture import material_spec, write_surface_map
    w = material_spec("wood", seed=71)
    w = dataclasses.replace(w, octaves=[(s, a * 0.3) for s, a in w.octaves], knot_count=0)
    write_surface_map(GRAIN, 512, 512, w, grain_axis="v")


def materials() -> dict:
    fm = F.forge_material
    return {
        # weathered white-painted glazing bars; light woods need a narrow swing
        "frame": fm("gh_frame", "wood", (0.80, 0.80, 0.76), texture_path=GRAIN,
                    swing=(0.86, 1.06)),
        # sage-green painted kick boards
        "kick": fm("gh_kick", "wood", (0.45, 0.52, 0.44), texture_path=GRAIN,
                   swing=(0.82, 1.10)),
        # opaque here; made translucent from the element pass after render
        "glass": F.toon_material("gh_glass", (0.62, 0.78, 0.76)),
        "handle": F.toon_material("gh_handle", (0.20, 0.20, 0.21)),
    }


def box(name, centre, size, mat, parts, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
    o = bpy.context.active_object
    o.name, o.scale = name, size
    o.rotation_euler.z = rot
    o.data.materials.append(mat)
    parts.append(o)
    return o


def to_world(origin, heading, u, n, z):
    """Local run coords -> world: u along heading, n along the left normal."""
    ch, sh = math.cos(heading), math.sin(heading)
    return (origin[0] + u * ch - n * sh, origin[1] + u * sh + n * ch, z)


def member(key, origin, heading, side, u0, u1, z0, z1, mat, parts,
           depth=D, inset=0.0):
    """A box spanning [u0,u1] x [z0,z1] on a run; ``side`` (+1/-1) picks which
    normal side is inside the tile, ``inset`` pushes it off the edge line."""
    c = to_world(origin, heading, (u0 + u1) / 2, side * (inset + depth / 2), (z0 + z1) / 2)
    return box(key, c, (u1 - u0, depth, z1 - z0), mat, parts, heading)


def pane(key, origin, heading, side, u0, u1, z0, z1, M, parts):
    return member(f"glass_{key}", origin, heading, side, u0, u1, z0, z1, M["glass"],
                  parts, depth=GLASS_T, inset=D / 2 - GLASS_T / 2)


def wall(key, origin, heading, side, M, parts, length=1.0, start_stile=True):
    """One glazed wall run: kick board, sill, mid mullion, transom, top rail,
    four panes. The stile sits at the run's start only; the next tile's wall
    (or the SE post) closes the far end, as vanilla wall runs do."""
    L = length
    mw = 0.04
    fr, kk = M["frame"], M["kick"]
    s0 = STILE if start_stile else 0.0
    if start_stile:
        member(f"{key}_stile", origin, heading, side, 0.0, STILE, 0.0, H, fr, parts)
    member(f"{key}_kick", origin, heading, side, s0, L, 0.0, KICK, kk, parts,
           depth=D * 0.8, inset=D * 0.1)
    member(f"{key}_sill", origin, heading, side, s0, L, KICK, KICK + SILL, fr, parts)
    member(f"{key}_top", origin, heading, side, s0, L, H - RAIL, H, fr, parts)
    m0, m1 = L / 2 - mw / 2, L / 2 + mw / 2
    member(f"{key}_mull", origin, heading, side, m0, m1, KICK + SILL, H - RAIL, fr, parts,
           depth=D * 0.9, inset=D * 0.05)
    for tag, (a, b) in (("l", (s0, m0)), ("r", (m1, L))):
        member(f"{key}_tr{tag}", origin, heading, side, a, b, TRANSOM, TRANSOM + 0.04, fr,
               parts, depth=D * 0.8, inset=D * 0.1)
        pane(f"{key}_lo{tag}", origin, heading, side, a, b, KICK + SILL, TRANSOM, M, parts)
        pane(f"{key}_hi{tag}", origin, heading, side, a, b, TRANSOM + 0.04, H - RAIL, M, parts)


def leaf(key, hinge, heading, side, M, parts):
    """Door leaf from ``hinge`` along ``heading``: glazed over a kick panel."""
    LW, LH, st = 0.84, 2.06, 0.05
    fr = M["frame"]
    member(f"{key}_st0", hinge, heading, side, 0.0, st, 0.0, LH, fr, parts, depth=0.04)
    member(f"{key}_st1", hinge, heading, side, LW - st, LW, 0.0, LH, fr, parts, depth=0.04)
    member(f"{key}_kick", hinge, heading, side, st, LW - st, 0.0, 0.40, M["kick"], parts,
           depth=0.032, inset=0.004)
    for z0, z1 in ((0.40, 0.45), (1.06, 1.10), (LH - 0.05, LH)):
        member(f"{key}_rail{z0}", hinge, heading, side, st, LW - st, z0, z1, fr, parts,
               depth=0.04)
    for z0, z1 in ((0.45, 1.06), (1.10, LH - 0.05)):
        member(f"glass_{key}_{z0}", hinge, heading, side, st, LW - st, z0, z1, M["glass"],
               parts, depth=GLASS_T, inset=0.017)
    member(f"{key}_handle", hinge, heading, side, LW - 0.11, LW - 0.07, 0.98, 1.02,
           M["handle"], parts, depth=0.03, inset=0.035)


def door(key, origin, heading, side, M, parts, open_=False):
    """Jambs, header and a glazed transom stay put; only the leaf swings."""
    fr = M["frame"]
    J, HD = 0.07, 2.08
    member(f"{key}_j0", origin, heading, side, 0.0, J, 0.0, H, fr, parts)
    member(f"{key}_j1", origin, heading, side, 1.0 - J, 1.0, 0.0, H, fr, parts)
    member(f"{key}_head", origin, heading, side, J, 1.0 - J, HD, HD + 0.05, fr, parts)
    member(f"{key}_top", origin, heading, side, J, 1.0 - J, H - RAIL, H, fr, parts)
    pane(f"{key}_transom", origin, heading, side, J, 1.0 - J, HD + 0.05, H - RAIL, M, parts)
    if not open_:
        h = to_world(origin, heading, J + 0.01, 0.0, 0.0)
        leaf(f"{key}_leaf", h, heading, side, M, parts)
    else:
        # swung about the hinge jamb into the tile, lying along the tile's
        # north (W door) or west (N door) edge, as vanilla's barred cell door does
        h = to_world(origin, heading, J, side * (D + 0.01), 0.0)
        leaf(f"{key}_leaf", h, heading + side * math.pi / 2, -side, M, parts)


def build_walls(M) -> list:
    p: list = []
    S, E = -math.pi / 2, 0.0
    # (0,0) WallW on the west edge x=-0.5, run south from y=+0.5; inside is +x.
    wall("w", (-0.5, 0.5), S, +1, M, p)
    # (1,0) WallN on the north edge y=0.5, run east from x=0.5; inside is -y.
    wall("n", (0.5, 0.5), E, -1, M, p)
    # (0,1) world (0,-1): NW corner; the N arm butts the W arm's inner face and
    # stops 2 mm short of the east edge (a face ON the boundary would be cut).
    wall("cw", (-0.5, -0.5), S, +1, M, p)
    wall("cn", (-0.5 + D + 0.002, -0.5), E, -1, M, p, length=0.998 - D - 0.002,
         start_stile=False)
    # (1,1) world (1,-1): SE post at its own tile's NW corner.
    P = 0.05
    box("post", (0.5 + P / 2, -0.5 - P / 2, H / 2), (P, P, H), M["frame"], p)
    # (0,2)/(1,2) doors closed; (0,3)/(1,3) open.
    door("dw", (-0.5, -1.5), S, +1, M, p)
    door("dn", (0.5, -1.5), E, -1, M, p)
    door("dwo", (-0.5, -2.5), S, +1, M, p, open_=True)
    door("dno", (0.5, -2.5), E, -1, M, p, open_=True)
    return p


def build_roof(M) -> list:
    """A glazed floor panel: white frame round the edge, a cross of glazing
    bars, four panes. Sits on the upper level's floor plane (z = 0 here)."""
    p: list = []
    B, X, Z = 0.05, 0.035, 0.03
    fr = M["frame"]
    box("r_n", (0.0, 0.5 - B / 2, Z / 2), (1.0, B, Z), fr, p)
    box("r_s", (0.0, -0.5 + B / 2, Z / 2), (1.0, B, Z), fr, p)
    box("r_w", (-0.5 + B / 2, 0.0, Z / 2), (B, 1.0 - 2 * B, Z), fr, p)
    box("r_e", (0.5 - B / 2, 0.0, Z / 2), (B, 1.0 - 2 * B, Z), fr, p)
    box("r_x", (0.0, 0.0, Z / 2), (1.0 - 2 * B, X, Z * 0.9), fr, p)
    box("r_y", (0.0, 0.0, Z / 2), (X, 1.0 - 2 * B, Z * 0.9), fr, p)
    q = (0.5 - B - X / 2) / 2 + X / 2
    s = 0.5 - B - X / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"glass_r{sx}{sy}", (sx * q, sy * q, Z * 0.45), (s, s, 0.004), M["glass"], p)
    return p


COMMON = {"CanScrap": "", "Material": "Wood", "MaterialType": "Glass",
          "GroupName": "Badlands Greenhouse"}


def tile_props(i, j):
    s = lambda k: f"{SHEET}_{k}"
    wall_ = dict(COMMON, CustomName="Greenhouse Wall", GrimeType="FullWindow",
                 NoWallLighting="", wall="")
    door_ = {"CanScrap": "", "CustomName": "Greenhouse Door", "Material": "Door",
             "Material2": "Wood", "MaterialType": "Glass", "GroupName": "Badlands Greenhouse",
             "doorTrans": ""}
    return {
        (0, 0): dict(wall_, WallWTrans=""),
        (1, 0): dict(wall_, WallNTrans=""),
        (0, 1): dict(wall_, WallNWTrans="", CornerNorthWall=s(1), CornerWestWall=s(0)),
        (1, 1): {"CanScrap": "", "Material": "Wood", "GroupName": "Badlands Greenhouse",
                 "WallSE": "", "wall": ""},
        (0, 2): dict(door_, doorW="", attachedW=""),
        (1, 2): dict(door_, doorN="", attachedN=""),
        (0, 3): dict(door_, attachedW=""),
        (1, 3): dict(door_, attachedN=""),
    }[(i, j)]


ROOF_PROPS = dict(COMMON, CustomName="Greenhouse Roof", solidfloor="", transparentFloor="",
                  BlockRain="")


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    maps()
    F.register()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    pr = sc.pz_forge
    pr.sheet_name = SHEET
    pr.output_dir = str(OUT)
    pr.facings = "1"
    pr.show_guide = False
    pr.contrast_boost = 1.0
    pr.toon_shading = True
    if ROOF:
        pr.footprint_x = pr.footprint_y = 1
        pr.alignment = "FLOOR"
        pr.ground_occlusion = False
    else:
        pr.footprint_x, pr.footprint_y = 2, 4
        pr.isolate_tiles = True
    F.build_rig(bpy.context)
    sc.cycles.samples = int(ARGV[ARGV.index("--samples") + 1]) if "--samples" in ARGV else 512
    sc.cycles.use_denoising = True
    subject = bpy.data.objects[F.SUBJECT_NAME]
    M = materials()
    for o in (build_roof(M) if ROOF else build_walls(M)):
        o.parent = subject
    manifest = F.render_cells(bpy.context)
    for c in manifest["cells"]:
        c["group"] = 0
        c["tile_props"] = ROOF_PROPS if ROOF else tile_props(c["x"], c["y"])
    manifest["isolate_tiles"] = not ROOF
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"rendered {len(manifest['cells'])} cell(s) to {OUT}")


if __name__ == "__main__":
    main()
