"""Render a labeled contact sheet from one Project Zomboid texture pack."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pzforge.packfile import TexturePack


def sprite_image(entry, page) -> Image.Image:
    atlas = Image.open(io.BytesIO(page.png)).convert("RGBA")
    image = Image.new("RGBA", (entry.ow, entry.oh), (0, 0, 0, 0))
    image.paste(atlas.crop((entry.x, entry.y, entry.x + entry.w, entry.y + entry.h)),
                (entry.ox, entry.oy))
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack", type=Path)
    parser.add_argument("prefix")
    parser.add_argument("out", type=Path)
    parser.add_argument("--columns", type=int, default=8)
    args = parser.parse_args()

    texture_pack = TexturePack.read(args.pack)
    sprites = [(entry.name, sprite_image(entry, page))
               for page in texture_pack.pages for entry in page.entries
               if entry.name.startswith(args.prefix)]
    if not sprites:
        raise SystemExit(f"No sprites start with {args.prefix!r}.")

    cell_width = max(sprite.width for _, sprite in sprites)
    cell_height = max(sprite.height for _, sprite in sprites)
    label_height = 18
    rows = (len(sprites) + args.columns - 1) // args.columns
    sheet = Image.new("RGBA", (args.columns * cell_width,
                                rows * (cell_height + label_height)),
                      (26, 29, 33, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (name, sprite) in enumerate(sprites):
        x = (index % args.columns) * cell_width
        y = (index // args.columns) * (cell_height + label_height)
        sheet.alpha_composite(sprite, (x, y))
        draw.text((x + 4, y + cell_height + 2), name.rsplit("_", 1)[-1],
                  fill=(220, 220, 220, 255))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(args.out)
    print(f"Wrote {args.out} with {len(sprites)} sprites.")


if __name__ == "__main__":
    main()
