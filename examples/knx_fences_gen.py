"""BADLANDS fences on vanilla fencing art that vanilla never made buildable.

Writes FullBookcases scripts/entities/knx_fences.txt + _xuiSkin, 96px build
icons (cut from Tiles2x.pack), and merges tooltips into Tooltip.json.
Sprites are referenced by name; no vanilla pixels ship except the icons.
"""
import io, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pzforge.packfile import TexturePack
from PIL import Image

PZ = Path(r"X:\SteamLibrary\steamapps\common\ProjectZomboid\media")
MOD = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases")
F, G = "fencing_01_", "fixtures_doors_fences_01_"

HAMMER = "item 1 tags[base:hammer] mode:keep flags[Prop1;MayDegradeVeryLight]"
TORCH = "item {n} [Base.BlowTorch] flags[DontRecordInput]"
RODS = "item {n} [Base.WeldingRods] flags[DontRecordInput]"
TROWEL = "item 1 tags[base:masonstrowel] mode:keep flags[Prop1;MayDegradeLight]"
CONCRETE = "item {n} tags[base:concrete] flags[DontRecordInput]"

def wood(skill, planks, nails, extra=()):
    return dict(action="BuildWoodenStructureSmall", cat="Carpentry", skill=f"Woodwork:{skill}",
                inputs=[HAMMER, f"item {planks} [Base.Plank]", f"item {nails} [Base.Nails]", *extra])

def weld(skill, n, extra, action="BuildMetalStructureScrap"):
    return dict(action=action, cat="Welding", skill=f"MetalWelding:{skill}",
                inputs=[TORCH.format(n=n), *extra, RODS.format(n=n)])

GATE_HW = ["item 2 [Base.Hinge]", "item 1 [Base.Doorknob]"]
C = "badlands_corrugated_01_"   # our own sheet (tileset 11), examples/knx_corrugated.py
DRIVER = "item 1 tags[base:screwdriver] mode:keep flags[NoBrokenItems]"
CORR = lambda sheets, planks, screws, extra=(): dict(
    action="BuildWoodenStructureSmall", cat="Carpentry", skill="Woodwork:3",
    inputs=[DRIVER, f"item {sheets} [Base.SheetMetal]", f"item {planks} [Base.Plank]",
            f"item {screws} [Base.Screws]", *extra])

# name, display, W, N, post, icon sprite, health, build, tooltip
FENCES = [
    ("Picket", "Picket Fence", F+"4", F+"5", F+"7", F+"6", 200, wood(2, 2, 3),
     "White pickets, waist high. Keeps dogs in and nobody out, but it looks like home."),
    ("Board", "Board Fence", F+"34", F+"32", F+"37", F+"36", 250, wood(3, 2, 4),
     "Waist-high boards, gapped. Hides nothing, slows a crawl."),
    ("Privacy", "Privacy Fence", F+"10", F+"8", F+"13", F+"12", 350, wood(4, 4, 6),
     "Tall solid boards. Nobody sees in, and climbing it is work."),
    ("IronLow", "Wrought Iron Railing", F+"2", F+"1", F+"0", F+"3", 400,
     weld(3, 3, ["item 3 [Base.MetalBar]"]),
     "Low iron railing with finials. Hop it if you must."),
    ("IronTall", "Wrought Iron Fence", F+"66", F+"64", F+"69", F+"68", 600,
     weld(5, 5, ["item 6 [Base.MetalBar]"], "BuildWallMetal"),
     "Tall iron bars with spear tips. See through it, reach through it with a spear, climb it slowly."),
    ("Razor", "Razor-Top Mesh Fence", F+"90", F+"88", None, F+"92", 450,
     weld(4, 4, ["item 2 [Base.MetalPipe]", "item 3 [Base.Wire]", "item 2 [Base.BarbedWire]"], "BuildWireFence"),
     "Welded mesh panels topped with razor wire. Nobody climbs it."),
    ("Security", "Security Fence", F+"50", F+"48", F+"53", F+"52", 700,
     dict(action="BuildWallMetal", cat="Welding", skill="MetalWelding:5",
          inputs=[TORCH.format(n=5), TROWEL, "item 4 [Base.MetalPipe]", "item 4 [Base.MetalBar]",
                  CONCRETE.format(n=1), RODS.format(n=5)]),
     "Steel bars on a poured concrete footing. Can't be climbed; spears reach through."),
    ("Concrete", "Concrete Panel Wall", F+"40", F+"41", F+"43", F+"42", 900,
     dict(action="BuildWallHammer", cat="Masonry", skill="Masonry:4",
          inputs=[TROWEL, CONCRETE.format(n=2), "item 2 [Base.MetalBar]"]),
     "Precast concrete panels. Blocks sight and fire; climbing it is hard work."),
    ("Corrugated", "Corrugated Sheet Fence", C+"0", C+"1", C+"3", C+"2", 350, CORR(2, 2, 8),
     "Scrap roofing sheets screwed to 2x4 rails. Ugly, solid, and nobody sees in."),
]

GATES = [
    ("Picket", "Picket Gate", [G+"8", G+"9", G+"10", G+"11"], 250, wood(2, 3, 4, GATE_HW),
     "A white picket gate. Takes a doorknob, so it locks with a key."),
    ("Privacy", "Privacy Gate", [G+"12", G+"13", G+"14", G+"15"], 400, wood(4, 5, 6, GATE_HW),
     "A tall board gate with a peep window. Takes a doorknob, so it locks with a key."),
    ("IronLow", "Wrought Iron Gate", [G+"0", G+"1", G+"2", G+"3"], 400,
     weld(3, 3, ["item 2 [Base.MetalBar]", *GATE_HW]),
     "A low arched iron gate. Takes a doorknob, so it locks with a key."),
    ("IronTall", "Tall Wrought Iron Gate", [G+"20", G+"21", G+"22", G+"23"], 500,
     weld(5, 4, ["item 4 [Base.MetalBar]", *GATE_HW], "BuildWallMetal"),
     "A tall iron gate to match the fence. Takes a doorknob, so it locks with a key."),
    ("Corrugated", "Corrugated Gate", [C+"4", C+"5", C+"6", C+"7"], 350, CORR(2, 3, 10, GATE_HW),
     "A braced scrap-sheet gate. Takes a doorknob, so it locks with a key."),
]

def layer(face, sprite):
    return (f"            face {face}\n            {{\n                layer\n                {{\n"
            f"                    row = {sprite},\n                }}\n            }}\n")

def recipe(b, tip, time=200):
    ins = "".join(f"                {i},\n" for i in b["inputs"])
    lvl = int(b["skill"].split(":")[1])
    return (f"        component CraftRecipe\n        {{\n            timedAction = {b['action']},\n"
            f"            time = {time},\n            category = {b['cat']},\n            Tags = {b['cat']},\n"
            f"            SkillRequired = {b['skill']},\n            xpAward = {b['skill'].split(':')[0]}:{10 * lvl},\n"
            f"            Tooltip = {tip},\n            inputs\n            {{\n{ins}            }}\n        }}\n")

def ui(style):
    return (f"        component UiConfig\n        {{\n            xuiSkin = default,\n"
            f"            entityStyle = {style},\n            uiEnabled = false,\n        }}\n")

ents, skins, tips, icons = [], [], {}, {}
for key, disp, w, n, post, icon, hp, b, tip in FENCES:
    name = f"KNX_Fence{key}"; tk = f"Tooltip_craft_{name}Desc"
    sc = f"        component SpriteConfig\n        {{\n            health = {hp},\n            skillBaseHealth = 30,\n"
    sc += layer("W", w) + layer("N", n)
    if post: sc += f"            corner = {post},\n"
    sc += "        }\n"
    ents.append(f"    entity {name}\n    {{\n{ui('ES_'+name)}{sc}{recipe(b, tk)}    }}\n")
    skins.append((name, disp)); tips[tk] = tip; icons[f"Build_{name}"] = icon
for key, disp, (w, n, wo, no), hp, b, tip in GATES:
    name = f"KNX_Gate{key}"; tk = f"Tooltip_craft_{name}Desc"
    sc = (f"        component SpriteConfig\n        {{\n            skillBaseHealth = {hp},\n"
          f"            dontNeedFrame = true,\n            BreakSound = BreakDoor,\n")
    sc += layer("W", w) + layer("N", n) + layer("W_OPEN", wo) + layer("N_OPEN", no) + "        }\n"
    ents.append(f"    entity {name}\n    {{\n{ui('ES_'+name)}{sc}{recipe(b, tk)}    }}\n")
    skins.append((name, disp)); tips[tk] = tip; icons[f"Build_{name}"] = w

head = ("module Base\n{\n    /* BADLANDS fences: vanilla fencing art that vanilla never made buildable\n"
        "       (fencing_01 / fixtures_doors_fences_01), referenced by name. Tile props come\n"
        "       from the vanilla tiles. GENERATED by pz-sprite-forge examples/knx_fences_gen.py. */\n")
ent_dir = MOD / "42/media/scripts/entities"
(ent_dir / "knx_fences.txt").write_text(head + "\n".join(ents) + "}\n", encoding="utf-8", newline="\n")
sk = "".join(f"        entity ES_{n}\n        {{\n            LuaWindowClass = ISEntityWindow,\n"
             f"            DisplayName = {d},\n            Icon = Build_{n},\n        }}\n" for n, d in skins)
(ent_dir / "knx_fences_xuiSkin.txt").write_text(
    f"module Base\n{{\n    xuiSkin default\n    {{\n{sk}    }}\n}}\n", encoding="utf-8", newline="\n")

tp = MOD / "42/media/lua/shared/Translate/EN/Tooltip.json"
data = json.loads(tp.read_text(encoding="utf-8")); data.update(tips)
tp.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

want = set(icons.values())
pk = TexturePack.read(PZ / "texturepacks/Tiles2x.pack")
cut = {}
for pg in pk.pages:
    hits = [e for e in pg.entries if e.name in want]
    if not hits: continue
    im = Image.open(io.BytesIO(pg.png)).convert("RGBA")
    for e in hits:
        cut[e.name] = im.crop((e.x, e.y, e.x + e.w, e.y + e.h))
own = Image.open(MOD / "42/media/badlands_corrugated_01.png").convert("RGBA")
for k in range(8):
    cut[C + str(k)] = own.crop((k * 128, 0, k * 128 + 128, 256))
tex = MOD / "common/media/textures"
for out, spr in icons.items():
    im = cut[spr]; im = im.crop(im.getbbox())
    s = 88 / max(im.size)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    c = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    c.alpha_composite(im, ((96 - im.width) // 2, (96 - im.height) // 2))
    c.save(tex / f"{out}.png")
print(len(ents), "entities,", len(icons), "icons,", len(tips), "tooltips")
