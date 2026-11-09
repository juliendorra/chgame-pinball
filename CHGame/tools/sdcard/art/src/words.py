"""tools/sdcard/art/words.png: the WORDS folder's cover on the casino card
(it holds Crossword, Word Wheel, Words). `python tools/sdcard/covers.py`
redraws it; edit this, not the PNG. The folders' shared look is
folderkit.py, beside this file (cards.py is its worked example).

THE BRIEF (revision 2)
  Message: this way to the word games. A wine velvet bag of letter tiles
  has been opened under the lamp and the letters are leaping out of it on
  a beam of light: P, L, A rise out of its mouth and arc over, spelling
  PLAY with the sign above (WORDS... PLAY: word play), and the Y, the
  nearest, came the low road and tumbles straight at you.

  Composition (a folder: a sign over a door, then the one object that
  says what is inside; read in this order):
  - The sign: WORDS in the family's ice chrome on its navy panel and
    rainbow neon tube, rows 1 to 48 (folderkit.word). Calm night round it:
    the tiles keep 2 rows clear of its glow.
  - The hero: the Y tile, ivory, 43 px across, lower right, tumbling
    toward us (turned from the camera, its top tipped toward us, rolled 10
    degrees clockwise), a chunky block (its thickness shows: a cream top, a
    slate side) running off the right and bottom frames, 3 px of night
    between it and the A. Its
    face is bone, a cream corner toward the lamp and a tan foot, falling
    off along the light's diagonal in even 2-1 stairs; a cream rim on its
    lit edges. The Y cut in black, drawn by hand at its size and turned
    with the tile (words_y.txt), its upright walls catching the light in
    tan. The family's flash on its top rim, against the night: a cream
    heart, gold arms reaching out, a twinkle beside it. Three speed lines
    a few px behind it (bone, tan, slate), back toward the bag.
  - The bag, lower left, cut by the bottom frame: a drawstring pouch of
    wine velvet, leaning a little right. Velvet: wine where it faces us,
    red where the lamp grazes its shoulder (a sheen along its upper left
    rim), the gathers fanning down from the cord as crisp folds (a groove
    a step darker, a ridge a step lighter beside it). Its collar flares
    over a gold cord twisted like a rope, a knot, two tails with tassels.
    Its mouth an opening, in flat bands: the back of the collar wine, the
    hole black at the back and lit down inside (wine, red, gold, a small
    cream heart), the front lip red with a gold edge; two tiles' corners
    peeking over it, on the light.
  - The stream: P (13 px), L (16 px), A (19.5 px), growing as they come
    nearer, rising from the mouth in an arc, each tumbling its own way and
    a step darker and cooler the farther it is (P a tan face under a bone
    top; L bone; A bone under a cream top), 2 or 3 px of night between
    each; their letters stamped upright at their font's own size; the
    edges turned to the bag catching its gold. Short wakes behind P and L
    curve back down to the mouth.
  - Behind: the family's night; the bag's light as a bloom at its mouth
    and a beam up through the air the tiles fly in (fading out below the
    sign); a bloom round the flash; a gold twinkle left of the stream.
  - Light: the house key from the top left: the lit faces warm (cream,
    bone, red, gold), shadows cool (slate, navy), black only for outlines
    on the shadow side (folderkit.selout), seams where a nearer tile
    passes a farther one, and the cuts.
  Reading order: the sign; the Y; the bag and its light; P L A.

  Thumbnail (128 x 128):
      rows  1-48   [######## W O R D S ########]   the sign
      rows 51-80      ,,  [P][L][A]      *         wakes; the stream on the beam
      rows 72-128  (mouth)  ===    [ * Y   ]       speed lines; the Y, its flash
      rows 80-128  (bag)=cord=     [       ]       both cut by the frames

PALETTE (folderkit's 6 + 5 own + cream, black, red; the rainbow is the neon)
  navy0 navy1 navy2   the night, the beam, the sign's panel and extrusion,
                      the tiles' farthest shade
  ice0 ice1 ice2      the sign's face only (the title's reserved colours:
                      painted by nothing else)
  bone tan            the ivory, warm (cream its lit faces, the flash);
                      tan also the cord's twist and the cut's lit wall
  slate               the cool shade: the tiles' sides, the speed lines' tails
  wine                the velvet (with black and red), the collar's inside
  gold                the cord, the tassels, the light in the bag, the flash's
                      arms, the tiles' edges the bag's light catches
  red                 the velvet's sheen, the glow's rim

LETTERING: the sign is BAZAR (bmf collection), "freeware; authors vary,
  few gave terms" (a `?` face: it wants the credits row in
  docs/cover-art.md), at its own size, from folderkit's word_words.txt.
  The tiles' letters are u8g2's bitmaps of the X11 distribution's New
  Century Schoolbook Bold (ncenB08, B10, B12, B24; Adobe; the X11/Adobe
  notice: use, copy, modify and distribute with the notice kept, as Yacht
  Dice's timB), each at its own size, in words_tiles.txt beside this file
  (its header gives the source); the hero's Y is ncenB24's redrawn by hand
  turned with its tile (words_y.txt).

HOW IT IS PAINTED: the tiles are rounded boxes marched by render3d, one
camera for all, so each pixel knows its face; every face is then painted
flat as a level of the ivory ramp (the hero's front in clean stairs along
the light's diagonal), the rounded edges as crisp lines, the levels capped
toward the frame so rows and columns 0-1 and 126-127 stay dark; lone
pixels inside a tile take their neighbours' colour. The bag is drawn in
its own leaning frame: distance fields give its belly, shoulders, collar
and mouth, a sphere's normals its velvet levels (diffuse and a grazing
sheen), crisp rastered lines its gathers; the mouth is flat bands and the
peeking tiles, the knot and tassels hand stamps; the cord a band whose
twist is a diagonal pattern. The night is folderkit's with the bag's beam
and blooms, as levels; its lone pixels despeckled, the glints kept.
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
S = 4                                                           # samples a pixel, each way
_C = (np.arange(128 * S) + 0.5) / S
XS, YS = np.meshgrid(_C, _C)
EDGE = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))

OWN = {"bone": "#E4D4B2", "tan": "#A28C6E", "slate": "#4D5A8C", "wine": "#7A1030", "gold": "#E9AC3A"}
IVORY_R = ["black", "navy0", "navy1", "navy2", "slate", "tan", "bone", "cream"]   # the tiles, shading cool
VELVET_R = ["black", "wine", "red"]             # the bag
GLOW_R = ["black", "wine", "red", "gold", "cream"]   # the light in the bag

CAM = R.Camera((0.0, 2.6, 10.0), (0.0, 1.4, 0.0), fov=32)
KEY = (-0.5, 0.75, 0.45)                      # the key, in the picture's terms (right, up, toward us)

MOUTH_AT = (29.0, 85.0)                         # the bag's mouth on the picture: the light's source
LOOK = dict(centre=(70, 128), glow=(96, 70))    # the family's night: the glow behind the scene
BLOOM = (17.0, 1.0)                             # the bag's light in the air: radius, levels
BEAM = ((29.0, 85.0), (98.0, 48.0), 16.0, 1.8)   # a beam out of the mouth: from, toward, half angle, levels
BEAM_TOP = 54                                   # the row the beam fades out above (clear of the sign)

# the tiles, far to near: letter (words_tiles.txt), centre on the picture,
# size (px across), (yaw, pitch, roll) from facing the camera squarely (yaw
# +: its face turns right; pitch +: its top tips toward us; roll +:
# clockwise), the levels (IVORY_R) of its face and its top; the small tiles'
# letters are stamped upright at their font's size; glyph_at: the letter's
# middle on the face (-0.5..0.5)
TILES = [
    dict(ch="P", at=(37, 71), px=13.0, turn=(-30, 30, -7), face=5, top=6, glyph_at=(0.02, 0.08)),
    dict(ch="L", at=(54, 63), px=16.0, turn=(-38, 10, 7), face=6, top=6),
    dict(ch="A", at=(74, 62), px=19.5, turn=(-8, 30, -5), face=6, top=7),
    dict(ch="Y", at=(102, 100), px=43.0, turn=(-22, 15, 10), face=6, top=7, hero=True, thick=0.19),
]
HALF = (0.5, 0.5, 0.15)                         # a tile's half size (w, h, thickness; a tile's "thick" overrides it)
ROUND = 0.07
Y_AT = (-0.02, 0.12)                            # the hero's Y (words_y.txt): its middle on the face
HERO_BANDS = (0.15, 0.8)                        # cream to bone, bone to tan, along the face's light diagonal


# ---- helpers ------------------------------------------------------------------------

def half(t):
    return (HALF[0], HALF[1], t.get("thick", HALF[2]))


def glyphs():
    """The tiles' letters (words_tiles.txt beside this file): {letter: mask}."""
    out, cur = {}, None
    for ln in (HERE / "words_tiles.txt").read_text(encoding="utf-8").splitlines():
        if ln.startswith("// glyph "):
            cur = ln.split()[2]
            out[cur] = []
        elif cur and ln and not ln.startswith("//"):
            out[cur].append([c == "#" for c in ln])
    return {k: np.array(v, bool) for k, v in out.items()}


def at(sx, sy, dist):
    o, d = CAM.rays(np.array([float(sx)]), np.array([float(sy)]))
    return o[0] + d[0] * dist


def turn(axis, deg):
    a = np.radians(deg)
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def orient(yaw, pitch, roll):
    """A tile's rotation (local -> world): its face (local +z) toward the
    camera, its top (local +y) up the picture, then turned `yaw` about the
    picture's vertical (+: its face turns right), `pitch` about its
    horizontal (+: its top tips toward us), `roll` in the picture's plane
    (+: clockwise)."""
    f, u = -CAM.f, CAM.u
    B = np.stack([CAM.r, u, f], axis=1)
    M = turn(-CAM.f, -roll) @ turn(CAM.r, pitch) @ turn(u, yaw)
    return M @ B


def tile_render(cv, t):
    node = R.xf(R.prim(R.box(half(t), ROUND), 0), t["pos"], t["rot"], scale=t["size"])
    cx, cy = CAM.project(t["pos"])
    r = int(t["px"] * 0.9) + 4
    return R.render(cv, node, CAM, [R.Mat("#FFFFFF")], shadows=False, ao=False, ss=4,
                    region=(int(cx) - r, int(cy) - r, int(cx) + r, int(cy) + r))


def tile_pixels(cv, o, t):
    """Per pixel of a tile: mask, face (0 front, 1 top, 2 bottom, 3 left, 4
    right, 5 back), rounded-edge flag, mean world normal, mean local point;
    and per sample: the local point and the front-face flag."""
    s = cv.s
    rot, pos, size = t["rot"], np.asarray(t["pos"], float), t["size"]
    sel = (o["mat"] == 0) & (o["alpha"] > 0.5)
    m = ak.px_mean(sel.astype(np.float32), s) >= 0.5
    nrm = o["normal"].astype(np.float64)
    ln = nrm @ rot
    ax = np.argmax(np.abs(ln), -1)
    sg = np.take_along_axis(ln, ax[..., None], -1)[..., 0] > 0
    fc = np.select([(ax == 2) & sg, (ax == 1) & sg, (ax == 1) & ~sg, (ax == 0) & ~sg, (ax == 0) & sg], [0, 1, 2, 3, 4], 5)
    edge = np.sort(np.abs(ln), -1)[..., 1] > 0.3
    cnt = np.stack([ak.px_mean((sel & (fc == f)).astype(np.float32), s) for f in range(6)], -1)
    face = cnt.argmax(-1)
    nsel = np.maximum(ak.px_mean(sel.astype(np.float32), s), 1e-6)
    edge_px = ak.px_mean((sel & edge).astype(np.float32), s) / nsel > 0.5
    nmean = ak.px_mean(nrm * sel[..., None], s)
    nmean /= np.maximum(np.linalg.norm(nmean, axis=-1, keepdims=True), 1e-6)
    oa, da = CAM.rays(cv.X.reshape(-1).astype(np.float64), cv.Y.reshape(-1).astype(np.float64))
    dep = np.where(sel, o["depth"], 0.0).reshape(-1)
    hit = oa + da * dep[:, None]
    loc = ((hit - pos) @ rot / size).reshape(cv.N, cv.N, 3) * sel[..., None]
    lmean = ak.px_mean(loc, s) / nsel[..., None]
    return dict(m=m, face=face, edge=edge_px, n=nmean, l=lmean, loc=loc, front=sel & (fc == 0) & ~edge, sel=sel)


def face_pt(t, u, v):
    """A point of a tile's face (u right, v up, -0.5..0.5) on the picture."""
    return CAM.project(t["pos"] + t["rot"] @ np.array([u, v, half(t)[2]]) * t["size"])


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def tidy(m, passes=2):
    """A letter's pixels tidied: spurs (a pixel with one 4-neighbour or
    none) off, notches (a gap with three) filled."""
    for _ in range(passes):
        n = sum(ak.shift(m, dx, dy).astype(int) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        m = (m & (n >= 2)) | (~m & (n >= 3))
    return m


def lone_in(pic, m, keep=None):
    """Pixels of the mask m with no neighbour (of eight) of their colour
    inside m take the colour most of their neighbours inside m have."""
    a = pic.idx
    pa = np.pad(a, 1, mode="edge")
    pm = np.pad(m, 1)
    nb = [(pa[1 + dy:129 + dy, 1 + dx:129 + dx], pm[1 + dy:129 + dy, 1 + dx:129 + dx])
          for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
    same = np.zeros((128, 128), bool)
    for v, inm in nb:
        same |= inm & (v == a)
    lone = m & ~same
    if keep is not None:
        lone &= ~keep
    for y, x in zip(*np.nonzero(lone)):
        vals = [int(v[y, x]) for v, inm in nb if inm[y, x]]
        if vals:
            a[y, x] = max(set(vals), key=vals.count)


def facing(m, dx, dy, n=2):
    """How much each pixel's outward normal (from the mask smoothed) faces (dx, dy)."""
    b = fk._blur(m, n)
    gy, gx = np.gradient(b)
    nx, ny = -gx, -gy
    nn = np.hypot(nx, ny) + 1e-9
    return (nx * dx + ny * dy) / (nn * np.hypot(dx, dy))


# ---- the bag ------------------------------------------------------------------------
#
# A drawstring pouch of wine velvet, lower left, leaning right so its open
# mouth turns to the stream. Painted in its own frame (x right, y up its
# axis, from the neck where the cord cinches it): a round belly, the
# gathers fanning down from the cord, the ruffled collar above it flaring
# open; inside, the back of the collar in shade, the hole dark at the back
# and lit gold down inside, two tiles peeking over the front lip.

NECK_AT, LEAN = (27.0, 98.0), 9.0              # the neck on the picture; the bag's lean (degrees, right)
VEL = (0.55, 0.75, 1.9)                         # the velvet: base, diffuse, sheen (levels)
BELLY = (1.0, -20.0, 22.0, 20.0)                # its belly: an ellipse (middle, radii)
SHOULDER = [(-6.5, 0.5), (6.5, 0.5), (19.0, -12.0), (-17.0, -12.0)]
COLLAR = [(-6.0, -0.5), (6.0, -0.5), (14.5, 11.0), (-14.5, 11.0)]
OPENING = (0.0, 11.0, 15.0, 6.5)                # the mouth's rim: middle, radii
HOLE = (0.0, 10.6, 13.0, 5.2)                    # the dark inside it (the back of the collar shows above)
# the half width of the bag up its axis, for the gathers' paths
WIDTH = ([-42, -36, -28, -20, -13, -8, -4, -1, 0], [0, 12, 19.5, 22, 20.5, 15.5, 10.5, 7.2, 6.5])
GATHERS = [(-55, 11), (-30, 15), (-8, 17), (16, 15), (40, 11), (62, 8)]   # (azimuth deg, length)
# tiles in the mouth, back to front: middle (x, y), half sizes (w, h; a
# tile lying flat is seen squashed), turn (degrees)
PEEK = [("""
..cc...
.cbbbk.
cbbbbbt
bbbbbtt
.bbbttt
""", (18, 85)), ("""
cccccc
cbbbbt
cbbbbt
bbbbtt
""", (31, 86))]


def bag_xy(X, Y):
    """Picture points in the bag's frame."""
    a = np.radians(LEAN)
    dx, dy = X - NECK_AT[0], NECK_AT[1] - Y
    return dx * np.cos(a) - dy * np.sin(a), dx * np.sin(a) + dy * np.cos(a)


def bag_pic(x, y):
    """A point of the bag's frame on the picture."""
    a = np.radians(LEAN)
    return NECK_AT[0] + x * np.cos(a) + y * np.sin(a), NECK_AT[1] + x * np.sin(a) - y * np.cos(a)


def bag_key():
    a = np.radians(LEAN)
    kr, ku, kz = KEY
    k = np.array([kr * np.cos(a) - ku * np.sin(a), kr * np.sin(a) + ku * np.cos(a), kz])
    return k / np.linalg.norm(k)


def step_px(pic, pts, delta, ramp, where):
    """Moves the pixels at pts `delta` steps along the ramp (where they are on it)."""
    ids = [pic.pal[c] for c in ramp]
    for x, y in pts:
        if 0 <= x < 128 and 0 <= y < 128 and where[y, x]:
            v = int(pic.idx[y, x])
            if v in ids:
                pic.idx[y, x] = ids[int(np.clip(ids.index(v) + delta, 0, len(ids) - 1))]


def cov(m):
    return ak.px_mean(m.astype(np.float32), S)


def paint_bag(pic):
    """The velvet bag: its belly and gathers, its collar, its mouth and the
    tiles peeking out of it; returns its mask."""
    bx, by = bag_xy(XS, YS)
    Pb = (bx, by)
    belly = ak.ellipse(Pb, *BELLY)
    body_d = ak.smin(belly, ak.polygon(Pb, SHOULDER), 5.0)
    body_d = np.maximum(body_d, by - 0.5)
    collar_d = ak.union(ak.polygon(Pb, COLLAR), ak.ellipse(Pb, *OPENING))
    open_d = ak.ellipse(Pb, *OPENING)
    hole_d = ak.ellipse(Pb, *HOLE)
    body = cov(body_d < 0) >= 0.5
    collar = cov(collar_d < 0) >= 0.5
    opening = cov(open_d < 0) >= 0.5
    hole = cov(hole_d < 0) >= 0.5
    shape = body | collar
    x, y = bag_xy(X1, Y1)
    k = bag_key()

    # the belly: velvet, lit by the key (its shoulder up and left red, its
    # middle wine, its shade black), the gathers fanning down from the cord
    w = np.interp(y, *WIDTH)
    nx = np.clip((x - BELLY[0]) / np.maximum(w, 1e-3), -1, 1) * 0.95
    ny = np.clip((y - BELLY[1]) / BELLY[3], -1, 1) * 0.7
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    dif = nx * k[0] + ny * k[1] + nz * k[2]
    sheen = (1 - nz) ** 1.5 * np.clip(dif * 2.5, 0, 1)
    lv = VEL[0] + VEL[1] * np.clip(dif, 0, 1) + VEL[2] * sheen
    # its underside rounds away into the shade; the frame's last rows black
    ex, ey = (x - BELLY[0]) / BELLY[2], (y - BELLY[1]) / BELLY[3]
    lv -= 1.2 * smooth((np.hypot(ex, ey) - 0.7) / 0.25) * smooth((-ey - 0.1) / 0.4)
    cap = np.select([EDGE < 2, EDGE < 4], [0, 1], 2)
    lv = np.minimum(lv, cap)
    belly_m = body & ~collar
    ak.by_level(pic, fk.terrace_px(np.clip(lv, 0, 2), 1.0), VELVET_R, belly_m)
    # the gathers: crisp lines down the cloth from the cord, each a groove
    # a step darker with its ridge a step lighter beside it (toward the lamp)
    for az, ln in GATHERS:
        s_ = np.sin(np.radians(az))
        ys_ = np.linspace(-1.5, -1.5 - ln, 16)
        pts = [bag_pic(np.interp(v, *WIDTH) * s_, v) for v in ys_]
        line = ak.raster(pts)
        step_px(pic, [(x_, y_) for x_, y_, t_ in line if t_ < 0.85], -1, VELVET_R, belly_m)
        step_px(pic, [(x_ - 1, y_) for x_, y_, t_ in line if t_ < 0.55], +1, VELVET_R, belly_m & (cap >= 2))

    # the collar: pleats standing up from the cord to the rim, lit on the left
    hw = 6.0 + 8.5 * np.clip(y / 11.0, 0, 1)
    th = np.arcsin(np.clip(x / hw, -1, 1))
    lit = 0.5 - 0.5 * np.sin(th + 0.3)
    pl = 0.55 + 1.2 * lit + 0.55 * np.cos(5.0 * th + 0.6)
    front = collar & ~opening
    ak.by_level(pic, np.clip(np.round(pl), 0, 2), VELVET_R, front)

    # the mouth, in flat bands (no dither in so small a thing): the back of
    # the collar (wine; its top edge red where the lamp catches it), the
    # hole black at the back, lit down inside (wine, red, gold, a cream
    # heart low in front), the front lip gold where the light catches it
    back = opening & ~hole
    hx = x / HOLE[2]
    hy = (y - HOLE[1]) / HOLE[3]
    pic.put(back, "wine")
    edge = back & ~ak.shift(back, 0, 1)
    pic.put(edge & (x < 3), "red")
    r = np.hypot(hx / 0.95, (hy + 0.4) / 0.8)
    gl = np.select([hy > 0.3, hy > 0.05, r < 0.28, r < 0.62, r < 0.9], [0, 1, 4, 3, 2], 1)
    ak.put_levels(pic, hole, gl, GLOW_R)
    lip = back & (y < HOLE[1])
    pic.put(lip, "red")
    pic.put(lip & ak.shift(hole, 0, -1), "gold")
    fk.selout(pic, shape, "black")

    # two tiles' corners peeking over the front lip, on the light
    hidden = (body & ~collar) | front | lip
    peek = np.zeros((128, 128), bool)
    for rows, (ox, oy) in PEEK:
        m = stamp_px(pic, rows, int(round(ox)), int(round(oy)), where=~hidden)
        peek |= m
    return shape | peek


# the cord's knot, its two tails and their tassels, by hand (g gold, c
# cream, t tan, w wine, k black); its top-left from the knot's point
KNOT = """
.gcgg..
gcgggt.
.gtgtt.
.gt.gt.
gt...gt
gt...gt
ww...ww
gtg..gtg
gtg..gtg
gtt..gtt
g.t..g.t
"""
KNOT_AT = (-3, -1)
STAMP_KEY = {"g": "gold", "c": "cream", "t": "tan", "w": "wine", "k": "black", "b": "bone", "r": "red"}


def stamp_px(pic, rows, x, y, where=None):
    """Places a hand stamp with its top-left at (x, y); returns its mask."""
    out = np.zeros((128, 128), bool)
    for j, ln in enumerate(rows.strip("\n").splitlines()):
        for i, ch in enumerate(ln):
            if ch in STAMP_KEY and 0 <= x + i < 128 and 0 <= y + j < 128 and (where is None or where[y + j, x + i]):
                pic.px(x + i, y + j, STAMP_KEY[ch])
                out[y + j, x + i] = True
    return out


def paint_cord(pic):
    """The gold cord round the neck, a band 3 px deep twisted like a rope (a
    tan groove winding across it every 3 px), its knot and its two tails,
    each with a tassel."""
    x, y = bag_xy(X1, Y1)
    nw = np.interp(-0.5, *WIDTH) + 1.0
    t = np.arcsin(np.clip(x / nw, -1, 1))
    mid = -0.4 - 1.4 * np.cos(t)                                  # the band's middle: its front dips toward us
    band = (np.abs(x) <= nw) & (np.abs(y - mid) <= 1.5)
    tw = (XX + YY) % 3 == 0
    pic.put(band, "gold")
    pic.put(band & tw, "tan")
    pic.put(band & ~ak.shift(band, 0, -1), "tan")                 # its underside
    pic.put(band & ~ak.shift(band, 0, 1) & ~tw & (np.abs(x + 3.5) < 1.2), "cream")   # a glint on its top
    kx, ky = bag_pic(2.6, -2.0)
    knot = stamp_px(pic, KNOT, int(round(kx)) + KNOT_AT[0], int(round(ky)) + KNOT_AT[1])
    cords = band | knot
    fk.selout(pic, cords, "black")
    return cords


# ---- the tiles ----------------------------------------------------------------------

def paint_tile(pic, cv, t, key):
    """A tile: each face flat, a level of IVORY_R (the hero's face falling
    off from the corner nearest the lamp in clean 2-1 stairs), its rounded
    edges crisp lines, its letter cut in black."""
    G = t["G"]
    m = G["m"] = tidy(G["m"], 1)
    rot = t["rot"]
    axes = [rot[:, 2], rot[:, 1], -rot[:, 1], -rot[:, 0], rot[:, 0], -rot[:, 2]]
    F, T = t["face"], t["top"]
    lv = np.zeros((128, 128))
    for f in range(6):
        fm = m & (G["face"] == f)
        d = float(axes[f] @ key)
        lv[fm] = F if f == 0 else T if f == 1 else (F - 1 if d > 0.3 else F - 2)
    if t.get("hero"):
        # the face falls off along the light's diagonal in even stairs
        g = XX + 2 * YY
        (ax_, ay_), (bx_, by_) = face_pt(t, -0.5, 0.5), face_pt(t, 0.5, -0.5)
        g0, g1 = ax_ + 2 * ay_, bx_ + 2 * by_
        c1, c2 = g0 + HERO_BANDS[0] * (g1 - g0), g0 + HERO_BANDS[1] * (g1 - g0)
        fm = m & (G["face"] == 0) & ~G["edge"]
        lv[fm] = np.select([g < c1, g < c2], [7, 6], 5)[fm]
    # the rounded edges: a crisp line, its level by how it meets the key
    em = m & G["edge"]
    de = G["n"][em] @ key
    lv[em] = np.select([de > 0.62, de > 0.3], [T + (1 if T < 7 else 0), F], F - 1)
    if t.get("hero"):                                              # its lit rim, unbroken
        dfull = G["n"] @ key
        lv[em & (dfull > 0.3) & (facing(m, -1, -1.4) > 0.2)] = 7
    # the frame's vignette where it runs off the picture
    lv = np.minimum(lv - np.round(fk.edge_dark(X1, Y1) * 1.5), np.select([EDGE < 1, EDGE < 2, EDGE < 3], [2, 3, 4], 7))
    ak.put_levels(pic, m, np.clip(lv, 2, 7).astype(int), IVORY_R)
    if not t.get("hero"):                                          # small: the glyph upright at its own size
        gm = t["glyph"]
        cx, cy = t.get("glyph_at", (-0.02, 0.03))
        x, y = face_pt(t, cx, cy)
        h, w = gm.shape
        let = ak.place(gm, int(np.floor(x - w / 2 + 0.5)), int(np.floor(y - h / 2 + 0.5))) & m
    else:
        let = hero_glyph(t) & m
    pic.put(let, "black")
    if t.get("hero"):                                              # the cut's lit wall: its lower right
        ring = let & ~ak.erode(let, 1)
        wall = ring & (facing(let, 1, 0.25, 1) > 0.75)                 # its upright walls only: no dashes on the slants
        wall &= ak.nbrs(wall, diag=True)
        pic.put(wall, "tan")
    return m, let


def hero_glyph(t):
    """The hero's Y: drawn by hand at its size, turned with the tile
    (words_y.txt beside this file), its middle on the face's Y_AT."""
    rows = [ln for ln in (HERE / "words_y.txt").read_text(encoding="utf-8").splitlines()
            if ln and not ln.startswith("//")]
    g = np.array([[c == "#" for c in ln] for ln in rows], bool)
    h, w = g.shape
    x, y = face_pt(t, *Y_AT)
    return ak.place(g, int(np.floor(x - w / 2 + 0.5)), int(np.floor(y - h / 2 + 0.5)))


# ---- the night ----------------------------------------------------------------------

def paint_sky(pic, blooms):
    """The family's night and the light out of the bag: a bloom at its
    mouth and a beam up through the air the tiles fly in, fading out below
    the sign; `blooms` light the air round other bright points."""
    mx, my = MOUTH_AT
    look = dict(LOOK, blooms=[(mx, my - 3, *BLOOM), *blooms])
    lv = fk.sky_level(X1, Y1, **look)
    lb = fk.sky_level(X1, Y1, **look, beam=BEAM)
    lv = lv + (lb - lv) * np.clip((Y1 - BEAM_TOP) / 8.0, 0, 1)
    ak.by_level(pic, fk.terrace_px(lv, 1.5), fk.NIGHT_R, np.ones((128, 128), bool))


# ---- the flight ---------------------------------------------------------------------

# speed lines behind the Y, back along its flight from the bag's mouth: the
# row they leave its trailing edge on, the gap (px), length, rise toward
# the bag (px), radius at the root
TRAILS = [(84, 3, 22, -5, 1.3), (93, 3, 29, -6, 1.6), (104, 3, 16, -3, 1.1)]
# the small tiles' wakes, curving back down toward the mouth they rose out
# of: (tile, row, gap, length, drop toward the bag, radius at the root)
WAKES = [(0, 67, 2, 8, 7, 1.0), (0, 72, 2, 5, 5, 0.8), (1, 57, 2, 9, 6, 1.0), (1, 61, 2, 6, 4, 0.8)]
TRAIL_COLS = (("bone", 0.25), ("tan", 0.6), ("slate", 1.0))
FLASH_AT = (0.18, 0.53)                                           # where on the hero (u, v; 0.5 the rim)
FLASH = (6, 5, 7, 4)                                              # the hero's star: arms left, right, up, down


def paint_trails(pic, hero, masks):
    """The speed lines behind the Y and the wakes behind P and L, a few px
    off their trailing edges; returns their mask."""
    out = np.zeros((128, 128), bool)
    near = np.zeros((128, 128), bool)
    for m in masks:
        near |= ak.dilate(m, 2)
    for k, row, gap, ln, drop, r0 in WAKES:
        xs = np.nonzero(masks[k][row])[0]
        rx = xs.min() - gap
        out |= ak.streak(pic, (rx, row + 0.5), (rx - ln * 0.55, row + 0.5 + drop * 0.35), (rx - ln, row + 0.5 + drop), r0, 0.3,
                         ok=(YY >= fk.OBJECT_TOP + 3) & ~near, cols=TRAIL_COLS)
    for row, gap, ln, rise, r0 in TRAILS:
        xs = np.nonzero(hero[row])[0]
        rx = xs.min() - gap
        out |= ak.streak(pic, (rx, row + 0.5), (rx - ln * 0.5, row + 0.5 + rise * 0.2), (rx - ln, row + 0.5 + rise),
                         r0, 0.3, ok=(YY >= fk.OBJECT_TOP + 3) & ~ak.dilate(hero, 1), cols=TRAIL_COLS)
    return out


def star(pic, x, y, arms, light):
    """A four-pointed flash: a cream heart (the core and its four
    neighbours), its arms cream turning gold toward their tips (gold all
    along where they cross the lit tile), a cream pixel on each diagonal
    that falls on the dark."""
    for (dx, dy), arm in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for i in range(1, arm + 1):
            x_, y_ = x + dx * i, y + dy * i
            if 0 <= x_ < 128 and 0 <= y_ < 128:
                inner = i <= 1 or (i <= arm * 0.4 and not light[y_, x_])
                pic.px(x_, y_, "cream" if inner else "gold")
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        if not light[y + dy, x + dx]:
            pic.px(x + dx, y + dy, "cream")
    pic.px(x, y, "cream")


# ---- the picture --------------------------------------------------------------------

def draw():
    P = fk.palette(OWN, ramps=[IVORY_R, VELVET_R, GLOW_R])
    pic = ak.Picture.blank(P, "navy0")
    cv = ak.Canvas("#000000")
    key = KEY[0] * CAM.r + KEY[1] * CAM.u - KEY[2] * CAM.f
    key /= np.linalg.norm(key)

    k = np.tan(np.radians(CAM.fov) / 2)
    gl = glyphs()
    stream = [dict(t) for t in TILES]
    for t in stream:
        dist = 64.0 / (t["px"] * k)                              # a unit tile, t["px"] across
        t["pos"] = at(*t["at"], dist)
        t["rot"] = orient(*t["turn"])
        t["size"] = 1.0
        t["glyph"] = gl[t["ch"]]
        t["G"] = tile_pixels(cv, tile_render(cv, t), t)
    hero = stream[-1]
    fx, fy = face_pt(hero, *FLASH_AT)                             # the hero's top rim, near its corner: its flash
    hm = hero["G"]["m"]
    ys, xs = np.nonzero(hm & ~ak.shift(hm, 0, 1))                 # its top edge
    j = np.argmin(np.hypot(xs - fx, ys - fy))
    flash = (int(xs[j]), int(ys[j]))

    paint_sky(pic, blooms=[(flash[0], flash[1], 16.0, 0.8)])
    paint_trails(pic, hero["G"]["m"], [t["G"]["m"] for t in stream])
    bag = paint_bag(pic)
    bag |= paint_cord(pic)

    tiles = np.zeros((128, 128), bool)
    mx, my = MOUTH_AT
    for t in stream:
        m, let = paint_tile(pic, cv, t, key)
        fk.selout(pic, m, "black")
        pic.put(ak.dilate(m, 1) & ~m & tiles, "black")           # a seam where it overlaps a tile behind
        if not t.get("hero"):
            # the light out of the bag catches the edges turned to it
            foot = m & ~ak.shift(m, 0, -1) & ~let
            foot &= (ak.runs(foot, 1) >= 3) & (facing(m, mx - t["at"][0], my - t["at"][1]) > 0.3)
            pic.put(foot, "gold")
        lone_in(pic, m, keep=let)
        tiles |= m

    ak.despeckle(pic, 5, within=(YY >= fk.OBJECT_TOP) & ~tiles)
    ak.despeckle(pic, 4, within=(YY >= fk.OBJECT_TOP) & ~tiles & ~bag)      # the night's seams
    star(pic, *flash, FLASH, pic.where("cream", "bone", "tan", "gold"))
    for x, y, c in [(flash[0] - 12, flash[1] - 9, "gold"), (14, 66, "gold")]:
        fk.twinkle(pic, x, y, arm=c)
    fk.word(pic, "words", glints=[(3, 4, 2)])
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "words.png"))
