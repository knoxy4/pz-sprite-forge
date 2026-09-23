"""Traits and Professions cover (v3, renamed): 19 profession icons at 2x, 76 trait icons at 2x, character-screen style."""
import sys, pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, "build")
import compose_hero as C
W, H = C.W, C.H
M = pathlib.Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\BadlandsCharacters")
ch = [p for p in M.rglob("*.png") if "_src" not in p.parts and "_gen" not in p.parts and p.name != "poster.png"]
prof = sorted(p for p in ch if p.name.startswith("profession_"))
trait = sorted(p for p in ch if p.name.startswith("trait_"))
canvas = Image.new("RGB", (W, H)); d = ImageDraw.Draw(canvas)
for y in range(H):
    t = y / H; d.line([(0,y),(W,y)], fill=tuple(int(a+(b-a)*t**1.4) for a,b in zip((14,15,13),(34,30,24))))
canvas = canvas.convert("RGBA")
def slot(x, y, w, h, im):
    ImageDraw.Draw(canvas).rounded_rectangle((x, y, x+w, y+h), radius=6, fill=(28, 26, 22, 255), outline=(62, 56, 44, 255), width=2)
    canvas.alpha_composite(im, (x + (w-im.width)//2, y + (h-im.height)//2))
# professions: two rows of 10 / 9, 2x nearest, tinted the house cream (they ship greyscale)
cell, K = 120, 2
rows = [prof[:10], prof[10:]]
for r, row in enumerate(rows):
    ox = (W - len(row)*cell)//2; y = 236 + r*130
    for i, p in enumerate(row):
        im = Image.open(p).convert("RGBA"); im = im.crop(im.getbbox())
        f = min(104 / im.width, 104 / im.height); im = im.resize((max(1,int(im.width*f)), max(1,int(im.height*f))), Image.LANCZOS)
        # tint: multiply the greyscale by cream
        tint = Image.new("RGBA", im.size, (234, 224, 200, 255)); tint.putalpha(im.getchannel("A"))
        from PIL import ImageChops
        im = ImageChops.multiply(im, tint)
        slot(ox + i*cell + 4, y, cell - 8, 122, im)
# traits: 76 at 2x, four rows of 19
tc, K2 = 62, 2
for r in range(4):
    row = trait[r*19:(r+1)*19]; ox = (W - len(row)*tc)//2; y = 512 + r*44
    for i, p in enumerate(row):
        im = Image.open(p).convert("RGBA"); im = im.resize((im.width*K2, im.height*K2), Image.NEAREST)
        slot(ox + i*tc + 3, y, tc - 6, 40, im)
vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse((-300, -260, W+300, H+260), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(170))
canvas = Image.composite(canvas.convert("RGB"), Image.new("RGB", (W, H), (8,8,9)), vig).convert("RGBA")
d = ImageDraw.Draw(canvas)
f_over, f_main, f_tag = ImageFont.truetype(C.SERIF_L, 30), ImageFont.truetype(C.SERIF, 66), ImageFont.truetype(C.SERIF_L, 26)
over, name, tag = "BADLANDS", "TRAITS & PROFESSIONS", f"{len(prof)} professions and {len(trait)} traits for Knox County."
ow, mw = C.spaced_w(d, over, f_over, 11), C.spaced_w(d, name, f_main, 7)
ox_, oy_ = (W-ow)//2, 46; mx, my = (W-mw)//2, oy_+40
sh = Image.new("RGBA", (W, H), (0,0,0,0)); sd = ImageDraw.Draw(sh)
C.spaced(sd, (ox_+3, oy_+4), over, f_over, (0,0,0,220), 11); C.spaced(sd, (mx+4, my+6), name, f_main, (0,0,0,235), 7)
canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
d = ImageDraw.Draw(canvas)
C.spaced(d, (ox_, oy_), over, f_over, C.MUTED+(255,), 11); C.spaced(d, (mx, my), name, f_main, C.CREAM+(255,), 7)
ry = oy_+17
for x0, x1 in ((ox_-96, ox_-22), (ox_+ow+22, ox_+ow+96)): d.line([(x0,ry),(x1,ry)], fill=C.RULE+(210,), width=2)
tw = d.textlength(tag, font=f_tag); tx, ty = (W-tw)//2, my+92
sh2 = Image.new("RGBA", (W, H), (0,0,0,0)); ImageDraw.Draw(sh2).text((tx+2,ty+3), tag, font=f_tag, fill=(0,0,0,210))
canvas.alpha_composite(sh2.filter(ImageFilter.GaussianBlur(5)))
ImageDraw.Draw(canvas).text((tx,ty), tag, font=f_tag, fill=C.MUTED+(255,))
dst = C.OUT / "BadlandsCharacters_v3.jpg"
canvas.convert("RGB").save(dst, "JPEG", quality=90, optimize=True); print(dst, dst.stat().st_size//1024, "KB", len(prof), len(trait))

