"""Inventory icons for the BADLANDS beehive items, rendered then cut to 32x32.

    Item_KNX_HiveFrame        empty Langstroth frame, pale wax foundation
    Item_KNX_HiveFrameHoney   the same frame, capped comb, honey amber
    Item_KNX_JarOfHoney       glass jar, amber fill, tin lid
    Item_KNX_BeeColony        cut from the swarm-trap S sprite (the nuc box)

Vanilla item icons are 32x32 RGBA, three-quarter view, hard alpha edge.

    blender -b -P examples/knx_bee_icons.py      (renders build/bee_icons/*.png)
    python  examples/knx_bee_icons.py --pack      (downsamples into the mod)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "build" / "bee_icons"
MOD_TEX = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases\42\media\textures")
TRAP_CELL = ROOT / "build" / "hive_cells" / "badlands_hive_01_trap_S_x0_y0.png"


def render() -> None:
    import bpy
    from mathutils import Vector

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = sc.render.resolution_y = 256
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

    def mat(name, rgb, rough=0.6, alpha=1.0, metal=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        b.inputs["Alpha"].default_value = alpha
        if alpha < 1.0:
            m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
        return m

    wood = mat("wood", (0.55, 0.40, 0.22))
    wax = mat("wax", (0.85, 0.78, 0.50), 0.8)
    comb = mat("comb", (0.85, 0.52, 0.06), 0.35)
    glass = mat("glass", (0.80, 0.85, 0.85), 0.1, 0.35)
    honey = mat("honey", (0.90, 0.55, 0.05), 0.2)
    tin = mat("tin", (0.55, 0.55, 0.52), 0.35, 1.0, 0.8)

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    sc.camera = cam

    def box(loc, size, m):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        o = bpy.context.active_object
        o.scale = size
        o.data.materials.append(m)
        return o

    def cyl(loc, r, d, m, v=32):
        bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=loc)
        o = bpy.context.active_object
        o.data.materials.append(m)
        return o

    def shoot(name, objs, scale):
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        c = sum(pts, Vector()) / len(pts)
        d = Vector((0.55, -0.85, 0.55)).normalized()
        cam.location = c + d * 5
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = scale
        sc.render.filepath = str(RAW / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)

    def frame(fill):
        parts = [box((0, 0, 0.21), (0.48, 0.03, 0.03), wood),     # top bar with lugs
                 box((0, 0, -0.21), (0.40, 0.03, 0.02), wood),
                 box((-0.19, 0, 0), (0.02, 0.03, 0.42), wood),
                 box((0.19, 0, 0), (0.02, 0.03, 0.42), wood),
                 box((0, 0, 0), (0.36, 0.022, 0.40), fill)]
        return parts

    shoot("KNX_HiveFrame", frame(wax), 0.62)
    shoot("KNX_HiveFrameHoney", frame(comb), 0.62)
    # No glass shell: at 32 px it only greys the honey out.  Amber body, a paper
    # label band, tin lid.
    label = mat("label", (0.86, 0.82, 0.70), 0.9)
    jar = [cyl((0, 0, 0), 0.16, 0.36, honey), cyl((0, 0, -0.02), 0.162, 0.12, label),
           cyl((0, 0, 0.20), 0.15, 0.05, tin)]
    shoot("KNX_JarOfHoney", jar, 0.52)


def pack() -> None:
    from PIL import Image

    def to_icon(img, size=32, fit=30):
        box = img.getbbox()
        img = img.crop(box)
        s = min(fit / img.width, fit / img.height)
        img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.alpha_composite(img, ((size - img.width) // 2, (size - img.height) // 2))
        px = out.load()
        for y in range(size):
            for x in range(size):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 0 if a < 40 else 255)
        return out

    MOD_TEX.mkdir(parents=True, exist_ok=True)
    for name in ("KNX_HiveFrame", "KNX_HiveFrameHoney", "KNX_JarOfHoney"):
        to_icon(Image.open(RAW / f"{name}.png").convert("RGBA")).save(MOD_TEX / f"Item_{name}.png")
    to_icon(Image.open(TRAP_CELL).convert("RGBA")).save(MOD_TEX / "Item_KNX_BeeColony.png")
    sheet = Image.new("RGBA", (32 * 4 * 4, 32 * 4), (58, 54, 48, 255))
    for i, n in enumerate(("KNX_HiveFrame", "KNX_HiveFrameHoney", "KNX_JarOfHoney", "KNX_BeeColony")):
        sheet.alpha_composite(Image.open(MOD_TEX / f"Item_{n}.png").resize((128, 128), Image.NEAREST), (i * 128, 0))
    sheet.save(ROOT / "build" / "bee_icons_check.png")
    print("icons written to", MOD_TEX)


if __name__ == "__main__":
    if "--pack" in sys.argv:
        pack()
    else:
        RAW.mkdir(parents=True, exist_ok=True)
        render()
