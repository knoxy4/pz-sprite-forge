"""BadlandsGreenhouse poster.png (512x512, the in-game mod list card): the
Workshop hero render on the cover's backdrop, no type (the mod list prints the
name beside it). Writes the mod root and 42/ copies."""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\KNX\dev\pz-sprite-forge")
MOD = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\BadlandsGreenhouse")
S = 512
bg = Image.new("RGB", (S, S))
d = ImageDraw.Draw(bg)
top, floor = (15, 16, 13), (44, 42, 31)
for y in range(S):
    t = y / S
    d.line([(0, y), (S, y)], fill=tuple(int(a + (b - a) * t ** 1.4) for a, b in zip(top, floor)))
glow = Image.new("RGB", (S, S), (0, 0, 0))
ImageDraw.Draw(glow).ellipse((S // 2 - 220, 170, S // 2 + 220, 620), fill=(70, 52, 22))
bg = ImageChops.add(bg, glow.filter(ImageFilter.GaussianBlur(90))).convert("RGBA")
im = Image.open(ROOT / "build/heroes_furniture/greenhouse_hero.png").convert("RGBA")
im = im.crop(im.getbbox())
k = 468 / max(im.size)
im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
x, y = (S - im.width) // 2, (S - im.height) // 2 + 6
sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((x + 20, y + im.height - 70, x + im.width - 20, y + im.height + 14), fill=(0, 0, 0, 150))
bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
bg.alpha_composite(im, (x, y))
for p in (MOD / "poster.png", MOD / "42" / "poster.png"):
    bg.convert("RGB").save(p, optimize=True)
print("poster", bg.size)
