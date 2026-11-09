"""pixkit: the game's drawing on the PC, for mockups and asset previews.

A 128x128 framebuffer of palette indices with Python versions of the
primitives the game uses: CHGfx's hline/rect/ellipse/dither and text,
and the game's own fillRound/roundRect/panel, text35/text35x2, the
outlined-letter masks and the banner. The 3x5 font is parsed out of the
CHGame library (platform/board/arduino/CHGame/libraries/CHGame/src/chgame/Draw.cpp), so the two
can't drift apart.
"""
import math
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent                  # the repository's tools/
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import artlib  # noqa: E402

# Palette (RGB444), the same 16 slots as CHBlackjack and CHChess.
PALETTE = [0x000, 0xFFF, 0x042, 0x173, 0x4B5, 0xBBC, 0xE12, 0x702,
           0xFC2, 0x741, 0x26E, 0x125, 0xFB8, 0x6EF, 0xF0F, 0xFC2]
NAMES = ["INK", "WHITE", "FELT_DK", "FELT", "FELT_LT", "SILVER", "RED", "WINE",
         "GOLD", "WOOD", "BLUE", "NAVY", "SKIN", "CYAN", "FX_A", "FX_B"]
(INK, WHITE, FELT_DK, FELT, FELT_LT, SILVER, RED, WINE,
 GOLD, WOOD, BLUE, NAVY, SKIN, CYAN, FX_A, FX_B) = range(16)

# The animated slots, frozen for a still: FX_A one step of the rainbow,
# FX_B part way up its gold-to-white pulse.
RAINBOW = [0xF22, 0xF82, 0xFE2, 0x8F2, 0x2F4, 0x2FC, 0x2EF, 0x28F,
           0x42F, 0xA2F, 0xF2E, 0xF28]
FX_B_FRAME = 0xFE9

RAIN = [RED, GOLD, FELT_LT, CYAN, BLUE]          # fx::RAIN, the casino rainbow


def rgb(c444):
    return ((c444 >> 8) & 15) * 17, ((c444 >> 4) & 15) * 17, (c444 & 15) * 17


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
def _font35():
    """The CHGame library's 3x5 font: one glyph (3 column bytes) per
    character from '!' to 'z', blank where there is none."""
    src = REPO / "platform/board/arduino/CHGame/libraries/CHGame/src/chgame/Draw.cpp"
    text = re.sub(r"//[^\n]*", "", src.read_text(encoding="utf-8"))
    body = text[text.index("FONT35[FONT35_LAST - FONT35_FIRST + 1][3]"):]
    body = body[:body.index("};")]
    glyphs = [tuple(int(v, 16) for v in g)
              for g in re.findall(r"\{(0x[0-9A-Fa-f]+),(0x[0-9A-Fa-f]+),(0x[0-9A-Fa-f]+)\}", body)]
    assert len(glyphs) == ord("z") - ord("!") + 1, len(glyphs)
    return glyphs


FONT35 = _font35()


UPPER35 = False         # set_upper35(True): lower case drawn as capitals (CHWordWheel upper-cases its text)


def set_upper35(on):
    global UPPER35
    UPPER35 = on


def glyph35(ch):
    """Index into FONT35, -1 = none."""
    o = ord(ch)
    if UPPER35 and 97 <= o <= 122:
        o -= 32
    return o - 33 if 33 <= o <= 122 else -1


def _font57():
    """CHGfx's 5x7 font, from the installed library (found as the simulator
    finds it: $CHSIM_CHGFX, or the Arduino sketchbook's libraries)."""
    sys.path.insert(0, str(HERE / "chsim"))
    from chsim import chgfx_dir  # noqa: E402
    text = (chgfx_dir() / "CHGfx_font.h").read_text(encoding="utf-8")
    body = text[text.index("chgfx_font5x7"):]
    body = body[body.index("{") + 1:body.index("};")]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    vals = [int(v, 16) for v in re.findall(r"0x[0-9A-Fa-f]+", body)]
    return [vals[i:i + 5] for i in range(0, len(vals), 5)]


FONT57 = _font57()


def text35_width(s):
    w = best = 0
    for ch in s:
        if ch == "\n":
            best = max(best, w)
            w = 0
        else:
            w += 2 if ch == "~" else 4
    best = max(best, w)
    return best - 1 if best else 0


def text57_width(s):
    return 6 * max(len(line) for line in s.split("\n"))


# ---------------------------------------------------------------------------
# Framebuffer
# ---------------------------------------------------------------------------
INSET = [[1], [2, 1], [3, 1, 1], [4, 2, 1, 1]]


def ellipse_rows(rx, ry):
    """CHGfx's EllipseRows: the half-width of each row 0..ry below centre."""
    rx2, ry2, x = rx * rx, ry * ry, rx
    out = []
    for dy in range(ry + 1):
        if not ry:
            out.append(x)
            continue
        lim = rx2 * (ry2 - dy * dy + (ry >> 1))
        while x and x * x * ry2 > lim:
            x -= 1
        out.append(x)
    return out


class FB:
    W = H = 128

    def __init__(self, fill=INK):
        self.p = bytearray([fill]) * (128 * 128)
        self.clip = (0, 0, 128, 128)                    # x0, y0, x1, y1

    # --- CHGfx primitives -------------------------------------------------
    def set_clip(self, x, y, w, h):
        self.clip = (max(0, x), max(0, y), min(128, x + w), min(128, y + h))

    def reset_clip(self):
        self.clip = (0, 0, 128, 128)

    def clear(self, c):
        self.p[:] = bytes([c]) * len(self.p)

    def pixel(self, x, y, c):
        x0, y0, x1, y1 = self.clip
        if x0 <= x < x1 and y0 <= y < y1:
            self.p[y * 128 + x] = c

    def get(self, x, y):
        return self.p[y * 128 + x]

    def hline(self, x, y, w, c):
        x0, y0, x1, y1 = self.clip
        if not (y0 <= y < y1):
            return
        a, b = max(x, x0), min(x + w, x1)
        if a < b:
            self.p[y * 128 + a:y * 128 + b] = bytes([c]) * (b - a)

    def vline(self, x, y, h, c):
        for yy in range(y, y + h):
            self.pixel(x, yy, c)

    def fill_rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            self.hline(x, yy, w, c)

    def rect(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def fill_ellipse(self, cx, cy, rx, ry, c):
        for dy, hw in enumerate(ellipse_rows(rx, ry)):
            self.hline(cx - hw, cy + dy, 2 * hw + 1, c)
            if dy:
                self.hline(cx - hw, cy - dy, 2 * hw + 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        rows = ellipse_rows(rx, ry)
        for dy in range(ry + 1):
            hw = rows[dy]
            if dy == ry:
                self.hline(cx - hw, cy + dy, 2 * hw + 1, c)
                if dy:
                    self.hline(cx - hw, cy - dy, 2 * hw + 1, c)
                break
            below = rows[dy + 1]
            a = min(below + 1, hw)
            n = hw - a + 1
            for sy in ((cy + dy, cy - dy) if dy else (cy,)):
                self.hline(cx + a, sy, n, c)
                self.hline(cx - hw, sy, n, c)

    def dither(self, x, y, w, h, c, phase=0):
        """Pixels where x + y + phase is even get the colour."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if not ((xx + yy + phase) & 1):
                    self.pixel(xx, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.pixel(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    # --- the games' own primitives -------------------------------------------
    def fill_round(self, x, y, w, h, r, c):
        r = min(r, 4, h // 2)
        ins = INSET[r - 1 if r else 0]
        for i in range(r):
            self.hline(x + ins[i], y + i, w - 2 * ins[i], c)
            self.hline(x + ins[i], y + h - 1 - i, w - 2 * ins[i], c)
        self.fill_rect(x, y + r, w, h - 2 * r, c)

    def round_rect(self, x, y, w, h, r, c):
        r = min(r, 4, h // 2)
        if not r:
            self.rect(x, y, w, h, c)
            return
        ins = INSET[r - 1]
        self.hline(x + ins[0], y, w - 2 * ins[0], c)
        self.hline(x + ins[0], y + h - 1, w - 2 * ins[0], c)
        for i in range(1, r):
            n = max(1, ins[i - 1] - ins[i])
            self.hline(x + ins[i], y + i, n, c)
            self.hline(x + w - ins[i] - n, y + i, n, c)
            self.hline(x + ins[i], y + h - 1 - i, n, c)
            self.hline(x + w - ins[i] - n, y + h - 1 - i, n, c)
        self.vline(x, y + r, h - 2 * r, c)
        self.vline(x + w - 1, y + r, h - 2 * r, c)

    def panel(self, x, y, w, h, r, fill, edge):
        self.fill_round(x, y, w, h, r, fill)
        self.round_rect(x, y, w, h, r, edge)

    def glyph(self, x, y, cols, c):
        for i, bits in enumerate(cols):
            yy = y
            while bits:
                if bits & 1:
                    self.pixel(x + i, yy, c)
                bits >>= 1
                yy += 1

    def text35(self, x, y, s, c):
        x0 = x
        for ch in s:
            if ch == "\n":
                x = x0
                y += 7
                continue
            if ch == "~":
                x += 2
                continue
            g = glyph35(ch)
            if g >= 0:
                self.glyph(x, y, FONT35[g], c)
            x += 4
        return x - x0

    def text35x2(self, x, y, s, c):
        x0 = x
        for ch in s:
            if ch == "\n":
                x = x0
                y += 14
                continue
            if ch == "~":
                x += 4
                continue
            g = glyph35(ch)
            if g >= 0:
                for col in range(3):
                    bits, row = FONT35[g][col], 0
                    while bits:
                        if bits & 1:
                            self.fill_rect(x + col * 2, y + row * 2, 2, 2, c)
                        bits >>= 1
                        row += 1
            x += 8

    def text57(self, x, y, s, c):
        for ch in s:
            o = ord(ch)
            if not 32 <= o <= 126:
                o = ord("?")
            self.glyph(x, y, FONT57[o - 32], c)
            x += 6

    def centred35(self, y, s, c, cx=64):
        self.text35(cx - text35_width(s) // 2, y, s, c)

    def centred57(self, y, s, c, cx=64):
        self.text57(cx - text57_width(s) // 2, y, s, c)

    # --- sprites ------------------------------------------------------------
    def sprite(self, spr, x, y, remap=None):
        for j, row in enumerate(spr):
            for i, v in enumerate(row):
                if v is not None:
                    self.pixel(x + i, y + j, remap[v] if remap else v)

    def dither_rect_row(self, *a):                       # unused helper slot
        raise NotImplementedError

    # --- output -------------------------------------------------------------
    def image(self, scale=3, fx_a=RAINBOW[6], fx_b=FX_B_FRAME):
        pal = [rgb(c) for c in PALETTE]
        pal[FX_A], pal[FX_B] = rgb(fx_a), rgb(fx_b)
        im = Image.new("RGB", (128, 128))
        im.putdata([pal[v] for v in self.p])
        return im.resize((128 * scale, 128 * scale), Image.NEAREST) if scale != 1 else im

    def save(self, path, scale=3, **kw):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.image(scale, **kw).save(path)


def load_png(path):
    """A palette-exact PNG as rows of palette indices (None = transparent)."""
    im = Image.open(path).convert("RGBA")
    lut = {rgb(c): i for i, c in enumerate(PALETTE[:15])}
    rows = []
    for y in range(im.height):
        row = []
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a < 128:
                row.append(None)
                continue
            if (r, g, b) not in lut:
                raise ValueError(f"{path}: off-palette pixel {(r, g, b)} at {x},{y}")
            row.append(lut[(r, g, b)])
        rows.append(row)
    return rows


DEALER = load_png(artlib.COMMON / "dealer.png")      # CHBlackjack's dealer, CHChess's glove: the shared art
HAND = load_png(artlib.COMMON / "hand.png")
HAND_TIP = 5

# Sprite remaps (16 entries, art colour -> screen colour).
RM_ID = list(range(16))
RM_CPU = RM_ID[:]
RM_CPU[GOLD], RM_CPU[WOOD] = RED, WINE                    # the croupier's red cuff
RM_ALERT = RM_ID[:]
RM_ALERT[WHITE], RM_ALERT[SILVER], RM_ALERT[GOLD], RM_ALERT[WOOD] = RED, WINE, RED, WINE


# ---------------------------------------------------------------------------
# Masks: big outlined, shadowed, gradient lettering (the CHGame library's chgame/Mask.cpp)
# ---------------------------------------------------------------------------
class Mask:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.bits = [[0] * (w + 2) for _ in range(h + 2)]   # 1 px margin

    def plot(self, x, y, scale=1):
        for j in range(scale):
            for i in range(scale):
                xx, yy = x + 1 + i, y + 1 + j
                if 0 <= xx < self.w + 2 and 0 <= yy < self.h + 2:
                    self.bits[yy][xx] = 1

    def text35(self, x, y, s, scale=1, dy=None):
        for k, ch in enumerate(s):
            if ch == "~":
                x += 2 * scale
                continue
            g = glyph35(ch)
            oy = y + (dy[k] if dy else 0)
            if g >= 0:
                for col in range(3):
                    for row in range(6):
                        if FONT35[g][col] & (1 << row):
                            self.plot(x + col * scale, oy + row * scale, scale)
            x += 4 * scale

    def blit(self, rows, x=0, y=0):
        """rows: strings, '#' set."""
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#":
                    self.plot(x + i, y + j)

    def draw(self, fb, x, y, fill, outline=-1, shadow=-1, ramp=None):
        rows, cols = self.h + 2, self.w + 2
        ox, oy = x - 1, y - 1

        def at(r, c):
            return 0 <= r < rows and 0 <= c < cols and self.bits[r][c]

        for r in range(rows):
            grown = [any(at(r + a, c + b) for a in (-1, 0, 1) for b in (-1, 0, 1))
                     for c in range(cols)] if outline >= 0 else self.bits[r]
            if shadow >= 0:
                for c in range(cols):
                    if grown[c]:
                        fb.pixel(ox + 1 + c, oy + r + 1, shadow)
            if outline >= 0:
                for c in range(cols):
                    if grown[c]:
                        fb.pixel(ox + c, oy + r, outline)
            if 0 < r < rows - 1:
                col = ramp[r - 1] if ramp else fill
                for c in range(cols):
                    if self.bits[r][c]:
                        fb.pixel(ox + c, oy + r, col)


def isin(a):
    """fx::isin: a in 1/256 turns, -255..255 (the device's table is uint8,
    so it tops out at 255 for a = 62..66; checked equal for every a)."""
    return max(-255, min(255, int(round(math.sin(a * 2 * math.pi / 256) * 256))))


B_RAINBOW, B_GOLD, B_RED, B_CYAN, B_WHITE, B_BLACK, B_GREEN = range(7)


def banner(fb, text, style, cy, t=12):
    """fx::drawBanner at frame t of the banner (t >= 7: settled at scale 3)."""
    scale = 2 if t < 3 else (4 if t < 7 else 3)
    w = text35_width(text) * scale
    while w > 124 and scale > 2:
        scale -= 1
        w = text35_width(text) * scale
    h = 6 * scale
    dy = [((isin(t * 10 + k * 36) * 2) >> 8) + 2 for k in range(len(text))]
    m = Mask(w + 1, h + 5)
    m.text35(0, 0, text, scale, dy)
    ramp = []
    for r in range(h + 5):
        if style == B_RAINBOW:
            ramp.append(RAIN[((r // 2) + t // 3) % 5])
        elif style == B_GOLD:
            ramp.append(FX_B if r < 3 else (GOLD if r < h // 2 + 6 else WOOD))
        elif style == B_RED:
            ramp.append(WHITE if r < 3 else RED)
        elif style == B_CYAN:
            ramp.append(WHITE if r < 3 else CYAN)
        elif style == B_BLACK:
            ramp.append(WHITE if r < 3 else (SILVER if r < h // 2 + 3 else NAVY))
        elif style == B_GREEN:
            ramp.append(WHITE if r < 3 else (FELT_LT if r < h // 2 + 6 else FELT))
        else:
            ramp.append(WHITE)
    outline = FX_A if style == B_RAINBOW else INK
    shadow = INK if style == B_RAINBOW else WINE
    m.draw(fb, 64 - w // 2, cy - h // 2 - 2, 0, outline, shadow, ramp)


def title35(fb, text, y, scale, top, mid, low, shadow, low_from):
    """CHChess's title35: masked lettering sized to the text."""
    w = text35_width(text) * scale
    h = 5 * scale
    m = Mask(w, h + scale)
    m.text35(0, 0, text, scale)
    ramp = [top if i < scale else (mid if i < low_from else low) for i in range(h + scale + 2)]
    m.draw(fb, 64 - w // 2, y, mid, INK, shadow, ramp)
    return w


# ---------------------------------------------------------------------------
# Chips (the casino chip family: tools/art/common/chip_*.txt, as the games draw them)
# ---------------------------------------------------------------------------
CHIP_BODY = [WHITE, RED, BLUE, FELT_LT, INK]
CHIP_EDGE = [BLUE, WHITE, WHITE, WHITE, GOLD]
CHIP_SHADE = [SILVER, WINE, NAVY, FELT_DK, INK]
CHIP_LABEL = [WHITE, SKIN, CYAN, WHITE, NAVY]
CHIP_VALUE = [1, 5, 10, 25, 100]
_CHIP_ART = {}


def chip_denom(amount):
    for i in range(4, -1, -1):
        if amount >= CHIP_VALUE[i]:
            return i
    return 0


def _chip_art(name):
    if name not in _CHIP_ART:
        text = (artlib.COMMON / f"{name}.txt").read_text(encoding="utf-8")
        _CHIP_ART[name] = [ln.rstrip() for ln in text.splitlines() if ln and not ln.startswith("#")]
    return _CHIP_ART[name]


def chip(fb, cx, y, d, top=True):
    """The 15 px chip: its sprite's placeholder letters (w body, u inserts, s
    shade, c label, k ink) in denomination d's colours; a stack's lower chips
    alternate two cuts by row, as in the games."""
    role = {"w": CHIP_BODY[d], "u": CHIP_EDGE[d], "s": CHIP_SHADE[d], "c": CHIP_LABEL[d], "k": INK}
    if top:
        name, x0, y0 = "chip_top", cx - 7, y - 1
    else:
        name, x0, y0 = ("chip_side_alt" if (y >> 1) & 1 else "chip_side"), cx - 7, y + 1
    for j, row in enumerate(_chip_art(name)):
        for i, ch in enumerate(row):
            if ch in role:
                fb.pixel(x0 + i, y0 + j, role[ch])


def chip_stack(fb, cx, base_y, amount, max_chips=10):
    chips = []
    for d in range(4, -1, -1):
        while amount >= CHIP_VALUE[d] and len(chips) < 24:
            chips.append(d)
            amount -= CHIP_VALUE[d]
    first = max(0, len(chips) - max_chips)
    for i in range(first, len(chips)):
        chip(fb, cx, base_y - 2 * (i - first), chips[i], i == len(chips) - 1)
