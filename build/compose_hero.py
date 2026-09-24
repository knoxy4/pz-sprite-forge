"""Workshop covers from the real 4x renders: one layout entry per mod."""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = pathlib.Path("build/heroes_final"); OUT.mkdir(exist_ok=True)
W, H = 1280, 720
CREAM, MUTED, RULE = (234,224,200), (188,176,150), (150,132,96)
SERIF, SERIF_L = r"C:\Windows\Fonts\constanb.ttf", r"C:\Windows\Fonts\constan.ttf"

# mod -> renders dir, over-line, name, tagline, [(render, cx, ground y, height)] back-to-front
COVERS = {
 "BadlandsPower": ("build/heroes_power", "BADLANDS", "POWER",
     "Four generators and a battery bank. Keep the lights on.",
     [("propane_E", 425, 530, 265), ("wasteoil_E", 860, 530, 265),
      ("bank_S", 205, 695, 330), ("scrap_S", 640, 705, 295), ("diesel_S", 1075, 695, 345)]),
 "FullBookcases": ("build/heroes_furniture", "BADLANDS", "FURNITURE",
     "Shelving that shows what's left on it. Seating, water, media, medical.",
     [("utility_S", 250, 555, 265), ("medtable_S", 560, 560, 240), ("vcr_S", 820, 555, 250), ("rainrack_S", 1075, 545, 270),
      ("bookcase_S", 135, 695, 325), ("gunrack_S", 390, 705, 320), ("patchwork_S", 680, 705, 265), ("recliner_S", 1140, 710, 255)]),
 "FullBookcases_all": ("build/heroes_furniture", "BADLANDS", "FURNITURE",
     "Shelving that shows what's left on it. Seating, water, media, medical.",
     [("pantry_S", 90, 420, 200, .85), ("wine_S", 265, 420, 200, .85), ("utility_S", 445, 420, 200, .85), ("linenshelf_S", 640, 420, 195, .85),
      ("closetrod_S", 835, 420, 195, .85), ("bootcubby_S", 1015, 420, 195, .85), ("wardrobe_S", 1195, 420, 195, .85),
      ("tire_S", 230, 505, 170, .6), ("wash_S", 470, 500, 200, .6), ("taperack_S", 700, 495, 120, .6), ("raindrum_S", 900, 500, 195, .6), ("bbq_S", 1110, 505, 185, .6),
      ("medtable_S", 545, 595, 215, .3), ("vcr_S", 830, 585, 225, .3), ("rainrack_S", 1040, 590, 240, .3),
      ("bookcase_S", 130, 710, 320, 0), ("gunrack_S", 390, 712, 310, 0), ("patchwork_S", 690, 712, 265, 0), ("recliner_S", 1130, 715, 255, 0)]),
 "ikag_mycology": ("build/heroes_furniture", "BADLANDS", "MYCOLOGY",
     "Grow your own, spore print to harvest.",
     [("my_rack_S", 1010, 690, 420, .25),
      ("my_loaded_S", 190, 640, 230, 0), ("my_colonized_S", 480, 665, 250, 0), ("my_fruiting_S", 760, 700, 300, 0)]),
 "BadlandsGreenhouse": ("build/heroes_furniture", "BADLANDS", "GREENHOUSE",
     "Glass walls, a glass roof, and tomatoes in January.",
     [("greenhouse_hero", 640, 712, 468)]),
 "pzj_alphashipment": ("build/heroes_furniture", "ALPHA", "SHIPMENT",
     "A distributor drop nobody unpacked.",
     [("sh_pallet_S", 470, 700, 400), ("sh_crate_E", 960, 705, 250)]),
 "pzj_ikag_ration": ("build/heroes_furniture", "BADLANDS", "RATION PACK",
     "Civil-relief rations by the pallet. Tear one open and see what you got.",
     [("ra_pallet_S", 500, 700, 440), ("ra_sack_E", 1010, 690, 310), ("ra_pouch_S", 215, 708, 140)]),
}

def load(R, name, h, depth=0.0):
    im = Image.open(R/f"{name}.png").convert("RGBA"); im = im.crop(im.getbbox())
    s = h / im.height
    im = im.resize((int(im.width*s), int(im.height*s)), Image.LANCZOS)
    if depth > 0:
        # atmospheric fade: pull colour toward the backdrop, soften, thin the alpha
        fog = Image.new("RGBA", im.size, (28, 27, 20, 255))
        rgb = Image.blend(im, fog, depth*0.55)
        a = im.getchannel("A").point(lambda v: int(v*(1-0.12*depth)))
        rgb.putalpha(a)
        im = rgb.filter(ImageFilter.GaussianBlur(depth*1.4))
    return im

def spaced_w(d, text, font, track): return sum(d.textlength(c, font=font) for c in text) + track*(len(text)-1)
def spaced(dr, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        dr.text((x, y), ch, font=font, fill=fill); x += dr.textlength(ch, font=font) + track

def compose(mod):
    rdir, over, name, tag, items = COVERS[mod]
    R = pathlib.Path(rdir)
    bg = Image.new("RGB", (W, H)); d = ImageDraw.Draw(bg)
    top, floor = (15, 16, 13), (44, 42, 31)
    for y in range(H):
        t = y / H
        d.line([(0,y),(W,y)], fill=tuple(int(a+(b-a)*t**1.4) for a,b in zip(top,floor)))
    glow = Image.new("RGB", (W, H), (0,0,0))
    ImageDraw.Draw(glow).ellipse((W//2-420, 300, W//2+420, 900), fill=(70, 52, 22))
    bg = ImageChops.add(bg, glow.filter(ImageFilter.GaussianBlur(160)))
    canvas = bg.convert("RGBA")
    for it in items:
        rname, cx, gy, h = it[:4]; depth = it[4] if len(it) > 4 else 0.0
        im = load(R, rname, h, depth)
        sh = Image.new("RGBA", (W, H), (0,0,0,0))
        ImageDraw.Draw(sh).ellipse((cx-im.width//2-10, gy-im.height*0.16, cx+im.width//2+10, gy+im.height*0.06), fill=(0,0,0,int(170*(1-0.7*depth))))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
        canvas.alpha_composite(im, (cx-im.width//2, gy-im.height))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-300, -260, W+300, H+260), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(170))
    canvas = Image.composite(canvas.convert("RGB"), Image.new("RGB", (W, H), (8,8,9)), vig).convert("RGBA")

    d = ImageDraw.Draw(canvas)
    f_over, f_main, f_tag = ImageFont.truetype(SERIF_L, 30), ImageFont.truetype(SERIF, 96), ImageFont.truetype(SERIF_L, 26)
    ow, mw = spaced_w(d, over, f_over, 11), spaced_w(d, name, f_main, 10)
    ox, oy = (W-ow)//2, 46
    mx, my = (W-mw)//2, oy+40
    sh = Image.new("RGBA", (W, H), (0,0,0,0)); sd = ImageDraw.Draw(sh)
    spaced(sd, (ox+3, oy+4), over, f_over, (0,0,0,220), 11)
    spaced(sd, (mx+4, my+6), name, f_main, (0,0,0,235), 10)
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(canvas)
    spaced(d, (ox, oy), over, f_over, MUTED+(255,), 11)
    spaced(d, (mx, my), name, f_main, CREAM+(255,), 10)
    ry = oy+17
    for x0, x1 in ((ox-96, ox-22), (ox+ow+22, ox+ow+96)):
        d.line([(x0,ry),(x1,ry)], fill=RULE+(210,), width=2)
    tw = d.textlength(tag, font=f_tag); tx, ty = (W-tw)//2, my+118
    sh2 = Image.new("RGBA", (W, H), (0,0,0,0)); ImageDraw.Draw(sh2).text((tx+2,ty+3), tag, font=f_tag, fill=(0,0,0,210))
    canvas.alpha_composite(sh2.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(canvas).text((tx,ty), tag, font=f_tag, fill=MUTED+(255,))
    dst = OUT/f"{mod}_v2.jpg"
    canvas.convert("RGB").save(dst, "JPEG", quality=90, optimize=True)
    print(dst, dst.stat().st_size//1024, "KB")

if __name__ == "__main__":
    for mod in (sys.argv[1:] or COVERS):
        compose(mod)








