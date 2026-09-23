"""32x32 icons for the drying-rack food line: 5 families x 4 states.

    Strips          fresh colour (progress 0 of the rack style)
    StripsSalted    fresh colour + a salt crust (white specks)
    Dried           dried colour (progress 100)
    Jerky           dried colour + a twine tie round the bundle

    blender -b -P examples/knx_jerky_icons.py     (renders build/jerky_icons/*.png)
    python  examples/knx_jerky_icons.py --pack     (32x32 into the mod + check sheet)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "build" / "jerky_icons"
MOD_TEX = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases\42\media\textures")
FAMS = ["Beef", "Pork", "Poultry", "Game", "Fish"]
STATES = ["Strips", "StripsSalted", "Dried", "Jerky"]
FRESH = {"Beef": (0.55, 0.10, 0.09), "Pork": (0.78, 0.40, 0.38), "Poultry": (0.88, 0.66, 0.60),
         "Game": (0.40, 0.07, 0.08), "Fish": (0.78, 0.70, 0.62)}
DRY = {"Beef": (0.30, 0.15, 0.09), "Pork": (0.50, 0.26, 0.15), "Poultry": (0.70, 0.50, 0.30),
       "Game": (0.24, 0.09, 0.07), "Fish": (0.62, 0.44, 0.22)}


def render() -> None:
    import bpy
    from mathutils import Vector

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = sc.render.resolution_y = 256
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

    def mat(name, rgb, rough=0.55):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        b.inputs["Roughness"].default_value = rough
        return m

    def clear():
        for o in list(bpy.data.objects):
            if o.type == "MESH":
                bpy.data.objects.remove(o, do_unlink=True)

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(30))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    sc.camera = cam

    def box(loc, size, rot, m):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        o = bpy.context.active_object
        o.scale = size
        o.rotation_euler = rot
        o.data.materials.append(m)
        return o

    fat = mat("fat", (0.86, 0.80, 0.68))
    salt = mat("salt", (0.95, 0.95, 0.93), 0.9)
    twine = mat("twine", (0.62, 0.55, 0.38), 0.9)
    for fam in FAMS:
        for st in STATES:
            clear()
            dry = st in ("Dried", "Jerky")
            m = mat(f"{fam}_{st}", DRY[fam] if dry else FRESH[fam])
            k = 0.85 if dry else 1.0
            objs = []
            for i in range(3):
                off = (i - 1) * 0.11
                rot = (0, 0, math.radians(-35 + 10 * i))
                if fam == "Game":
                    for j in range(4):
                        objs.append(box((off + 0.02 * j, -0.13 + 0.09 * j, 0.03), (0.07 * k,) * 3,
                                        (0.3 * j, 0.2 * i, 0.5 * j), m))
                elif fam == "Fish":
                    objs.append(box((off, 0, 0.012 * i), (0.14 * k, 0.40 * k, 0.02), rot, m))
                elif fam == "Poultry":
                    objs.append(box((off, 0, 0.015 * i), (0.08 * k, 0.30 * k, 0.03), rot, m))
                else:
                    w = 0.11 if fam == "Pork" else 0.07
                    objs.append(box((off, 0, 0.012 * i), (w * k, 0.48 * k, 0.018), rot, m))
                    if fam == "Pork":
                        objs.append(box((off + 0.045 * math.cos(rot[2]), 0.045 * math.sin(rot[2]), 0.012 * i + 0.002),
                                        (0.025, 0.47 * k, 0.02), rot, fat))
            if st == "StripsSalted":
                for j in range(22):
                    h1 = ((j * 2654435761 + 97) % 1009) / 1009.0
                    h2 = ((j * 40503 + 13) % 997) / 997.0
                    a, b = (h1 - 0.5) * 0.36, (h2 - 0.5) * 0.42
                    objs.append(box((a, b, 0.06), (0.018, 0.018, 0.01), (0, 0, j), salt))
            if st == "Jerky":
                objs.append(box((0, 0, 0.05), (0.42, 0.035, 0.03), (0, 0, math.radians(-20)), twine))
            pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
            c = sum(pts, Vector()) / len(pts)
            d = Vector((0.35, -0.55, 0.75)).normalized()
            cam.location = c + d * 5
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            cam.data.ortho_scale = 0.72
            sc.render.filepath = str(RAW / f"KNX_{fam}{st}.png")
            bpy.ops.render.render(write_still=True)


def pack() -> None:
    from PIL import Image

    def to_icon(img, size=32, fit=30):
        img = img.crop(img.getbbox())
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

    sheet = Image.new("RGBA", (128 * 4, 128 * 5), (58, 54, 48, 255))
    for r, fam in enumerate(FAMS):
        for c, st in enumerate(STATES):
            name = f"KNX_{fam}{st}"
            icon = to_icon(Image.open(RAW / f"{name}.png").convert("RGBA"))
            icon.save(MOD_TEX / f"Item_{name}.png")
            sheet.alpha_composite(icon.resize((128, 128), Image.NEAREST), (c * 128, r * 128))
    sheet.save(ROOT / "build" / "jerky_icons_check.png")
    print("20 icons ->", MOD_TEX)


if __name__ == "__main__":
    if "--pack" in sys.argv:
        pack()
    else:
        RAW.mkdir(parents=True, exist_ok=True)
        render()
