"""tools/sdcard/art/dice.png: the DICE folder's cover on the casino card (it
holds Craps and Yacht Dice). `python tools/sdcard/covers.py` redraws it;
edit this, not the PNG. The folders' shared look is folderkit.py, beside
this file (cards.py is its worked example).

THE BRIEF (revision 2)
  Message: this way to the dice. Through this door the dice are rolling: a
  pair tossed up into the spotlight, tumbling at you, and it is a natural:
  the red die's 6 and the ivory's 1 on top, a seven. A casino's red die and
  an ivory one: the dice of both games inside (Craps' red, Yacht's ivory).

  Composition (a folder: the sign over the door, then the one object that
  says what is inside; read in this order):
  - The sign: DICE in the family's ice chrome on its navy panel and rainbow
    neon tube (folderkit.word), rows 1 to 48. Calm night beside it.
  - The hero: the red die, big, lower right, tumbling on a three-quarter
    corner: its 6 on top (lit, rose), its 5 to us (the red front, every pip
    in the frame), its 4 on the shade side (wine). Its shade face runs off
    the right frame and its foot off the bottom, darkening into them. Its
    top vertex sits under the sign, where a cream four-pointed glint
    catches the lamp, its arms clear of the die's edges.
  - The second die: ivory, further back at the upper left, about half the
    size, on its corner another way: its 1 on top (big and red: the pair's
    colour echo), a 3 to us and a 2 on its shade side (one pip shows; the
    other is behind the hero). The hero's upper-left edge covers its
    lower-right corner behind a black seam: depth by overlap, size and
    value (bone, tan and slate, no cream but a 1-px rim on its key edge).
  - The motion: they are at the top of the toss, so each speed line leaves
    its die level, 4-7 px off its trailing edge, and bends down along the
    arc it rose on; full-bodied, then tapering to a point, stepping down its
    die's ramp: three from the hero (46, 36 and 26 px: rose, red, wine), two
    from the ivory (bone, tan, slate), all ending clear of the frame.
  - Behind: the family's night: the casino's glow, a navy1 plateau behind
    the dice (from under the sign's halo down, so the hero's top edge and
    the air between the dice are on it), and the spotlight's beam slanting
    in from the top left past the sign onto the dice (the key light made
    visible; hard edged, a clean stair). A twinkle in the open night right
    of the sign, one left of the ivory die. No floor: the dice are in flight
    (a stage floor was tried: its pool and shadows read as a puddle).
  - Thumbnail:
        +--------------------------------+
        | .      [ D I C E ]  (neon)   + |
        |  .  beam                       |
        | +  ___      +  ___________     |
        |  - |_1_|.   /     6     /|     |
        | -  |_3_|2|/___________/ |     |
        |  ~~~~~~   | o      o  |  o  | |
        | ~~~~~~    |  o  o  o  | 4  o | |
        +--------------------------------+
  - Light: the house key from the top left. The dice's tops lit, the faces
    turned to us a step down, the faces turned right in shade; black
    outlines on the shadow sides only. Each face is flat, painted from the
    cube's own straight edges (pixel by pixel as levels on the die's ramp),
    its bands measured in pixels from the neighbouring face, in hard steps
    (a dithered seam along a shallow edge reads as stitching):
    the red die's top rose, a cream rim on the silhouette edge that faces
    the key squarely, a cream bevel on the edge it shares with the front
    tapering from 3 px at the key vertex to nothing two thirds along, and a
    1-px red line on the edge it shares with the shade face (an edge facing
    away from the light: no highlight). The front: red, a rose band under
    the bevel while it lasts, a rose rim where the key grazes its left edge.
    The shade face: wine, flat. Pips drilled: cream with the rim's shadow
    (red on the top, wine on the front) in an unbroken arc inside its upper
    left; rose on the shade face. The ivory: bone top, tan front, slate
    side, square black pips (3 x 3: a smaller ellipse reads as a cross), its
    1 red with a wine crescent.
  - The frame: everything steps down its ramp in whole steps into the
    vignette (no checker at the frame): a die one step within 5 px of it,
    two within 2 (a pip steps whole, or is left out in the dark); the night
    rounds to whole levels there; rows and columns 0-1 black.

PALETTE (folderkit's 6 + 5 own + cream, black, red; the rainbow is the neon)
  navy0 navy1 navy2   the night, the glow, the beam; the ivory die's side pip
  ice0 ice1 ice2      the sign's face only (the title's reserved colours:
                      nothing else uses them)
  wine rose           the red die, on black, wine, red, rose, cream: its shade
                      face and pip shadows, its lit top and speed lines
  bone tan slate      the ivory die, on slate, tan, bone, cream: its lit top,
                      its front, its cool shade side; its speed lines
  cream               the glint and twinkles' cores, the red die's pips, bevel
                      and rim, the ivory's rim
  red                 the red die's front, the ivory die's 1
  (grey unused)

LETTERING: BAZAR (bmf collection), "freeware; authors vary, few gave terms"
  (a `?` face, already on the credits for the folders in docs/cover-art.md),
  at its own size, from folderkit's word_dice.txt, untouched.
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

OWN = {"wine": "#6A0C24", "rose": "#FF7A5A", "bone": "#E4D4B2", "tan": "#A28C6E", "slate": "#4D5A8C"}
RED_R = ["black", "wine", "red", "rose", "cream"]
IVORY_R = ["black", "navy0", "navy1", "navy2", "slate", "tan", "bone", "cream"]
IVORY_TONES = (6, 5, 4)                        # the far die's top, front and side on IVORY_R (its rim a step up)

CAM = R.Camera((0.0, 2.6, 10.0), (0.0, 1.4, 0.0), fov=18)    # long: the faces' far edges stay near parallel
KEY = (-0.45, 0.8, 0.4)                       # the dice's key, in the picture's terms (right, up, toward us)

# the dice, far to near: their middle on the picture, distance from the
# camera, rounding; the face turned to us and the face up, then turned (orient())
DICE = [
    dict(name="ivory", at=(42, 72), dist=15.5, round=0.12, front=3, top=1, yaw=-30, pitch=45, roll=-20),
    dict(name="red", at=(93, 92), dist=7.6, round=0.09, front=5, top=6, yaw=-49, pitch=20, roll=-14),
]
FACES = {6: ((0, 1, 0), (1, 0, 0), (0, 0, 1)), 1: ((0, -1, 0), (1, 0, 0), (0, 0, 1)),     # normal, u, v
         2: ((0, 0, 1), (1, 0, 0), (0, 1, 0)), 5: ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
         3: ((1, 0, 0), (0, 0, 1), (0, 1, 0)), 4: ((-1, 0, 0), (0, 0, 1), (0, 1, 0))}
FACE_TAB = np.array([[4, 3], [1, 6], [5, 2]])   # (axis, outward?) -> the face's pips
S = 0.26                                       # pip spacing (die edge 1)
PIPS = {1: [(0, 0)], 2: [(-S, -S), (S, S)], 3: [(-S, -S), (0, 0), (S, S)],
        4: [(-S, -S), (S, -S), (-S, S), (S, S)], 5: [(-S, -S), (S, -S), (-S, S), (S, S), (0, 0)],
        6: [(-S, -S), (-S, 0), (-S, S), (S, -S), (S, 0), (S, S)]}
PIP_R = 0.095

# the night: folderkit's sky, the casino's glow behind the dice (a navy1
# plateau: centre, radii, levels), the spotlight's beam (source, target,
# half-angle, levels; hard edged)
LOOK = dict(centre=(84, 120), glow=(90, 70))
GLOW = ((92, 92), (58, 46), 0.9)
BEAM = ((-12, -16), (80, 102), 10.5, 0.85)

RIM = 0.8                                      # the hero's cream rim: on the silhouette facing the key this squarely
BEVEL = 3.2                                    # the hero's bevel: px at the key vertex
# speed lines, the dice's path back the way they came: they are at the top
# of the toss, so each line leaves its die level and bends down along the
# arc it rose on: (die, the row it leaves from, gap from the die's
# trailing edge, length, drop at its tail, radius at the root, colours
# along it)
HERO_COLS = (("rose", 0.35), ("red", 0.7), ("wine", 1.0))
IVORY_COLS = (("bone", 0.35), ("tan", 0.7), ("slate", 1.0))
TRAILS = [
    ("red", 98, 7, 46, 14, 2.4, HERO_COLS),
    ("red", 107, 7, 36, 10, 2.1, HERO_COLS),
    ("red", 116, 7, 26, 6, 1.8, HERO_COLS),
    ("ivory", 77, 4, 19, 7, 1.6, IVORY_COLS),
    ("ivory", 86, 4, 15, 5, 1.4, IVORY_COLS),
]
GLINT = (-2, -4, (4, 5, 3, 3))                  # the hero's glint: from its top vertex, arms (left, right, up, down)
TWINKLES = [(113, 28, "slate"), (11, 64, "slate")]   # sparks in the open night: x, y, arm colour


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def orient(front, top, yaw, pitch, roll):
    """A rotation (local -> world): the die's `front` face toward the camera
    and its `top` face up, then turned `yaw` degrees about the vertical
    (+: its front turns right), `pitch` about the screen's x (+: its top
    tips toward us) and `roll` about the line of sight (+: clockwise)."""
    n1, n2 = np.array(FACES[front][0], float), np.array(FACES[top][0], float)
    A = np.stack([n1, n2, np.cross(n1, n2)], axis=1)
    f, u = -CAM.f, CAM.u - (CAM.u @ CAM.f) * CAM.f
    u /= np.linalg.norm(u)
    B = np.stack([f, u, np.cross(f, u)], axis=1)

    def turn(axis, deg):
        a = np.radians(deg)
        axis = axis / np.linalg.norm(axis)
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
    M = turn(-CAM.f, -roll) @ turn(CAM.r, pitch) @ turn(u, yaw)
    return M @ B @ A.T


def at(sx, sy, dist):
    """The world point `dist` from the camera along the ray through (sx, sy)."""
    o, d = CAM.rays(np.array([float(sx)]), np.array([float(sy)]))
    return o[0] + d[0] * dist


def face_of(loc):
    """The face (pip count) each local normal points out of."""
    k = np.argmax(np.abs(loc), axis=-1)
    out = np.take_along_axis(loc, k[..., None], -1)[..., 0] > 0
    return FACE_TAB[k, out.astype(int)]


def axes(f):
    """A face's normal and its two in-plane axes (the die's own frame)."""
    return tuple(np.array(a, float) for a in FACES[f])


def corners(d):
    """The die's eight corners on the picture."""
    return np.array([CAM.project(d["pos"] + d["rot"] @ (np.array([sx, sy, sz]) * 0.5))
                     for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])


def geometry(cv, d, mat):
    """The die ray-marched (for its geometry only), then per pixel: its mask,
    the face each pixel belongs to (the face its mean hit point is nearest:
    the cube's own straight edges, rounded corners and all) and the mean hit
    point in the die's frame. Faces are ranked by how they face the key."""
    c = corners(d)
    x0, y0 = np.floor(c.min(0)) - 2
    x1, y1 = np.ceil(c.max(0)) + 2
    node = R.xf(R.prim(R.box((0.5,) * 3, d["round"]), mat), d["pos"], d["rot"])
    o = R.render(cv, node, CAM, [R.Mat("#FFFFFF")] * (mat + 1), shadows=False, ao=False, ss=4,
                 region=(max(x0, 0), max(y0, 0), min(x1, 128), min(y1, 128)))
    s = cv.s
    sel = (o["mat"] == mat) & (o["alpha"] > 0.5)
    m = ak.px_mean(sel.astype(np.float32), s) >= 0.5
    o_all, d_all = CAM.rays(cv.X.reshape(-1).astype(np.float64), cv.Y.reshape(-1).astype(np.float64))
    dep = np.where(sel, o["depth"], 0.0).reshape(-1)
    hit = o_all + d_all * dep[:, None]
    loc = ((hit - d["pos"]) @ d["rot"]).reshape(cv.N, cv.N, 3) * sel[..., None]
    nsel = np.maximum(ak.px_mean(sel.astype(np.float32), s), 1e-6)
    lmean = ak.px_mean(loc, s) / nsel[..., None]
    fg = face_of(lmean)
    shown = [f for f in range(1, 7) if (m & (fg == f)).sum() >= 6]
    if (m & ~np.isin(fg, shown)).any():                                   # stray pixels of a hidden face
        best = np.stack([lmean @ axes(f)[0] for f in shown], -1).argmax(-1)
        fg = np.where(m & ~np.isin(fg, shown), np.array(shown)[best], fg)
    key_s = KEY[0] * CAM.r + KEY[1] * CAM.u - KEY[2] * CAM.f
    key_s /= np.linalg.norm(key_s)
    rank = sorted(shown, key=lambda f: -(d["rot"] @ axes(f)[0]) @ key_s)
    F = {f: m & (fg == f) for f in shown}
    return dict(m=m, fg=fg, loc=lmean, rank=rank, F=F, key=key_s)


def along(d, g, f1, f2):
    """Along the edge between faces f1 and f2: 0 at its end nearer the key
    (up and left on the picture), 1 at the other."""
    n1, n2 = axes(f1)[0], axes(f2)[0]
    e = np.cross(n1, n2)
    mid = 0.5 * (n1 + n2)
    ends = [CAM.project(d["pos"] + d["rot"] @ (mid + k * 0.5 * e)) for k in (-1, 1)]
    t = g["loc"] @ e                                                     # -0.5 .. 0.5
    if ends[1][0] + ends[1][1] < ends[0][0] + ends[0][1]:
        t = -t
    return t + 0.5


def contour(m, lit, facing=0.35):
    """The pixels of `lit` on m's outer edge that face the key (up and left)."""
    b = fk._blur(m, 2)
    gy, gx = np.gradient(b)
    n = np.hypot(gx, gy) + 1e-9
    f = (gx + gy) / (n * np.sqrt(2))                                 # the outward normal is -grad: this is its
    rim = m & ~ak.erode(m, 1)                                        # dot with (-1, -1)
    return rim & lit & (f > facing)


def pips(pic, d, f, inner, col, min_px=2, big=False, skip=None):
    """A face's pips, one round stamp each, sized as the perspective gives
    them (a pip whose middle or most of it falls in `skip` is left out: the
    dark, or a die in front)."""
    rot, pos = d["rot"], np.asarray(d["pos"], float)
    nn_, uu, vv = FACES[f]
    nw, uw, vw = (rot @ np.array(a, float) for a in (nn_, uu, vv))
    cs, ws, hs = [], [], []
    for a, b in PIPS[f]:
        c = pos + (nw * 0.5 + uw * a + vw * b)
        pr = PIP_R * (2.0 if big else 1.0)
        ring = np.array([CAM.project(c + pr * (np.cos(t) * uw + np.sin(t) * vw))
                         for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)])
        cs.append(CAM.project(c))
        ws.append(np.ptp(ring[:, 0]))
        hs.append(np.ptp(ring[:, 1]))
    w, h = int(round(np.mean(ws))), int(round(np.mean(hs)))
    w, h = min(w, h + 1, 9), min(h, w + 1, 9)
    if max(w, h) <= 4:                                                # small: a square dot (4 x 3 reads as a cross)
        w = h = max(min(w, h), min_px)
    out = []
    if not inner.any():
        return out
    ys, xs = np.nonzero(inner)
    mx, my = xs.mean(), ys.mean()
    while w >= min_px and h >= min_px:
        tpl = ak.pip_template(w, h)
        placed = []
        for cx, cy in cs:
            x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
            for _ in range(4):
                m = ak.place(tpl, x0, y0)
                if (ak.dilate(m, 1) & ~inner).sum() == 0:
                    placed.append(m)
                    break
                ex, ey = mx - (x0 + w / 2), my - (y0 + h / 2)
                x0 += int(np.sign(ex)) if abs(ex) > 0.5 else 0
                y0 += int(np.sign(ey)) if abs(ey) > 0.5 else 0
        clash = any((ak.dilate(a, 1) & b).any() for i, a in enumerate(placed) for b in placed[i + 1:])
        if len(placed) == len(cs) and not clash:
            break
        w, h = w - 1, h - 1
    else:
        return out
    for m in placed:
        ys, xs = np.nonzero(m)
        if skip is not None and (skip[int(round(ys.mean())), int(round(xs.mean()))] or (skip & m).sum() > m.sum() // 2):
            continue
        pic.put(m, col)
        out.append(m)
    return out


def crescent(pm):
    """The upper-left arc of a pip's inner ring: one unbroken pixel line."""
    ring = pm & ~(ak.shift(pm, 1, 0) & ak.shift(pm, -1, 0) & ak.shift(pm, 0, 1) & ak.shift(pm, 0, -1))
    ys, xs = np.nonzero(pm)
    cx, cy = xs.mean() + 0.5, ys.mean() + 0.5
    w, h = np.ptp(xs) + 1, np.ptp(ys) + 1
    return ring & ((X1 - cx) / w + (Y1 - cy) / h < -0.12)


def swoosh(pic, root, ctrl, end, r0, ok, cols, taper=0.6, ss=4):
    """A speed line: a quadratic curve from `root` through `ctrl` to `end`,
    r0 px in radius at the root, thinning as (1 - t) ** taper (it stays
    full-bodied, then points), painted where `ok` is (a pixel is in when
    half of it is covered); its colour steps along it: cols [(name, up to t)].
    Returns its mask."""
    pts = np.array(ak.bezier(root, ctrl, end, n=80))
    t_pts = np.linspace(0, 1, len(pts))
    c = (np.arange(128 * ss) + 0.5) / ss
    X, Y = np.meshgrid(c, c)
    x0, y0 = pts.min(0) - r0 - 1
    x1, y1 = pts.max(0) + r0 + 1
    box = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
    xs, ys = X[box], Y[box]
    d2 = (xs[:, None] - pts[None, :, 0]) ** 2 + (ys[:, None] - pts[None, :, 1]) ** 2
    j = d2.argmin(1)
    r = r0 * (1 - t_pts[j]) ** taper
    cov = np.zeros(X.shape)
    cov[box] = np.sqrt(d2[np.arange(len(j)), j]) < r
    m = cov.reshape(128, ss, 128, ss).mean(axis=(1, 3)) >= 0.5
    m &= ok
    py, px = np.nonzero(m)
    t = ((px[:, None] + 0.5 - pts[None, :, 0]) ** 2 + (py[:, None] + 0.5 - pts[None, :, 1]) ** 2).argmin(1) / (len(pts) - 1)
    lo = 0.0
    for name, hi in cols:
        sel = (t >= lo) & (t <= hi)
        pic.idx[py[sel], px[sel]] = pic.pal[name]
        lo = hi
    return m


def step_down(pic, m, steps, ramps, floor=0):
    """Each pixel of m `steps` colours down the first ramp that holds its
    colour, no lower than the ramp's `floor`-th (unless it starts lower)."""
    for ramp in ramps:
        ids = [pic.pal[c] for c in ramp]
        for i, c in enumerate(ids):
            sel = m & (pic.idx == c) & (steps > 0)
            if sel.any():
                j = np.clip(i - steps[sel], min(floor, i), len(ids) - 1)
                pic.idx[sel] = np.array(ids, np.uint8)[j]
                m = m & ~sel


def vignette_steps(deep=False):
    """The frame's darkening in whole steps (no checker at the frame); deep:
    the dice's, a step down within 5 px of the frame (black within 2)."""
    if deep:
        return (EDGE < 6).astype(int)
    return np.round(fk.edge_dark(X1, Y1) * 2.0).astype(int)


# ---- the night ------------------------------------------------------------------------

def night_level():
    """folderkit's night, the glow's plateau behind the dice and the beam,
    as a float level on NIGHT_R."""
    vig = fk.edge_dark(X1, Y1)
    lv = fk.sky_level(X1, Y1, **LOOK) + vig
    (gx, gy), (rx, ry), k = GLOW
    r = np.hypot((X1 - gx) / rx, (Y1 - gy) / ry)
    lv = lv + k * smooth((1.0 - r) / 0.25)
    (sx, sy), (tx, ty), half, kb = BEAM
    ax_, ay_ = tx - sx, ty - sy
    n = np.hypot(ax_, ay_)
    ax_, ay_ = ax_ / n, ay_ / n
    dx, dy = X1 - sx, Y1 - sy
    a = dx * ax_ + dy * ay_
    across = np.abs(-dx * ay_ + dy * ax_)
    inside = across <= a * np.tan(np.radians(half))                       # hard sides: a clean stair
    lv = lv + kb * inside * np.clip(1.25 - a / n, 0, 1)
    return np.clip(lv - vig, 0, 3)


def night(pic):
    """The night on the pixels: flat plateaus, seams a pixel or so wide; at
    the frame, whole levels with no seam along it (a checker row there reads
    as stitching): black on the outer 3 rows and columns, never darker than
    navy0 inside them, and no navy2 near them (the corners dark)."""
    lv = night_level()
    fade = 0.6 * np.clip((12 - EDGE) / 8.0, 0, 1)
    lv = np.where(lv > 2.0, np.maximum(lv - fade, 1.9), lv)
    lv = np.where(EDGE < 9, np.round(lv), fk.terrace_px(lv, 1.2))
    lv = np.where(EDGE < 3, 0, np.maximum(lv, 1.0))
    ak.by_level(pic, lv, fk.NIGHT_R, np.ones((128, 128), bool))
    ak.despeckle(pic, 5)


# ---- the dice -------------------------------------------------------------------------

def paint_red(pic, d, g):
    """The red die, face by face, as levels on RED_R (0 black .. 4 cream):
    flat faces, bands measured in pixels from the neighbouring face, hard
    steps (a seam along a shallow edge reads as stitching)."""
    top, front, shade = g["rank"][:3]
    F, m = g["F"], g["m"]
    lv = np.zeros((128, 128))
    d_top, d_shade = ak.distance_px(F[top], 8), ak.distance_px(F[shade], 8)
    d_front = ak.distance_px(F[front], 8)
    s = along(d, g, top, front)
    w = np.round(BEVEL * (1 - s / 0.66))                                  # the bevel's width along its edge
    # the top: rose, red along its edge with the shade face (an edge facing
    # away from the light)
    lt = np.where(d_shade <= 1, 2.0, 3.0)
    lv[F[top]] = lt[F[top]]
    # the front: red; rose under the bevel while the bevel lasts
    lf = np.where((d_top <= 2) & (w >= 1), 3.0, 2.0)
    lv[F[front]] = lf[F[front]]
    # the shade face: wine, flat
    lv[F[shade]] = 1.0
    ak.by_level(pic, lv, RED_R, m)
    # the bevel: the rounded edge between the top and the front faces the
    # key: cream, BEVEL px at the key vertex tapering to nothing two thirds along
    pic.put(F[top] & (d_front <= w) & (w >= 1), "cream")
    # rims where the key grazes the silhouette: cream on the top, rose on the front
    pic.put(contour(m, F[top], facing=RIM), "cream")
    pic.put(contour(m, F[front], facing=0.2), "rose")


def paint_ivory(pic, d, g):
    """The ivory die, a step back: levels on IVORY_R (a bone top, a tan
    front, a slate side; a cream rim only where its silhouette faces the
    key squarely)."""
    top, front, side = g["rank"][:3]
    F, m = g["F"], g["m"]
    lv = np.zeros((128, 128))
    for f, k in zip((top, front, side), IVORY_TONES):
        lv[F[f]] = k
    ak.by_level(pic, lv, IVORY_R, m)
    pic.put(contour(m, F[top], facing=RIM), IVORY_R[IVORY_TONES[0] + 1])


def draw():
    P = fk.palette(OWN, ramps=[RED_R, IVORY_R])
    pic = ak.Picture.blank(P, "navy0")
    cv = ak.Canvas("#000000")

    dice_ = [dict(d) for d in DICE]
    for d in dice_:
        d["pos"] = at(*d["at"], d["dist"])
        d["rot"] = orient(d["front"], d["top"], d["yaw"], d["pitch"], d["roll"])
    geo = [geometry(cv, d, k) for k, d in enumerate(dice_)]
    hero = geo[-1]

    # the hero's glint: its top vertex catches the lamp
    ys, xs = np.nonzero(hero["m"])
    j = np.argmin(ys * 1.0 + 0.15 * xs)
    gx, gy = int(xs[j]) + GLINT[0], int(ys[j]) + GLINT[1]
    night(pic)

    # the speed lines: each die's path back the way it came
    ok = (YY >= fk.OBJECT_TOP + 2) & (EDGE >= 5)
    lines = np.zeros((128, 128), bool)
    names = [dd["name"] for dd in dice_]
    for name, row, gap, L, drop, r0, cols in TRAILS:
        m = geo[names.index(name)]["m"]
        xs = np.nonzero(m[row])[0]
        rx, ry = xs.min() - gap, row + 0.5                              # off the die's trailing (left) edge
        lines |= swoosh(pic, (rx, ry), (rx - L * 0.5, ry + drop * 0.05), (rx - L, ry + drop), r0, ok, cols)

    # the dice, far to near
    vsteps = vignette_steps()
    dsteps = vignette_steps(deep=True)
    dice = np.zeros((128, 128), bool)
    keep = np.zeros((128, 128), bool)
    for k, (d, g) in enumerate(zip(dice_, geo)):
        m = g["m"]
        st = dsteps.copy()
        if d["name"] == "red":
            paint_red(pic, d, g)
            pcol = {0: ("cream", "red"), 1: ("cream", "wine"), 2: ("rose", None)}
        else:
            paint_ivory(pic, d, g)
            pcol = {0: ("black", None), 1: ("black", None), 2: ("navy0", None)}
        for r, f in enumerate(g["rank"][:3]):
            fm = g["F"][f]
            if not ak.erode(fm, 2).any():
                continue
            col, rim = pcol[r]
            big = f == 1 and d["name"] == "ivory"
            if big:
                col, rim = "red", "wine"
            front = np.zeros((128, 128), bool)                       # the dice in front of this one
            for g2 in geo[k + 1:]:
                front |= ak.dilate(g2["m"], 2)
            for pm in pips(pic, d, f, fm, col, big=big, skip=(EDGE < 5) | front,
                           min_px=3 if d["name"] == "ivory" else 2):
                st[pm] = dsteps[pm].max()                            # a pip steps down whole
                if rim and pm.sum() >= 12 and not st[pm].any():     # the rim's shadow inside the pip, up and left
                    pic.put(crescent(pm), rim)
                keep |= pm
        step_down(pic, m, st, [RED_R, IVORY_R], floor=1)               # the frame's dark: a step, wine at the least
        fk.selout(pic, m, "black", facing=0.15 if d["name"] == "red" else 0.35)
        pic.put(ak.dilate(m, 1) & ~m & dice, "black")                 # a seam where it overlaps a die behind
        pic.put(m & (EDGE < 3), "black")                              # then black, as the night
        dice |= m
    ak.despeckle(pic, 5, keep=keep, within=dice)
    # pinholes of night shut in by the dice's outlines and the frame's dark
    for _ in range(2):
        blk = pic.where("black")
        nb = sum(ak.shift(blk, dx, dy).astype(int) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        hole = ~dice & ~blk & ~lines & (nb >= 3) & ak.dilate(dice, 2)
        hole |= ~dice & ~blk & ~lines & (nb >= 2) & (EDGE < 6) & ak.dilate(dice, 4)   # and in the frame's dark
        pic.put(hole, "black")
    night_px = pic.where(*fk.NIGHT_R[1:]) & ~dice & ak.dilate(dice, 3) & (YY >= fk.OBJECT_TOP)
    ak.despeckle(pic, 3, within=night_px)
    ak.despeckle(pic, 4, keep=keep, within=(EDGE < 8) & (YY >= fk.OBJECT_TOP), passes=2)   # stray corners at the frame

    # the frame: the speed lines step down into the vignette too (the night has it already)
    step_down(pic, lines & ~dice, vsteps, [RED_R, IVORY_R])

    ak.glint(pic, gx, gy, arms=GLINT[2], tip="rose")
    for ddx, ddy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):                # its diagonal sparkle
        pic.px(gx + ddx, gy + ddy, "cream" if not dice[gy + ddy, gx + ddx] else "rose")
    for tx, ty, arm in TWINKLES:
        fk.twinkle(pic, tx, ty, arm=arm)
    fk.word(pic, "dice", glints=[(3, 4, 2)])
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "dice.png"))
