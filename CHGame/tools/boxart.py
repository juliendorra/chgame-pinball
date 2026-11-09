"""boxart: the visual menu's pictures as PNGs, and the quick plain ones.

Every picture the visual menu shows (a game's box art, a folder's cover, the
cart's cover, the menu's own screens) is a 128x128 PNG that follows the
picture rule (spec/card.md): at most 11 colours besides #FF00FF and the
menu's four (#FFF4D6, #808080, #000000, #D62020). The included pictures are
painted with tools/artkit (docs/cover-art.md). This module:

    png(picture), save(picture, path)   the PNG laid out as the card holds it
                                        (an artkit Picture, a PIL image or a
                                        pixkit.FB), checked against the rule
    cli()                               `chgame boxart`: a sketch's docs/cart.png
                                        from its tools/cart.py; --check, --sheet
    placeholder(title, shot)            the plain pictures the tools draw for a
    folder_cover(name)                  game or a folder that has none: the
                                        title in the display font over the
                                        game's first frame, a folder and its name
    card_art(), RANKS, SUITS            the games' card ranks, suits and pips
                                        (tools/art/common), for a recipe

The plain pictures are drawn on a pixkit.FB of HOUSE palette indices, plus
CREAM and GREY (the menu's text and disabled colours). RED is drawn as the
menu's red, #D62020, and INK as its black, so neither takes one of the 11.

    python tools/boxart.py sheet OUT.png A.png B.png ...   # side by side, 2x, for a look
"""
from __future__ import annotations

import io
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent         # the repository's tools/
sys.path.insert(0, str(HERE))
import artlib  # noqa: E402
import pixkit as pk  # noqa: E402
from pixkit import (INK, WHITE, FELT_DK, FELT, FELT_LT, SILVER, RED, WINE, GOLD, WOOD,  # noqa: E402,F401
                    BLUE, NAVY, SKIN, CYAN, FX_A, FX_B)

CREAM, GREY = 16, 17                                   # the menu's text and disabled colours
RGB = {i: pk.rgb(c) for i, c in enumerate(pk.PALETTE)}
RGB.update({INK: (0, 0, 0), RED: (214, 32, 32), FX_A: (255, 0, 255), FX_B: pk.rgb(pk.FX_B_FRAME),
            CREAM: (255, 244, 214), GREY: (128, 128, 128)})
UI = [(255, 244, 214), (128, 128, 128), (0, 0, 0), (214, 32, 32)]     # palette 11-14
MAGENTA = (255, 0, 255)                                               # palette 15


def canvas(fill=INK):
    return pk.FB(fill)


# ---- backgrounds ------------------------------------------------------------------
# The plain pictures keep to one rule, so a folder never passes for a game:
# a folder is the navy gradient with its art in blues, folder() then blues();
# a game is on the dark green felt, game().

def game():
    """A game's picture, ready for its charm: green felt, gold frame."""
    fb = canvas()
    felt(fb)
    return fb


def folder():
    """A folder's cover, ready for its word and charm: the navy gradient (dark
    above, a navy band below) in a frame. Draw on it in any colours, then
    blues() for the folders' palette."""
    fb = canvas(INK)
    fb.dither(0, 0, 128, 128, NAVY, 0)
    fb.fill_rect(3, 74, 122, 51, NAVY)
    fb.rect(2, 2, 124, 124, GOLD)
    return fb


# Every house colour to its blue: the titles' gold ramp to white, cyan and
# blue, reds and greens to blues, warm lights to silver and white. Black, navy, the
# blues, silver, white and the menu's colours stay.
BLUES = {FX_B: WHITE, GOLD: CYAN, WOOD: BLUE, WINE: INK, RED: BLUE, SKIN: SILVER,
         FELT_DK: NAVY, FELT: BLUE, FELT_LT: CYAN, CREAM: WHITE}


def blues(fb, box=(0, 0, 128, 128)):
    """The folders' palette: every pixel in box through BLUES."""
    x0, y0, w, h = box
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            i = y * 128 + x
            fb.p[i] = BLUES.get(fb.p[i], fb.p[i])


def felt(fb, base=FELT, dark=FELT_DK, frame=GOLD):
    """The games' title backdrop (CHBlackjack's feltBackdrop): `base`, its
    edges dithered with `dark`, a frame two pixels in."""
    fb.clear(base)
    fb.dither(0, 0, 128, 6, dark, 0)
    fb.dither(0, 122, 128, 6, dark, 1)
    fb.dither(0, 0, 6, 128, dark, 0)
    fb.dither(122, 0, 6, 128, dark, 1)
    if frame is not None:
        fb.rect(2, 2, 124, 124, frame)


# ---- lettering ----------------------------------------------------------------------

def ramp(h, top=FX_B, mid=GOLD, low=WOOD):
    """The titles' gradient: `top` for the first rows, `mid`, then `low` for
    the lower part (CHBlackjack's title ramp, stretched to h rows)."""
    return [top if i < max(2, h // 5) else (mid if i < h * 3 // 4 else low) for i in range(h + 2)]


def lettering(fb, rows, x, y, fill=None, outline=INK, shadow=WINE, colours=(FX_B, GOLD, WOOD)):
    """1 bpp rows ('#' set) drawn as the games draw titles: `fill` (a colour),
    or a ramp of `colours` (top, middle, low: the titles' gold by default), an
    outline and a shadow a pixel down and right. Returns (x, y, w, h)."""
    w, h = max(len(r) for r in rows), len(rows)
    m = pk.Mask(w, h)
    m.blit(rows)
    m.draw(fb, x, y, fill if fill is not None else colours[1], outline, shadow,
           None if fill is not None else ramp(h, *colours))
    return x, y, w, h


_FONT = None


def font():
    """The display font (tools/art/common/font.txt): {char: {"w", "top", "rows"}}."""
    global _FONT
    if _FONT is None:
        f, cur = {}, None
        for ln in (artlib.COMMON / "font.txt").read_text(encoding="utf-8").splitlines():
            if not ln.strip() or ln.startswith("# "):
                continue
            if ln.startswith("= "):
                parts = ln[2:].split()
                cur = {"top": int(parts[1]) if len(parts) > 1 else 0, "rows": []}
                f[parts[0]] = cur
                continue
            cur["rows"].append(ln.rstrip())
        for g in f.values():
            g["w"] = max(len(r) for r in g["rows"])
            g["rows"] = [r.ljust(g["w"], ".") for r in g["rows"]]
        _FONT = f
    return _FONT


def text_rows(s, scale=1, gap=1, space=4):
    """s in the display font as 1 bpp rows (13 rows a line, before scaling).
    The font has capitals, digits and ! ? - + . , : ' (and '&' drawn as '+')."""
    f = font()
    s = s.replace("&", "+")
    w = sum(f[c]["w"] + gap if c in f else space for c in s) - gap
    grid = [["."] * max(w, 1) for _ in range(13)]
    x = 0
    for c in s:
        if c not in f:
            x += space
            continue
        g = f[c]
        for r, row in enumerate(g["rows"]):
            for i, ch in enumerate(row):
                if ch == "#":
                    grid[g["top"] + r][x + i] = "#"
        x += g["w"] + gap
    while grid and "#" not in grid[-1]:
        grid.pop()
    rows = ["".join(r) for r in grid]
    if scale > 1:
        rows = ["".join(ch * scale for ch in r) for r in rows for _ in range(scale)]
    return rows


def title(fb, s, y, scale=None, max_w=118, **kw):
    """s in the display font, centred, as lettering(); scale 2 if it fits in
    max_w, else 1 (or as given). Returns (x, y, w, h)."""
    if scale is None:
        scale = 2 if len(text_rows(s)[0]) * 2 <= max_w else 1
    rows = text_rows(s, scale)
    return lettering(fb, rows, 64 - len(rows[0]) // 2, y, **kw)


# ---- the card art -------------------------------------------------------------------

def glyph_sheet(path):
    """A text-art file of glyphs side by side, a blank column between (comment
    lines '# '): [rows of characters] per glyph."""
    rows = [ln.rstrip() for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]
    parts = [r.split(" ") for r in rows]
    return [[p[k] for p in parts] for k in range(len(parts[0]))]


_CARD_ART = {}


def card_art():
    if not _CARD_ART:
        c = artlib.COMMON
        _CARD_ART.update(ranks=glyph_sheet(c / "ranks.txt"), suits=glyph_sheet(c / "suits.txt"),
                         pip13=glyph_sheet(c / "pip13.txt"), pip9=glyph_sheet(c / "pip9.txt"),
                         court=glyph_sheet(c / "court.txt"))
    return _CARD_ART


RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = "cdhs"                                         # suits.txt's order; the pips' is h d s c


# ---- defaults for what has no picture ---------------------------------------------------

def wrap(s, width=118, scale=1):
    """s split into lines of the display font that fit `width` at `scale`."""
    lines, cur = [], ""
    for w in s.upper().split():
        t = (cur + " " + w).strip()
        if cur and len(text_rows(t)[0]) * scale > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def titled(fb, s, y_mid, max_lines=3):
    """s centred on y_mid in the display font: two lines at scale 2 if they
    fit, else up to max_lines at scale 1."""
    for scale in (2, 1):
        lines = wrap(s, 118, scale)
        if len(lines) <= (2 if scale == 2 else max_lines) and all(len(text_rows(x)[0]) * scale <= 118 for x in lines):
            break
    h = 13 * scale + 3
    y = y_mid - len(lines) * h // 2
    for k, line in enumerate(lines):
        title(fb, line, y + k * h, scale=scale)


def shot_backdrop(fb, shot):
    """A game's screenshot (PNG or GIF bytes, the screen at any scale; its
    first frame), dimmed into four shades of the games' green behind
    everything else."""
    from PIL import Image
    im = Image.open(io.BytesIO(shot))
    im.seek(0)
    im = im.convert("L").resize((128, 128), Image.NEAREST)
    shades = [INK, FELT_DK, FELT, FELT_LT]
    lum = im.tobytes()
    for i, v in enumerate(lum):
        fb.p[i] = shades[min(3, v // 72)]


def placeholder(title_text, shot=None):
    """A game without a picture of its own: its title over its first gameplay
    frame (dimmed), or on felt. What `chgame export` and the cart tools give
    it (spec/card.md keeps it outside the format: the cart carries the PNG)."""
    fb = game()
    if shot:
        shot_backdrop(fb, shot)
        fb.fill_rect(3, 40, 122, 48, INK)
        fb.hline(3, 39, 122, GOLD)
        fb.hline(3, 88, 122, GOLD)
    fb.rect(2, 2, 124, 124, GOLD)
    titled(fb, title_text, 64)
    return png(fb)


def folder_cover(name):
    """A folder without a cover: a folder and its name, in the folders' blues."""
    fb = folder()
    fb.fill_round(36, 14, 22, 10, 2, WOOD)
    fb.fill_round(36, 19, 56, 35, 3, WOOD)
    fb.fill_round(38, 23, 52, 29, 2, GOLD)
    fb.hline(40, 27, 48, WHITE)
    titled(fb, name, 88, 2)
    blues(fb)
    return png(fb)


# ---- output -------------------------------------------------------------------------

def image(fb):
    im = Image.new("RGB", (128, 128))
    im.putdata([RGB[v] for v in fb.p])
    return im


def png(fb_or_image) -> bytes:
    """An indexed PNG laid out as the card holds it: the picture's own colours
    at 0-10 in order of first appearance, the menu's four at 11-14, #FF00FF at
    15, so a paint program shows the same palette the menu gets."""
    if hasattr(fb_or_image, "image") and not isinstance(fb_or_image, (Image.Image, pk.FB)):
        fb_or_image = fb_or_image.image()                # an artkit Picture
    im = image(fb_or_image) if isinstance(fb_or_image, pk.FB) else fb_or_image.convert("RGB")
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    own = []
    for p in px:
        if p not in UI and p != MAGENTA and p not in own:
            own.append(p)
    if len(own) > 11:
        raise ValueError(f"{len(own)} colours besides #FF00FF and the menu's four; 11 at most")
    pal = own + [(0, 0, 0)] * (11 - len(own)) + UI + [MAGENTA]
    index = {MAGENTA: 15}
    for k, c in enumerate(UI):
        index.setdefault(c, 11 + k)
    for k, c in enumerate(own):
        index[c] = k
    out = Image.new("P", (128, 128))
    out.putpalette([v for c in pal for v in c])
    out.putdata([index[p] for p in px])
    b = io.BytesIO()
    out.save(b, "PNG", optimize=True)
    return b.getvalue()


def save(fb_or_image, path):
    """Checks the picture rule (chcart's own check) and writes the PNG."""
    data = png(fb_or_image)
    from chcart import model
    issues = model.check_picture(data, str(path))
    if issues:
        raise ValueError("; ".join(str(i) for i in issues))
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return path


def sheet(paths, out, scale=2, cols=6, gap=6):
    """Pictures side by side at `scale`, for a look."""
    ims = [Image.open(p).convert("RGB").resize((128 * scale, 128 * scale), Image.NEAREST) for p in paths]
    rows = (len(ims) + cols - 1) // cols
    n = min(cols, len(ims))
    s = 128 * scale
    im = Image.new("RGB", (n * (s + gap) + gap, rows * (s + gap) + gap), (24, 24, 28))
    for k, p in enumerate(ims):
        im.paste(p, (gap + (k % cols) * (s + gap), gap + (k // cols) * (s + gap)))
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return out


# ---- the programs' box art ------------------------------------------------------------

def recipes():
    """Every example with a box-art recipe, tools/cart.py: {name: folder}."""
    root = HERE.parent / "platform" / "board" / "arduino" / "CHGame" / "libraries" / "CHGame" / "examples"
    return {d.name: d for sub in ("Games", "Apps") for d in sorted((root / sub).iterdir())
            if (d / "tools" / "cart.py").is_file()}


def render(sketch):
    """The PNG a sketch's tools/cart.py draws (its draw() returns a PIL image,
    an artkit Picture or a pixkit FB)."""
    import importlib.util
    f = pathlib.Path(sketch) / "tools" / "cart.py"
    spec = importlib.util.spec_from_file_location(f"cart_{pathlib.Path(sketch).name}", f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return png(mod.draw())


def cli(argv, sketch=None):
    """`chgame boxart`: a sketch's docs/cart.png from its tools/cart.py;
    --check: every recipe's picture is the committed one; --sheet F: all of
    them side by side."""
    if "--sheet" in argv:
        out = argv[argv.index("--sheet") + 1]
        print(sheet([d / "docs" / "cart.png" for d in recipes().values()], out, cols=6))
        return 0
    if "--check" in argv:
        stale = [n for n, d in recipes().items()
                 if not (d / "docs" / "cart.png").exists() or (d / "docs" / "cart.png").read_bytes() != render(d)]
        print(f"boxart: {len(recipes())} recipes" + (f", stale: {', '.join(stale)} (chgame boxart in each)" if stale else ", all current"))
        return 1 if stale else 0
    d = pathlib.Path(sketch)
    if not (d / "tools" / "cart.py").is_file():
        print(f"{d.name}: no tools/cart.py (copy one from another game; docs/cover-art.md has the method)")
        return 2
    data = render(d)
    from chcart import model
    issues = model.check_picture(data, "docs/cart.png")
    if issues:
        print("; ".join(str(i) for i in issues))
        return 1
    out = d / "docs" / "cart.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() or out.read_bytes() != data:
        out.write_bytes(data)
    print(f"{out}: drawn")
    return 0


def main(argv):
    if len(argv) >= 3 and argv[0] == "sheet":
        print(sheet(argv[2:], argv[1]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
