r"""tools/sdcard/art/casino.png: the CASINO folder's cover on the casino card
(it holds Bingo, Roulette, Slots). `python tools/sdcard/covers.py` redraws
it; edit this, not the PNG. The folders' shared look is folderkit.py,
beside this file.

THE BRIEF (revision 3)
  Message: this way to the house games. The house's tower of chips stands
  in the spotlight and the play has just started: the roulette ball has
  struck its top, knocked the top chip askew, sent the one above it
  spinning off (a lucky seven on its face) and bounced away. Chips, the
  ball and the seven: roulette, slots and bingo, the games the house runs.

  Composition (a folder: a sign over a door, then the one object that
  says what is inside; read in this order). A thumbnail:

      +--------------------------------+
      |  [====== C A S I N O ======]   |   the sign, rows 1-48
      | \                              |   a calm moat, rows 49-56
      |  \      .--/-.  *    .-7-.     |   the knocked chip; the strike;
      |   .--.  |####|   \\  '---'     |   the chip in the air
      |   |##|  |####|    \\           |
      |   |##|  |####|     o           |   the ball, its comet tail back
      | .-|##|  |####|  ~~~~~~~        |   to the strike; the lit stage
      | |##|    |####|  ~~ _ ~~        |   its shadow, well under it
      +--------------------------------+

  - The sign: CASINO in the family's ice chrome on its navy panel and
    rainbow neon tube, rows 1 to 48 (folderkit.word; the N's 1-px spike
    trimmed in the mask here). A cream glint where the O's right stem
    meets the chrome's horizon. Nothing but the night within 8 rows of it.
  - The hero: a tower of seven red clay chips, centre left (x 39-77, rows
    66-114), on a lacquered stage in the spot. Drawn on the pixels: every
    chip shares one clean front arc (a whole row per column), five rows
    each: a lip a level up, three rows of edge, a groove (wine in the light,
    black in the shade); the edge in flat vertical bands by how it turns to
    the key (rose, red, wine), six inserts per chip laid like bricks, each
    one flat colour (cream, bone, grey, navy2 at the far shade). The light
    falls off down the tower. On top, the eighth chip, knocked 4 px right
    and tipped (its arc and face sheared, rounded once): its lifted left
    edge opens a wedge over the chip below, in wine shade with a black
    contact line, so the knock reads at 1x. Its face: rose toward the back
    left (a curved seam), red toward us, inserts at its rim, a wine inlay
    ring.
  - The strike: a cream flash with gold tips and gold diagonals at the
    knocked chip's top right, where the action leaves from.
  - The action, right, on one orthographic camera with the stacks (rays
    traced against a flat cylinder and a sphere, majority of 16 samples):
    the chip knocked off the top spins up and away, its face turned to us
    and up toward the lamp: flat plateaus (rose, red, a wine step), the
    inserts at its rim, a clean inlay ring and the lucky seven in it (a
    hand stamp, gold with a wine shadow, set italic as the face leans), a
    sliver of edge in the shade at its lower right. Below it the ivory
    roulette ball in the air (rows 86-97): bone in the light, grey and
    navy in its shade, cream only in its glint; its comet tail, a clean
    line thick and cream at the root, tapering through bone and grey to
    navy, runs back up the arc toward the strike, with two shorter lines
    beside it; two lines run back from the chip too. Each line has a dark
    edge under it, so it holds on the night. The ball's small shadow lies
    on the stage eight rows under it.
  - Depth, left: behind the tower a stack of six black chips (navy, navy2
    inserts, grey only where the lamp reaches, flat bands), smaller and
    flatter: further back, in the beam. In front, lower left and cut by
    the frame, three gold chips (the high rollers'), rounder (nearer),
    outside the spot: amber with gold where the lamp reaches, red inserts,
    no cream; the frame's vignette takes their left columns down to amber
    and black.
  - Behind: the night (folderkit's sky: a navy glow behind the tower, the
    spotlight's beam slanting in from the left, under the sign's end). The
    stage from row 88: dark lacquer, a pool of the spot's light on it right
    of the tower (stepped plateaus, narrow seams), the beam carried on
    across it; the wall darker just above its edge, so the stage shows.
    Every stack casts a shadow to the lower right (a level darker, flat);
    the stacks' reflections in the lacquer (each column mirrored under its
    foot, a step and then two toward the night). The frame stays dark;
    nothing that matters under the install bar.
  - Light: the house key from the top left; lit faces warm, the shade cool
    (navy), black only for outlines on the shadow side (folderkit.selout),
    each stack outlined before the next one in front is painted.
  Reading order: the sign; the tower and its knocked top (the biggest red,
  the most cream); the flash, the flying chip with its seven, the ball and
  its tail; the gold; the dark stack and the stage.

PALETTE (folderkit's 6 + 5 own + cream, black, red, grey; the rainbow is the neon)
  navy0 navy1 navy2   the night, the beam, the stage, the far shade, the reflections,
                      the black chips, the tails' ends and edges
  ice0 ice1 ice2      the sign's face only (nothing else uses them)
  wine rose           the red chips' shade and light (red between, cream the hottest)
  amber gold          the gold chips; gold the flash's tips and the seven
  bone                the inserts, the ball and the tails between cream and grey

LETTERING: BAZAR (bmf collection), "freeware; authors vary, few gave terms"
  (a `?` face: it wants the credits row in docs/cover-art.md), at its own
  size, from folderkit's word_casino.txt.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import folderkit as fk  # noqa: E402  (puts the repository's tools/ on the path)
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

YY, XX = fk.YY, fk.XX

OWN = {"wine": "#6C0E2C", "rose": "#F0543A", "bone": "#D8C49C", "amber": "#9A5410", "gold": "#F2B83A"}
RED_R = ["black", "wine", "red", "rose", "cream"]
GOLD_R = ["black", "amber", "gold", "cream"]
IVORY_R = ["navy1", "navy2", "grey", "bone", "cream"]

FLOOR = 88                                                     # the stage's back edge
LOOK = dict(centre=(62, 72), glow=(50, 42), beam=((-14, 18), (60, 84), 11.0, 1.3))   # the night (folderkit's)
POOL = (82.0, 102.0, 54.0, 15.0, 2.3)                          # the spot's pool on the stage: x, y, radii, levels
FLASH = (81, 62)                                               # where the ball struck the top
SIGN_GLINT = (107, 25)                                         # a glint on the sign: the O's right stem, at its horizon

KEY = np.array([-0.55, 0.65, 0.52])                           # the house key, in the world (y up, z to us)
KEY = KEY / np.linalg.norm(KEY)
KEY2 = np.array([KEY[0], KEY[2]]) / np.hypot(KEY[0], KEY[2])  # its bearing on the floor (x right, toward us)

# the camera: orthographic, looking down at the stage (a level disc of
# radius R shows as an ellipse SIN_E * R high: the tower's 7 / 19.5)
SIN_E = 0.36
COS_E = np.sqrt(1 - SIN_E ** 2)
VDIR = np.array([0.0, -SIN_E, -COS_E])                         # the view, into the picture
UPS = np.array([0.0, COS_E, -SIN_E])                           # the picture's up, in the world
EXS = np.array([1.0, 0.0, 0.0])

SPOTS, SPOT_W = 6, 0.26                                        # inserts round a chip's edge, the share of each sixth
# a chip's colours: body ramp, levels (shade, lit), inserts (ramp, shade, lit), the face's levels (front, back)
RED = dict(ramp=RED_R, lv=(0.85, 3.05), ins=(IVORY_R, 1.0, 4.3), face=(2.0, 3.2))
GOLD = dict(ramp=GOLD_R, lv=(0.6, 1.85), ins=(RED_R, 1.0, 2.3), face=(1.0, 2.25), lip_top=2, lip=2)
DARK = dict(ramp=["black", "navy0", "navy1", "navy2"], lv=(0.8, 2.6), ins=(IVORY_R, 0.6, 2.2), face=(1.8, 2.5))
# the upright stacks, drawn on the pixels: middle (x, a pixel's middle is .5), half width,
# the ellipse's half height, the bottom chip's bottom (row, at the middle), chips, their
# thickness (px), colours, the light lost from the top chip to the bottom one, the inserts'
# turn (seed); slope: a chip knocked askew (rows down per px right), q: dither steps
STACKS = [
    dict(name="back", cx=28.5, R=13.5, ry=5.0, base=94, n=6, T=4, kind=DARK, fall=0.3, seed=5, q=1),
    dict(name="tower", cx=58.5, R=19.5, ry=7.0, base=108, n=7, T=5, kind=RED, fall=0.45, seed=3, q=1),
    dict(name="knocked", cx=62.5, R=19.5, ry=7.0, base=71, n=1, T=5, kind=RED, fall=0.0, seed=4, slope=0.13, q=1),
    dict(name="gold", cx=13.5, R=17.5, ry=8.0, base=119, n=3, T=5, kind=GOLD, fall=0.5, seed=8, vignette=1.6, q=1),
]
AMB = 0.12                                                     # light on an edge turned from the key
SHADOW = (20, 0.12)                                            # a stack's shadow on the floor: how far right, slope
REFLECT = (3, 6)                                               # the reflection: a step darker for so many rows, two to here
REFLECT_MAP = {"cream": "grey", "bone": "grey", "grey": "navy2", "rose": "wine", "red": "wine", "wine": "navy1",
               "gold": "amber", "amber": "wine", "black": "navy0"}

# in flight, on the same camera: the chip knocked off the top (its face
# turned to us, up and left, toward the lamp), and the roulette ball
FLY = dict(at=(109.5, 69.0), R=12.8, H=2.5, tilt=50.0, toward=38.0, spin=-20.0, off=0.35)
BALL = (104.5, 92.0, 6.3)                                      # x, y, radius
BALL_SHADOW = (108.0, 108.5, 5.0, 1.6)                         # its shadow on the floor: x, y, radii

# speed lines: what they follow (its path: from the strike, the turn, to
# the thing), then each line: offset across (px), gap from its edge, length, root radius
TRAILS = [("ball", (FLASH, (92.0, 71.0), (104.5, 92.0)), [(0.0, 2.0, 29.0, 1.7), (-3.4, 2.0, 9.0, 1.0), (3.4, 3.0, 14.0, 1.0)]),
          ("fly", (FLASH, (92.0, 68.0), (109.5, 69.0)), [(-1.0, 2.0, 13.0, 1.1), (3.2, 2.0, 8.0, 0.8)])]
TRAIL_COLS = (("cream", 0.1), ("bone", 0.35), ("grey", 0.75), ("navy2", 1.0))

# the lucky seven on the flying chip's face, a hand stamp (its face leans
# right as it rises: the seven is set italic to match); its middle's offset
SEVEN = """
.#######
.#######
......##
.....##.
.....##.
....##..
....##..
...##...
"""
SEVEN_AT = (0.0, 0.0)


# ---- the stacks, on the pixels ------------------------------------------------------------

def stack_geom(st):
    """Where a stack is: per pixel its side, its top face, which chip and
    which row of it. Every chip shares one front arc (a whole row per
    column), so every groove is the same clean arc; a chip knocked askew
    (slope) has its arc and face sheared, rounded once."""
    cx, R_, ry, base, n, T = st["cx"], st["R"], st["ry"], st["base"], st["n"], st["T"]
    slope = st.get("slope", 0.0)
    u = (np.arange(128) + 0.5 - cx) / R_
    cols = np.abs(u) < 1
    e = ry * np.sqrt(np.clip(1 - u * u, 0, 1))
    s = slope * u * R_
    yt = base - n * T                                          # the top face's middle row
    if slope:
        ytop = np.floor(yt + s - e + 0.5)
        ybot = np.floor(yt + s + e + 0.5)
    else:
        a = np.floor(e + 0.5)
        ytop, ybot = yt - a, yt + a
    ytop = np.where(cols, ytop, 0).astype(int)
    ybot = np.where(cols, ybot, 0).astype(int)
    TOP, BOT, C = ytop[None, :], ybot[None, :], cols[None, :] & (YY >= 0)
    U = u[None, :] + 0 * YY
    rel = YY - BOT
    side = C & (rel >= 0) & (rel < n * T)
    face = C & (YY >= TOP) & (YY < BOT)
    k = np.clip(n - 1 - rel // T, 0, n - 1)
    row = rel % T
    phi = np.arcsin(np.clip(U, -1, 1))
    v = (YY + 0.5 - (yt + s[None, :])) / ry
    return dict(side=side, face=face, k=k, row=row, phi=phi, U=U, V=v, top=ytop, bot=ybot, yt=yt,
                s=s, all=side | face, cols=cols)


def stack_offsets(st):
    """The inserts' turn on each chip: like bricks, each chip half a step
    round from the one under it, give or take a little."""
    rng = np.random.default_rng(st["seed"])
    step = 2 * np.pi / SPOTS
    return np.array([(k % 2) * step / 2 + rng.uniform(-0.12, 0.12) * step for k in range(st["n"])])


def paint_stack(pic, st):
    g = stack_geom(st)
    kind = st["kind"]
    ramp, (lo, hi) = kind["ramp"], kind["lv"]
    iramp, ilo, ihi = kind["ins"]
    top = len(ramp) - 1
    q = st.get("q", 2)
    n, T = st["n"], st["T"]
    side, face, k, row, phi = g["side"], g["face"], g["k"], g["row"], g["phi"]
    off = stack_offsets(st)
    step = 2 * np.pi / SPOTS
    dark = fk.edge_dark(XX + 0.5, YY + 0.5) * st.get("vignette", 0.0)
    # the light on the edge: by how it turns to the key, less down the stack
    dif = np.clip(KEY2[0] * np.sin(phi) + KEY2[1] * np.cos(phi), 0, 1)
    S = 1.0 - st["fall"] * (1 - k / max(n - 1, 1))
    L = (AMB + (1 - AMB) * dif) * S
    lip = side & (row == 0)
    groove = side & (row == T - 1)
    body = side & ~lip & ~groove
    lv = lo + (hi - lo) * L - dark
    ak.by_level(pic, ak.terrace(np.clip(lv, 0, top), 0.12), ramp, body, q=q)
    liplv = np.round(lv + 0.3 + 0.5 * dif)
    cap = np.where(k == n - 1, kind.get("lip_top", top), kind.get("lip", top))
    ak.by_level(pic, np.clip(np.minimum(liplv, cap), 0, top), ramp, lip, q=1)
    pic.put(groove & (L - 0.3 * dark > 0.40), ramp[1])
    pic.put(groove & (L - 0.3 * dark <= 0.40), "black")
    spot = side & (((phi + off[k]) % step) < SPOT_W * step)
    spot &= ak.runs(spot, 1) >= 2                              # none a lone column wide, where the edge turns away
    # each insert one flat colour: the light at its middle
    j = np.floor((phi + off[k]) / step)
    phic = (j + SPOT_W / 2) * step - off[k]
    difc = np.clip(KEY2[0] * np.sin(phic) + KEY2[1] * np.cos(phic), 0, 1)
    slv = ilo + (ihi - ilo) * (AMB + (1 - AMB) * difc) * S - dark
    ak.by_level(pic, np.clip(np.round(slv), 0, len(iramp) - 1), iramp, spot & ~groove, q=1)
    # the top face: lit from high up, brighter toward the back left; the
    # inserts at its rim, an inlay ring
    U, v = g["U"], g["V"]
    rad = np.hypot(U, v)
    f0, f1 = kind["face"]
    flv = f1 - (f1 - f0) * np.clip(np.hypot(U + 0.6, v + 0.6) / 1.9, 0, 1) - dark
    ak.by_level(pic, fk.terrace_px(np.clip(flv, 0, top), 1.0), ramp, face, q=q)
    fphi = np.arctan2(U, v)
    fspot = face & (rad > 0.74) & (((fphi + off[n - 1]) % step) < SPOT_W * step)
    jf = np.floor((fphi + off[n - 1]) / step)
    fc = (jf + SPOT_W / 2) * step - off[n - 1]                 # each insert's middle: one flat colour
    flc = ilo + (ihi - ilo) * 0.95 - 0.87 * (np.sin(fc) + np.cos(fc)) * 0.6 - dark
    ak.by_level(pic, np.clip(np.round(np.minimum(flc, ihi)), 0, len(iramp) - 1), iramp, fspot, q=1)
    ring = []
    for t in np.linspace(0, 2 * np.pi, 240):
        uu, vv = 0.56 * np.sin(t), 0.56 * np.cos(t)
        x = st["cx"] + uu * st["R"]
        ring.append((x, g["yt"] + st.get("slope", 0.0) * uu * st["R"] + vv * st["ry"]))
    ak.ink(pic, ring, ramp[1], where=face)
    g["off"] = off
    return g


def stack_shadow(st, g):
    """The stack's shadow on the floor: its foot, drawn out to the right."""
    n, T = st["n"], st["T"]
    foot = g["cols"][None, :] & (YY >= g["top"][None, :] + n * T) & (YY < g["bot"][None, :] + n * T)
    out = np.zeros((128, 128), bool)
    ln, slope = SHADOW
    for t in range(ln + 1):
        out |= ak.shift(foot, t, int(round(t * slope)))
    return out


def reflect(pic, st, g, avoid):
    """The lacquered floor gives the stack back, dimmed: each column mirrored
    under its foot, every colour a step toward the night for a few rows,
    then two steps, then gone (flat steps, no dither)."""
    D1, D2 = REFLECT
    src = pic.copy()
    names = {pic.pal[nm]: nm for nm in REFLECT_MAP}
    for x in np.nonzero(g["cols"])[0]:
        b = g["bot"][x] + st["n"] * st["T"] - 1               # the stack's last row in this column
        for d in range(1, D2 + 1):
            y, ys = b + d, b + 1 - d
            if not (0 <= y < 128 and 0 <= ys < 128) or avoid[y, x] or y < FLOOR:
                continue
            nm = names.get(int(src.idx[ys, x]))
            if nm:
                nm = REFLECT_MAP[nm]
                if d > D1:
                    nm = REFLECT_MAP.get(nm, nm)
                pic.px(x, y, nm)


# ---- in flight, on the same camera --------------------------------------------------------

def grid(ss):
    """The sample points, ss x ss a pixel."""
    c = (np.arange(128 * ss) + 0.5) / ss
    return np.meshgrid(c, c)


def down(a, ss):
    """Mean over each pixel's samples."""
    return a.reshape(128, ss, 128, ss, *a.shape[2:]).mean(axis=(1, 3))


def fly_frame():
    """The flying chip's axis and the two directions in its face (right, up)."""
    t, w = np.radians(FLY["tilt"]), np.radians(FLY["toward"])
    tip = np.cos(w) * UPS - np.sin(w) * EXS                    # the way the axis leans, in the picture: up left
    a = np.cos(t) * (-VDIR) + np.sin(t) * tip
    a /= np.linalg.norm(a)
    up = np.array([0.0, 1.0, 0.0]) - a[1] * a
    up /= np.linalg.norm(up)
    sp = np.radians(FLY["spin"])
    rt = np.cross(up, a)
    up, rt = np.cos(sp) * up + np.sin(sp) * rt, np.cos(sp) * rt - np.sin(sp) * up
    return a, rt, up


def hit_chip(ss=4):
    """Rays (one per sample, straight down the view) against the flying
    chip, a flat cylinder: per pixel which part most of its samples hit
    (0 none, 1 the face to us, 2 the edge) and, there, the mean point."""
    sx, sy = FLY["at"]
    R_, H = FLY["R"], FLY["H"]
    a, rt, up = fly_frame()
    X, Y = grid(ss)
    o = (X - sx)[..., None] * EXS + (sy - Y)[..., None] * UPS - 60.0 * VDIR
    d = VDIR
    oa = o @ a
    da = d @ a
    op = o - oa[..., None] * a
    dp = d - da * a
    A = dp @ dp
    B = op @ dp
    Cc = (op * op).sum(-1) - R_ * R_
    disc = B * B - A * Cc
    ts = np.where(disc >= 0, (-B - np.sqrt(np.maximum(disc, 0))) / A, np.inf)
    ok_s = (disc >= 0) & (np.abs(oa + ts * da) <= H)
    ts = np.where(ok_s, ts, np.inf)
    sgn = -np.sign(da)                                         # the cap that faces us
    tc = (sgn * H - oa) / da
    qc = op + tc[..., None] * dp
    ok_c = (qc * qc).sum(-1) <= R_ * R_
    tc = np.where(ok_c, tc, np.inf)
    kind = np.where(np.isinf(np.minimum(ts, tc)), 0, np.where(tc <= ts, 1, 2))
    t = np.where(kind == 1, tc, np.where(kind == 2, ts, 0))
    p = o + t[..., None] * d
    out = {}
    cov = down((kind > 0).astype(np.float64), ss)
    f1 = down((kind == 1).astype(np.float64), ss)
    f2 = down((kind == 2).astype(np.float64), ss)
    m = cov >= 0.5
    out["face"] = m & (f1 >= f2)
    out["side"] = m & (f1 < f2)
    for nm, sel in (("pf", kind == 1), ("ps", kind == 2)):
        w = down(sel.astype(np.float64), ss)
        out[nm] = down(p * sel[..., None], ss) / np.maximum(w, 1e-9)[..., None]
    out["a"], out["rt"], out["up"], out["sgn"] = a, rt, up, float(np.sign(sgn.mean()))
    return out


def to_px(p):
    """A point of the flying chip (its own frame's origin at FLY['at']) to the picture."""
    sx, sy = FLY["at"]
    return sx + p @ EXS, sy - p @ UPS


def paint_flyer(pic):
    """The chip in the air: its face (flat plateaus: rose where it turns to
    the lamp, red, a wine step at its lower right), the inserts at its rim
    and round its edge, each one flat colour, a clean inlay ring and the
    lucky seven in it; its edge, a sliver at the lower right, in the shade."""
    h = hit_chip()
    a, rt, up = h["a"], h["rt"], h["up"]
    R_, H = FLY["R"], FLY["H"]
    face, side = h["face"], h["side"]
    pf, ps = h["pf"], h["ps"]
    fu, fv = (pf @ rt) / R_, (pf @ up) / R_
    rad = np.hypot(fu, fv)
    step = 2 * np.pi / SPOTS
    # the face: brighter toward the lamp (up left in the face), plateaus
    sheen = np.hypot(fu + 0.45, fv - 0.45)
    flv = 3.3 - 1.0 * sheen
    ak.by_level(pic, np.clip(np.round(flv), 1, 3), RED_R, face, q=1)
    ang = np.arctan2(fv, fu)
    spot = face & (rad > 0.78) & (((ang + FLY["off"]) % step) < SPOT_W * step)
    jj = np.floor((ang + FLY["off"]) / step)
    for j in np.unique(jj[spot]):
        sel = spot & (jj == j)
        if sel.sum() < 3:                                      # no scraps where the rim turns away
            continue
        c = (j + SPOT_W / 2) * step - FLY["off"]
        lit = 4.2 - 1.6 * np.hypot(np.cos(c) + 0.6, np.sin(c) - 0.6) / 1.6
        pic.put(sel, IVORY_R[int(np.clip(np.round(lit), 1, 4))])
    # the edge: by the key on its normal; inserts round it
    nrm = ps - (ps @ a)[..., None] * a
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
    dif = np.clip(nrm @ KEY / 0.76, 0, 1)
    slv = 0.9 + 1.6 * dif
    ak.by_level(pic, np.clip(np.round(slv), 0, 4), RED_R, side, q=1)
    sang = np.arctan2(ps @ up, ps @ rt)
    sspot = side & (((sang + FLY["off"]) % step) < SPOT_W * step)
    sj = np.floor((sang + FLY["off"]) / step)
    for j in np.unique(sj[sspot]):
        sel = sspot & (sj == j)
        if sel.sum() >= 3:                                     # no scraps where the edge turns away
            pic.put(sel, "bone" if slv[sel].mean() >= 1.6 else "grey")
    # the inlay ring and the seven, drawn through the face's plane
    sg = h["sgn"]
    ring = [to_px(sg * H * a + R_ * 0.60 * (np.cos(t) * rt + np.sin(t) * up)) for t in np.linspace(0, 2 * np.pi, 240)]
    ak.ink(pic, ring, "wine", where=face)
    return h


def seven_mask(h):
    """The lucky seven on the flying chip's face, at its middle."""
    m = np.array([[c == "#" for c in ln] for ln in SEVEN.strip().split()], bool)
    cx, cy = to_px(h["sgn"] * FLY["H"] * h["a"])
    x = int(np.floor(cx - m.shape[1] / 2 + 0.5 + SEVEN_AT[0]))
    y = int(np.floor(cy - m.shape[0] / 2 + 0.5 + SEVEN_AT[1]))
    return ak.place(m, x, y)


def paint_ball(pic):
    """The roulette ball: ivory, bone in the light, grey and navy in its
    shade; cream only in a small glint where it catches the lamp."""
    bx, by, r = BALL
    ss = 4
    X, Y = grid(ss)
    nx, ny = (X - bx) / r, (by - Y) / r
    inside = nx * nx + ny * ny <= 1
    m = down(inside.astype(np.float64), ss) >= 0.5
    cx, cy = XX + 0.5, YY + 0.5
    ux, uy = np.clip((cx - bx) / r, -1, 1), np.clip((by - cy) / r, -1, 1)
    uz = np.sqrt(np.clip(1 - ux * ux - uy * uy, 0, 1))
    n = ux[..., None] * EXS + uy[..., None] * UPS + uz[..., None] * (-VDIR)
    dif = np.clip(n @ KEY, 0, 1)
    lv = 1.0 + 2.25 * dif
    ak.by_level(pic, ak.terrace(np.clip(lv, 0, 3), 0.2), IVORY_R, m, q=2)
    hv = KEY - VDIR
    hv /= np.linalg.norm(hv)
    spec = np.clip(n @ hv, 0, 1) ** 40
    k = np.argmax(np.where(m, spec, -1))
    gy, gx = divmod(int(k), 128)
    return m, (gx, gy)


def ball_shadow():
    """The ball's shadow on the stage, well under it (it is in the air)."""
    x, y, rx, ry = BALL_SHADOW
    return ((XX + 0.5 - x) / rx) ** 2 + ((YY + 0.5 - y) / ry) ** 2 <= 1.0


def bez(p0, p1, p2, n=60):
    """n points along a quadratic Bezier curve."""
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.array(p, dtype=np.float64) for p in (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def trail(pic, pts, r0, ok, cols, edge=None, ss=4):
    """A speed line along pts (from the thing in flight back toward where
    it came from): a clean 1-px line, thickened at its root (r0 px there,
    tapering over its first third); its colour steps along it; `edge`: a
    dark line under it so it holds on the night."""
    Pt = np.asarray(pts, dtype=np.float64)
    m = np.zeros((128, 128), bool)
    for x, y in ak.line_px([tuple(p) for p in Pt]):
        if 0 <= x < 128 and 0 <= y < 128:
            m[y, x] = True
    n3 = max(2, len(Pt) // 3)
    X, Y = grid(ss)
    d = ak.polyline((X, Y), [tuple(p) for p in Pt[:n3]], r0, 0.2)
    m |= down((d < 0).astype(np.float64), ss) >= 0.5
    m &= ok
    ys, xs = np.nonzero(m)
    t = ((xs[:, None] + 0.5 - Pt[None, :, 0]) ** 2 + (ys[:, None] + 0.5 - Pt[None, :, 1]) ** 2).argmin(1) / (len(Pt) - 1)
    if edge:
        e = (ak.shift(m, 0, 1) | ak.shift(m, 1, 1)) & ~m & ok
        pic.put(e & ~pic.where("black"), edge)
    lo = 0.0
    for name, hi in cols:
        sel = (t >= lo) & (t <= hi)
        if name:
            pic.idx[ys[sel], xs[sel]] = pic.pal[name]
        lo = hi
    return m


def star(pic, x, y, arms, tip="gold", diag=(2, 2, 1, 1), dcol="gold"):
    """The strike: a four-pointed flash, a cream core and arms (left,
    right, up, down) turning `tip` at their ends; shorter `dcol` rays on
    the diagonals (up left, up right, down left, down right)."""
    pic.px(x, y, "cream")
    for (dx, dy), arm in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for i in range(1, arm + 1):
            pic.px(x + dx * i, y + dy * i, tip if i > (arm + 1) // 2 else "cream")
    for (dx, dy), arm in zip(((-1, -1), (1, -1), (-1, 1), (1, 1)), diag):
        for i in range(1, arm + 1):
            pic.px(x + dx * i, y + dy * i, dcol)


# ---- the night and the stage --------------------------------------------------------------

def stage_level(blooms=()):
    """The night (folderkit's, behind the stage) and the stage: from row
    FLOOR down a lacquered floor, dark, with the spot's pool of light on it
    (brighter than the wall behind, so the stage's edge shows) and the
    beam's light carried on across it."""
    X, Y = XX + 0.5, YY + 0.5
    back = fk.sky_level(X, Y, **LOOK, blooms=blooms)
    beam = back - fk.sky_level(X, Y, **dict(LOOK, beam=None), blooms=blooms)
    back = np.minimum(back, 1.15 + 0.9 * np.clip((FLOOR - Y) / 12.0, 0, 1))
    px, py, rx, ry, k = POOL
    t = np.clip(1 - np.hypot((X - px) / rx, (Y - py) / ry), 0, 1)
    floor = 0.95 + k * t * t * (3 - 2 * t) + 0.7 * beam - fk.edge_dark(X, Y)
    return np.clip(np.where(Y >= FLOOR, floor, back), 0, 3)


def put_stage(pic, where, shadow, blooms=()):
    """The night and the stage on the pixels, as folderkit.put_sky: flat
    plateaus of NIGHT_R with narrow seams; a level darker, flat, in the
    shadows the stacks and the ball cast."""
    lv = stage_level(blooms)
    ak.by_level(pic, fk.terrace_px(lv, 1.5), fk.NIGHT_R, where & ~shadow)
    ak.put_levels(pic, where & shadow, np.clip(np.round(lv) - 1, 0, 3).astype(int), fk.NIGHT_R)
    return lv


# ---- the picture --------------------------------------------------------------------------

def draw():
    P = fk.palette(OWN, ramps=[RED_R, GOLD_R, ["grey", "bone", "cream"], ["wine", "rose"]])
    pic = ak.Picture.blank(P, "navy0")
    geo = {st["name"]: stack_geom(st) for st in STACKS}
    obj = np.zeros((128, 128), bool)
    for g in geo.values():
        obj |= g["all"]
    fx, fy = FLASH
    shadow = ball_shadow()
    for st in STACKS:
        if st["name"] != "knocked":
            shadow |= stack_shadow(st, geo[st["name"]])
    blooms = [(fx, fy, 12.0, 0.6)]
    put_stage(pic, np.ones((128, 128), bool), shadow & ~obj & (YY >= FLOOR), blooms)
    things = {}
    for st in STACKS:                                         # back to front, each outlined before the next
        g = paint_stack(pic, st)
        if st["name"] == "knocked":
            # the chip under it shows in the wedge it was lifted off, in its shade
            t = geo["tower"]
            wedge = t["face"] & ~g["all"]
            pic.put(wedge, "wine")
        fk.selout(pic, g["all"], "black")
        if st["name"] != "knocked":
            reflect(pic, st, g, obj)
        things[st["name"]] = g["all"]
    h = paint_flyer(pic)
    fly = h["face"] | h["side"]
    things["fly"] = fly
    things["ball"], (gx, gy) = paint_ball(pic)
    for nm in ("fly", "ball"):
        fk.selout(pic, things[nm], "black")
    s7 = seven_mask(h)
    pic.put(ak.shift(s7, 1, 1) & ~s7 & h["face"], "wine")
    pic.put(s7, "gold")
    allobj = obj | fly | things["ball"]
    ok = ~ak.dilate(allobj, 1, diag=True) & ~((np.abs(XX - fx) <= 3) & (np.abs(YY - fy) <= 3))
    for nm, (p0, p1, p2), lines in TRAILS:
        m = things[nm]
        path = bez(p0, p1, p2, 200)[::-1]                     # from the thing back to the strike
        for off, start, length, r0 in lines:
            tg = np.gradient(path, axis=0)
            tg /= np.linalg.norm(tg, axis=1, keepdims=True)
            q = path + off * np.stack([-tg[:, 1], tg[:, 0]], 1)
            inside = m[np.clip(q[:, 1].astype(int), 0, 127), np.clip(q[:, 0].astype(int), 0, 127)]
            i0 = int(np.nonzero(~inside)[0][0]) if (~inside).any() else 0
            seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(q, axis=0).T))])
            sel = (seg >= seg[i0] + start) & (seg <= seg[i0] + start + length)
            if sel.sum() >= 2:
                trail(pic, q[sel], r0, ok, TRAIL_COLS, edge="navy0")
    ak.despeckle(pic, 5, within=YY >= fk.OBJECT_TOP)
    before = pic.idx.copy()
    ak.glint(pic, gx, gy, 1, core="cream")
    star(pic, fx, fy, (4, 6, 4, 4))
    sparkle = pic.idx != before
    ak.despeckle(pic, 4, keep=sparkle, within=(YY >= fk.OBJECT_TOP) & ~allobj)
    m = fk.word_mask("casino").copy()
    m[0:2, 59] = False                                         # the N's hair-thin spike
    sign = fk.word(pic, m, glints=[])
    ak.glint(pic, *SIGN_GLINT, 2)                              # where the chrome catches the lamp
    # the top rows by the frame: flat (no dither beside the tube)
    lv = stage_level(blooms)
    top = (YY < 6) & ~sign["halo"]
    ak.put_levels(pic, top, np.clip(np.round(lv), 0, 3).astype(int), fk.NIGHT_R)
    return pic.image()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parents[2]))                  # the repository's tools/
    import boxart
    print(boxart.save(draw(), HERE.parent / "casino.png"))
