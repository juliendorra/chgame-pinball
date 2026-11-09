"""A cover's title on the game's title screen.

The cover (a game's tools/cart.py, docs/cover-art.md) sets the title in a
pixel font and paints it. The title screen draws the same lettering with
the CHGame library's titleArt() (chgame/Mask.h): an extrusion, an ink
outline thickened down and right for the shadow, and the face in the house
gold as a smooth gradient - a hint of white at the top fading through light
yellow into GOLD, then GOLD into a WOOD foot - blended by a 4x4 ordered
dither, since the palette has no light yellow or amber of its own. No bevel
or glints (the owner's choice, 2026-10-06: the cover's chrome bands looked
washed out and busy at 1x). The cover recipe stays the source of the
lettering: its title_lines() gives each line of its title as the cover
places it, and a game's tools/assets.py packs them with this module:

    import cart, titleart
    for prefix, ln in zip(("LOGO", "LOGO2"), cart.title_lines()):
        titleart.emit(o, prefix, ln)        # o: the assets' Out (array, const)

A line is a dict: mask (2D bool, as drawn: arched, kerned, emboldened),
depth (the extrusion, <= 4), side (its colour, a cover colour name). What
the game gets:

    LOGO        1 bpp rows, MSB-first (the mask trimmed to its ink)
    LOGO_W, LOGO_H
    LOGO_BASE   the face's base colour (GOLD)
    LOGO_RAMP   a byte a row: a colour (high nibble) over the base where the
                row's 4-pixel dither pattern (low nibble) has bits
    LOGO_DEPTH, LOGO_SIDE
"""
import numpy as np

INK, WHITE, FELT_DK, FELT, FELT_LT, SILVER, RED, WINE, GOLD, WOOD, BLUE, NAVY, SKIN, CYAN, FX_A, FX_B = range(16)
NAMES = ["INK", "WHITE", "FELT_DK", "FELT", "FELT_LT", "SILVER", "RED", "WINE",
         "GOLD", "WOOD", "BLUE", "NAVY", "SKIN", "CYAN", "FX_A", "FX_B"]

# The covers' depth colours in the house palette.
HOUSE = {
    "black": INK, "wine": WINE, "red": RED, "rose": RED, "gold0": WOOD, "wood0": WOOD, "wood1": WOOD,
    "navy": NAVY, "navy0": NAVY, "navy1": NAVY, "indigo": NAVY, "blue": BLUE,
}

# The gradient, as fractions of the face's height (the owner's choice).
TOP_WHITE = 0.6               # how much white in the top row's dither
LIGHT_END = 0.3               # where the white has faded out into GOLD
FOOT = (0.75, 0.97)           # GOLD fades into WOOD between these: the GOLD middle dominates
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def house(name):
    if isinstance(name, int):
        return name
    if name not in HOUSE:
        raise KeyError(f"titleart: no house colour for the cover's {name!r} (add it to HOUSE)")
    return HOUSE[name]


BASE = GOLD


def ramp(h):
    """The face's gradient for h rows: (colour, 0..16 of it over BASE)."""
    out = []
    for j in range(h):
        t = (j + 0.5) / h
        if t < LIGHT_END:
            out.append((WHITE, round(16 * TOP_WHITE * (1 - t / LIGHT_END))))
        else:
            out.append((WOOD, round(16 * min(1.0, max(0.0, (t - FOOT[0]) / (FOOT[1] - FOOT[0]))))))
    return out


def pattern(j, level):
    """Row j's 4-pixel dither nibble for a level 0..16: MSB the first pixel of
    every four, counted from the lettering's left edge less one (maskTitle's
    rows start a pixel left of the mask)."""
    return sum(8 >> i for i in range(4) if BAYER4[j & 3][(i - 1) & 3] < level)


def trim(mask):
    """The mask cut to its ink."""
    ys, xs = np.nonzero(mask)
    return mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def pack(line):
    """A line -> (bits rows, w, h, ramp, depth, side)."""
    m = trim(np.asarray(line["mask"], bool))
    h, w = m.shape
    depth = int(line.get("depth", 3))
    assert 0 <= depth <= 4, "maskTitle: depth <= 4"
    bits = [[1 if v else 0 for v in r] for r in m]
    return bits, w, h, ramp(h), depth, house(line.get("side", "wine"))


def rows1(bits):
    out = []
    for row in bits:
        for x0 in range(0, len(row), 8):
            out.append(sum(0x80 >> i for i in range(8) if x0 + i < len(row) and row[x0 + i]))
    return out


def emit(o, prefix, line, what="the title"):
    """Write one line's arrays and constants with an assets Out (array, const)."""
    bits, w, h, rp, depth, side = pack(line)
    o.array(prefix, rows1(bits), comment=f"{what}: the cover's lettering, {w}x{h}, 1 bpp MSB-first rows")
    o.const(f"{prefix}_W", w)
    o.const(f"{prefix}_H", h)
    o.const(f"{prefix}_BASE", BASE)
    o.array(f"{prefix}_RAMP", [c << 4 | pattern(j, lv) for j, (c, lv) in enumerate(rp)],
            comment="its face's gradient: per row, a colour (high nibble) over the base where its dither (low) has bits")
    o.const(f"{prefix}_DEPTH", depth)
    o.const(f"{prefix}_SIDE", side)
    return w, h


class Into:
    """An Out for the assets scripts that collect their header and source
    lines in lists (decls, defs) instead."""

    def __init__(self, decls, defs):
        self.decls, self.defs = decls, defs

    def array(self, name, data, ctype="uint8_t", comment=""):
        lines = [",".join(f"0x{v:02X}" for v in data[i:i + 16]) for i in range(0, len(data), 16)]
        head = f"// {comment}\n" if comment else ""
        self.defs.append(head + f"const {ctype} {name}[{len(data)}] = {{\n  " + ",\n  ".join(lines) + "\n};")
        self.decls.append(f"extern const {ctype} {name}[{len(data)}];")

    def const(self, name, value):
        self.decls.append(f"constexpr int {name} = {value};")


def preview(line, bg=FELT, scale=4):
    """The line as the game draws it (titleArt), for a quick look: a PIL image."""
    from PIL import Image
    pal = [0x000, 0xFFF, 0x042, 0x173, 0x4B5, 0xBBC, 0xE12, 0x702,
           0xFC2, 0x741, 0x26E, 0x125, 0xFB8, 0x6EF, 0xF0F, 0xFC2]
    rgb = [((v >> 8) * 17, ((v >> 4) & 15) * 17, (v & 15) * 17) for v in pal]
    bits, w, h, rp, depth, side = pack(line)
    fb = draw(bits, rp, depth, side, bg)
    im = Image.new("RGB", (fb.shape[1], fb.shape[0]))
    im.putdata([rgb[c] for c in fb.flatten()])
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def draw(bits, rp, depth, side, bg=FELT, pad=3):
    """What titleArt() paints (chgame/Mask.cpp), pixel for pixel, on a plain ground."""
    m = np.array(bits, bool)
    h, w = m.shape
    fb = np.full((h + depth + 2 * pad, w + depth + 2 * pad), bg, np.int16)

    def sh(a, dx, dy):
        o = np.zeros_like(a)
        H, W = a.shape
        o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = a[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]
        return o

    face = np.zeros(fb.shape, bool)
    face[pad:pad + h, pad:pad + w] = m
    union, ext = face.copy(), np.zeros_like(face)
    for k in range(1, depth + 2):
        union |= sh(face, k, k)
        if k <= depth:
            ext |= sh(face, k, k)
    grown = union.copy()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            grown |= sh(union, dx, dy)
    gap = ~face & sh(face, 1, 0) & sh(face, -1, 0)
    ext &= ~face & ~gap
    fb[grown & ~ext & ~face] = INK
    fb[ext] = side
    for j in range(h):
        c, lv = rp[j]
        nib = pattern(j, lv)
        for i in range(w):
            if m[j, i]:
                fb[pad + j, pad + i] = c if nib & (8 >> ((i + 1) & 3)) else BASE
    return fb
