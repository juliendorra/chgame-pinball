"""tools/sdcard/art/cards.png: the CARDS folder's cover on the casino card
(it holds Blackjack, Poker, Solitaire). `python tools/sdcard/covers.py`
redraws it; edit this, not the PNG. The folders' shared look is
folderkit.py, beside this file (this picture is its worked example).

THE BRIEF (revision 1)
  Message: card games inside. A winning hand of aces, and the ace of
  spades leaping out of it at you.

  Composition (a folder: a sign over a door, then the one object that
  says what is inside; read in this order):
  - The sign: CARDS in the family's ice chrome on its navy panel and
    rainbow neon tube, rows 1 to 48 (folderkit.word). Calm night round it.
  - The hero: the ace of spades, 1.5 times a hand card's size, flicked out
    of the hand toward the viewer. It leans right 1:4 and is turned out of
    the picture's plane (its top tipped toward us, its left side away),
    seen in perspective, and it breaks the right and bottom frames. Its
    face is the brightest thing in the picture: cream where the key light
    falls (top left), bowing to bone and a warm tan at the right and foot,
    a glossy sheen across it. The index (A over a spade, turned 1:4 by
    hand) in its top-left corner (its upside-down twin at the bottom right
    is off the frame); the big spade in the middle in black enamel, with a slate
    reflection a pixel inside its lit (top-left) contour. Its top and left
    edges are gilt (gold); its right edge, turned to us, shows the gilt
    thickness in shade (wine). A flash on its peak (the top-left corner):
    a cream star whose arms turn gold, on a bloom of navy in the air, two
    small sparks thrown off it.
  - The hand, lower left, smaller and further back: a fan of four cards
    held from below the frame, each card to the right in front, so every
    index shows in its top-left corner as in a real hand. From the back: a
    face-down card (wine, a gold lattice of even 1-px lines at 45 degrees to
    its edges), the aces of hearts, clubs and diamonds. Each card a step
    darker than the one in front; their left edges gilt, so the cards
    separate by warm lines, not dark ones. Only the front card (diamonds)
    shows its big centre pip, whole; the others' are under the cards in
    front (no slivers). The hand falls into the dark toward its foot.
  - Behind: the night as a stage's backdrop, a sunburst of 14 navy rays
    from behind the hero (fading out before the sign), the hand's shadow
    cast on it down and right (a level darker, flat), a vignette at the
    frame. Nothing busy under the sign.
  - Light: the house key from the top left: lit faces warm, shadows cool
    (slate, navy), black only for outlines on the shadow side.
  Reading order: the sign; the ace of spades (biggest, brightest, the big
  black spade); the hand of aces; the back's wine and gold.

PALETTE (folderkit's 6 + 5 own + cream, black, red; the rainbow is the neon)
  navy0 navy1 navy2   the night, the rays, the sign's panel and extrusion
  ice0 ice1 ice2      the sign's face only
  card0 card1         the card stock, warm: a tan, a bone (cream the lit face)
  slate               the cool shade: the spade's reflection, the far fade
  wine gold           the card back and its lattice, the gilt edges, the
                      hero's edge thickness; red the red suits

LETTERING: BAZAR (bmf collection), "freeware; authors vary, few gave terms"
  (a `?` face: it wants the credits row in docs/cover-art.md), at its own
  size, from folderkit's word_cards.txt.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import folderkit as fk  # noqa: E402  (puts the repository's tools/ on the path)
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

YY, XX = fk.YY, fk.XX

OWN = {"card0": "#B4A285", "card1": "#ECDFC2", "slate": "#4D5A8C", "wine": "#76102E", "gold": "#E9AC3A"}
CARD_R = ["black", "navy0", "navy1", "navy2", "slate", "card0", "card1", "cream"]
SLATE, CARD0, CARD1, CREAM = 4, 5, 6, 7                       # levels on CARD_R

LOOK = dict(centre=(86, 84), glow=(66, 48), rays=14, ray_reach=(8, 90), ray_k=1.3, spin=4.0, ray_width=0.4,
            ray_top=50)

SIZE = (36.0, 52.0, 3.6)                                       # a card: width, height, corner radius
FAN = ((46.0, 146.0), 62.0)                                    # the hand's pivot (below the frame), its radius
# back to front: suit, angle (+ leans right; slopes 1:2, 1:4, 1:8, 0, 1:4:
# even steps), where (None: on the fan, or its middle (x, y)), scale,
# light (bow across, fall down, levels lost to the dark further back),
# and (pitch, yaw) out of the picture's plane
HAND = [
    ("back", -26.565, None, 0.94, (0.8, 1.2, 0.8)),
    ("hearts", -14.036, None, 0.94, (0.8, 1.2, 0.85)),
    ("clubs", -7.125, None, 0.94, (0.8, 1.2, 0.6)),
    ("diamonds", 0.0, None, 0.94, (0.8, 1.2, 0.35)),
    ("spades", 14.036, (100.0, 101.0), 1.5, (1.3, 0.8, -0.05), (-12.0, 18.0)),  # the hero, flicked out at us
]
FOCAL = 150.0                                                  # the camera's distance (px), for the hero's perspective
FADE = ((66.0, 60.0), 52.0, 30.0, 2.0)                         # the spot's pool: middle, radius lit, falloff, levels lost
HERO_FADE = 0.5                                                # the hero is in the spot: half the pool's falloff
INDEX = (5.0, 6.5, 10.0)                                       # the A's middle from the top-left corner (card units),
                                                               # the suit's that many px under it
SHADOW = (2, 1)                                                # the shadow a card throws on the one behind
HERO_SHADOW = (4, 3)
BACKDROP_SHADOW = ((4, 3), (7, 6))                             # the hand's shadow on the backdrop: the fan's, the hero's
LATTICE = 6                                                    # the card back's lattice pitch (px)
PIP = 21.0                                                     # the hero's big spade (card units)
GLOSS = (0.62, 0.42, 0.05, 0.22, 0.9)                          # the hero's sheen: u, v weights, band from, to, levels
BIG_PIP = 19.0                                                 # a big centre pip (card units), on a card that shows it whole
SPARKS = [(-12, 6), (13, -4)]                                  # small twinkles round the flash, from the peak
BOTTOM_INDEX = False                                           # the hero's upside-down index: off the frame but a blob
FLASH = (8, 6, 5, 4)                                           # the peak's star: arms left, right, up, down
FLASH_AT = (-2.0, -2.0)                                        # its middle, from the peak

# the index stamps: upright, and turned by hand where a shear breaks them
STAMPS = {
    ("A", 0): """
...#...
..###..
..###..
.##.##.
.##.##.
.#####.
##...##
##...##
##...##
""",
    ("A", 14): """
.....#.
....###
...####
..##.##
..##.##
.######
.##..##
##...##
##...##
.....##
""",
    ("hearts", 0): """
.##.##.
#######
#######
.#####.
..###..
...#...
""",
    ("hearts", -14): """
....##..
.##.###.
#######.
#######.
.######.
..####..
...##...
....#...
""",
    ("diamonds", 0): """
...#...
..###..
.#####.
#######
.#####.
..###..
...#...
""",
    ("spades", 0): """
...#...
..###..
.#####.
#######
#######
##.#.##
...#...
..###..
""",
    ("spades", 14): """
....#...
...###..
..#####.
.#######
########
.######.
..#.#.#.
...#....
..###...
""",
    ("clubs", 0): """
..###..
.#####.
..###..
##.#.##
#######
##.#.##
...#...
..###..
""",
}


def stamp(rows):
    return np.array([[c == "#" for c in ln] for ln in rows.strip("\n").split("\n")], bool)


def glyph(name, deg):
    """The stamp for `name` on a card turned `deg`: a hand-turned one, its
    mirror, or the upright one (for turns under 8 degrees)."""
    k = int(round(deg))
    if (name, k) in STAMPS:
        return stamp(STAMPS[(name, k)])
    if (name, -k) in STAMPS:                                  # every glyph is symmetric: mirror it
        return stamp(STAMPS[(name, -k)])[:, ::-1]
    return stamp(STAMPS[(name, 0)])


def hatch(deg, pitch):
    """Parallel 1-px lines `pitch` px apart (measured along the picture's
    axis they cross), at `deg` degrees from the horizontal: one pixel per
    column for a shallow line, one per row for a steep one, so they step
    evenly."""
    t = np.radians(deg)
    x, y = XX + 0.5, YY + 0.5
    if abs(np.tan(t)) <= 1.0:
        f = (y - x * np.tan(t)) % pitch
    else:
        f = (x - y / np.tan(t)) % pitch
    return np.abs(f - pitch / 2) < 0.5


def put_glyph(pic, m, x, y, colour, where=None):
    """Stamps m with its middle at (x, y)."""
    h, w = m.shape
    ox, oy = int(np.floor(x - (w - 1) / 2 + 0.5)), int(np.floor(y - (h - 1) / 2 + 0.5))
    out = np.zeros((128, 128), bool)
    for py, px in zip(*np.nonzero(m)):
        X, Y = ox + px, oy + py
        if 0 <= X < 128 and 0 <= Y < 128:
            out[Y, X] = True
    if where is not None:
        out &= where
    pic.put(out, colour)
    return out


# ---- the hand's geometry -----------------------------------------------------------------

def frame(k):
    """Card k's middle and angle (radians)."""
    _, deg, where = HAND[k][:3]
    a = np.radians(deg)
    if where is not None:
        return where[0], where[1], a
    (px, py), r = FAN
    return px + r * np.sin(a), py - r * np.cos(a), a


def tilt(k):
    """Card k's turn out of the picture's plane: (pitch, yaw) in degrees
    (pitch: its top leaned away from the viewer; yaw: its left side)."""
    return HAND[k][5] if len(HAND[k]) > 5 else None


def corners(k):
    """Card k's corners on the picture (top-left, top-right, bottom-right,
    bottom-left): turned by its angle in the picture's plane, then out of
    it by its tilt, seen in perspective from FOCAL px away."""
    w, h, _ = SIZE
    cx, cy, a = frame(k)
    sc = HAND[k][3]
    p, q = np.radians(tilt(k) or (0.0, 0.0))
    out = []
    for u, v in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x, y = u * sc, v * sc
        x, y = x * np.cos(a) - y * np.sin(a), x * np.sin(a) + y * np.cos(a)
        z = y * np.sin(p)                                     # toward the viewer: the top goes away
        y = y * np.cos(p)
        z, x = z * np.cos(q) + x * np.sin(q), x * np.cos(q) - z * np.sin(q)   # the left side goes away
        f = FOCAL / (FOCAL - z)
        out.append((cx + x * f, cy + y * f))
    return out


def local(X, Y, k):
    """Picture points in card k's own units (u right, v down, 0 its middle)."""
    w, h, _ = SIZE
    if tilt(k):
        U, V = ak.quad_uv((X, Y), corners(k), w, h)
        return U - w / 2, V - h / 2
    cx, cy, a = frame(k)
    sc = HAND[k][3]
    dx, dy = (X - cx) / sc, (Y - cy) / sc
    return dx * np.cos(a) + dy * np.sin(a), -dx * np.sin(a) + dy * np.cos(a)


def to_screen(k, u, v):
    """A point of card k (its own units) on the picture."""
    w, h, _ = SIZE
    if tilt(k):
        H = ak.homography([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], corners(k))
        d = H[2, 0] * u + H[2, 1] * v + H[2, 2]
        return (H[0, 0] * u + H[0, 1] * v + H[0, 2]) / d, (H[1, 0] * u + H[1, 1] * v + H[1, 2]) / d
    cx, cy, a = frame(k)
    sc = HAND[k][3]
    u, v = u * sc, v * sc
    return cx + u * np.cos(a) - v * np.sin(a), cy + u * np.sin(a) + v * np.cos(a)


def tangent_pt(T, C, r, side):
    """Where a line from T touches the circle (C, r), on `side` (+1 or -1)."""
    dx, dy = C[0] - T[0], C[1] - T[1]
    d = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx) + side * np.arcsin(r / d)
    L = np.sqrt(d * d - r * r)
    return (T[0] + L * np.cos(ang), T[1] + L * np.sin(ang))


def spade_sdf(P, cx, cy, s):
    """A playing-card spade about s tall centred at (cx, cy) in the frame P
    (a distance field): two round lobes, straight sides tangent to them up
    to a sharp tip, a stem with concave sides flaring to a broad foot."""
    r = 0.25 * s
    CL, CR = (cx - 0.25 * s, cy + 0.05 * s), (cx + 0.25 * s, cy + 0.05 * s)
    T = (cx, cy - 0.52 * s)
    body = ak.union(ak.circle(P, *CL, r), ak.circle(P, *CR, r),
                    ak.polygon(P, [T, tangent_pt(T, CR, r, -1), CR, (cx, cy + 0.22 * s), CL, tangent_pt(T, CL, r, 1)]))
    stem = ak.polygon(P, [(cx - 0.05 * s, cy + 0.12 * s), (cx + 0.05 * s, cy + 0.12 * s),
                          (cx + 0.25 * s, cy + 0.52 * s), (cx - 0.25 * s, cy + 0.52 * s)])
    cut = ak.union(ak.circle(P, cx - 0.37 * s, cy + 0.30 * s, 0.25 * s), ak.circle(P, cx + 0.37 * s, cy + 0.30 * s, 0.25 * s))
    return ak.union(body, ak.sub(stem, cut))


def pip_sdf(suit, P, cx, cy, s):
    """A big centre pip about s tall at (cx, cy) in the frame P (a distance field)."""
    x, y = P
    if suit == "diamonds":
        return np.abs(x - cx) / (0.37 * s) + np.abs(y - cy) / (0.5 * s) - 1.0
    if suit == "hearts":
        r = 0.26 * s
        return ak.union(ak.circle(P, cx - r, cy - 0.18 * s, r), ak.circle(P, cx + r, cy - 0.18 * s, r),
                        ak.polygon(P, [(cx - 2 * r, cy - 0.12 * s), (cx + 2 * r, cy - 0.12 * s), (cx, cy + 0.5 * s)]))
    if suit == "clubs":
        r = 0.2 * s
        return ak.union(ak.circle(P, cx, cy - 0.27 * s, r), ak.circle(P, cx - 0.24 * s, cy + 0.08 * s, r),
                        ak.circle(P, cx + 0.24 * s, cy + 0.08 * s, r),
                        ak.polygon(P, [(cx - 0.05 * s, cy), (cx + 0.05 * s, cy), (cx + 0.2 * s, cy + 0.5 * s),
                                       (cx - 0.2 * s, cy + 0.5 * s)]))
    return spade_sdf(P, cx, cy, s)


def facing(m, dx, dy, n=2):
    """How much each pixel's outward normal (from the smoothed mask) faces
    the direction (dx, dy): -1..1."""
    b = fk._blur(m, n)
    gy, gx = np.gradient(b)
    nx, ny = -gx, -gy
    nn = np.hypot(nx, ny) + 1e-9
    return (nx * dx + ny * dy) / (nn * np.hypot(dx, dy))


def star(pic, x, y, arms, light):
    """A four-pointed flash at (x, y): arms (left, right, up, down) long,
    cream turning gold toward their tips (gold all along where they cross
    the lit card), and a cream pixel on each diagonal."""
    pic.px(x, y, "cream")
    for (dx, dy), arm in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for i in range(1, arm + 1):
            x_, y_ = x + dx * i, y + dy * i
            if 0 <= x_ < 128 and 0 <= y_ < 128:
                pic.px(x_, y_, "gold" if (light[y_, x_] or i > 0.6 * arm) else "cream")
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        if not light[y + dy, x + dx]:
            pic.px(x + dx, y + dy, "cream")


# ---- the picture -----------------------------------------------------------------------

def draw():
    P = fk.palette(OWN, ramps=[CARD_R, ["black", "wine", "red"], ["wine", "gold", "cream"]])
    pic = ak.Picture.blank(P, "navy0")
    w, h, rc = SIZE
    n = len(HAND)
    hero = n - 1
    pkx, pky = to_screen(hero, -w / 2 + 1.0, -h / 2 + 1.0)      # the hero's peak, where it flashes
    s = 4                                                        # samples a pixel, each way
    c = (np.arange(128 * s) + 0.5) / s
    X, Y = np.meshgrid(c, c)

    def cov(d):
        return ak.px_mean((d < 0).astype(np.float32), s)

    masks = [cov(ak.box(local(X, Y, k), 0, 0, w / 2, h / 2, rc)) >= 0.5 for k in range(n)]
    hand = np.zeros((128, 128), bool)
    for m in masks:
        hand |= m
    # the night: a sunburst behind the hero; the hand's shadow falls on it,
    # down and right (the backdrop is a stage's, a step behind the cards)
    shadow = np.zeros((128, 128), bool)
    for k in range(n):
        shadow |= ak.shift(masks[k], *BACKDROP_SHADOW[k == hero])
    fk.put_sky(pic, shadow=shadow, **LOOK, blooms=[(pkx, pky, 14.0, 1.2)])
    (fx, fy), r0, r1, fl = FADE
    pool = np.clip((np.hypot(XX + 0.5 - fx, YY + 0.5 - fy) - r0) / r1, 0, 1) * fl
    edge = fk.edge_dark(XX + 0.5, YY + 0.5) * 2.0
    e = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))
    frame_cap = np.select([e < 1, e < 2], [3.0, 4.0], CREAM)        # rows and columns 0-1, 126-127 stay dark
    vis_all = []
    for k in range(n):
        suit, deg, _, _, (bow, fall, depth) = HAND[k][:5]
        m = masks[k]
        over = np.zeros((128, 128), bool)
        for j in range(k + 1, n):
            over |= masks[j]
        vis = m & ~over
        vis_all.append(vis)
        U, V = local(XX + 0.5, YY + 0.5, k)
        un, vn = U / (w / 2), V / (h / 2)
        # the face: lit from the top left, bowed a little across, a step
        # darker for each card further back, falling into the dark at the foot
        lv = CREAM + 0.5 - bow * (un + 1) / 2 - fall * (vn + 1) / 2 - depth
        if k == hero:
            a, b, g0, g1, gk = GLOSS
            g = a * un + b * vn
            lv += gk * ((g > g0) & (g < g1))
        lv = np.maximum(lv, CARD0) - (pool * (HERO_FADE if k == hero else 1.0) + edge)
        L = np.minimum(fk.terrace_px(np.clip(lv, 0, CREAM), 1.2), frame_cap)
        # the shadows the cards in front throw on this one (the fan opens to
        # the left, each card in front to the right: they fall under it)
        shade = np.zeros((128, 128), bool)
        for j in range(k + 1, n):
            sx, sy = HERO_SHADOW if j == hero else SHADOW
            steps = max(abs(sx), abs(sy))
            for i in range(1, steps + 1):
                shade |= ak.shift(masks[j], int(round(sx * i / steps)), int(round(sy * i / steps)))
        shade &= vis
        if suit == "back":
            inner = vis & (cov(ak.box(local(X, Y, k), 0, 0, w / 2 - 3.0, h / 2 - 3.0, rc - 2.0)) >= 0.5)
            border = vis & ~inner
            ak.by_level(pic, L, CARD_R, border)
            # the back: wine, a gold lattice at 45 degrees to its edges (on
            # the picture slopes 1:3 and 3:1, as the card is turned 1:2)
            field = ak.by_level(pic, fk.terrace_px(np.clip(lv - CARD0 + 1.6, 0, 1), 1.2), ["black", "wine"], inner, q=1)
            lat = inner & (hatch(deg + 45.0, LATTICE) | hatch(deg - 45.0, LATTICE))
            pic.put(lat & (field == 1), "gold")                    # gold on the wine, wine in the shade
            pic.put(lat & (field == 0), "wine")
            pic.put(shade & border, "slate")
            pic.put(shade & inner, "black")
        else:
            ak.by_level(pic, L, CARD_R, vis)
            pic.put(shade, "slate")
        # gilt edges where the light reaches: the top and the left
        top = vis & ~ak.shift(m, 0, 1) & (V < -h / 2 + 2.5)
        left = vis & ~ak.shift(m, 1, 0) & (U < -w / 2 + 2.5)
        gilt = (top | left) & ~shade & (L >= CARD0 - 0.01)
        pic.put(gilt, "gold")
        # the big centre pip, where the card shows it whole (the front of the fan)
        if suit in ("hearts", "diamonds", "clubs") and k != hero:
            Uc, Vc = local(X, Y, k)
            pd = pip_sdf(suit, (Uc, Vc), 0, 0, BIG_PIP)
            pp = cov(pd) >= 0.5
            if (pp & ~vis).sum() == 0 and pp.any():
                ink = "red" if suit in ("hearts", "diamonds") else "black"
                pic.put(pp, ink)
                lit = facing(pp, -1, -1)
                rim = pp & ~ak.erode(pp, 1)
                pic.put(rim & (lit < -0.35), "wine" if ink == "red" else "black")
                pic.put(rim & (lit > 0.5), "cream" if ink == "red" else "slate")
        # the corner index: A over the suit, top left (and, with BOTTOM_INDEX, turned at the hero's bottom right)
        if suit != "back":
            ink = "red" if suit in ("hearts", "diamonds") else "black"
            for sgn in [1] + ([-1] if (k == hero and BOTTOM_INDEX) else []):
                du, dv, gap = INDEX
                for nm, dv_ in (("A", dv), (suit, dv + gap / HAND[k][3])):
                    x0, y0 = to_screen(k, sgn * (-w / 2 + du), sgn * (-h / 2 + dv_))
                    st = glyph(nm, deg)
                    if sgn < 0:
                        st = st[::-1, ::-1]
                    put_glyph(pic, st, x0, y0, ink, where=vis & ~gilt)
    # the hero's big spade: black enamel, a slate reflection a pixel inside
    # its lit (top-left) contour, on its upper half
    U, V = local(X, Y, hero)
    sd = spade_sdf((U, V), 0, 1.5, PIP)
    pm = (cov(sd) >= 0.5) & vis_all[hero]
    pic.put(pm, "black")
    din = ak.px_mean(sd, s) * HAND[hero][3]                      # px inside (negative)
    face = facing(pm, -1, -1.6)
    upper = YY + 0.5 < to_screen(hero, 0, 1.5)[1]
    pic.put(pm & upper & (din > -2.6) & (din <= -1.2) & (face > 0.6), "slate")    # a reflection a pixel inside the rim
    fk.selout(pic, hand, "black")
    # the hero turns its right edge to us: the card's gilt thickness, in shade
    hm = masks[hero]
    thick = hm & ~ak.shift(hm, -1, 0) & (facing(hm, 1, 0) > 0.5)
    pic.put(thick & (YY < 126), "wine")
    ak.despeckle(pic, 5, within=YY >= fk.OBJECT_TOP)
    # the flash: a star on the peak, cream on the night, gold on the card
    star(pic, int(np.floor(pkx + FLASH_AT[0])), int(np.floor(pky + FLASH_AT[1])), FLASH,
         pic.where("cream", "card1", "card0", "gold"))
    for dx, dy in SPARKS:                                         # the flash's sparks, in the air
        fk.twinkle(pic, int(np.floor(pkx + dx)), int(np.floor(pky + dy)), arm="gold")
    fk.word(pic, "cards", glints=[(3, 4, 2)])
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "cards.png"))
