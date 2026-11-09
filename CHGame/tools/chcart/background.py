"""The menu's picture: one 128x128 image behind the SD menu, with the CHGAME
logo (or anything else) painted into it. docs/menu-image.md is the
step-by-step guide.

    chgame background --template my-menu.png       the default picture, to edit
    chgame background my-menu.png --preview p.gif  converted if need be, and the menu drawn on it
    chgame background photo.jpg --out my-menu.png  any image made into one the menu can show
    chgame background my-menu.png --card E:\\       straight onto a mounted card (GAMES/MENU.BG)
    chgame cart background mycart.chgame my-menu.png   into a cart (converted the same way)

The layout. The menu draws only its list, over rows 20-119: ten rows of ten
pixels, titles from x 8, the selection bar across the whole width in the
rainbow, a red chip at x 2-4 for the installed game, `>` at x 122 for a
folder. Rows 0-19 and 120-127 are the picture's alone: the logo at the top,
key hints at the foot. Messages (INSTALLING, errors) are boxes over rows
36-87.

The colours. Pure magenta, #FF00FF, is drawn in the menu's colour 15: one
colour turning through the rainbow, or, on a bootloader built in the static
style (Tools > Bootloader: SD Text Menu (Static); --style static here
previews that), in the menu's text colour, so the bar, the boxes and the
logo match the titles. Besides
it the picture may use 11 colours, plus the menu's own four (text #FFF4D6,
greyed #808080, selected text #000000, chip #D62020, or the cart's
`menu.colors`). convert() makes any image fit: it scales it to 128x128
(`fit`: "cover" crops to fill, "contain" adds black bars; whole multiples of
128 are scaled down pixel for pixel), turns near-magenta into exact
magenta, and reduces the other colours to 11 (Pillow's median cut,
`dither` optional). A picture that already fits is kept byte for byte.
"""
from __future__ import annotations

import io
import pathlib
import re

from . import model, runtime

LIST_Y, ROWS, ROW_H = 20, 10, 10
FONT57 = runtime.REPO / "platform" / "bootloader" / "src" / "font5x7.h"
SAMPLE = ["BACKGAMMON", "BLACKJACK", "CHESS", "FOUR IN A ROW", "MAHJONG", "POKER", "SOLITAIRE", "WORDS",
          "YACHT DICE", "APPS"]


def ready(png, ui=None):
    """True if the bytes are a PNG the menu takes as it is."""
    return not model._check_background(png, ui or dict(model.UI_COLORS), "picture")


def convert(src, ui=None, fit="cover", dither=False):
    """(PNG bytes, [what was done]) from any image Pillow reads (a path or
    bytes)."""
    from PIL import Image, ImageOps
    ui = ui or dict(model.UI_COLORS)
    data = pathlib.Path(src).read_bytes() if not isinstance(src, (bytes, bytearray)) else bytes(src)
    if ready(data, ui):
        return data, []
    notes = []
    im = Image.open(io.BytesIO(data))
    im.seek(0)
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        back = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        im = Image.alpha_composite(back, rgba)
        notes.append("transparent parts made black")
    im = im.convert("RGB")
    w, h = im.size
    if (w, h) != (128, 128):
        if w == h and w % 128 == 0:
            im = im.resize((128, 128), Image.NEAREST)
            notes.append(f"scaled from {w}x{h}, pixel for pixel")
        elif fit == "contain":
            im = ImageOps.pad(im, (128, 128), Image.LANCZOS, color=(0, 0, 0))
            notes.append(f"scaled from {w}x{h} to fit, with black bars")
        else:
            im = ImageOps.fit(im, (128, 128), Image.LANCZOS)
            notes.append(f"scaled from {w}x{h} and cropped to fill")
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    near = [r >= 200 and b >= 200 and g <= 80 for r, g, b in px]
    if sum(near) and any(p != model.RAINBOW_RGB for p, n in zip(px, near) if n):
        notes.append("near-magenta made exact #FF00FF (the rainbow)")
    px = [model.RAINBOW_RGB if n else p for p, n in zip(px, near)]
    im.putdata(px)
    special = {model.RAINBOW_RGB} | {model.hex_rgb(c) for c in ui.values()}
    others = {p for p in px if p not in special}
    if len(others) > 11:
        q = im.quantize(colors=11, method=Image.Quantize.MEDIANCUT,
                        dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE).convert("RGB")
        qpx = list(q.get_flattened_data() if hasattr(q, "get_flattened_data") else q.getdata())
        px = [model.RAINBOW_RGB if p == model.RAINBOW_RGB else c for p, c in zip(px, qpx)]
        im.putdata(px)
        notes.append(f"{len(others)} colours reduced to 11" + (" (dithered)" if dither else ""))
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    data = out.getvalue()
    problems = model._check_background(data, ui, "picture")
    if problems:                            # (should not happen; say so rather than write a bad one)
        raise model.CartError(problems)
    return data, notes


def template():
    """The default picture (spec/assets/menu-default.png, painted by
    tools/art/menu/menu.py): the starting point."""
    return runtime.DEFAULT_BACKGROUND.read_bytes()


# ---- the preview: the menu as the bootloader draws it (src/menu.c, lcd.c) --------------

def hue(p):
    """lcd.c's colour wheel: RGB565 for step p (192 to a turn)."""
    c, p = 0, p + 64
    for _ in range(3):
        q = p % 192
        v = q if q < 32 else 31 if q < 96 else 127 - q if q < 128 else 0
        c = c << 5 | (10 + ((v * 11) >> 4))
        p += 128
    return (c & 0x7FE0) << 1 | (c & 0x1F)


def rgb(c565):
    """RGB565 to 8-bit RGB, full range (as the bootloader's panel model shows it)."""
    return (c565 >> 11) * 255 // 31, ((c565 >> 5) & 63) * 255 // 63, (c565 & 31) * 255 // 31


def glyphs():
    src = FONT57.read_text()
    body = src[src.index("font5x7[(FONT5X7_LAST - 31) * 5] = {"):].split("};")[0]
    return [int(v, 16) for v in re.findall(r"0x([0-9A-Fa-f]{2})", body)]


def text(put, x, y, s, colour, g=None):
    g = g or glyphs()
    for ch in s:
        o = ord(ch) if 32 <= ord(ch) <= 0x5F else ord("?")
        col = g[(o - 32) * 5:(o - 32) * 5 + 5]
        for cx in range(5):
            for cy in range(7):
                if col[cx] >> cy & 1:
                    put(x + cx, y + cy, colour)
        x += 6


def preview(png, ui=None, phase=0, titles=None, scale=3, installed=(2,), folders=(ROWS - 1,), style="rainbow"):
    """A PIL image of the menu over the picture, as the panel shows it
    (RGB565): a list of titles, the first selected, a chip on the rows in
    `installed`, a folder's `>` on those in `folders`. Colour 15 is the
    rainbow's colour at `phase`, or the menu's text colour (style "static",
    as src/menu.c draws it: never the hot pink the palette holds)."""
    from PIL import Image
    ui = ui or dict(model.UI_COLORS)
    bg = runtime.menu_background(png, ui)
    pal = [rgb(int.from_bytes(bg[8 + 2 * i:10 + 2 * i], "little")) for i in range(16)]
    idx = [[0] * 128 for _ in range(128)]
    for y in range(128):
        for x in range(128):
            b = bg[512 + y * 64 + x // 2]
            idx[y][x] = b >> 4 if x % 2 == 0 else b & 15

    def put(x, y, c):
        if 0 <= x < 128 and 0 <= y < 128:
            idx[y][x] = c
    g = glyphs()
    for i, t in enumerate((titles or SAMPLE)[:ROWS]):
        y = LIST_Y + i * ROW_H
        c = 11
        if i == 0:
            for yy in range(y, y + ROW_H):
                for x in range(128):
                    idx[yy][x] = 15
            c = 13
        if i in installed:
            for yy in range(y + 2, y + 8):
                for x in range(2, 5):
                    idx[yy][x] = 14
        text(put, 8, y + 1, t.upper()[:19], c, g)
        if i in folders:
            text(put, 122, y + 1, ">", c, g)
    im = Image.new("RGB", (128, 128))
    pal[15] = rgb(hue(phase)) if style == "rainbow" else pal[11]
    im.putdata([pal[idx[y][x]] for y in range(128) for x in range(128)])
    return im.resize((128 * scale, 128 * scale), Image.NEAREST)


def save_preview(png, path, ui=None, scale=3, style="rainbow"):
    """A preview as a PNG, or as a GIF with the rainbow turning (.gif)."""
    path = pathlib.Path(path)
    if path.suffix.lower() == ".gif" and style == "rainbow":
        frames = [preview(png, ui, phase, scale=scale) for phase in range(0, 192, 8)]
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=160, loop=0)
    else:
        preview(png, ui, scale=scale, style=style).save(path)


def write_to_card(png, card, ui=None):
    """The picture as the card's GAMES/MENU.BG (the top of its menu)."""
    f = pathlib.Path(card) / "GAMES" / "MENU.BG"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(runtime.menu_background(png, ui or dict(model.UI_COLORS)))
    return f


def colors_arg(pairs):
    """{"text": "#FFFFFF", ...} from ["text=#FFFFFF", ...]."""
    out = dict(model.UI_COLORS)
    for kv in pairs or []:
        k, _, v = kv.partition("=")
        if k not in model.UI_COLORS or not model.COLOR_RE.match(v):
            raise ValueError(f"--color {kv}: KEY=#RRGGBB, KEY one of {', '.join(model.UI_COLORS)}")
        out[k] = v.upper()
    return out
