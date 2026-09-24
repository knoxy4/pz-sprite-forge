"""BADLANDS Greenhouse Workshop hero: the real wall/door/roof geometry from
knx_greenhouse.py assembled into a 3x2 greenhouse, in winter.

Same rig, camera angle, key light and toon materials as the shipping tiles;
beauty pass only (no style pass), at ~3x tile density. Inside: two raised beds
of staked tomatoes in fruit. Outside: snow, drifts against the kick boards, and
a frost-killed row along the east wall -- the mod's whole pitch in one frame.
Glass is translucent here (EEVEE blended); the tiles bake that in afterwards.

    & 'C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe' -b \
        -P examples/knx_greenhouse_hero.py
Output: build/heroes_furniture/greenhouse_hero.png
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(ROOT))
import pz_sprite_forge as F  # noqa: E402

OUT = ROOT / "build" / "heroes_furniture" / "greenhouse_hero.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("knx_greenhouse", ROOT / "examples" / "knx_greenhouse.py")
G = importlib.util.module_from_spec(spec)
sys.modules["knx_greenhouse"] = G
spec.loader.exec_module(G)

NX, NY = 3, 2          # footprint in tiles: x in [-1.5, 1.5], y in [-1, 1]
X0, X1, Y0, Y1 = -1.5, 1.5, -1.0, 1.0
rng = random.Random(42)


def glassify(mat, fac=0.62):
    """Toon emission -> mixed with a transparent BSDF, EEVEE blended."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    link = out.inputs["Surface"].links[0]
    src = link.from_socket
    nt.links.remove(link)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = fac
    nt.links.new(src, mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    else:
        mat.blend_method = "BLEND"
    if hasattr(mat, "use_transparent_shadow"):
        mat.use_transparent_shadow = True
    mat.show_transparent_back = True


def mats() -> dict:
    tm = F.toon_material
    M = G.materials()
    # at 3x the grain map's swing reads as camo on the pale boards: flatten it
    M["kick"] = F.forge_material("gh_kick_h", "wood", (0.45, 0.52, 0.44), texture_path=G.GRAIN,
                                 swing=(0.93, 1.04))
    M["frame"] = F.forge_material("gh_frame_h", "wood", (0.82, 0.82, 0.79), texture_path=G.GRAIN,
                                  swing=(0.95, 1.03))
    glassify(M["glass"], fac=0.80)
    M.update({
        "soil": tm("gh_soil", (0.30, 0.22, 0.15)),
        "dirt": tm("gh_dirt", (0.40, 0.33, 0.25)),
        "bed": tm("gh_bed", (0.46, 0.34, 0.22)),
        "stake": tm("gh_stake", (0.55, 0.45, 0.31)),
        "stem": tm("gh_stem", (0.30, 0.42, 0.18)),
        "leaf": tm("gh_leaf", (0.24, 0.45, 0.17)),
        "leaf2": tm("gh_leaf2", (0.32, 0.52, 0.20)),
        "tom": tm("gh_tom", (0.78, 0.16, 0.08)),
        "tom2": tm("gh_tom2", (0.86, 0.46, 0.10)),
        "snow": tm("gh_snow", (0.86, 0.89, 0.94)),
        "trodden": tm("gh_trodden", (0.76, 0.78, 0.81)),
        "dead": tm("gh_dead", (0.33, 0.25, 0.16)),
        "deadleaf": tm("gh_deadleaf", (0.28, 0.22, 0.13)),
    })
    return M


def blob(name, loc, scale, mat, parts, rot=(0.0, 0.0, 0.0), seg=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(4, seg // 2), location=loc)
    o = bpy.context.active_object
    o.name, o.scale, o.rotation_euler = name, scale, rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    parts.append(o)
    return o


def rod(name, a, b, r, mat, parts):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    parts.append(o)
    return o


def tomato(key, x, y, z0, M, p):
    h = 0.70 + rng.random() * 0.15
    G.box(f"{key}_stake", (x + 0.05, y + 0.03, z0 + 0.48), (0.02, 0.02, 0.96), M["stake"], p)
    lean = (rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04))
    rod(f"{key}_stem", (x, y, z0), (x + lean[0], y + lean[1], z0 + h), 0.012, M["stem"], p)
    for k in range(7):
        t = 0.25 + 0.7 * k / 6
        a = rng.uniform(0, 2 * math.pi)
        r = 0.07 + 0.05 * (1 - t)
        blob(f"{key}_lf{k}", (x + lean[0] * t + r * math.cos(a), y + lean[1] * t + r * math.sin(a), z0 + h * t),
             (0.10 + 0.04 * (1 - t), 0.07, 0.035), M["leaf" if k % 2 else "leaf2"], p,
             rot=(rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4), a), seg=8)
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, 2 * math.pi)
        z = z0 + h * rng.uniform(0.28, 0.62)
        rr = rng.uniform(0.026, 0.036)
        blob(f"{key}_t{k}", (x + 0.06 * math.cos(a), y + 0.06 * math.sin(a), z), (rr, rr, rr * 0.9),
             M["tom" if rng.random() < 0.7 else "tom2"], p, seg=10)


def dead_plant(key, x, y, M, p):
    """A frost-killed tomato: stem folded over at the knee, leaves hanging limp,
    one blackened fruit, snow on the bend."""
    h = 0.34 + rng.random() * 0.12
    knee = (x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), h)
    a = rng.uniform(0, 2 * math.pi)
    tip = (knee[0] + 0.22 * math.cos(a), knee[1] + 0.22 * math.sin(a), h * 0.45)
    rod(f"{key}_stem", (x, y, 0.0), knee, 0.012, M["dead"], p)
    rod(f"{key}_fold", knee, tip, 0.010, M["dead"], p)
    for k in range(6):
        src = knee if k < 3 else tip
        t = rng.uniform(0.3, 0.9)
        c = (x + (src[0] - x) * t + rng.uniform(-0.04, 0.04), y + (src[1] - y) * t + rng.uniform(-0.04, 0.04),
             src[2] * t - 0.02)
        blob(f"{key}_lf{k}", c, (0.025, 0.05, 0.012), M["deadleaf"], p,
             rot=(rng.uniform(1.1, 1.5), 0.0, rng.uniform(0, 6.28)), seg=6)  # hanging, edge-on
    blob(f"{key}_rot", (tip[0], tip[1], tip[2] - 0.03), (0.024, 0.024, 0.02), M["deadleaf"], p, seg=8)
    blob(f"{key}_snowcap", (knee[0], knee[1], knee[2] + 0.012), (0.045, 0.035, 0.014), M["snow"], p, seg=8)


def snow_field(M, p):
    """An irregular snow patch (not a slab): a noisy ellipse, soft rim."""
    import bmesh
    me = bpy.data.meshes.new("snowfield")
    bm = bmesh.new()
    n = 64
    ring = []
    for k in range(n):
        a = 2 * math.pi * k / n
        r = 1.0 + 0.06 * math.sin(3 * a + 1.3) + 0.04 * math.sin(7 * a) + rng.uniform(-0.02, 0.02)
        ring.append(bm.verts.new((2.75 * r * math.cos(a), 2.35 * r * math.sin(a), 0.0)))
    c = bm.verts.new((0.0, 0.0, 0.0))
    for k in range(n):
        bm.faces.new((c, ring[k], ring[(k + 1) % n]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("snowfield", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(M["snow"])
    mod = o.modifiers.new("thick", "SOLIDIFY")
    mod.thickness = 0.05
    mod.offset = -1
    p.append(o)
    # trodden path out of the door, a few boot-scuffed patches
    for k, (dx, dy, sx, sy) in enumerate(((0.0, 0.55, 0.30, 0.62), (0.06, 1.35, 0.26, 0.55))):
        blob(f"path{k}", (dx, Y0 - dy, 0.001), (sx, sy, 0.003), M["trodden"], p,
             rot=(0, 0, 0.08 * (k - 0.5)), seg=24)  # one worn strip out of the door


def build(M) -> list:
    p: list = []
    S, E = -math.pi / 2, 0.0
    H = G.H
    # --- shell: N and W runs, S run with the door in the middle, E run ------
    for i in range(NX):
        G.wall(f"n{i}", (X0 + i, Y1), E, -1, M, p)
        if i == NX // 2:
            G.door("ds", (X0 + i, Y0), E, +1, M, p, open_=True)
        else:
            G.wall(f"s{i}", (X0 + i, Y0), E, +1, M, p)
    for j in range(NY):
        G.wall(f"w{j}", (X0, Y1 - j), S, +1, M, p)
        G.wall(f"e{j}", (X1, Y1 - j), S, -1, M, p)
    P = 0.05
    G.box("post_se", (X1 - P / 2, Y0 + P / 2, H / 2), (P, P, H), M["frame"], p)
    # --- roof: one real roof panel per tile, on the wall tops ---------------
    for i in range(NX):
        for j in range(NY):
            for o in G.build_roof(M):
                o.location = (o.location.x + X0 + 0.5 + i, o.location.y + Y0 + 0.5 + j, o.location.z + H)
                p.append(o)
    # --- ground: snow outside, packed dirt inside ---------------------------
    snow_field(M, p)
    G.box("dirt", (0.0, 0.0, 0.002), (X1 - X0 - 0.08, Y1 - Y0 - 0.08, 0.006), M["dirt"], p)
    for k in range(18):  # drifts banked against the outside of the kick boards
        side = k % 4
        t = rng.uniform(0.05, 0.95)
        if side == 0:
            c = (X0 + t * (X1 - X0), Y0 - 0.10, 0.0)
        elif side == 1:
            c = (X1 + 0.10, Y0 + t * (Y1 - Y0), 0.0)
        elif side == 2:
            c = (X0 + t * (X1 - X0), Y1 + 0.10, 0.0)
        else:
            c = (X0 - 0.10, Y0 + t * (Y1 - Y0), 0.0)
        if side == 0 and abs(c[0] - (X0 + 1.5)) < 0.5:
            continue  # keep the doorway clear
        blob(f"drift{k}", c, (rng.uniform(0.35, 0.55), rng.uniform(0.14, 0.22), rng.uniform(0.04, 0.08)),
             M["snow"], p, rot=(0, 0, 0 if side % 2 == 0 else math.pi / 2), seg=12)
    # --- inside: two raised beds either side of the path, tomatoes in fruit --
    for b, (bx0, bx1) in enumerate(((X0 + 0.14, X0 + 0.95), (X1 - 0.95, X1 - 0.14))):
        cx, w = (bx0 + bx1) / 2, bx1 - bx0
        G.box(f"bed{b}", (cx, 0.0, 0.14), (w, 1.7, 0.28), M["bed"], p)
        G.box(f"bedsoil{b}", (cx, 0.0, 0.281), (w - 0.06, 1.64, 0.01), M["soil"], p)
        for k in range(4):
            for c2 in (-1, 1):
                tomato(f"tm{b}{k}{c2}", cx + c2 * w * 0.22 + rng.uniform(-0.03, 0.03),
                       -0.62 + k * 0.41 + rng.uniform(-0.04, 0.04), 0.285, M, p)
    # --- outside: the row that didn't make it -------------------------------
    for k in range(5):
        dead_plant(f"dead{k}", X1 + 0.65 + rng.uniform(-0.05, 0.05), -0.85 + k * 0.42, M, p)
        blob(f"deadsnow{k}", (X1 + 0.65, -0.85 + k * 0.42, 0.0), (0.16, 0.12, 0.04), M["snow"], p, seg=10)
    return p


def main() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    G.maps()
    F.register()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    pr = sc.pz_forge
    pr.sheet_name = "greenhouse_hero"
    pr.footprint_x = pr.footprint_y = 1
    pr.facings = "1"
    pr.show_guide = False
    pr.contrast_boost = 1.0
    pr.toon_shading = True
    pr.ground_occlusion = False
    F.build_rig(bpy.context)
    subject = bpy.data.objects[F.SUBJECT_NAME]
    for o in build(mats()):
        if o.parent is None:
            o.parent = subject
    F.apply_render_settings(bpy.context)
    sc.render.resolution_x, sc.render.resolution_y = 2400, 1800
    sc.render.resolution_percentage = 100
    sc.render.filter_size = 1.2
    cam = bpy.data.objects[F.CAMERA_NAME]
    cam.data.ortho_scale = 7.6
    cam.data.shift_x = cam.data.shift_y = 0.0
    cam.location = Vector((0.0, 0.0, 1.0)) + F.camera_direction() * 100.0
    sc.camera = cam
    if hasattr(sc, "eevee"):
        sc.eevee.taa_render_samples = 128
    sc.render.filepath = str(OUT)
    bpy.ops.render.render(write_still=True)
    print(f"hero render -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
