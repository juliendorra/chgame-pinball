"""tools/sdcard/art/tiles.png: the TILES folder's cover on the casino card
(it holds Dominoes and Mahjong). `python tools/sdcard/covers.py` redraws
it; edit this, not the PNG. The folders' shared look is folderkit.py,
beside this file.

THE BRIEF (revision 2)
  Message: this way to the tiles. A domino tips over, swept round its
  foot, and is a breath from clacking into a mahjong tile that stands its
  ground; light bursts from the gap it is about to close: the two tile
  games inside, in one beat of action.

  Composition (a folder: a sign over a door, then the one object that
  says what is inside; read in this order):

      +--------------------------------+
      |      [ = = T I L E S = = ]   + |   the sign, rows 1-48; a twinkle
      |   .--~~-.    . | .    ______   |   the burst fans up from the gap
      | ~~   .--._  . :|: .  /_____/|  |   trails arch round the domino's
      | ~~~ ,   __   :|:    | _|_  ||  |   foot, the outer one over its apex
      |  ~~   /o  o/  :|    ||_|_| ||  |   the domino leaning 1:2, 6 over 5,
      |      /o  o/   :|    |  |   ||  |   its corner 4 px short of the
      |     /o  o/    :|    |  '   ||  |   tile, the gap lit; the tile face
      |    /----/      |    |      ||  |   on, 中 in red, its jade back on
      |   /o  o/       |    |      ||  |   the top and side; both fall into
      +--------------------------------+   the dark frame

  - The sign: TILES in the family's ice chrome on its navy panel and
    rainbow neon tube. Nothing near it but the night; one twinkle in the
    night right of it.
  - The light behind: folderkit's night with a pool of light behind the
    tiles (an ellipse: navy2 at its heart, navy1, then the night), and a
    burst of ten rays (folderkit's rays, round their own centre) fanning
    up from the gap between the tiles, where the clack is coming: the gap
    itself lit navy2. Flat plateaus with narrow 25/50/75% seams; the
    tiles' shadow on the backdrop down and right, a level darker (not in
    the gap); at the frame, whole levels that only darken toward it.
  - The mahjong tile, the red dragon (the hero): stood face on to the
    camera (a level camera above and right of the tiles, slid by a lens
    shift: the faces facing us stay true rectangles, their verticals
    vertical, while the tops and right sides recede up and right). Its
    face is flat bone lit by hand: a cream rim on the edges facing the
    lamp, a solid cream hot corner and one 1:1 gloss line by it, the
    right edge rolling away in tan (2 px), the foot falling into the frame
    in whole steps; 中 on clean bone. 中 is a hand stamp with a brush's
    character (a press at the box's top left, a shoulder at its turn, the
    long stroke ending in a hanging needle), red, cut into the face: the
    cut's near walls (inside each stroke's top and left) in the shade of
    the face's edge, tan. Its top shows the ivory (cream at the rounded
    front edge), then the jade back (jade1, a jade0 far edge); its right
    side in shade, one value each, slate on the ivory and jade0 on the
    jade, darker only at its foot. A cream glint on its top corner (arms
    left and up, into the night).
  - The domino, tipping (the action): its face turned to us, leaning 1:2
    (26.57 degrees: its long edges step 2 rows a column, its short edges 2
    columns a row), so its face is a rectangle on the pixel lattice and
    is painted on it: clean bands, no seams across them. Its leading
    corner 4 px short of the mahjong tile, the gap lit between them. Six
    over five, every pip whole inside the frame; black pips, each with a
    grey pixel of the lamp; a 1-px centre line with a silvered pin; a
    cream rim on its lit long edge and a cream ridge where its face meets
    its top end; a small hot corner at its apex; its foot a step down in
    tan, falling into the frame. Its thickness shows (the lean turns its
    long side out of the recession): its top end a tan band with a cream
    lip at the apex, its long side 3 px of slate, a black outline on the
    shadow side only (none on the end's lit edge).
  - The fall: three arcs swept back round the domino's foot behind it,
    the outer one over its apex, 2 px at the root and 1 px most of their
    length, cream at the root, bone, tan, slate at the tip, each ending
    clear of the frame (their centre a quarter of the way up the domino
    from the corner it pivots on: they curve where the eye can see it).
  - The light: the house key from the top left: rims and hot corners up
    and left, the shade sides cool, black outlines on the shadow sides;
    the frame kept dark (rows and columns 0-1 and 126-127 black and navy0
    only, but for the sign's own glow on row 1).
  Reading order: the sign; 中 (the reddest, biggest mark); the domino
  and its fall into the lit gap; the jade back.

PALETTE (folderkit's 6 + 5 own + cream, grey, black, red; the rainbow is the neon)
  navy0 navy1 navy2   the night, the pool of light, the burst, the backdrop's shadows,
                      the far shade
  ice0 ice1 ice2      the sign's face only (quantised out: fk.EXCLUDE)
  bone tan            the ivory, warm: lit face, its turning edges, the domino's foot
                      (cream the rims, hot corners, the glint)
  slate               the cool shade: the tiles' shaded sides, the trails' tips
  jade0 jade1         the mahjong tile's back: its side, its top
  red                 中; black the pips, the centre line, the outlines; grey the
                      pips' gloss and the pin

LETTERING: BAZAR (bmf collection), "freeware; authors vary, few gave terms"
  (a `?` face, on the credits for the folders in docs/cover-art.md), at its
  own size, from folderkit's word_tiles.txt.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import folderkit as fk  # noqa: E402  (puts the repository's tools/ on the path)
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402
from artkit import render3d as R  # noqa: E402

YY, XX = fk.YY, fk.XX
X1, Y1 = XX + 0.5, YY + 0.5
EDGE = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))      # px from the frame
S = 4                                         # samples a pixel, each way (for the faces' coverage)
_C = (np.arange(128 * S) + 0.5) / S
XS, YS = np.meshgrid(_C, _C)

OWN = {"bone": "#E6D5B0", "tan": "#A08868", "slate": "#4D5A8C", "jade0": "#0B5A4A", "jade1": "#34A878"}
IVORY_R = ["black", "navy0", "navy1", "navy2", "slate", "tan", "bone", "cream"]
JADE_R = ["black", "navy0", "navy1", "jade0", "jade1"]
SLATE, TAN, BONE, CREAM = 4, 5, 6, 7                            # levels on IVORY_R

# a level camera (no pitch: the faces facing it stay true rectangles, their
# verticals vertical), above and right of the tiles, the picture slid by a
# lens shift: the tops and right sides recede to a point up and right
CAM_Y = 3.1
CAM = R.Camera((3.1, CAM_Y, 7.4), (3.1, CAM_Y, 0.0), fov=22, shift=(147, -64 - (CAM_Y - 2.8) * 46))

# ---- the scene (world units: x right, y up, z toward the camera) ----------------

MJ_HALF = (0.50, 0.68, 0.42)                  # the mahjong tile: width, height, depth (halves)
MJ_IVORY = 0.40                               # its ivory face's share of the depth (the rest the jade back)
MJ_AT = (0.42, 0.68, -0.18)                   # its middle
DOM_SCALE = 0.93
DOM_HALF = (0.33 * DOM_SCALE, 0.68 * DOM_SCALE, 0.15)   # the domino: width, length, thickness (halves)
DOM_LEAN = -np.degrees(np.arctan(0.5))       # its top falling right, toward the mahjong tile (1:2)
DOM_AT = (-0.89, 0.04, 0.10)                  # its middle's x, its lift off the floor, its z

# ---- the light ----------------------------------------------------------------

LOOK = dict(centre=(80, 110), glow=(76, 56))  # the night's glow behind the tiles
POOL = ((84, 76), (58, 44), 1.3)             # a pool of light on the backdrop: middle, radii, levels
BURST = dict(centre=(63, 76), rays=10, ray_reach=(6, 90), ray_k=1.5, ray_width=0.35, spin=9.0, ray_top=48)
                                              # rays from the gap the domino is about to close
BACKDROP_SHADOW = (5, 4)                      # the tiles' shadow on the backdrop (px)
GAP_BLOOM = ((63.0, 76.0), 10.0, 1.6)        # the light in the gap: middle, radius, levels (no shadow in it)
HOT, GLOSS = 6, 10                            # the tile face's hot corner (px from its corner, 1:1), its gloss line
ROLL = 3                                      # the tile face's right edge rolling away (tan, px)
SIDE_FOOT = 0.88                              # the tile's side darker below this share of its height
DOM_FOOT = 0.86                               # the domino's face: its foot in tan past this share of its length
DOM_HOT = 3                                   # its apex's hot corner: this far each way (half lattice steps)
END_LIP = 2.6                                 # the cream lip at its top end's apex (px)
GLINT_ARMS = (4, 0, 4, 0)                     # the lamp's glint on the tile's top corner: arms l r u d
SPARKS = [(115, 38, "slate")]                  # twinkles in the air: x, y, arm colour

# ---- the marks ----------------------------------------------------------------

# the red dragon, 中, a brush's: a press at the box's top left, a shoulder
# at its turn, the long stroke ending in a hanging needle (its middle on
# the face's)
CHUN = """
...............####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
##............#####........###...
################################.
#################################
#################################
#################################
#################################
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
#####.........#####........#####.
################################.
################################.
################################.
################################.
################################.
#####.........#####..............
.####.........#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............#####..............
..............####...............
..............####...............
...............###...............
...............###...............
...............##................
................#................
................#................
"""
CHUN_LIFT = 2                                 # px above the face's middle
CUT_WALL = "tan"                              # the cut's near walls, in shade (None: flat paint)

PIP_AT = {6: [(0.25, 0.2), (0.75, 0.2), (0.25, 0.5), (0.75, 0.5), (0.25, 0.8), (0.75, 0.8)],
          5: [(0.25, 0.2), (0.75, 0.2), (0.5, 0.5), (0.25, 0.8), (0.75, 0.8)]}
HALVES = (6, 5)                               # the domino's halves: the top end's, the foot's
PIP = 5                                       # a pip's size (px)
PIP_GLOSS = "grey"                            # a pixel of the lamp on each pip's paint, up and left
PIN = [((0, -1), "cream"), ((-1, 0), "cream"), ((0, 0), "grey"), ((1, 0), "grey"), ((0, 1), "grey")]

# the fall: arcs round the domino's foot, behind it: (radius, a share of
# its top corner's; how much of them is 2 px)
ARCS = [(1.07, 0.3), (0.92, 0.3), (0.77, 0.25)]
ARC_COLS = (("cream", 0.18), ("bone", 0.45), ("tan", 0.75), ("slate", 1.0))
ARC_GAP = 3.0                                 # px between the edge and a trail's root
TRAIL_CENTRE = 0.25                           # the arcs' centre: this far from the foot's corner to its top


# ---- boxes in perspective -----------------------------------------------------------

# a box's faces: local normal, corners (signs of the half sizes: TL, TR, BR, BL
# as seen from outside, upright), and the local axes its U and V run along
FACES = {
    "front": ((0, 0, 1), [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1)], (0, 1)),
    "top": ((0, 1, 0), [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)], (0, 2)),
    "right": ((1, 0, 0), [(1, 1, 1), (1, 1, -1), (1, -1, -1), (1, -1, 1)], (2, 1)),
    "left": ((-1, 0, 0), [(-1, 1, -1), (-1, 1, 1), (-1, -1, 1), (-1, -1, -1)], (2, 1)),
    "bottom": ((0, -1, 0), [(-1, -1, 1), (1, -1, 1), (1, -1, -1), (-1, -1, -1)], (0, 2)),
    "back": ((0, 0, -1), [(1, 1, -1), (-1, 1, -1), (-1, -1, -1), (1, -1, -1)], (0, 1)),
}


class Box:
    """A box in the world: middle, half sizes, a rotation (local -> world)."""

    def __init__(self, centre, half, rot):
        self.c = np.asarray(centre, dtype=np.float64)
        self.h = np.asarray(half, dtype=np.float64)
        self.R = np.asarray(rot, dtype=np.float64)

    def world(self, q):
        return self.c + self.R @ np.asarray(q, dtype=np.float64)

    def visible(self, name):
        n = np.asarray(FACES[name][0], dtype=np.float64)
        return float((self.R @ n) @ (CAM.pos - self.world(n * self.h))) > 0

    def quad(self, name):
        """The face's corners on the picture: TL, TR, BR, BL."""
        return [CAM.project(self.world(np.asarray(s) * self.h)) for s in FACES[name][1]]

    def dims(self, name):
        a, b = FACES[name][2]
        return 2 * self.h[a], 2 * self.h[b]

    def to_screen(self, name, u, v):
        """A point of a face (its own U, V) on the picture."""
        w, h = self.dims(name)
        H = ak.homography([(0, 0), (w, 0), (w, h), (0, h)], self.quad(name))
        d = H[2, 0] * u + H[2, 1] * v + H[2, 2]
        return (H[0, 0] * u + H[0, 1] * v + H[0, 2]) / d, (H[1, 0] * u + H[1, 1] * v + H[1, 2]) / d


def faces(box):
    """The box's visible faces: {name: (mask, U, V, w, h)}, every pixel of
    its silhouette given to the face that covers most of it."""
    covs = {}
    for nm in FACES:
        if box.visible(nm):
            d = ak.polygon((XS, YS), box.quad(nm))
            covs[nm] = ak.px_mean((d < 0).astype(np.float32), S)
    stack = np.stack(list(covs.values()))
    sil = np.clip(stack.sum(0), 0, 1) >= 0.5
    best = stack.argmax(0)
    out = {}
    for k, nm in enumerate(covs):
        w, h = box.dims(nm)
        U, V = ak.quad_uv((X1, Y1), box.quad(nm), w, h)
        out[nm] = (sil & (best == k), U, V, w, h)
    return out


def scene():
    """The mahjong tile and the domino (its lowest corner DOM_AT[1] off the floor)."""
    mj = Box(MJ_AT, MJ_HALF, np.eye(3))
    rot = R.rot_z(DOM_LEAN)
    low = min((rot @ (np.array([a, b, c]) * DOM_HALF))[1] for a in (-1, 1) for b in (-1, 1) for c in (-1, 1))
    dom = Box((DOM_AT[0], -low + DOM_AT[1], DOM_AT[2]), DOM_HALF, rot)
    return mj, dom


# ---- helpers ------------------------------------------------------------------------

def text_mask(art):
    rows = art.strip("\n").split("\n")
    w = max(len(r) for r in rows)
    return np.array([[c == "#" for c in r.ljust(w, ".")] for r in rows], bool)


def stamp(m, cx, cy):
    """A small mask with its middle at (cx, cy) on a picture-sized one."""
    h, w = m.shape
    return ak.place(m, int(np.floor(cx - w / 2 + 0.5)), int(np.floor(cy - h / 2 + 0.5)))


def bounds(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max(), ys.max()


def silhouette(F):
    m = np.zeros((128, 128), bool)
    for v in F.values():
        m |= v[0]
    return m


def vignette(e):
    """Whole levels an object loses at e px from the frame: it steps down
    its ramp into the dark (no dither at the frame)."""
    return np.select([e <= 0, e <= 1, e <= 2, e <= 4, e <= 6], [7, 6, 3, 2, 1], 0)


# ---- the painting -------------------------------------------------------------------

def night_level():
    """folderkit's night with the pool of light behind the tiles, the
    burst from the gap between them (folderkit's rays, round a centre of
    their own) and the light in the gap."""
    lv = fk.sky_level(X1, Y1, **LOOK)
    (cx, cy), (rx, ry), k = POOL
    r = np.hypot((X1 - cx) / rx, (Y1 - cy) / ry)
    t = np.clip(1 - r, 0, 1)
    lv = lv + k * t * t * (3 - 2 * t) * np.clip((EDGE - 1) / 5.0, 0, 1)
    look = dict(glow=(1, 1), **BURST)
    lv = lv + fk.sky_level(X1, Y1, **look) - fk.sky_level(X1, Y1, **dict(look, rays=0))
    (bx, by), br, bk = GAP_BLOOM
    t = np.clip(1 - np.hypot(X1 - bx, Y1 - by) / br, 0, 1)
    return np.clip(lv + bk * t * t, 0, 3)


def backdrop(pic, both):
    """The night, the pool of light, the burst, and the tiles' shadow on
    it, down and right, a level darker. At the frame, whole levels that
    only ever darken toward it (no dotted seams or stripes along it)."""
    shadow = ak.shift(both, *BACKDROP_SHADOW) & ~both
    shadow &= np.hypot(X1 - GAP_BLOOM[0][0], Y1 - GAP_BLOOM[0][1]) > GAP_BLOOM[1]   # the gap keeps its light
    lv = night_level()
    flat = EDGE <= 4
    ak.by_level(pic, fk.terrace_px(lv, 1.5), fk.NIGHT_R, ~shadow & ~flat)
    ak.put_levels(pic, shadow & ~flat, np.clip(np.round(lv) - 1, 0, 3).astype(int), fk.NIGHT_R)
    L = np.clip(np.round(lv) - shadow, 0, 3).astype(int)
    for e in range(4, -1, -1):                                # from inside out: never lighter than inward
        ring = EDGE == e
        inward = np.full((128, 128), 3)
        inward[:, :-1] = np.where(XX[:, :-1] < 64, np.minimum(inward[:, :-1], L[:, 1:]), inward[:, :-1])
        inward[:, 1:] = np.where(XX[:, 1:] >= 64, np.minimum(inward[:, 1:], L[:, :-1]), inward[:, 1:])
        inward[:-1, :] = np.where(YY[:-1, :] < 64, np.minimum(inward[:-1, :], L[1:, :]), inward[:-1, :])
        inward[1:, :] = np.where(YY[1:, :] >= 64, np.minimum(inward[1:, :], L[:-1, :]), inward[1:, :])
        L = np.where(ring, np.minimum(L, inward), L)
    ak.put_levels(pic, flat, L, fk.NIGHT_R)


def paint_mahjong(pic, F):
    """The red dragon: a bone face lit by hand with 中 cut in red, the top
    and the right side showing the jade back. Returns the face's top-left
    corner."""
    m, U, V, w, h = F["front"]
    x0, y0, x1, y1 = bounds(m)
    dx, dy = XX - x0, YY - y0
    lvl = np.full((128, 128), BONE, int)
    lvl[dx + dy < HOT] = CREAM                                              # the hot corner
    lvl[(dx + dy == GLOSS)] = CREAM                                         # one 1:1 gloss line
    lvl[XX > x1 - ROLL] = TAN                                               # the edge rolling away
    lvl = lvl - vignette(EDGE)
    ak.put_levels(pic, m, lvl, IVORY_R)
    lit = (((XX == x0) & (YY > y0)) | (YY == y0)) & (EDGE > 2)
    pic.put(m & lit, "cream")                                       # the edges facing the lamp
    # 中, red, cut in the face: the cut's near walls (inside the stroke's
    # top and left) in the shade of the face's edge
    face = m & (EDGE > 2)
    cm = stamp(text_mask(CHUN), (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2 - CHUN_LIFT) & face
    pic.put(cm, "red")
    if CUT_WALL:
        pic.put(cm & (~ak.shift(cm, 1, 0) | ~ak.shift(cm, 0, 1)), CUT_WALL)
    # the top: ivory (cream at its rounded front edge), then the jade back
    m, U, V, w, h = F["top"]
    ivory = V > 2 * MJ_HALF[2] - MJ_IVORY * 2 * MJ_HALF[2]
    pic.put(m & ivory, "bone")
    pic.put(m & ivory & ~ak.shift(m & ivory, 0, -1), "cream")
    pic.put(m & ~ivory, "jade1")
    pic.put(m & ~ivory & ~ak.shift(m, 0, 1) & (U > 0.12 * w), "jade0")     # its back edge
    # the right side, in shade: one value each, darker only at its foot
    m, U, V, w, h = F["right"]
    ivory = U < MJ_IVORY * 2 * MJ_HALF[2]
    foot = (V / h > SIDE_FOOT).astype(int)
    ak.put_levels(pic, m & ivory, SLATE - foot - vignette(EDGE), IVORY_R)
    ak.put_levels(pic, m & ~ivory, 3 - foot - vignette(EDGE), JADE_R)
    return x0, y0


class Lattice:
    """The domino on the picture: it leans 1:2 (26.57 degrees) and faces
    us, so its face is a rectangle on the pixel lattice, ii = 2 dx + dy
    across it and jj = 2 dy - dx along it (from its top-left corner, both
    sqrt(5) to the pixel): every edge and every band steps 2-2-2. Its top
    end and its long side are the face swept back by the recession (one
    vector: the domino is small and far from the vanishing point)."""

    def __init__(self, dom):
        fq = [np.array(q) for q in dom.quad("front")]
        tq = [np.array(q) for q in dom.quad("top")]
        self.ax, self.ay = int(np.floor(fq[0][0])), int(np.floor(fq[0][1]))
        self.iw = int(round(np.sqrt(5) * np.hypot(*(fq[1] - fq[0]))))
        self.jl = int(round(np.sqrt(5) * np.hypot(*(fq[3] - fq[0]))))
        self.rec = tuple(int(round(v)) for v in tq[0] - fq[0])      # front corner to back corner
        dx, dy = XX - self.ax, YY - self.ay
        self.ii, self.jj = 2 * dx + dy, 2 * dy - dx
        self.front = (self.ii >= 0) & (self.ii <= self.iw) & (self.jj >= 0) & (self.jj <= self.jl)
        sweep = self.front.copy()
        rx, ry = self.rec
        n = max(abs(rx), abs(ry))
        for k in range(1, n + 1):
            sweep |= ak.shift(self.front, int(round(rx * k / n)), int(round(ry * k / n)))
        rest = sweep & ~self.front
        self.end = rest & (self.jj < 0)                       # its top end, beyond the face's top edge
        self.side = rest & ~self.end                          # its long side, beyond its right edge
        self.all = sweep

    def at(self, u, v):
        """The picture point of the face's (u, v), shares of its width and length."""
        I, J = u * self.iw, v * self.jl
        return self.ax + (2 * I - J) / 5 + 0.5, self.ay + (I + 2 * J) / 5 + 0.5


def paint_domino(pic, L):
    """The domino: a bone face on its lattice, its centre line and pin, its
    pips; its top end and long side (its thickness). Returns the small
    marks to put after the clean-up: [(x, y, colour)]."""
    jewels = []
    m, ii, jj = L.front, L.ii, L.jj
    jf = int(round(DOM_FOOT * L.jl))
    lvd = np.where(jj > jf, TAN, BONE) - vignette(EDGE)
    ak.put_levels(pic, m, lvd, IVORY_R)
    rim = m & ((ii < 2) | (jj < 2)) & (EDGE > 2)                 # its lit edges: the long edge, the ridge
    pic.put(rim & (lvd >= BONE), "cream")
    pic.put(m & (ii < 2 * DOM_HOT) & (jj < 2 * DOM_HOT), "cream")   # the apex's hot corner
    # the centre line, the pips, the pin
    mid = int(round(L.jl / 2))
    pic.put(m & (jj >= mid) & (jj <= mid + 1) & (ii > 2) & (ii < L.iw - 2), "black")
    tpl = ak.pip_template(PIP, PIP)
    for half, n in enumerate(HALVES):
        for pu, pv in PIP_AT[n]:
            px_, py_ = L.at(pu, (half + pv) / 2)
            pm = stamp(tpl, px_ - 0.5, py_ - 0.5) & m
            pic.put(pm, "black")
            gx, gy = int(np.floor(px_ - 0.5 - PIP / 2 + 0.5)) + 1, int(np.floor(py_ - 0.5 - PIP / 2 + 0.5)) + 1
            if PIP_GLOSS and pm.sum() == tpl.sum():
                jewels.append((gx, gy, PIP_GLOSS))
    ak.lonely(pic, "tan", within=m, into="bone")                # the foot's edge where a pip cuts it
    pcx, pcy = L.at(0.5, 0.5)
    px0, py0 = int(np.floor(pcx)), int(np.floor(pcy))
    for (dx, dy), c in PIN:
        if m[py0 + dy, px0 + dx]:
            jewels.append((px0 + dx, py0 + dy, c))
    # its top end, a level down (tan); a cream lip at the apex
    ak.put_levels(pic, L.end, TAN - vignette(EDGE), IVORY_R)
    pic.put(L.end & (ii < 2 * END_LIP), "cream")
    # its long side (the thickness, in shade): slate, darker into the frame
    ak.put_levels(pic, L.side, SLATE - vignette(EDGE), IVORY_R)
    return jewels


def trails(pic, L, ok):
    """The fall: arcs swept back round the domino's foot, behind it: each
    starts ARC_GAP px behind the domino's trailing edge (or behind its top
    corner, for an arc wider than the domino) and runs back until it
    meets the frame or the sign's margin; 2 px at the root, then 1 px; its
    colours step down along it (a cartoon's arcs: their centre a little up
    the domino from the corner it pivots on, so they curve where the eye
    can see it)."""
    foot = np.array(L.at(1, 1))                                # the corner it pivots on
    centre = foot + TRAIL_CENTRE * (np.array(L.at(0.5, 0)) - foot)
    apex = np.array(L.at(0, 0)) - 0.5
    ra = np.hypot(*(apex - centre))
    aa = np.arctan2(*(apex - centre)[::-1])
    body = ak.dilate(L.all, 1)
    for f, thick in ARCS:
        r = f * ra
        ang = aa + 0.5 - np.arange(0, 2.0, 0.25 / r)           # from ahead of the top corner, back
        pts = [centre + r * np.array([np.cos(a), np.sin(a)]) for a in ang]
        hit = [i for i, q in enumerate(pts) if inside(body, q)]
        i0 = (hit[-1] + 1) if hit else int(np.searchsorted(-ang, -aa))
        i0 += int(np.ceil(ARC_GAP / 0.25))                     # the gap (the steps are a quarter px)
        n = i0
        while n < len(pts) and inside(ok, pts[n]):
            n += 1
        seg = [tuple(q) for q in pts[i0:n]]
        if len(seg) < 12:
            continue
        for x, y, t in ak.raster(seg):
            if not (0 <= x < 128 and 0 <= y < 128 and ok[y, x]):
                continue
            c = next((nm for nm, hi in ARC_COLS if t <= hi), ARC_COLS[-1][0])
            pic.px(x, y, c)
            if t < thick:                                       # the root, 2 px: a pixel outward
                nx, ny = x + 0.5 - centre[0], y + 0.5 - centre[1]
                ox, oy = (0, int(np.sign(ny))) if abs(ny) >= abs(nx) else (int(np.sign(nx)), 0)
                if ok[y + oy, x + ox]:
                    pic.px(x + ox, y + oy, c)


def inside(m, p):
    x, y = int(np.floor(p[0])), int(np.floor(p[1]))
    return 0 <= x < 128 and 0 <= y < 128 and bool(m[y, x])


def frame(pic):
    """Rows and columns 0-1 and 126-127 kept dark for the installed
    border: black and navy0 only."""
    for e, cap in ((0, "black"), (1, "navy0")):
        sel = EDGE == e
        keep = (pic.idx == pic.pal["black"]) | (pic.idx == pic.pal["navy0"])
        pic.put(sel & ~keep, cap)


def draw():
    P = fk.palette(OWN, ramps=[IVORY_R, JADE_R])
    pic = ak.Picture.blank(P, "navy0")
    mj, dom = scene()
    F, L = faces(mj), Lattice(dom)
    obj_mj, obj_dom = silhouette(F), L.all
    both = obj_mj | obj_dom
    backdrop(pic, both)
    x0, y0 = paint_mahjong(pic, F)
    jewels = paint_domino(pic, L)
    fk.selout(pic, both, "black")
    ak.despeckle(pic, 5, within=YY >= fk.OBJECT_TOP)
    ak.despeckle(pic, 3, within=(YY >= fk.OBJECT_TOP) & ~both)               # the backdrop's seams
    trails(pic, L, ~both & ~ak.dilate(both, 1) & (YY >= fk.OBJECT_TOP + 2) & (EDGE >= 3))
    for x, y, c in jewels:
        pic.px(x, y, c)
    ak.glint(pic, x0, y0, 2, tip="bone", arms=GLINT_ARMS)       # the lamp on the tile's top corner
    for x, y, c in SPARKS:
        fk.twinkle(pic, x, y, arm=c)
    frame(pic)
    fk.word(pic, "tiles", glints=[(3, 4, 2)])
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "tiles.png"))
