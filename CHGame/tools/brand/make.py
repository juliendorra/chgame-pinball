"""The CHGame brand's pictures, written to docs/brand/. The look and the
rules are docs/brand/README.md.

    python tools/brand/make.py                 # everything
    python tools/brand/make.py banner          # docs/brand/banner.gif, the README's banner
    python tools/brand/make.py buttons         # docs/brand/btn-*.svg, the README's link buttons
    python tools/brand/make.py warning         # docs/brand/warning.svg, the README's Rev0 caution
    python tools/brand/make.py xoxo            # docs/brand/xoxo.gif, the special thanks' X and O
    python tools/brand/make.py wordmark        # docs/brand/wordmark.svg (the API reference's header)
    python tools/brand/make.py swatches        # docs/brand/palette.svg
    python tools/brand/make.py social          # docs/brand/social.png, GitHub's link preview (upload it by hand)
    python tools/brand/make.py banner --still out/banner.png   # one frame, to look at

Neobrutalism in the house palette: flat colours, ink outlines, hard
shadows offset down and right, nothing blurred. The lettering is pixel
art, like the console's own: the pixel CHGAME logo is the owner's
(logo-pixel.png: ink, and magenta where the device turns it through the
rainbow), everything else is Bitrimus (tools/art/fonts/about-bitrimus.json,
CC0). The badge logo is the owner's too (docs/brand/logo.png); both are
drawn as they are, never redrawn.

The banner is the handheld with the visual menu on its screen: the casino
card's splash, then the games' box art (each program's docs/cart.png)
rising from the bottom at each press of DOWN, while the logo's magenta
turns through the rainbow.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "docs" / "brand"
EXAMPLES = ROOT / "platform/board/arduino/CHGame/libraries/CHGame/examples"

# The palette (docs/brand/README.md). INK and YELLOW are the logo's own.
INK = "#252628"
YELLOW = "#F9D84A"
CREAM = "#FFFDF6"
PAPER = "#FBFAF5"
MINT = "#BDE2C7"
SAGE = "#B7DACC"
LAVENDER = "#C8B6F3"
CORAL = "#F4A28C"
DOTS = "#E6E2D3"
PALETTE = [("Ink", INK), ("Yellow", YELLOW), ("Cream", CREAM), ("Paper", PAPER),
           ("Mint", MINT), ("Sage", SAGE), ("Lavender", LAVENDER), ("Coral", CORAL)]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- lettering

class Face:
    """A pixel face from a fontscout JSON, set on a fixed line (so every
    string shares one baseline): top is the face's highest pixel, the
    mask is `line` rows tall."""

    def __init__(self, path, gap=0):
        d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        self.g = d["glyphs"]
        self.space = d.get("space") or 3
        self.gap = gap
        ys = [(g[3], g[3] + g[1]) for g in self.g.values() if g[0] and g[1]]
        self.top = min(y for y, _ in ys)
        self.line = max(y for _, y in ys) - self.top

    def mask(self, s):
        cols = []
        for ch in s:
            g = self.g.get(ch)
            if g is None or not g[0]:
                adv = g[4] if g and g[4] else self.space
                cols.append((None, adv + self.gap))
                continue
            cols.append((g, g[4] + self.gap))
        w = sum(a for _, a in cols) - self.gap
        m = np.zeros((self.line, max(1, w)), dtype=bool)
        pen = 0
        for g, adv in cols:
            if g is not None:
                gw, gh, gx, gy, _, rows = g
                for j, r in enumerate(rows):
                    for i, c in enumerate(r):
                        if c in "#1":
                            m[gy - self.top + j, pen + gx + i] = True
            pen += adv
        return m


def art(s):
    """An inline icon: rows of '#' and '.'."""
    rows = [r.strip() for r in s.strip().splitlines()]
    return np.array([[c == "#" for c in r] for r in rows])


BITRIMUS = ROOT / "tools/art/fonts/about-bitrimus.json"

ICONS = {
    "globe": art("""
        ...#####...
        ..#..#..#..
        .#..#.#..#.
        #...#.#...#
        ###########
        #...#.#...#
        ###########
        #...#.#...#
        .#..#.#..#.
        ..#..#..#..
        ...#####...
    """),
    "page": art("""
        ######...
        #....##..
        #....#.#.
        #....####
        #.#####.#
        #.......#
        #.#####.#
        #.......#
        #.####..#
        #.......#
        #########
    """),
    "play": art("""
        ##.......
        ####.....
        ######...
        ########.
        #########
        ########.
        ######...
        ####.....
        ##.......
    """),
    "pad": art("""
        ..#########..
        .#.........#.
        #..#.....#..#
        #.###...#.#.#
        #..#.....#..#
        #....###....#
        .####...####.
    """),
    "basket": art("""
        ##.........
        .#########.
        .#########.
        .########..
        ..#######..
        ..#........
        ..########.
        ...##..##..
        ...##..##..
    """),
    "chat": art("""
        .#########.
        #.........#
        #..#.#.#..#
        #.........#
        .##.######.
        ..##.......
        ..#........
    """),
}


def scaled(m, s):
    return np.kron(m, np.ones((s, s), dtype=bool))


# ---------------------------------------------------------------- drawing

SS = 4  # supersampling for the smooth shapes


class Canvas:
    """An RGB picture with neobrutalist shapes (supersampled, then reduced)
    and pixel lettering (exact)."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w, h), rgb(bg))

    def shapes(self, paint):
        """paint(draw, k) draws at k times the size on a transparent layer."""
        big = Image.new("RGBA", (self.w * SS, self.h * SS), (0, 0, 0, 0))
        paint(ImageDraw.Draw(big), SS)
        small = big.resize((self.w, self.h), Image.Resampling.BOX)
        self.im.paste(small, (0, 0), small)

    def mask(self, m, x, y, colour):
        layer = Image.fromarray((m * 255).astype(np.uint8))
        self.im.paste(rgb(colour), (int(x), int(y)), layer)

    def image(self, im, x, y):
        if im.mode == "RGBA":
            self.im.paste(im, (int(x), int(y)), im)
        else:
            self.im.paste(im.convert("RGB"), (int(x), int(y)))


def card(d, k, x, y, w, h, fill, r=16, bw=5, shadow=10, border=INK):
    """A neobrutalist card: hard shadow, ink border, flat fill."""
    if shadow:
        d.rounded_rectangle([k * (x + shadow), k * (y + shadow), k * (x + w + shadow) - 1,
                             k * (y + h + shadow) - 1], radius=k * r, fill=rgb(INK))
    d.rounded_rectangle([k * x, k * y, k * (x + w) - 1, k * (y + h) - 1], radius=k * r, fill=rgb(border))
    if fill:
        d.rounded_rectangle([k * (x + bw), k * (y + bw), k * (x + w - bw) - 1, k * (y + h - bw) - 1],
                            radius=k * max(0, r - bw), fill=rgb(fill))


def disc(d, k, cx, cy, rad, fill, bw=5, shadow=8):
    if shadow:
        d.ellipse([k * (cx - rad + shadow), k * (cy - rad + shadow), k * (cx + rad + shadow) - 1,
                   k * (cy + rad + shadow) - 1], fill=rgb(INK))
    d.ellipse([k * (cx - rad), k * (cy - rad), k * (cx + rad) - 1, k * (cy + rad) - 1], fill=rgb(INK))
    d.ellipse([k * (cx - rad + bw), k * (cy - rad + bw), k * (cx + rad - bw) - 1, k * (cy + rad - bw) - 1],
              fill=rgb(fill))


# ---------------------------------------------------------------- the pixel logo

PIXEL_LOGO = HERE / "logo-pixel.png"         # the owner's: ink letters, a magenta shadow


def pixel_logo():
    """(ink, accent) masks of the pixel CHGAME logo: black is the ink, magenta
    the colour that turns through the rainbow on the device."""
    a = np.array(Image.open(PIXEL_LOGO).convert("RGB")).astype(int)
    ink = (a.sum(axis=2) < 128)
    accent = (a[:, :, 0] > 200) & (a[:, :, 1] < 80) & (a[:, :, 2] > 200)
    return ink, accent


def rainbow(t):
    """The device's rainbow at full value: a hue from 0 to 1."""
    h = (t % 1.0) * 6
    i, f = int(h), h - int(h)
    v = [(1, f, 0), (1 - f, 1, 0), (0, 1, f), (0, 1 - f, 1), (f, 0, 1), (1, 0, 1 - f)][i % 6]
    return tuple(int(round(c * 255)) for c in v)


# ---------------------------------------------------------------- banner

W, H = 1280, 480
LOGO_S = 4                                  # the pixel logo's scale on the banner

# The covers on the handheld's screen, in the order DOWN shows them.
COVERS = ["CHBlackjack", "CHChess", "CHSlots", "CHRoulette", "CHMahjong", "CHPoker", "CHCraps",
          "CHWords", "CHBackgammon", "CHBoardwalk", "CHYacht", "CHSnakes", "CHDominoes",
          "CHCrossword", "CHBingo", "CHFour", "CHCheckers", "CHSolitaire", "CHTicTacToe",
          "CHWordWheel", "CHStlView"]


def cover_paths():
    out = [ROOT / "tools/sdcard/art/cover.png"]                 # the power-on splash
    for name in COVERS:
        hits = list(EXAMPLES.glob(f"*/{name}/docs/cart.png"))
        if not hits:
            sys.exit(f"no box art for {name}")
        out.append(hits[0])
    return out


# The handheld: CHGame Rev0's layout (the expansion port's holes along the
# top, over the screen; a D-pad left, B and A right, two small buttons under
# the screen), in the brand's colours, every button white.
BX, BY, BW, BH = 640, 50, 584, 380
SCR = 256                                   # 128 x 128 at 2x
BEZ = 14
SX = BX + (BW - SCR) // 2
SY = BY + 36 + BEZ
DPAD = (BX + (SX - BEZ - BX) // 2 + 2, SY + 112)    # centre
KEY = 34                                    # D-pad key size
RIGHT_X = SX + SCR + BEZ + (BX + BW - SX - SCR - BEZ) // 2
B_BTN = (RIGHT_X + 22, SY + 70)
A_BTN = (RIGHT_X - 20, SY + 140)
WHITE = "#FFFFFF"
HOLES, HOLE, HOLE_GAP = 8, 10, 16


def dpad_key(d, k, cx, cy, pressed):
    off = 4 if pressed else 0
    card(d, k, cx - KEY // 2 + off, cy - KEY // 2 + off, KEY, KEY, WHITE, r=8, bw=4,
         shadow=0 if pressed else 4)


def draw_board(c: Canvas, pressed=None, led=False):
    def paint(d, k):
        card(d, k, BX, BY, BW, BH, YELLOW, r=48, bw=6, shadow=14)
        # the screen's bezel
        card(d, k, SX - BEZ, SY - BEZ, SCR + 2 * BEZ, SCR + 2 * BEZ, INK, r=12, bw=0, shadow=0)
        # D-pad
        cx, cy = DPAD
        g = KEY + 2
        for name, (dx, dy) in (("up", (0, -g)), ("left", (-g, 0)), ("right", (g, 0)), ("down", (0, g))):
            dpad_key(d, k, cx + dx, cy + dy, pressed == name)
        # B and A
        for name, (bx, by) in (("b", B_BTN), ("a", A_BTN)):
            off = 4 if pressed == name else 0
            disc(d, k, bx + off, by + off, 25, WHITE, bw=5, shadow=0 if pressed == name else 5)
        # the two small buttons under the screen
        for i in (-1, 1):
            card(d, k, BX + BW // 2 + i * 50 - 22, SY + SCR + BEZ + 14, 44, 18, WHITE, r=9, bw=4, shadow=3)
        # status LED, and the expansion port's holes, centred over the screen
        disc(d, k, RIGHT_X + 22, SY + 4, 9, MINT if led else CREAM, bw=3, shadow=0)
        hx = SX + (SCR - (HOLES * HOLE_GAP - (HOLE_GAP - HOLE))) // 2
        for i in range(HOLES):
            card(d, k, hx + i * HOLE_GAP, BY + 16, HOLE, HOLE, CREAM, r=2, bw=2, shadow=0)
    c.shapes(paint)


LX, LY = 60, 52                             # the left column's corner
COL_W = 560                                 # the left column's width


def draw_static(c: Canvas):
    """Everything but the board, the screen and the logo's rainbow; returns
    the rainbow's mask (full size)."""
    # dotted paper
    dots = np.zeros((H, W), dtype=bool)
    for dy in (0, 1):
        for dx in (0, 1):
            dots[12 + dy::24, 12 + dx::24] = True
    c.mask(dots, 0, 0, DOTS)

    # the badge, with a hard shadow
    logo = Image.open(OUT / "logo.png").convert("RGBA")
    a = np.array(logo)[:, :, 3] > 128
    c.mask(a, LX + 10, LY + 10, INK)
    c.image(logo, LX, LY)

    # the pixel logo beside it: ink now, the rainbow per frame
    ink, accent = (scaled(m, LOGO_S) for m in pixel_logo())
    wx = LX + logo.width + 26
    wy = LY + (logo.height - ink.shape[0]) // 2
    c.mask(ink, wx, wy, INK)
    turning = np.zeros((H, W), dtype=bool)
    turning[wy:wy + accent.shape[0], wx:wx + accent.shape[1]] = accent

    # what it is
    face = Face(BITRIMUS)
    y = LY + logo.height + 34
    for line in ("The lowest-cost game system.", "Program it in Arduino."):
        m = scaled(face.mask(line), 3)
        c.mask(m, LX, y, INK)
        y += m.shape[0] + 10

    # pills, in rows that fit the column
    ph, gap = 50, 16
    pills, x, py = [], LX, y + 18
    for label, fill in (("RISC-V", LAVENDER), ("128x128", MINT), ("20 GAMES INCLUDED", SAGE)):
        m = scaled(face.mask(label), 3)
        w = m.shape[1] + 40
        if x > LX and x + w > LX + COL_W:
            x, py = LX, py + ph + gap
        pills.append((x, py, w, m, fill))
        x += w + gap + 2

    def pill_shapes(d, k):
        for x, py, w, m, fill in pills:
            card(d, k, x, py, w, ph, fill, r=ph // 2, bw=4, shadow=5)
    c.shapes(pill_shapes)
    for x, py, w, m, fill in pills:
        c.mask(m, x + 20, py + (ph - 21) // 2 - 3, INK)

    # a frame round it all
    def frame(d, k):
        d.rectangle([0, 0, k * W - 1, k * H - 1], outline=rgb(INK), width=k * 6)
    c.shapes(frame)
    return turning


def cover(path):
    im = Image.open(path).convert("RGB")
    if im.size != (128, 128):
        sys.exit(f"{path}: {im.size}, not 128x128")
    return im.resize((SCR, SCR), Image.Resampling.NEAREST)


# Timing (ms). DOWN brings the next game's box art up from the bottom, as the
# visual menu does (platform/bootloader/src/lcd.c, lcd_slide): the new picture
# rises over the old one in steps.
SPLASH_MS, HOLD_MS, STEP_MS = 2400, 1200, 60
SLIDE = (32, 64, 96)                        # rows of the new picture shown (of 128)
TICK_MS = 150                               # the rainbow moves this often
TURN_MS = 3800                              # about one turn of the wheel, as on the device


def banner_frames():
    """[(RGB image, ms)]: the splash, then each cover rising after a press of
    DOWN; the logo's magenta turns through the rainbow all the while."""
    base = Canvas(W, H, PAPER)
    turning = draw_static(base)
    states = {}
    for pressed in (False, True):
        c = Canvas(W, H, PAPER)
        c.im = base.im.copy()
        draw_board(c, pressed="down" if pressed else None, led=pressed)
        states[pressed] = c.im
    covers = [cover(p) for p in cover_paths()]

    # the timeline: (screen picture, DOWN held, ms)
    steps = []

    def hold(pic, ms):
        while ms > 0:
            steps.append((pic, False, min(TICK_MS, ms)))
            ms -= TICK_MS

    hold(covers[0], SPLASH_MS)
    order = list(range(1, len(covers))) + [0]
    prev = covers[0]
    for i in order:
        new = covers[i]
        for rows in SLIDE:
            pic = prev.copy()
            pic.paste(new.crop((0, 0, SCR, rows * 2)), (0, SCR - rows * 2))
            steps.append((pic, True, STEP_MS))
        steps.append((new, True, STEP_MS))
        steps.append((new, False, STEP_MS))
        hold(new, HOLD_MS - 2 * STEP_MS)
        prev = new

    # The rainbow moves only while the screen is still: a frame that changed
    # both the logo and the screen would be stored as one rectangle round
    # both, text and all.
    still = [i > 0 and steps[i][0] is steps[i - 1][0] and steps[i][1] == steps[i - 1][1]
             for i in range(len(steps))]
    total = sum(ms for (_, _, ms), s in zip(steps, still) if s)
    turn = total / max(1, round(total / TURN_MS))     # a whole number of turns a loop
    mask = Image.fromarray((turning * 255).astype(np.uint8))
    frames, t = [], 0
    for (pic, down, ms), moving in zip(steps, still):
        if moving:
            t += ms
        im = states[down].copy()
        im.paste(pic, (SX, SY))
        im.paste(rainbow(t / turn), (0, 0), mask)
        frames.append((im, ms))
    return frames


def social_png(path):
    """GitHub's social preview, 1280 x 640: the banner's opening picture (the
    logo in its own magenta) on the same dotted paper, framed again. GitHub takes it only through the
    repository's Settings, so it is uploaded by hand."""
    b = Canvas(W, H, PAPER)
    turning = draw_static(b)
    draw_board(b)
    b.image(cover(cover_paths()[0]), SX, SY)
    b.mask(turning, 0, 0, "#FF00FF")         # the logo's own magenta, still
    first = b.im
    c = Canvas(W, 640, PAPER)
    dots = np.zeros((640, W), dtype=bool)
    for dy in (0, 1):
        for dx in (0, 1):
            dots[12 + dy::24, 12 + dx::24] = True
    c.mask(dots, 0, 0, DOTS)
    c.im.paste(first.crop((6, 6, W - 6, H - 6)), (6, 80 + 6))

    def frame(d, k):
        d.rectangle([0, 0, k * W - 1, k * 640 - 1], outline=rgb(INK), width=k * 6)
    c.shapes(frame)
    c.im.save(path, optimize=True)


def write_gif(frames, path):
    """Each frame quantised on its own (none needs more than 256 colours);
    Pillow writes only what changed."""
    ims, durs = [], []
    for im, ms in frames:
        n = len(im.getcolors(1 << 16) or [])
        if not n or n > 256:
            p = im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        else:
            p = im.quantize(n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        ims.append(p)
        durs.append(ms)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, optimize=False,
                disposal=1)


# ---------------------------------------------------------------- buttons

BUTTONS = [
    # file, label, icon, fill
    ("btn-website", "chgame.website", "globe", YELLOW),
    ("btn-start", "Get started", "play", LAVENDER),
    ("btn-docs", "API docs", "page", MINT),
    ("btn-shop", "Buy one", "basket", SAGE),
    ("btn-forum", "Forum", "chat", CREAM),
]


def runs_path(m, ox, oy, s):
    """An SVG path of a mask: one rectangle per horizontal run."""
    out = []
    for y in range(m.shape[0]):
        row = m[y]
        x = 0
        while x < len(row):
            if row[x]:
                x0 = x
                while x < len(row) and row[x]:
                    x += 1
                out.append(f"M{ox + x0 * s} {oy + y * s}h{(x - x0) * s}v{s}h{-(x - x0) * s}z")
            else:
                x += 1
    return "".join(out)


def button_svg(label, icon, fill, s=2, h=44, bw=3, sh=4, r=10):
    face = Face(BITRIMUS)
    t = face.mask(label)
    ic = ICONS[icon]
    pad, gap = 12, 8
    w = pad + ic.shape[1] * s + gap + t.shape[1] * s + pad
    ty = (h - t.shape[0] * s) // 2 + 1
    iy = (h - ic.shape[0] * s) // 2
    W_, H_ = w + sh, h + sh
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" '
        f'role="img" aria-label="{label}"><title>{label}</title>'
        f'<rect x="{sh + bw / 2}" y="{sh + bw / 2}" width="{w - bw}" height="{h - bw}" rx="{r}" fill="{INK}" '
        f'stroke="{INK}" stroke-width="{bw}"/>'
        f'<rect x="{bw / 2}" y="{bw / 2}" width="{w - bw}" height="{h - bw}" rx="{r}" fill="{fill}" '
        f'stroke="{INK}" stroke-width="{bw}"/>'
        f'<path fill="{INK}" shape-rendering="crispEdges" d="'
        + runs_path(ic, pad, iy, s) + runs_path(t, pad + ic.shape[1] * s + gap, ty, s)
        + '"/></svg>\n'
    )


def wordmark_svg(s=3):
    """The pixel logo for the API reference's header: its ink, and the
    device's magenta held still in the brand's yellow."""
    ink, accent = pixel_logo()
    W_, H_ = ink.shape[1] * s, ink.shape[0] * s
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" '
            f'role="img" aria-label="CHGame"><title>CHGame</title>'
            f'<path fill="{YELLOW}" shape-rendering="crispEdges" d="{runs_path(accent, 0, 0, s)}"/>'
            f'<path fill="{INK}" shape-rendering="crispEdges" d="{runs_path(ink, 0, 0, s)}"/></svg>\n')


# ---------------------------------------------------------------- the warning

WARNING_TITLE = "IN DEVELOPMENT: REV0 HARDWARE"
WARNING_LINES = ["CHGame is in active development.",
                 "This board is Rev0, Rev1 will change the button wiring."]

ICON_WARN = art("""
    .....##.....
    ....####....
    ....####....
    ...##..##...
    ...##..##...
    ..###..###..
    ..###..###..
    .##########.
    .####..####.
    ############
""")


def warning_svg(w=820):
    """The README's caution panel: hazard tape along the top, dotted paper below
    (the banner's),
    ink outline and hard shadow, pixel lettering."""
    face = Face(BITRIMUS)
    title = face.mask(WARNING_TITLE)
    lines = [face.mask(t) for t in WARNING_LINES]
    tape, pad, bw, sh, r = 18, 22, 3, 6, 12
    icon_s, ts, bs = 5, 3, 2
    icon_w = ICON_WARN.shape[1] * icon_s
    tx = pad + icon_w + 24
    ty = tape + 18
    body_y = ty + title.shape[0] * ts + 10
    h = body_y + len(lines) * (lines[0].shape[0] * bs + 6) + 14
    W_, H_ = w + sh, h + sh
    dots = (f'<pattern id="d" width="24" height="24" patternUnits="userSpaceOnUse">'
            f'<rect x="12" y="12" width="2" height="2" fill="{DOTS}"/></pattern>')   # the banner's dotted paper
    clip = dots + f'<clipPath id="c"><rect x="{bw / 2}" y="{bw / 2}" width="{w - bw}" height="{h - bw}" rx="{r}"/></clipPath>'
    stripes = "".join(f'<path d="M{x} {tape}L{x + tape} 0h14L{x + 14} {tape}z" fill="{INK}"/>'
                      for x in range(-tape, w + tape, 28))
    body = runs_path(title, tx, ty, ts) + "".join(
        runs_path(m, tx, body_y + i * (m.shape[0] * bs + 6), bs) for i, m in enumerate(lines))
    iy = (h + tape - ICON_WARN.shape[0] * icon_s) // 2
    alt = WARNING_TITLE + ". " + " ".join(WARNING_LINES)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" '
        f'role="img" aria-label="{alt}"><title>{alt}</title><defs>{clip}</defs>'
        f'<rect x="{sh + bw / 2}" y="{sh + bw / 2}" width="{w - bw}" height="{h - bw}" rx="{r}" fill="{INK}"/>'
        f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{PAPER}"/>'
        f'<rect width="{w}" height="{h}" fill="url(#d)"/>'
        f'<rect width="{w}" height="{tape}" fill="{YELLOW}"/>{stripes}'
        f'<rect y="{tape}" width="{w}" height="{bw}" fill="{INK}"/></g>'
        f'<rect x="{bw / 2}" y="{bw / 2}" width="{w - bw}" height="{h - bw}" rx="{r}" fill="none" '
        f'stroke="{INK}" stroke-width="{bw}"/>'
        f'<path fill="{YELLOW}" shape-rendering="crispEdges" d="{runs_path(ICON_WARN, pad + icon_s, iy + icon_s, icon_s)}"/>'
        f'<path fill="{INK}" shape-rendering="crispEdges" d="{runs_path(ICON_WARN, pad, iy, icon_s)}{body}"/>'
        '</svg>\n')


# ---------------------------------------------------------------- XOXO

TICTACTOE = EXAMPLES / "Games/CHTicTacToe/tools/art/pieces"
XOXO_S = 3                                  # pixel scale
XOXO_MS = 90                                # a step of the spin
XOXO_PHASE = [0, 2, 1, 3]                   # each letter starts at a different step of its turn


def xoxo_frames():
    """CHTicTacToe's held X and O, spinning without stop as they do in the
    glove (its Iso.cpp spin(): front, a quarter turn, edge on, the quarter
    mirrored; each shape repeats every half turn), spelling XOXO, each
    letter at its own step of the turn."""
    def load(n):
        im = Image.open(TICTACTOE / f"{n}.png").convert("RGBA")
        ax, ay = (int(v) for v in (TICTACTOE / f"{n}.anchor").read_text().split())
        return im, ax, ay
    sets = {k: [load(f"{k}_l"), load(f"{k}_l1"), load(f"{k}_l2")] for k in "xo"}

    def step(k, i):
        im, ax, ay = sets[k][1 if i == 3 else i]
        if i == 3:
            im, ax = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT), im.width - 1 - ax
        return im, ax, ay

    # room for every frame: the highest top and the lowest bottom about the
    # pieces' common base line, and a pixel to spare
    up = max(ay for v in sets.values() for _, _, ay in v)
    down = max(im.height - ay for v in sets.values() for im, _, ay in v)
    pitch = 32
    base, h, w = up + 1, up + down + 2, 4 * pitch + 4
    frames = []
    for f in range(4):
        c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for n, k in enumerate("xoxo"):
            im, ax, ay = step(k, (f + XOXO_PHASE[n]) % 4)
            c.alpha_composite(im, (pitch // 2 + 2 + n * pitch - ax, base - ay))
        frames.append(c.resize((c.width * XOXO_S, c.height * XOXO_S), Image.Resampling.NEAREST))
    return frames


def write_xoxo(path):
    """A transparent GIF with one palette for every frame, so the
    transparent colour is the same index throughout and never shows."""
    key = (1, 254, 3)
    keyed = []
    for f in xoxo_frames():
        bg = Image.new("RGB", f.size, key)
        bg.paste(f, (0, 0), f.split()[3].point(lambda a: 255 if a > 127 else 0))
        keyed.append(bg)
    strip = Image.new("RGB", (keyed[0].width, keyed[0].height * len(keyed)))
    for i, k in enumerate(keyed):
        strip.paste(k, (0, i * k.height))
    pal = strip.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    ims = [k.quantize(palette=pal, dither=Image.Dither.NONE) for k in keyed]
    flat = pal.getpalette()[:768]
    t = next(i for i in range(len(flat) // 3) if tuple(flat[3 * i:3 * i + 3]) == key)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=XOXO_MS, loop=0,
                disposal=2, transparency=t, optimize=False)


def swatches_svg():
    face = Face(BITRIMUS)
    cw, ch, gap, s = 132, 104, 18, 2
    W_ = len(PALETTE) * (cw + gap) - gap + 6
    H_ = ch + 6
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" '
             f'role="img" aria-label="The CHGame palette"><title>The CHGame palette</title>']
    for i, (name, hexv) in enumerate(PALETTE):
        x = i * (cw + gap)
        parts.append(f'<rect x="{x + 6 + 1.5}" y="{6 + 1.5}" width="{cw - 3}" height="{ch - 3}" rx="10" '
                     f'fill="{INK}"/>')
        parts.append(f'<rect x="{x + 1.5}" y="1.5" width="{cw - 3}" height="{ch - 3}" rx="10" fill="{hexv}" '
                     f'stroke="{INK}" stroke-width="3"/>')
        fg = CREAM if name == "Ink" else INK
        for j, s_ in enumerate((name, hexv.upper())):
            m = face.mask(s_)
            parts.append(f'<path fill="{fg}" shape-rendering="crispEdges" d="'
                         + runs_path(m, x + 14, 52 + j * 24, s) + '"/>')
    parts.append("</svg>\n")
    return "".join(parts)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", nargs="*", default=["banner", "buttons", "wordmark", "warning", "xoxo", "swatches", "social"])
    ap.add_argument("--still", help="write one frame of the banner as a PNG here instead")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if "banner" in a.what:
        frames = banner_frames()
        if a.still:
            frames[0][0].save(a.still)
            print(a.still)
        else:
            p = OUT / "banner.gif"
            write_gif(frames, p)
            print(f"{p.relative_to(ROOT).as_posix()}: {len(frames)} frames, {p.stat().st_size:,} B")
    if "buttons" in a.what:
        for name, label, icon, fill in BUTTONS:
            p = OUT / f"{name}.svg"
            p.write_text(button_svg(label, icon, fill), encoding="utf-8", newline="\n")
        print(f"docs/brand/btn-*.svg: {len(BUTTONS)} buttons")
    if "social" in a.what:
        p = OUT / "social.png"
        social_png(p)
        print(f"{p.relative_to(ROOT).as_posix()}: {p.stat().st_size:,} B")
    if "xoxo" in a.what:
        p = OUT / "xoxo.gif"
        write_xoxo(p)
        print(f"{p.relative_to(ROOT).as_posix()}: {p.stat().st_size:,} B")
    for what, name, svg in (("wordmark", "wordmark.svg", wordmark_svg), ("warning", "warning.svg", warning_svg),
                            ("swatches", "palette.svg", swatches_svg)):
        if what in a.what:
            p = OUT / name
            p.write_text(svg(), encoding="utf-8", newline="\n")
            print(p.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
