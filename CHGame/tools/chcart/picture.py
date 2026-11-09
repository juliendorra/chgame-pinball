"""The visual menu's pictures: a game's box art (cartImage), a folder's or
the cart's cover, the about page. docs/visual-menu.md is the guide.

    chgame picture --template my-art.png          a blank picture, the menu's marks shown, to paint on
    chgame picture my-art.png --preview p.gif     converted if need be, shown as the menu shows it
    chgame picture photo.jpg --out my-art.png     any image made into one the menu can show
    chgame picture my-art.png --card E:\\          as the card's cover (GAMES/COVER.PIC): the splash
    chgame cart picture mycart.chgame my-art.png [--game ID | --folder F | --about]

The rule (spec/card.md): 128x128, opaque, at most 11 colours besides #FF00FF
and the menu's four (#FFF4D6, #808080, #000000, #D62020), which may be used
freely: they keep those values in every picture, whatever a cart's
menu.colors. #FF00FF is colour 15: on a Rainbow bootloader it turns through
the colour wheel, so use it on purpose (a logo, a glint). convert() makes any
image fit, as `chgame background` does for the list menu's picture.

What the bootloader draws over a picture (src/visual.c): over the installed
game, a border one pixel wide round the whole picture in colour 15 (the
rainbow; Static: #FFF4D6); while installing, a bar over rows 110-119
(x 8-119: a frame in colour 15, black inside, filling in colour 15). The rest
is the picture's own.
"""
from __future__ import annotations

import io
import pathlib

from . import background, model, runtime

# src/visual.c's BAR_X, BAR_Y, BAR_W, BAR_H and the installed game's border
BAR_X, BAR_Y, BAR_W, BAR_H = 10, 112, 108, 6
BORDER = ((0, 0, 128, 1), (0, 127, 128, 1), (0, 0, 1, 128), (127, 0, 1, 128))


def convert(src, fit="cover", dither=False):
    """(PNG bytes that follow the rule, [notes]) from any image."""
    return background.convert(src, dict(model.UI_COLORS), fit, dither)


def ready(png):
    return model.picture_ok(png)


def template():
    """A blank picture to paint on: the marks the menu draws over a picture
    shown where they go (the installed game's border, the install bar's rows)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (128, 128), (32, 32, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([BAR_X - 2, BAR_Y - 2, BAR_X + BAR_W + 1, BAR_Y + BAR_H + 1], outline=(128, 128, 128))
    d.rectangle([0, 0, 127, 127], outline=(255, 0, 255))
    background.text(lambda x, y, c: d.point((x, y), fill=c), 22, 58, "YOUR PICTURE", (255, 244, 214))
    background.text(lambda x, y, c: d.point((x, y), fill=c), 34, 100, "THE BAR", (128, 128, 128))
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def preview(png, phase=0, scale=3, style="rainbow", mark=False, bar=None, dark=0):
    """A PIL image of the picture as the panel shows it (RGB565): with the
    installed game's border (mark), the install bar at `bar` (0..1, None: none), every
    colour halved `dark` times (a fade). Colour 15 is the rainbow's colour at
    `phase`, or #FF00FF (style "static")."""
    from PIL import Image
    pic = runtime.menu_picture(png)
    pal = [int.from_bytes(pic[8 + 2 * i:10 + 2 * i], "little") for i in range(16)]
    if style == "rainbow":
        pal[15] = background.hue(phase)
    for _ in range(dark):
        pal = [c >> 1 & 0x7BEF for c in pal]
    idx = [pic[512 + i // 2] >> 4 if i % 2 == 0 else pic[512 + i // 2] & 15 for i in range(128 * 128)]

    def fill(x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                idx[yy * 128 + xx] = c
    if mark:
        for edge in BORDER:
            fill(*edge, 15 if style == "rainbow" else 11)
    if bar is not None:
        fill(BAR_X - 2, BAR_Y - 2, BAR_W + 4, BAR_H + 4, 15)
        fill(BAR_X - 1, BAR_Y - 1, BAR_W + 2, BAR_H + 2, 13)
        fill(BAR_X, BAR_Y, round(BAR_W * bar), BAR_H, 15)
    im = Image.new("RGB", (128, 128))
    im.putdata([background.rgb(pal[i]) for i in idx])
    return im.resize((128 * scale, 128 * scale), Image.NEAREST) if scale != 1 else im


def save_preview(png, path, scale=3, style="rainbow"):
    """A preview: a PNG, or a GIF of the picture fading in, installing and
    fading out (.gif), as the visual menu shows a game."""
    path = pathlib.Path(path)
    if path.suffix.lower() != ".gif":
        preview(png, scale=scale, style=style, mark=True).save(path)
        return
    frames, ph = [], 0
    for d in range(6, -1, -1):
        frames.append(preview(png, ph, scale, style, dark=d))
        ph += 4
    for _ in range(10):
        frames.append(preview(png, ph, scale, style))
        ph += 4
    for k in range(13):
        frames.append(preview(png, ph, scale, style, bar=k / 12))
        ph += 4
    for d in range(1, 7):
        frames.append(preview(png, ph, scale, style, bar=1, dark=d))
        ph += 4
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=80, loop=0)


def write_to_card(png, card):
    """The picture as the card's cover, GAMES/COVER.PIC: the visual menu's splash."""
    f = pathlib.Path(card) / "GAMES" / "COVER.PIC"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(runtime.menu_picture(png))
    return f
