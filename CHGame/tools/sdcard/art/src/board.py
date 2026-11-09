"""tools/sdcard/art/board.png: the BOARD folder's cover on the casino card
(it holds Backgammon, Boardwalk, Checkers, Chess, Four in a Row, Snakes &
Ladders, Tic Tac Toe). `python tools/sdcard/covers.py` redraws it; edit
this, not the PNG. The folders' shared look is folderkit.py, beside this
file (cards.py is its worked example).

THE BRIEF (revision 2)
  Message: this way to the board games. The two great pieces of the board,
  the chess knight and the checker, meet in a spotlight on a checkerboard
  at night: the red king checker hops up into the light, spinning, and its
  lip flashes; the polished ivory knight turns its head to stare at it.

  Composition (a folder: a sign over a door, then what is inside; read in
  this order):
  - The sign: BOARD in the family's ice chrome on its navy panel and
    rainbow neon tube, rows 1 to 48 (folderkit.word). Calm night round it.
  - The hero: a Staunton knight in polished ivory, right of centre, the
    whole height under the sign (ear tips on row 51), in profile facing
    left, turned a little to us, its gold collar a ring round the foot at
    the bottom frame. Lit by the key: cream only in a band a few pixels deep
    along the edges that face the lamp (brow, bridge of the nose, muzzle,
    chest, the foot's left), bone1 the side turned to us, bone0 the neck
    behind the jaw with a tapered polished streak (bone1, a cream core)
    down its curve, the far rim slate, black outline on the shadow side.
    Carved: a mane of five ridges (a bone1 ridge over a black groove, each
    notched into the crest), the jowl (a cream crescent, its jaw line in
    bone0), an almond eye under its brow with a catch-light, a flared
    nostril, the mouth. It is the brightest, biggest thing under the sign.
  - The second: the red checker, a king, in the air at the left at the
    knight's eye level: thick (its edge a wine band in shade, finely reeded
    only where the lamp reaches it), a raised lip round the face (cream
    toward the lamp) with the face sunk inside it (a wine ring), a gold
    crown embossed in the middle (stamped by hand). Its lip flashes into
    the night (the family's flash, as on CARDS' ace: a cream star whose
    arms turn gold at the tips, one gold spark); two spin arcs whip round
    its lower left, cream at the head, red, then wine.
  - The ground: a checkerboard in perspective, turned 32 degrees, small
    squares each one flat colour from a pool of light between the pieces
    (slate and navy1 there, falling to navy and the night at the back and
    toward the frame). The checker's shadow below it and the knight's to
    the lower right drop the squares a level or two (never to black).
  - Behind: the night (folderkit), a spotlight shaft slanting in from the
    top left under the sign (hard edges stepping evenly, 3-1 and 3-2),
    onto the checker and the pool. The bottom two rows one dark value.
  - Light: the house key from the top left: lit faces warm (ivory, red,
    gold), shadows cool (slate, navy), black only for outlines and grooves.
  Reading order: the sign; the ivory knight; the red checker and its
  flash; the board.

  Thumbnail (128 x 128), x across:
      rows   1-48   x 18-110  the sign: [ B O A R D ] in its neon frame
      rows  50-100  x  0-60   the spotlight shaft from the top left
      rows  51-125  x 62-108  the knight (ears, eye, muzzle, mane, chest)
      rows  53-66   x 15-36   the flash on the checker's upper-left lip
      rows  59-99   x 14-57   the checker; its spin arcs x 5-35, rows 80-106
      rows  66-127  x  0-127  the checkerboard, its pool between the pieces
      rows 105-125  x 20-60   the checker's shadow (under the install bar)
      rows 116-125  x 72-108  the gold collar round the knight's foot

PALETTE (folderkit's 6 + 5 own + cream, black, red; the rainbow is the neon)
  navy0 navy1 navy2   the night, the shaft, the board's squares, the sign's
                      panel and extrusion
  ice0 ice1 ice2      the sign's face only (the title's reserved colours)
  bone0 bone1         the ivory, warm (cream its lit edges and glints)
  slate               the board's lit squares; the knight's far rim only
  wine                the checker's edge, its ring, the crown's emboss,
                      the spin arcs' tails, the collar's shaded end
  gold                the crown, the knight's collar, the flash's tips
  red                 the checker (black only its outline)

LETTERING: BAZAR (bmf collection), "freeware; authors vary, few gave terms"
  (a `?` face: it wants the credits row in docs/cover-art.md), at its own
  size, from folderkit's word_board.txt.

HOW IT IS PAINTED: render3d marches the knight (a lathe foot and the head's
profile, its crest notched at the mane's grooves, given rounded depth, with
a jowl, a brow and two cone ears) and the checker (a rounded cylinder,
turned to a chosen face normal) once for which piece each pixel shows and
once at the pixel centres for the point and the normal. Every surface is
then coloured on the pixels as levels of its ramp, in flat bands with
1-px seams; the carving, the collar, the reeding and the crown are clean
1-px lines and hand stamps placed through the camera. The board's squares
come from where each pixel's ray meets the floor; the shadows from
render3d's ground(), each piece with its own light so both fall down and
to the right.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import folderkit as fk  # noqa: E402  (puts the repository's tools/ on the path)
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402
from artkit import render3d as R  # noqa: E402
from artkit import canvas as CV  # noqa: E402

YY, XX = fk.YY, fk.XX

OWN = {"bone0": "#A28A66", "bone1": "#E2CFA8", "slate": "#4A5A8E", "wine": "#741030", "gold": "#E9AC3A"}
IVORY_R = ["black", "slate", "bone0", "bone1", "cream"]
RED_R = ["black", "wine", "red", "cream"]
BOARD_R = ["black", "navy0", "navy1", "navy2", "slate"]
KEY = np.array([-0.55, 0.75, 0.45])
KEY /= np.linalg.norm(KEY)
SHADOW_L = np.array([-0.15, 1.0, 0.45])                # the checker's shadow: from above, a little in front
SHADOW_L /= np.linalg.norm(SHADOW_L)
KNIGHT_SHADOW_L = np.array([-0.55, 0.75, -0.25])       # the knight's: down and right of its foot

# ---- the knight: its own frame has the profile facing -x, the foot on y 0 ---------------------
KNIGHT, CHECKER = 0, 1
NMAT = 2
KNIGHT_BASE = [(0, 0), (0.43, 0), (0.43, 0.06), (0.40, 0.09), (0.39, 0.13), (0.43, 0.17), (0.38, 0.20),
               (0.32, 0.22), (0.28, 0.27), (0.0, 0.30)]
HEAD = [(0.30, 0.27), (0.36, 0.42), (0.38, 0.58), (0.37, 0.75), (0.33, 0.95), (0.27, 1.12), (0.19, 1.28),
        (0.10, 1.40), (0.02, 1.46), (-0.06, 1.47), (-0.14, 1.43), (-0.21, 1.36), (-0.27, 1.29), (-0.35, 1.21),
        (-0.46, 1.10), (-0.56, 1.00), (-0.63, 0.92), (-0.66, 0.86), (-0.65, 0.80), (-0.60, 0.775),
        (-0.55, 0.77), (-0.60, 0.745), (-0.58, 0.70), (-0.50, 0.665), (-0.38, 0.665), (-0.25, 0.68),
        (-0.17, 0.74), (-0.12, 0.72), (-0.15, 0.62), (-0.20, 0.50), (-0.26, 0.40), (-0.28, 0.32), (-0.24, 0.27)]
EARS = [((0.00, 1.40, 0.06), (0.03, 1.66, 0.07)), ((0.10, 1.36, -0.05), (0.18, 1.60, -0.06))]
CHEEK = (-0.24, 0.86, 0.14, 0.13)                       # the jowl's bulge: middle (x, y), radii
BROW = (-0.22, 1.27, 0.08)                              # the brow's bulge: middle (x, y), radius
ROUND = 0.11                                            # the head's edges' rounding
THICK = (0.20, 0.14)                                    # its half thickness: at the neck, at the muzzle
KNIGHT_AT = np.array([0.66, 0.0, 0.25])
KNIGHT_TURN = 14.0                                      # its face a little toward us (degrees about y)
KNIGHT_S = 1.10

# its carving (in its own frame)
SPLIT = [(0.08, 1.42), (0.04, 1.24), (0.0, 1.08), (-0.06, 0.97), (-0.09, 0.90), (-0.10, 0.84), (-0.13, 0.78),
         (-0.16, 0.745), (-0.10, 0.70), (-0.05, 0.60), (0.0, 0.48), (0.05, 0.36), (0.07, 0.28)]   # face | neck
SEAM_PX = 0.024                                         # a pixel, in the knight's own units
COLLAR = (0.43, 0.175, 3)                               # the collar: radius, height, rows
HOT = (0.70, 5)                                         # cream: the key's diffuse past this, this many px deep
STREAK = [(0.17, 1.12), (0.13, 0.96), (0.12, 0.80), (0.135, 0.62), (0.17, 0.46), (0.21, 0.34)]
STREAK_W = (0.06, 0.018)                                # its half width (bone1), its core (cream)
MANE = [(0.10, 1.40), (0.19, 1.28), (0.27, 1.12), (0.33, 0.95), (0.37, 0.75), (0.38, 0.58), (0.36, 0.42)]
RIDGES = (5, 0.19, 0.03, 0.84)                          # how many, how deep in (units), how far down, crest share
NOTCH = (0.045, 0.045)                                  # the crest's notch at each groove: depth, half width
EYE = (-0.25, 1.21)                                     # the eye's middle
EYE_PX = ["...bbbb",                                   # the eye, by hand: its brow (bone0) over an
          "..b####",                                    # almond (black) slanting down to the front,
          ".##CC##",                                    # a catch-light (cream)
          "###C##.",
          ".###..."]
EYE_KEY = {"b": "bone0", "#": "black", "C": "cream"}
NOSTRIL = (-0.58, 0.90, 0.035, 0.025)
MOUTH = ((-0.605, 0.772), (-0.47, 0.765))

# ---- the checker: a cylinder along its own y ------------------------------------------------------
CHECKER_R, CHECKER_H = 0.53, 0.14                      # radius, half thickness
CHECKER_ON = (36.0, 79.0, 0.35)                         # its middle on the picture (x, y) and its depth (world z)
CHECKER_FACE = ((-0.35, 0.80, 0.50), 0.0)             # its face's normal (up left, toward us); the crown's turn
REED = 12.0                                             # the reeded edge's ridges (degrees)
EDGE_LIT = 0.25                                        # the edge is red where the key's diffuse passes this
RECESS = 0.80                                           # the face's raised lip ends here (of the radius)
CROWN = ["C.......C.......g",                         # the king's crown, by hand: gold, cream glints
         "gg.....gCg.....gg",                         # on its points, embossed (wine below and right)
         "ggg...ggggg...ggg",
         "gggg.ggggggg.gggg",
         "ggggggggggggggggg",
         "ggggggggggggggggg",
         "ggggggggggggggggg",
         ".ggggggggggggggg."]
CROWN_KEY = {"g": "gold", "C": "cream"}
FLASH = (7, 5, 5, 2)                                    # the lip's flash: arms left, right, up, down
FLASH_OUT = 3.0                                         # its middle, out from the lip into the night (px)
FLASH_DIR = 128.0                                       # where on the lip it flashes (degrees on the picture, y up)
LIP_ARC = 58.0                                          # the lit lip: degrees either side of the flash
SPARKS = [(-7, 10), (11, -7)]                           # its sparks, from the flash
SPIN = [(3.0, 276.0, 188.0, 1.8), (7.5, 262.0, 198.0, 1.4)]   # spin arcs: out from the rim (px), from, to (deg), radius

# ---- the board, the camera, the night ------------------------------------------------------------
BOARD_YAW = 32.0                                        # the squares' rows run on the diagonal
SQUARE = 0.50                                           # a square's side
POOL = (-0.1, -0.7, 1.9, 1.4)                             # the pool of light on it: middle (x, z), radii
FOG = (9.0, 1.4)                                        # whole squares fade out from this far, over this
CAM_AT = ((0.0, 3.0, 6.2), (0.0, 0.75, 0.0), 28.0)      # position, target, field of view
EAR_Y = 50.0                                            # the knight's ear tip's row (about)
KNIGHT_X = 90.0                                         # the knight's axis's column
LOOK = dict(centre=(70, 100), glow=(76, 50))
BEAM = ((-75.0, 25.0), 1 / 3, 2 / 3, 1.0, (118.0, 165.0))   # the spotlight: its source, its edges' slopes
                                                        # (even 3-1 and 3-2 steps), its lift, where it fades


# ---- geometry --------------------------------------------------------------------------------------

def smin(a, b, k):
    s = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * s - k * s * (1 - s)


def cone(p, a, b, r0, r1):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - a - t[:, None] * ab, axis=1) - (r0 + (r1 - r0) * t)


def head_sdf(p):
    """The horse's head: its profile (HEAD) given depth, thinner toward the
    muzzle, every edge well rounded; a jowl, a brow and two ears."""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    r = ROUND
    d2 = CV.polygon((x, y), head_poly()).astype(np.float64)
    h = THICK[0] - (THICK[0] - THICK[1]) * np.clip((-x - 0.05) / 0.55, 0, 1)
    a = d2 + r
    b = np.abs(z) - h + r
    d = np.minimum(np.maximum(a, b), 0) + np.hypot(np.maximum(a, 0), np.maximum(b, 0)) - r
    cx, cy, rx, ry = CHEEK
    cheek = (np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + (z / 0.17) ** 2) - 1.0) * 0.11
    d = smin(d, cheek, 0.04)
    bx, by, br = BROW
    brow = np.sqrt((x - bx) ** 2 + (y - by) ** 2 + (np.abs(z) - 0.10) ** 2) - br
    d = smin(d, brow, 0.05)
    e = np.minimum(*[cone(p, a_, b_, 0.075, 0.025) for a_, b_ in EARS])
    return smin(d, e, 0.03)


def path_len(pts):
    return float(np.sum(np.hypot(*np.diff(np.asarray(pts, float), axis=0).T)))


def inward(tx, ty):
    """The way into the head from its back contour (toward the face)."""
    ix, iy = -ty, tx
    return (-ix, -iy) if ix > 0 else (ix, iy)


def grooves():
    """Where the mane's grooves meet the crest: arc lengths along MANE."""
    n_r, deep, drop, share = RIDGES
    L = path_len(MANE)
    return [L * (0.04 + share * (k + 0.5) / n_r) for k in range(n_r)]


_POLY = []


def head_poly():
    """HEAD with a notch cut into the crest at each of the mane's grooves."""
    if not _POLY:
        ns = grooves()
        pts = []
        for s in np.linspace(0, path_len(MANE), 200):
            x, y = point_along(MANE, s)
            ix, iy = inward(*tangent_along(MANE, s))
            cut = NOTCH[0] * max(max(0.0, 1 - abs(s - sk) / NOTCH[1]) for sk in ns)
            pts.append((x + ix * cut, y + iy * cut))
        _POLY.extend([HEAD[0]] + pts[::-1] + HEAD[8:])
    return _POLY


def knight_rot():
    return R.rot_y(KNIGHT_TURN)


def knight_point(q):
    """A point in the knight's own frame, in the world."""
    return KNIGHT_AT + knight_rot() @ (np.asarray(q, float) * KNIGHT_S)


def knight_local(p):
    """World points (..., 3) in the knight's own frame."""
    return ((p - KNIGHT_AT) @ knight_rot()) / KNIGHT_S


def side_z(x):
    """The knight's flat side (toward us) at its own x."""
    return THICK[0] - (THICK[0] - THICK[1]) * np.clip((-x - 0.05) / 0.55, 0, 1)


def on_side(cam, pts):
    """Points (x, y) on the knight's flat side to picture points."""
    return [tuple(float(v) for v in cam.project(knight_point((x, y, side_z(x))))) for x, y in pts]


def checker_rot():
    """The checker's frame (columns: across its face, its axis, down its
    face): its face turned to CHECKER_FACE's normal, the crown upright but
    for the turn."""
    n = np.asarray(CHECKER_FACE[0], float)
    n /= np.linalg.norm(n)
    up = np.array([0.0, 1.0, 0.0]) - n[1] * n
    up /= np.linalg.norm(up)
    a = np.radians(CHECKER_FACE[1])
    up = up * np.cos(a) + np.cross(n, up) * np.sin(a)
    e3 = -up
    e1 = np.cross(n, e3)
    return np.stack([e1, n, e3], 1)


def camera():
    """The camera, slid (a lens shift) so the knight's ear tip lands on row
    EAR_Y and its axis on column KNIGHT_X."""
    pos, tgt, fov = CAM_AT
    c = R.Camera(pos, tgt, fov=fov)
    _, ey = c.project(knight_point(EARS[0][1]))
    ax, _ = c.project(knight_point((0, 0, 0)))
    return R.Camera(pos, tgt, fov=fov, shift=(KNIGHT_X - ax, EAR_Y - (ey - 0.075 * KNIGHT_S * 30)))


def checker_at(cam):
    """The checker's middle in the world: on the picture at CHECKER_ON, at its depth."""
    sx, sy, z = CHECKER_ON
    o, d = cam.rays(np.array([sx]), np.array([sy]))
    t = (z - o[0, 2]) / d[0, 2]
    return o[0] + d[0] * t


def scene(cam, which=(KNIGHT, CHECKER)):
    parts = []
    if KNIGHT in which:
        kn = R.SU(R.prim(R.lathe(KNIGHT_BASE), KNIGHT), R.prim(head_sdf, KNIGHT), 0.05)
        parts.append(R.xf(kn, KNIGHT_AT, knight_rot(), scale=KNIGHT_S))
    if CHECKER in which:
        parts.append(R.xf(R.prim(R.cylinder(CHECKER_R, CHECKER_H, 0.05), CHECKER), checker_at(cam), checker_rot()))
    return R.U(*parts) if len(parts) > 1 else parts[0]


def geometry(cam, sc):
    """Per pixel: the piece (the majority of 16 samples), and at the pixel's
    centre the point and the normal."""
    big = ak.Canvas("#000000")
    out = R.render(big, sc, cam, [R.Mat("#FFFFFF", spec=0.0)] * NMAT, ss=2, shadows=False, ao=False)
    mat = R.majority(out, big.s)
    one = ak.Canvas("#000000", ss=1)
    o1 = R.render(one, sc, cam, [R.Mat("#FFFFFF", spec=0.0)] * NMAT, ss=None, shadows=False, ao=False)
    o, d = cam.rays((XX + 0.5).reshape(-1).astype(np.float64), (YY + 0.5).reshape(-1).astype(np.float64))
    dep = o1["depth"].reshape(-1)
    hit = np.isfinite(dep)
    z = np.where(hit, dep, 0)
    p = o + d * z[:, None]
    n = o1["normal"].reshape(-1, 3).astype(np.float64)
    return dict(mat=mat, p=p.reshape(128, 128, 3), n=n.reshape(128, 128, 3), o=o, d=d)


def bands(l, cuts):
    """A value through flat bands: cuts [(threshold, level)] ascending."""
    out = np.full(l.shape, float(cuts[0][1]))
    for c, v in cuts[1:]:
        out = np.where(l >= c, float(v), out)
    return out


def ellipse_d(lx, ly, cx, cy, rx, ry, deg=0.0):
    """An ellipse's distance (roughly, in its radii) in a plane's own coordinates."""
    t = np.radians(deg)
    dx, dy = lx - cx, ly - cy
    u = dx * np.cos(t) + dy * np.sin(t)
    v = -dx * np.sin(t) + dy * np.cos(t)
    return np.hypot(u / rx, v / ry) - 1.0


def box_blur(m, n=2):
    """A mask box-blurred over (2n+1)^2 pixels, as floats."""
    a = np.pad(m.astype(np.float64), n, mode="edge")
    c = np.pad(np.cumsum(np.cumsum(a, 0), 1), ((1, 0), (1, 0)))
    k = 2 * n + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def step_down(pic, m, steps):
    """Recolours m by `steps` [(from, to)], all read from the pixels as they were."""
    cur = pic.idx.copy()
    for a_, b_ in steps:
        pic.put(m & (cur == pic.pal[a_]), b_)


def arc(cx, cy, rx, ry, a0, a1, n=24):
    """Points on an ellipse's arc, angles in degrees (y up)."""
    a = np.radians(np.linspace(a0, a1, n))
    return list(zip(cx + rx * np.cos(a), cy + ry * np.sin(a)))


# ---- the knight ----------------------------------------------------------------------------

def paint_knight(pic, G, kn, cam):
    """The ivory knight, carved and polished. Its flat side in zones drawn
    in its own profile plane (so they follow the perspective): the face
    bone with cream bands where the brow, the bridge of the nose and the
    chest meet the lamp, the neck a step down with a polished streak; the
    rounded edges turned from the key a step or two down; then the carving
    as clean lines: the mane's ridges, the jowl, the eye, the nostril, the
    mouth. Returns the pixels to keep from the clean-up."""
    lp = knight_local(G["p"])
    ln = G["n"] @ knight_rot()
    kl = knight_rot().T @ KEY
    lx, ly, lz = lp[..., 0], lp[..., 1], lp[..., 2]
    dif = (ln * kl).sum(-1)
    base = kn & (ly < 0.29)
    head = kn & ~base
    keep = np.zeros((128, 128), bool)
    sy, sx = zip(*sorted((y_, x_) for x_, y_ in SPLIT))
    neck = lx > np.interp(ly, sy, sx)
    # the light by the key: bone1 the side to us, bone0 and the far rim in slate where it turns away;
    # cream only in a band a few pixels deep along the edges that face the lamp (a 50% seam)
    de = ak.distance_px(~kn, 8)
    lv = bands(dif, [(-9, 1), (-0.15, 2), (0.15, 3)])
    hot = dif > HOT[0]
    cream = np.where(hot & (de <= HOT[1]), 4.0, np.where(hot & (de <= HOT[1] + 1), 3.5, 0.0))
    # the neck a step down behind the jaw, with a polished streak down it
    st = ak.tube((lx, ly), STREAK, [1e-3])
    t = np.clip(st["s"] / st["len"], 0, 1)
    taper = np.sin(np.pi * t) ** 0.8
    w0 = STREAK_W[0] * taper
    sk = np.where(st["d"] < w0, 3.0, np.where(st["d"] < w0 + SEAM_PX, 2.5, 2.0))
    sk = np.where((st["d"] < STREAK_W[1] * taper) & (t > 0.28) & (t < 0.72), 4.0, sk)
    lv = np.where(neck & (dif >= 0.15), sk, lv)
    lv = np.maximum(lv, np.where(neck & (lx > 0.0), 0.0, cream))
    # the ears: by the key; the far one in shade
    ears = head & (ly > 1.40) & (lx > -0.08)
    lv = np.where(ears, bands(dif, [(-9, 1), (-0.1, 2), (0.3, 3), (0.62, 4)]), lv)
    lv = np.where(ears & (lz < 0.0), np.minimum(lv, 2.0), lv)
    ak.by_level(pic, lv, IVORY_R, head, q=2)
    rim = kn & ~ak.erode(kn, 1)
    pic.put(kn & pic.where("slate") & ~(rim & (lx > 0.05)), "bone0")    # slate only as the far rim
    gy, gx = np.gradient(box_blur(kn, 2))
    up_left = (gx + gy) / (np.hypot(gx, gy) + 1e-9) / np.sqrt(2)          # the outward normal toward the lamp
    near = head & rim & (lz >= -0.02)
    pic.put(near & (up_left > 0.35) & pic.where("bone0", "slate"), "bone1")
    pic.put(head & rim & (up_left > 0.6) & (lx < 0.05), "cream")
    # the foot: lit left, shaded right, in flat bands; the gold collar
    nxz = np.maximum(np.hypot(ln[..., 0], ln[..., 2]), 1e-6)
    c = (ln[..., 0] * kl[0] + ln[..., 2] * kl[2]) / nxz / np.hypot(kl[0], kl[2])
    lb = bands(c, [(-9, 1), (-0.55, 2), (0.0, 3)])
    lb = np.where((c > 0.6) & (de <= HOT[1]), 4.0, lb)
    ak.by_level(pic, lb, IVORY_R, base, q=1)
    pic.put(base & pic.where("slate") & ~rim, "bone0")
    # the gold collar: its near half, a band of clean lines round the foot
    pts = []
    for a in np.radians(np.arange(0, 360, 3)):
        q = np.array([np.cos(a), 0.0, np.sin(a)])
        w = knight_point(q * COLLAR[0] + np.array([0, COLLAR[1], 0]))
        if (knight_rot() @ q) @ (cam.pos - w) > 0:
            lit = (np.cos(a) * kl[0] + np.sin(a) * kl[2]) / np.hypot(kl[0], kl[2])
            pts.append((a, cam.project(w), lit))
    pts.sort(key=lambda e: e[1][0])
    for dy in range(COLLAR[2]):
        for i in range(len(pts) - 1):
            (_, (x0, y0), l0), (_, (x1, y1), _) = pts[i], pts[i + 1]
            col = "cream" if (l0 > 0.88 and dy == 0) else ("wine" if l0 < -0.55 else "gold")
            ak.ink(pic, [(x0, y0 + dy), (x1, y1 + dy)], col, where=base)
    # the mane: ridges slanting down the crest, each lit above a dark groove
    n_r, deep, drop, share = RIDGES
    for s in grooves():
        x0, y0 = point_along(MANE, s)
        tx, ty = tangent_along(MANE, s)
        ix, iy = inward(tx, ty)
        p0 = (x0 + NOTCH[0] * ix, y0 + NOTCH[0] * iy)
        p1 = (x0 + deep * ix + drop * tx, y0 + deep * iy + drop * ty)
        a, b = on_side(cam, [p0, p1])
        groove = [(x_, y_) for x_, y_ in ak.line_px([a, b]) if head[y_, x_]]
        for j, (x_, y_) in enumerate(groove):
            pic.px(x_, y_, "black")
            keep[y_, x_] = True
            for hx, hy in ((x_, y_ - 1), (x_, y_ - 2))[:1 if j in (0, len(groove) - 1) else 2]:
                if head[hy, hx] and not rim[hy, hx] and (hx, hy) not in groove:
                    pic.px(hx, hy, "bone1")
                    keep[hy, hx] = True
    # the jowl: a cream crescent on its upper front, its edge behind and under it
    cx, cy, rx, ry = CHEEK
    face = head & ~neck
    for f, a0, a1 in ((0.80, 100, 196), (0.68, 118, 172)):
        for x_, y_ in ak.ink(pic, on_side(cam, arc(cx, cy, rx * f, ry * f, a0, a1)), "cream", where=face):
            keep[y_, x_] = True
    ak.ink(pic, on_side(cam, arc(cx, cy, rx * 1.02, ry * 1.04, 64, -132)), "bone0",
           where=head & pic.where("bone1", "cream"))
    # the eye, by hand, under its brow
    (ex, ey), = on_side(cam, [EYE])
    ex, ey = int(np.floor(ex)) - 3, int(np.floor(ey)) - 2
    ak.patch(pic, ex, ey, EYE_PX, EYE_KEY)
    keep[ey - 1:ey + len(EYE_PX) + 1, ex - 1:ex + len(EYE_PX[0]) + 1] = True
    # the nostril, flared, and the mouth
    nx_, ny_, nrx, nry = NOSTRIL
    dn = ellipse_d(lx, ly, nx_, ny_, nrx, nry, -30)
    flare = head & (ellipse_d(lx, ly, nx_ + 0.02, ny_ - 0.012, nrx * 1.8, nry * 1.9, -30) < 0) & (dn > 0)
    pic.put(flare & pic.where("bone1", "cream"), "bone0")
    pic.put(head & (dn < 0), "black")
    keep |= ak.dilate(head & (dn < 0), 1, diag=True)
    m0, m1 = on_side(cam, list(MOUTH))
    for x_, y_ in ak.ink(pic, [m0, m1], "black", where=head):
        keep[y_, x_] = True
    return keep


def point_along(pts, s):
    pts = np.asarray(pts, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    k = int(np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1))
    f = (s - cum[k]) / seg[k]
    return tuple(pts[k] + (pts[k + 1] - pts[k]) * f)


def tangent_along(pts, s):
    pts = np.asarray(pts, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    k = int(np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1))
    d = (pts[k + 1] - pts[k]) / seg[k]
    return float(d[0]), float(d[1])


# ---- the checker ---------------------------------------------------------------------------

def paint_checker(pic, G, chk, cam, at):
    """The red checker, a king: a raised lip round its face (cream where it
    meets the lamp), the face sunk inside it (its wall a wine ring toward
    the lamp), a gold crown embossed in the middle; its thick edge red in
    the light and wine in the shade, finely reeded (1-px ridges a step
    lighter than the edge, never black)."""
    Rc = checker_rot()
    lp = (G["p"] - at) @ Rc
    ln = G["n"] @ Rc
    kl = Rc.T @ KEY
    dif = (ln * kl).sum(-1)
    face = chk & (ln[..., 1] > 0.6)
    rim = chk & ~face
    side = rim & (np.abs(lp[..., 1]) < CHECKER_H * 0.75)
    u, v = lp[..., 0] / CHECKER_R, lp[..., 2] / CHECKER_R
    r = np.hypot(u, v)
    lv = np.where(face, 2.0, bands(dif, [(-9, 1), (EDGE_LIT, 2)]))
    ak.by_level(pic, lv, RED_R, chk, q=1)
    # the reeding: short ridges across the edge, a step lighter than it
    before = pic.idx.copy()
    for a in np.radians(np.arange(0, 360, REED)):
        c, s = np.cos(a), np.sin(a)
        p0 = cam.project(at + Rc @ np.array([c * CHECKER_R, CHECKER_H * 0.5, s * CHECKER_R]))
        p1 = cam.project(at + Rc @ np.array([c * CHECKER_R, -CHECKER_H * 0.5, s * CHECKER_R]))
        if (Rc @ np.array([c, 0.0, s])) @ (cam.pos - at) <= 0.1:
            continue                                            # the far side
        for x_, y_, _ in ak.raster([p0, p1]):
            if 0 <= x_ < 128 and 0 <= y_ < 128 and side[y_, x_]:
                if before[y_, x_] == pic.pal["red"]:
                    pic.px(x_, y_, "wine")
    # the lip where it meets the lamp, toward the flash
    mx, my = face_middle(cam, at)
    sa = (np.degrees(np.arctan2(my - (YY + 0.5), XX + 0.5 - mx)) - FLASH_DIR + 180) % 360 - 180
    pic.put(chk & ~side & (r > 0.86) & (np.abs(sa) < LIP_ARC), "cream")
    lit = (u * kl[0] + v * kl[2]) / max(np.hypot(kl[0], kl[2]), 1e-6)
    wall = face & (np.abs(r - RECESS) < 0.045)
    pic.put(wall & (lit > -0.35), "wine")
    x0, y0 = int(round(mx - len(CROWN[0]) / 2)), int(round(my - len(CROWN) / 2))
    crown = np.zeros((128, 128), bool)
    for j, row in enumerate(CROWN):
        for i, ch in enumerate(row):
            crown[y0 + j, x0 + i] = ch in CROWN_KEY
    pic.put(ak.shift(crown, 1, 1) & ~crown & face, "wine")
    ak.patch(pic, x0, y0, CROWN, CROWN_KEY)
    return face, side


def face_middle(cam, at):
    return cam.project(at + checker_rot() @ np.array([0.0, CHECKER_H, 0.0]))


def flash_at(cam, at):
    """Where the checker's lip flashes: the point of its face's rim that
    lies toward FLASH_DIR on the picture, and the way out from it."""
    Rc = checker_rot()
    mx, my = face_middle(cam, at)
    best = None
    for a in np.radians(np.arange(0, 360, 2)):
        q = np.array([np.cos(a) * CHECKER_R, CHECKER_H, np.sin(a) * CHECKER_R])
        x, y = cam.project(at + Rc @ q)
        da = (np.degrees(np.arctan2(my - y, x - mx)) - FLASH_DIR + 180) % 360 - 180
        if best is None or abs(da) < best[0]:
            best = (abs(da), x, y)
    _, x, y = best
    dx, dy = x - mx, y - my
    n = np.hypot(dx, dy)
    return float(x), float(y), dx / n, dy / n


def star(pic, x, y, arms, on):
    """A four-pointed flash at (x, y): arms (left, right, up, down) long,
    cream turning gold toward their tips, a cream pixel on each diagonal
    in the night."""
    pic.px(x, y, "cream")
    for (dx, dy), arm in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for i in range(1, arm + 1):
            x_, y_ = x + dx * i, y + dy * i
            if 0 <= x_ < 128 and 0 <= y_ < 128:
                pic.px(x_, y_, "gold" if i > max(2, 0.6 * arm) else "cream")
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        if not on[y + dy, x + dx]:
            pic.px(x + dx, y + dy, "cream")


# ---- the picture -----------------------------------------------------------------------------

def sky_level(X, Y, look):
    """The family's night (folderkit) with this picture's spotlight: a shaft
    a level lighter between two straight edges from its source off the top
    left, edges hard so they step evenly, fading out where it reaches the
    board."""
    (sx, sy), su, sl, k, (f0, f1) = BEAM
    lv = fk.sky_level(X, Y, **look)
    inside = (Y - sy >= su * (X - sx)) & (Y - sy <= sl * (X - sx))
    fade = np.clip((f1 - np.hypot(X - sx, Y - sy)) / (f1 - f0), 0, 1)
    return np.clip(lv + k * inside * fade, 0, 3)


def floor_hits(G):
    o, d = G["o"], G["d"]
    down = d[:, 1] < 0
    t = np.where(down, -o[:, 1] / np.minimum(d[:, 1], -1e-9), 1e9)
    return down.reshape(128, 128), (o + d * t[:, None]).reshape(128, 128, 3)


def paint_board(pic, G, cam, sc, pieces, look):
    """The checkerboard: each square one flat colour from the pool of light
    at its middle, whole squares fading into the night at the back; the
    pieces' shadows a level down."""
    down, bp = floor_hits(G)
    ry = R.rot_y(BOARD_YAW)
    q = (bp @ ry) / SQUARE
    si, sj = np.floor(q[..., 0]), np.floor(q[..., 2])
    light_sq = ((si + sj) % 2) == 0
    cw = (np.stack([si + 0.5, np.zeros_like(si), sj + 0.5], -1) * SQUARE) @ ry.T      # each square's middle
    ct = np.hypot(cw[..., 0] - cam.pos[0], cw[..., 2] - cam.pos[2])
    fog = np.clip((FOG[0] - ct) / FOG[1], 0, 1)
    pool = np.exp(-(((cw[..., 0] - POOL[0]) / POOL[2]) ** 2 + ((cw[..., 2] - POOL[1]) / POOL[3]) ** 2))
    blv = np.where(light_sq, np.interp(pool, [0, 0.25, 0.55], [2, 3, 4]), np.interp(pool, [0, 0.3, 0.75], [0, 1, 2]))
    sky = sky_level(XX + 0.5, YY + 0.5, look)
    blv = sky + (blv - sky) * fog - np.round(fk.edge_dark(XX + 0.5, YY + 0.5)) * fog
    shad = np.zeros((128, 128))
    for who, L in ((CHECKER, SHADOW_L), (KNIGHT, KNIGHT_SHADOW_L)):
        shad = np.maximum(shad, R.ground(ak.Canvas("#000000", ss=1), scene(cam, (who,)), cam, y=0.0,
                                         light=tuple(L / np.linalg.norm(L)), ss=None, ao=False, k=8.0))
    blv = np.where(shad > 0.5, np.maximum(blv - np.where(light_sq, 2.0, 1.0), np.minimum(blv, 1.0)), blv)
    floor = down & ~pieces & (fog > 0)
    ak.by_level(pic, np.clip(np.round(blv), 0, 4), BOARD_R, floor, q=1)
    return floor, shad > 0.5


FRAME_STEP = (("cream", "bone1"), ("bone1", "bone0"), ("bone0", "slate"), ("gold", "wine"), ("slate", "navy1"),
              ("red", "wine"), ("wine", "black"), ("navy2", "navy1"))


def frame_step(pic):
    """The outer two rows and columns a step darker; the bottom two rows,
    where the knight's foot runs off, one dark value."""
    e = np.minimum(np.minimum(XX, 127 - XX), YY)
    for width in (2, 1):
        step_down(pic, e < width, FRAME_STEP)
    bottom = ~pic.where("black", "navy0", "navy1")
    pic.put((YY == 126) & bottom, "navy1")
    pic.put((YY == 127) & ~pic.where("black", "navy0"), "navy0")


def draw():
    P = fk.palette(OWN, ramps=[IVORY_R, RED_R, BOARD_R, ["wine", "gold", "cream"]])
    pic = ak.Picture.blank(P, "navy0")
    cam = camera()
    at = checker_at(cam)
    sc = scene(cam)
    G = geometry(cam, sc)
    mat = G["mat"]
    for _ in range(2):                                          # no 1-px bumps on the silhouettes
        for k in (KNIGHT, CHECKER):
            m = mat == k
            n4 = sum(ak.shift(m, dx, dy).astype(int) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            mat[m & (n4 <= 1)] = -1
    pieces = mat >= 0
    kn, chk = mat == KNIGHT, mat == CHECKER
    lx, ly, ox, oy = flash_at(cam, at)
    fx, fy = int(np.floor(lx + ox * FLASH_OUT)), int(np.floor(ly + oy * FLASH_OUT))
    look = dict(LOOK)
    ak.by_level(pic, fk.terrace_px(sky_level(XX + 0.5, YY + 0.5, look), 1.5), fk.NIGHT_R, np.ones((128, 128), bool))
    paint_board(pic, G, cam, sc, pieces, look)
    # the spin: arcs round the checker's lower left, bright at their head, tapering
    ys_, xs_ = np.nonzero(chk)
    mx, my = xs_.mean() + 0.5, ys_.mean() + 0.5
    rad = np.sqrt(chk.sum() / np.pi)
    for out, a0, a1, r0 in SPIN:
        rr = rad + out
        am, half = np.radians((a0 + a1) / 2), np.radians(abs(a1 - a0) / 2)
        pt = lambda a: (mx + rr * np.cos(np.radians(a)), my - rr * np.sin(np.radians(a)))   # noqa: E731
        ctrl = (mx + rr / np.cos(half) * np.cos(am), my - rr / np.cos(half) * np.sin(am))
        ak.streak(pic, pt(a1), ctrl, pt(a0), r0, 0.25, ok=~ak.dilate(pieces, 1, diag=True),
                  cols=(("cream", 0.14), ("red", 0.55), ("wine", 1.0)))
    keep = paint_knight(pic, G, kn, cam)
    face, _ = paint_checker(pic, G, chk, cam, at)
    fk.selout(pic, pieces, "black")
    frame_step(pic)
    # the flash on the checker's lit lip, and its sparks
    before = pic.idx.copy()
    star(pic, fx, fy, FLASH, chk)
    clear = ~ak.dilate(pieces, 3, diag=True)
    for dx, dy in SPARKS:
        if clear[fy + dy, fx + dx]:
            fk.twinkle(pic, fx + dx, fy + dy, arm="gold")
    keep |= ak.dilate(pic.idx != before, 1, diag=True)
    ak.despeckle(pic, 4, keep=keep, within=YY >= fk.OBJECT_TOP, passes=2)
    ak.despeckle(pic, 3, keep=keep | pieces, within=YY >= fk.OBJECT_TOP)       # the board's slivers by the outline
    fk.word(pic, "board", glints=[(3, 4, 2)])
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "board.png"))
