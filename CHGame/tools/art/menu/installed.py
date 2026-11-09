"""spec/assets/system/installed.png: the visual menu's INSTALLED screen, the
picture of the program already in the handheld's flash when no entry on the
card holds it (A runs it). docs/cover-art.md is the house look;
tools/menuart.py calls draw() and writes the PNG. Edit this, not the PNG.

THE BRIEF
  Message: there is a program on board, ready to run. Not on the card: in
  the machine itself, in its flash, switched on and alive. (Revision 2, the
  owner's: the words PROGRAM IN FLASH / NOT ON CARD, and no key hint.)

  Composition (a thumbnail in words, top to bottom):
  - INSTALLED across the top (rows 3-28): chrome gold on calm black, a 2 px
    red depth (the family's, as on NO PICTURE and HOW IT WORKS) parted from
    the next letter by black, a black outline and drop shadow, a cream and
    gold0 bevel by edge runs, catch-lights on the I's and the D's top
    corners. Under it, quieter, in silver with a black rim:
    PROGRAM IN FLASH / NOT ON CARD (rows 30-46).
  - The hero: the handheld's chip, a big glossy black flat pack (a QFP,
    8 gull-wing legs a side) on its circuit board, in three-quarter view:
    the camera orbits 32 degrees round to its front left and looks down 32
    degrees, so its near corner points at us, low left of centre, and two
    rows of legs show (the key light turns with the camera, so it stays up
    left on the picture). Its top is one glossy plane: the far end mirrors
    the room (chip2) down to a crisp horizon (a one-row checker), the near
    end the dark floor (chip1); a window's reflection crosses its far left
    as two even parallel streaks (chip2, a grey core); a round dimple marks
    leg 1. Its edges: the key runs along the left one (grey, silver, cream
    at the near corner with a four-pointed glint), the front one in its
    shade (grey, then chip2). The left face takes the key (chip2), the front
    face is in shade (black, its top row rounding over in chip1).
    The focal point on the top: a play mark lit from inside, a neon ring
    (cyan, its near arc cream) and a symmetric cream triangle in a full
    cyan rim, one plateau of light round them (chip2) hugging the ellipse.
    The legs: lit as the key finds them (silver tops, grey or chip2 where
    they turn away, the left row's S curves read side on), cream only on
    the tips of the legs nearest the light; each throws a black shadow down
    and right; the far rows hide behind the body.
  - The board: green solder mask in perspective, the key's pool lying left
    of the chip (pcb2), falling to pcb1 and into the night, sooner behind
    the chip than in front, in plateaus that follow the board (no shelf).
    Copper traces fan out of every foot (straight, then bent 45 degrees, as
    a router lays them), a level above the mask, carrying the chip's light
    out of its feet (two levels brighter, then one, then the board's own):
    the chip is on. Five end in vias (one stamp, lit up left); the right
    row's end under the chip's shadow, behind its right edge.
  - The action: four light pulses race along the traces into the legs
    (cream heads at the foot end, cyan bodies with a one-pixel glow, tails
    fading into the trace): leading lines, every one pointing at the chip.
  - Behind it, in the night beyond the board: the family's reveal (as on
    the cover and NO PICTURE), spikes of light out of the mark that taper to
    points, a V of two rising past its far corner and long ones to the
    sides; a glow hugs the chip's far edges, so it stands backlit. Three
    motes hang in the dark under the words.
  - The installed program never shows the install bar (A runs it at once:
    platform/bootloader/src/visual.c).
  - The outer two rows and columns are kept dark for the installed border.
  Reading order: INSTALLED; the glowing mark on the chip; the pulses running
  into it.

PALETTE (11 own + cream, grey, black, red)
  pcb0 pcb1 pcb2 pcb3   the board and the night, dark to lit (BOARD ramp
                        black-pcb0..pcb3); the traces a level above the mask
                        round them; the spikes pcb1 with pcb2 cores; pcb3 the
                        traces at the feet, the pulses' tails and glow
  cyan                  the program's light: the mark, the pulses, the motes
  chip1 chip2           the epoxy (EPOXY ramp black-chip1-chip2-grey); chip2
                        also the mark's light and the window's reflection
  silver                the legs and the lit edge (METAL ramp chip1..cream),
                        the line of text, the vias
  gold0 gold1 gold2     the title's own face: nothing else uses them
  fixed: cream (glints, the mark's core, the pulses' heads, the legs' tips),
  grey (edges, legs, reflections), black (void, outlines, the shaded face),
  red (the title's depth)

LETTERING
  INSTALLED: ONE HUNDRED AND FIFTY NINE (bmf collection; author not stated,
  "freeware; authors vary, few gave terms": a `?` face, to be listed in the
  credits of docs/cover-art.md), set at its own size by
  tools/artkit/fontscout.py (--gap 2), emboldened by a pixel (ak.embolden),
  the A's bar joined to its left leg by hand. Chosen over the heavier TWO
  HUNDRED AND FOURTY FOUR and Cory (geos): it reads best at 1x, and its
  round, machined letters suit the subject.
  The line under it: Lepidos by surrealember (public domain),
  tools/art/fonts/installed-lepidos.json, its M drawn five wide here (the
  face's own reads as an H at 1x).
"""
from __future__ import annotations

import pathlib
import sys
import warnings

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402
from artkit import render3d as R  # noqa: E402

OUT = TOOLS.parent / "spec" / "assets" / "system" / "installed.png"
FONTS = TOOLS / "art" / "fonts"
SMALL = FONTS / "installed-lepidos.json"

# title: INSTALLED
# font: ONE HUNDRED AND FIFTY NINE (bmf/ONE HUNDRED AND FIFTY NINE)
# author: not stated
# terms: Freeware; authors vary, few gave terms
# source: https://github.com/tajmone/pixel-art-supplies/tree/master/fonts/bmf-fonts/bmf-cz
# set at the font's own size by tools/artkit/fontscout.py (--gap 2), then
# emboldened by a pixel (ak.embolden); the A's bar joined to its left leg by hand; the E's and
# the D's curves evened to a 4 px stroke by hand
TITLE = [
    "####..####.....####....############..############......######......####.......####..............######..#######.......",
    "####..####.....####...#############..############....##########....####.......####............########..#########.....",
    "####..#####....####..##############..############...############...####.......####..........##########..###########...",
    "####..#####....####..#####...............####.......#####..#####...####.......####.........#######......####.#######..",
    "####..######...####..####................####......#####....#####..####.......####.........#####........####...#####..",
    "####..######...####..#####...............####......####......####..####.......####........#####.........####....#####.",
    "####..#######..####...#####..............####......####......####..####.......####........####..........####.....####.",
    "####..#######..####....#####.............####......####......####..####.......####.......####...........####......####",
    "####..########.####.....#####............####......####......####..####.......####.......####...........####......####",
    "####..########.####......#####...........####......##############..####.......####.......#############..####......####",
    "####..#############.......#####..........####......##############..####.......####.......#############..####......####",
    "####..####.########........#####.........####......##############..####.......####.......#############..####......####",
    "####..####.########.........#####........####......####......####..####.......####.......####...........####......####",
    "####..####..#######..........#####.......####......####......####..####.......####.......####...........####......####",
    "####..####..#######...........#####......####......####......####..####.......####........####..........####.....####.",
    "####..####...######............####......####......####......####..####.......####........#####.........####....#####.",
    "####..####...######............####......####......####......####..#####......#####........#####........####...#####..",
    "####..####....#####...........#####......####......####......####...#####......#####.......#######......####.#######..",
    "####..####....#####..##############......####......####......####...########...########.....##########..###########...",
    "####..####.....####..#############.......####......####......####....#######....#######.......########..#########.....",
    "####..####.....####..############........####......####......####......#####......#####.........######..#######.......",
]
TITLE_Y = 3
TITLE_EXTRUDE = dict(dx=1, dy=1, depth=2, side="red", bottom="red")   # the family's red depth
TITLE_GLINTS = [(0, 0, (2, 1, 1, 1)), (112, 1, (2, 2, 2, 2))]   # catch-lights on the I's and the D's top corners: x, y, arms
WORDS = [("PROGRAM IN FLASH", 30), ("NOT ON CARD", 39)]

OWN = {
    "pcb0": "#03160F", "pcb1": "#0A3C26", "pcb2": "#17693E", "pcb3": "#2FA27C",
    "cyan": "#7AF2EE",
    "chip1": "#151A28", "chip2": "#323D58",
    "silver": "#B6C2D2",
    "gold0": "#8C4A0A", "gold1": "#EAA21E", "gold2": "#FFE47C",
}
BOARD = ["black", "pcb0", "pcb1", "pcb2", "pcb3"]
EPOXY = ["black", "chip1", "chip2", "grey"]
METAL = ["chip1", "chip2", "grey", "silver", "cream"]

# ---- the scene, in board units: x right, y up, z toward the viewer; the chip's middle at 0 ----
W, H, S = 10.0, 3.0, 0.45       # the body's half width, its height, its stand-off
NPIN, PITCH = 8, 2.5            # legs a side, and their spacing
PIN_W, PIN_T = 0.85, 0.32       # a leg's width and thickness
REACH = 2.7                     # how far a leg's foot reaches from the body
SHOULDER = 0.3                  # where a leg leaves the body (of its height)
YAW, DIST, TILT, FOV = -32.0, 51.0, 32.0, 42.0   # the camera: orbited left of the chip's front, its distance, looking down, fov
CENTRE = (60.0, 80.0)           # where the chip's middle lands on the picture
KEY = (-0.55, 0.75, 0.45)       # toward the key light (render3d's default)
POOL = (-14.0, 2.0, 30.0)       # the key's pool on the board: x, z, radius
REGION = (0, 36, 128, 128)      # where the chip is rendered
RING_R = 6.0                    # the play mark's ring on the top (board units)


def turn(v):
    """A direction given as seen from the camera (x right, y up, z toward it) in board units."""
    return R.rot_y(YAW) @ np.asarray(v, dtype=np.float64)


def camera():
    t = np.radians(TILT)
    pos = turn((0.0, 1.5 + DIST * np.sin(t), DIST * np.cos(t)))
    f = turn((0.0, -np.sin(t), -np.cos(t)))
    cam = R.Camera(pos, pos + f, fov=FOV)
    cx, cy = cam.project((0.0, S + H / 2, 0.0))
    return R.Camera(pos, pos + f, fov=FOV, shift=(CENTRE[0] - cx, CENTRE[1] - cy))


def on_plane(cam, X, Y, y0=0.0):
    """Where the rays through picture points (X, Y) meet the plane y = y0: (x, z)."""
    shp = np.shape(X)
    o, d = cam.rays(np.ravel(X).astype(np.float64), np.ravel(Y).astype(np.float64))
    t = (y0 - o[:, 1]) / np.where(np.abs(d[:, 1]) > 1e-9, d[:, 1], -1e-9)
    p = o + d * t[:, None]
    return p[:, 0].reshape(shp), p[:, 2].reshape(shp)


# ---- the chip: a rounded box and 32 gull-wing legs (distance functions) ----

def _box(q, c, h):
    d = np.abs(q - np.asarray(c)) - np.asarray(h)
    return np.linalg.norm(np.maximum(d, 0), axis=1) + np.minimum(d.max(axis=1), 0)


def _gullwing(q):
    """One leg, in its own frame: x out of the body's face (0 at the face), y up, z along the face."""
    y_sh = S + H * SHOULDER
    a = _box(q, (0.35, y_sh, 0.0), (0.65, PIN_T / 2, PIN_W / 2))                 # the shoulder
    # the leg: from the shoulder's end down to the foot, a slanted bar
    x0, y0, x1, y1 = 1.0, y_sh, 1.55, PIN_T / 2
    L = np.hypot(x1 - x0, y1 - y0)
    c, s = (x1 - x0) / L, (y1 - y0) / L
    lx, ly = q[:, 0] - (x0 + x1) / 2, q[:, 1] - (y0 + y1) / 2
    r = np.stack([lx * c + ly * s, -lx * s + ly * c, q[:, 2]], 1)
    b = _box(r, (0, 0, 0), (L / 2 + 0.12, PIN_T / 2, PIN_W / 2))
    f = _box(q, ((1.45 + REACH) / 2, PIN_T / 2, 0.0), ((REACH - 1.45) / 2, PIN_T / 2, PIN_W / 2))  # the foot
    return np.minimum(np.minimum(a, b), f)


def legs_sdf(p):
    z0 = -(NPIN - 1) * PITCH / 2
    best = np.full(len(p), np.inf)
    for sx, sz, swap in ((1, 1, False), (-1, -1, False), (1, -1, True), (-1, 1, True)):
        if swap:     # the front (+z) and back (-z) sides: outward is z
            q = np.stack([sx * p[:, 2] - W, p[:, 1], sz * p[:, 0]], 1)
        else:
            q = np.stack([sx * p[:, 0] - W, p[:, 1], sz * p[:, 2]], 1)
        k = np.clip(np.round((q[:, 2] - z0) / PITCH), 0, NPIN - 1)
        q[:, 2] = q[:, 2] - (z0 + k * PITCH)
        best = np.minimum(best, _gullwing(q))
    return best


def scene():
    body = R.xf(R.prim(R.box((W, H / 2, W), 0.4), 0), (0.0, S + H / 2, 0.0))
    return R.U(body, R.prim(legs_sdf, 1))


def leg_feet():
    """Each leg's foot tip on the board, (x, z), and the direction out: side by side."""
    z0 = -(NPIN - 1) * PITCH / 2
    out = {}
    e = W + REACH
    out["front"] = [((z0 + k * PITCH), e) for k in range(NPIN)]
    out["back"] = [((z0 + k * PITCH), -e) for k in range(NPIN)]
    out["left"] = [(-e, (z0 + k * PITCH)) for k in range(NPIN)]
    out["right"] = [(e, (z0 + k * PITCH)) for k in range(NPIN)]
    return out


# ---- the traces: from every foot, out, the outer ones bent 45 degrees (a fan), then on ----

FAN = 0.55          # how far the fan spreads the traces (in units of their offset from the middle)
STRAIGHT = 1.6      # the straight run out of a foot before the bend
FAR = 70.0          # where they end (off the picture)
NEAR = 40.0         # where the front ones end: past the picture's foot, short of the camera
RAYS, RAY_SPIN = 14, 8.0                        # the burst behind the chip: rays round, their turn
AURA = 2                                        # the glow round the chip's far side (pixels)
RAY_UP = 0.75                                   # rays steeper than this (sine) would only be stubs under the words
RAY_LEN, RAY_W = (78.0, 60.0), 9.0              # long and short rays (from the mark), their width at the chip
GLOW_LEN = 26       # how far (pixels) the traces carry the chip's light out of its feet
MOTES = [(13, 56, 1), (114, 50, 1), (24, 47, 1)]   # x, y, arm: light hanging in the dark

# short traces: (side, leg) -> its length from the foot (the back row's and most of the right row's
# end out of sight behind the chip; VIAS end in a via)
STUBS = {("left", 3): 3.6, ("left", 5): 7.0, ("front", 5): 3.8,
         **{("right", k): 2.4 for k in range(NPIN)}, ("right", 4): 4.6, ("right", 6): 3.2,
         **{("back", k): 3.0 + 1.6 * (k % 3) for k in range(NPIN)}}
VIAS = {("left", 3), ("left", 5), ("front", 5), ("right", 4), ("right", 6)}     # the stubs that end in a via
VIA = [".ss.",
       "skkg",
       ".gg."]          # a via, the same everywhere: a tinned ring lit up left, its hole black
DIMPLE = [".kk.",
          "kkkg",
          ".gg."]       # leg 1's dimple in the epoxy: dark up left, a grey lip lower right
# the play mark: a right-pointing triangle, its rows' lengths (cream), centred in the ring
TRIANGLE = [2, 5, 8, 11, 14, 17, 14, 11, 8, 5, 2]
BOARD_LV = (1.5, 1.5)      # the board's level away from the key's pool, and what the pool adds
FADE = (20.0, 12.0, 1.7)   # the lit board round the chip: where it starts to fade, over how far, how much sooner behind
HORIZON = 0.15      # where the top's gloss turns from the room (chip2) to the dark floor (chip1), far to near
WINDOW = (110.0, 2.1, 5.0, 0.6)  # the window's reflection: where (x + y of its middle), half widths, gap


def cut(pts, length):
    """The polyline's first `length` units."""
    out, acc = [pts[0]], 0.0
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        L = np.hypot(x1 - x0, z1 - z0)
        if acc + L >= length:
            t = (length - acc) / L
            out.append((x0 + t * (x1 - x0), z0 + t * (z1 - z0)))
            return out
        out.append((x1, z1))
        acc += L
    return out


def routes():
    """Each trace: (side, index, [(x, z) points from the foot outward])."""
    out = []
    for side, feet in leg_feet().items():
        for k, (x, z) in enumerate(feet):
            if side in ("front", "back"):
                sgn = 1 if side == "front" else -1
                off = x
                z1 = z + sgn * STRAIGHT
                spread = off * FAN
                z2 = z1 + sgn * abs(spread)
                pts = [(x, z), (x, z1), (x + spread, z2), (x + spread, sgn * (NEAR if sgn > 0 else FAR))]
            else:
                sgn = 1 if side == "right" else -1
                off = z
                x1 = x + sgn * STRAIGHT
                spread = off * FAN
                x2 = x1 + sgn * abs(spread)
                pts = [(x, z), (x1, z), (x2, z + spread), (sgn * FAR, z + spread)]
            if (side, k) in STUBS:
                pts = cut(pts, STUBS[(side, k)])
            out.append((side, k, pts))
    return out


# the pulses racing into the chip: (side, leg, the head's distance from the foot in pixels along the
# trace, the length in pixels)
PULSES = [("left", 2, 3, 10), ("left", 4, 5, 12), ("left", 6, 4, 11), ("front", 6, 3, 10)]


def trace_pixels(cam, pts, wide):
    """A trace as clean pixels from its foot outward: [(x, y, i)], i the step
    along it; `wide` doubles it (below a shallow run, right of a steep one)."""
    scr = [cam.project((x, 0.0, z)) for x, z in pts]
    line = ak.line_px(scr)
    out = []
    for i, (x, y) in enumerate(line):
        out.append((x, y, i))
        if wide:
            a = line[max(0, i - 2)]
            b = line[min(len(line) - 1, i + 2)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            out.append((x, y + 1, i) if abs(dx) >= abs(dy) else (x + 1, y, i))
    return out


def stamp(pic, rows, x, y, key, where=None):
    """Hand pixels (rows of characters, `key` {char: colour}) with their top left at (x, y)."""
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            u, v = x + i, y + j
            if ch in key and 0 <= u < 128 and 0 <= v < 128 and (where is None or where[v, u]):
                pic.px(u, v, key[ch])


def geometry(cv, cam, sc):
    """The chip at each pixel: its material (the majority of the samples),
    its normal, the point it shows, and how much of the key light reaches it
    (shadows included)."""
    s = cv.s
    out = R.render(cv, sc, cam, [R.Mat("#FFFFFF", spec=0.0), R.Mat("#FFFFFF", spec=0.0)],
                   lights=[(turn(KEY), "#FFFFFF", 1.0)], ambient="#000000", region=REGION, ss=2,
                   tmax=140.0, ao=False)
    mat = R.majority(out, s)
    nrm = np.stack([ak.px_mean(out["normal"][..., i], s) for i in range(3)], -1)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
    lit = ak.px_mean(out["rgb"][..., 0], s)
    dep = out["depth"].reshape(128, s, 128, s).transpose(0, 2, 1, 3).reshape(128, 128, s * s)
    dep = np.where(np.isfinite(dep), dep, np.nan)
    with warnings.catch_warnings():                             # (pixels the chip misses: all NaN)
        warnings.simplefilter("ignore", RuntimeWarning)
        tmid = np.nanmedian(dep, axis=-1)
    yy, xx = np.mgrid[0:128, 0:128]
    o, d = cam.rays((xx + 0.5).ravel().astype(np.float64), (yy + 0.5).ravel().astype(np.float64))
    hit = (o + d * np.nan_to_num(tmid.ravel(), nan=0.0)[:, None]).reshape(128, 128, 3)
    return mat, nrm, lit, hit


def tidy(pic, mask, keep=None, passes=2):
    """Lone pixels inside `mask` (no 4-neighbour of their colour within it)
    take the colour most of their 4-neighbours within the mask share."""
    a = pic.idx
    for _ in range(passes):
        nb = [(ak.shift(mask, dx, dy), np.roll(np.roll(a, dy, 0), dx, 1))
              for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        same = np.zeros(a.shape, bool)
        for m_, v in nb:
            same |= m_ & (v == a)
        lone = mask & ~same
        if keep is not None:
            lone &= ~keep
        best, cnt = a.copy(), np.zeros(a.shape, int)
        for _, v0 in nb:
            n = np.zeros(a.shape, int)
            for m_, v in nb:
                n += m_ & (v == v0)
            ok = n > cnt
            best, cnt = np.where(ok, v0, best), np.where(ok, n, cnt)
        fix = lone & (cnt >= 2)
        a[fix] = best[fix]
        if not fix.any():
            break


def traces_hot(pic):
    """What must not be glowed over: the lightest things already painted."""
    return pic.where("cream") | pic.where("cyan") | pic.where("silver") | pic.where("grey")


def ellipse_d(X, Y, cx, cy, a, b):
    """Roughly how many pixels (X, Y) lies outside the ellipse (negative inside)."""
    u, v = (X - cx) / a, (Y - cy) / b
    rho = np.hypot(u, v)
    g = np.hypot(u / a, v / b) / np.maximum(rho, 1e-6)
    return (rho - 1) / np.maximum(g, 1e-6)


def draw():
    P = ak.Palette(OWN, ramps=[BOARD, EPOXY, METAL, ["gold0", "gold1", "gold2", "cream"]])
    pic = ak.Picture.blank(P, "black")
    cv = ak.Canvas("#000000")
    s = cv.s
    yy, xx = np.mgrid[0:128, 0:128]
    X1, Y1 = xx + 0.5, yy + 0.5
    cam = camera()

    # the board under every pixel, in board units, and turned to the camera (u right, v toward us)
    BX, BZ = on_plane(cam, X1, Y1)
    a_ = np.radians(-YAW)
    U = BX * np.cos(a_) + BZ * np.sin(a_)
    V = -BX * np.sin(a_) + BZ * np.cos(a_)

    # ---- the chip, ray marched: what each pixel shows, and the shadow it casts
    sc = scene()
    mat, nrm, lit, hit = geometry(cv, cam, sc)
    dark = ak.px_mean(R.ground(cv, sc, cam, light=turn(KEY), region=(0, 36, 128, 128), ss=2), s)
    body, legs = mat == 0, mat == 1
    chip = body | legs
    board = ~chip

    # ---- the board: flat plateaus of solder mask. The key's pool lies left of the chip; round the
    # chip the board fades into the night (sooner behind it), black under the words; the chip
    # throws its shadow behind its right edge; the legs shade the board under them
    r = np.hypot(U - POOL[0], (V - POOL[1]) * 1.15) / POOL[2]
    lv = BOARD_LV[0] + BOARD_LV[1] * np.clip(1 - r, 0, 1) ** 0.7
    rb = np.hypot(U, V * np.where(V < 0, FADE[2], 1.0))               # the board round the chip, sooner behind it
    lv -= np.clip((rb - FADE[0]) / FADE[1], 0, 1) * 1.7
    lv -= np.clip((54 - Y1) / 6, 0, 1) * 2.6                          # nothing under the words
    lv -= np.clip((Y1 - 104) / 14, 0, 1) * 1.0
    lv -= np.clip(np.hypot((X1 - 56) / 74, (Y1 - 80) / 58) - 0.8, 0, 1) * 3.0
    lv -= np.minimum(dark, 1.0) * 1.4
    foot_d = np.maximum(np.abs(BX), np.abs(BZ)) - W                  # how far outside the body's square
    legzone = (foot_d > -0.5) & (foot_d <= REACH + 0.3)
    lv = np.where(legzone, np.minimum(lv, 1.0), lv)
    blv = np.clip(ak.terrace(lv, 0.08), 0, 4)
    ak.by_level(pic, blv, BOARD, board, q=2)
    bl_whole = np.clip(np.floor(blv + 0.5), 0, 4).astype(int)

    # ---- the burst: spikes of light out of the mark into the night behind the chip (the family's
    # reveal, as on the cover and NO PICTURE); each tapers to a point, its core brighter near the chip
    ecx0, ecy0 = cam.project((0.0, S + H, 0.0))
    ang = np.degrees(np.arctan2(Y1 - ecy0, X1 - ecx0))
    rd = np.hypot(X1 - ecx0, Y1 - ecy0)
    kr = np.floor((ang - RAY_SPIN) / (360.0 / RAYS) + 0.5).astype(int)
    dang = np.radians((ang - (RAY_SPIN + kr * 360.0 / RAYS) + 180) % 360 - 180)
    dperp = np.abs(rd * np.sin(dang))
    L = np.where(kr % 2 == 0, RAY_LEN[0], RAY_LEN[1])
    up_ = -np.sin(np.radians(RAY_SPIN + kr * 360.0 / RAYS))           # how steeply each ray rises
    L = np.where(up_ > 0.05, np.minimum(L, (ecy0 - 51.0) / np.maximum(up_, 1e-3)), L)   # ends short of the words
    wid = RAY_W * np.clip((L - rd) / np.maximum(L - 18.0, 1.0), 0, 1)
    (lx_, ly_), (rx_, ry_) = cam.project((-W, 0.0, -W)), cam.project((W, 0.0, W))
    behind = Y1 < ly_ + (X1 - lx_) * (ry_ - ly_) / (rx_ - lx_) - 2
    night = board & (bl_whole <= 1) & (Y1 > 48) & behind                 # only behind the chip
    spike = night & (dperp < wid / 2) & (np.cos(dang) > 0) & (up_ < RAY_UP)
    core = spike & (dperp < wid / 2 - 2.0) & (rd < L * 0.62)
    pic.put(spike, "pcb1")
    pic.put(core, "pcb2")
    # the chip's light behind it: a glow hugging its far side, against the night
    aura = ak.dilate(chip, AURA, diag=True) & board & behind & (bl_whole <= 1) & ~spike
    pic.put(aura, "pcb1")

    # ---- the traces: copper under the mask, a level above it; out of each foot the chip's light
    # runs into them (the underglow): two steps brighter, then one, then the board's own
    tr_lv = np.full((128, 128), -1)
    tpx = {}
    for side, k, pts in routes():
        wide = side in ("front", "left")
        px = [(x, y, i) for x, y, i in trace_pixels(cam, pts, wide) if 0 <= x < 128 and 0 <= y < 128]
        tpx[(side, k)] = px
        for x, y, i in px:
            if not board[y, x] or legzone[y, x]:
                continue
            base = bl_whole[y, x] + 1
            hot = 4 if i < 3 else (3 if i < GLOW_LEN - 3 * (bl_whole[y, x] < 1) else 0)
            tr_lv[y, x] = max(tr_lv[y, x], min(4, max(base, hot)))
    traces = tr_lv >= 0
    ak.put_levels(pic, traces, np.clip(tr_lv, 0, 4), BOARD)

    # ---- the pads under the feet (copper, in the legs' shade)
    c_ = (np.arange(128 * s) + 0.5) / s
    SX, SZ = on_plane(cam, *np.meshgrid(c_, c_))
    pads = np.zeros((128, 128), bool)
    for side, feet in leg_feet().items():
        ox, oz = {"front": (0, 1), "back": (0, -1), "left": (-1, 0), "right": (1, 0)}[side]
        for (x, z) in feet:
            cx_, cz_ = x - ox * 0.75, z - oz * 0.75
            hw, hd = (PIN_W / 2 + 0.22, 1.05) if oz else (1.05, PIN_W / 2 + 0.22)
            dd = np.maximum(np.abs(SX - cx_) - hw, np.abs(SZ - cz_) - hd)
            pads |= ak.px_mean((dd < 0).astype(np.float32), s) >= 0.5
    pads &= board
    ak.put_levels(pic, pads, np.clip(bl_whole + 1, 0, 3), BOARD)

    # ---- the vias: one stamp, where five of the short traces end
    keep = np.zeros((128, 128), bool)
    for side, k, pts in routes():
        if (side, k) in VIAS:
            vx, vy = cam.project((pts[-1][0], 0.0, pts[-1][1]))
            x0, y0 = int(round(vx - 2)), int(round(vy - 1.5))
            stamp(pic, VIA, x0, y0, {"s": "silver", "k": "black", "g": "grey"}, where=board)
            keep[max(0, y0):y0 + 3, max(0, x0):x0 + 4] = True

    # ---- the chip's body: glossy black epoxy
    n_x, n_y, n_z = nrm[..., 0], nrm[..., 1], nrm[..., 2]
    top = body & (n_y > 0.8)
    lface = body & (n_x < -0.7) & ~top
    fface = body & (n_z > 0.7) & ~top
    rim = body & ~top & ~lface & ~fface
    TX, TZ = on_plane(cam, X1, Y1, S + H)
    mx, my = cam.project((0.0, S + H, 0.0))                          # the top's middle on the picture
    ring_pts = np.array([cam.project((RING_R * np.cos(t), S + H, RING_R * np.sin(t)))
                         for t in np.linspace(0, 2 * np.pi, 360)])
    ea = (ring_pts[:, 0].max() - ring_pts[:, 0].min()) / 2
    eb = (ring_pts[:, 1].max() - ring_pts[:, 1].min()) / 2
    ecx, ecy = np.floor(mx) + 0.5, np.floor(my) + 0.5
    ed = ellipse_d(X1, Y1, ecx, ecy, ea, eb)                           # pixels out from the ring
    # the top: one plane. The far part mirrors the room (the view grazes it): chip2, down to a
    # crisp horizon (a one-row checker) parallel to the picture; nearer, the dark floor (chip1)
    ys_top = np.nonzero(top.any(axis=1))[0]
    yfar, ynear = ys_top.min(), ys_top.max()
    ys_ = yfar + int(round(HORIZON * (ynear - yfar)))                  # the room's horizon in the gloss
    pic.put(top, "chip1")
    pic.put(top & (Y1 < ys_), "chip2")
    pic.put(top & (yy == ys_) & ak.checker(), "chip2")
    # round the mark, its light on the epoxy: one plateau hugging the ring, a 1 px seam
    pic.put(top & (ed < 2.5), "chip2")
    pic.put(top & (ed >= 2.5) & (ed < 3.5) & ak.checker(), "chip2")
    # a window's reflection: two even, parallel bars across the far left part of the top
    wv = X1 + Y1
    inner = ak.erode(top, 1, diag=True) & (ed > 4.0) & (yy > ys_ + 1)
    w0 = WINDOW[0]
    bar1 = inner & (np.abs(wv - w0) < WINDOW[1])
    bar2 = inner & (np.abs(wv - (w0 + WINDOW[2])) < WINDOW[3])
    pic.put(bar1 | bar2, "chip2")
    pic.put(bar1 & (np.abs(wv - w0) < WINDOW[1] - 1.0), "grey")
    # the dimple by leg 1
    dx_, dy_ = cam.project((-W + 3.0, S + H, -W + 3.2))
    stamp(pic, DIMPLE, int(dx_) - 2, int(dy_) - 1, {"k": "black", "g": "grey"}, where=top)
    # the faces: the left one faces the key (chip2), the front one is in shade (black)
    pic.put(lface | rim, "chip2")
    pic.put(fface, "black")
    pic.put(fface & ~ak.shift(fface, 0, 1) & ~ak.shift(top, 0, 1), "chip1")   # its top, rounding over
    pic.put(rim & (n_x < -0.3) & (n_z > 0.3) & (n_y <= 0.25), "grey")   # the near corner, upright
    pic.put(body & ~ak.shift(body, 0, -1) & ~top, "black")             # where the body meets its shade
    # the top's edges: the key runs along the left one (cream by the near corner, silver, grey
    # toward the back), the front one in its shade (grey by the corner, then chip2)
    bd = top & ~ak.erode(top, 1)
    near_side = np.argmin(np.stack([TX + W, W - TZ, TZ + W, W - TX]), 0)
    e_l, e_f = bd & (near_side == 0), bd & (near_side == 1)
    e_l |= rim & ak.nbrs(e_l) & (n_x < -0.2) & (n_y > 0.2)              # the rounded rim beside them, so
    e_f |= rim & ak.nbrs(e_f) & (n_z > 0.2) & (n_y > 0.2)               # each line steps evenly
    pic.put(e_l, "grey")
    pic.put(e_l & (TZ > -W + 4.0), "silver")
    pic.put(e_l & (TZ > W - 3.5), "cream")
    pic.put(e_f, "chip2")
    pic.put(e_f & (TX < -W + 6.0), "grey")

    # ---- the legs: a silver top, grey or chip2 where they turn from the key; the far rows a step
    # darker; cream only on the tips of the legs nearest the light
    hx, hz = hit[..., 0], hit[..., 2]
    near = legs & ((hz > W - 0.2) | (hx < -W + 0.2))
    llv = np.where(lit > 0.62, 3, np.where(lit > 0.3, 2, 1))
    llv = np.where(near, llv, llv - 1)
    ak.put_levels(pic, legs, np.clip(llv, 0, 3), METAL)
    z0 = -(NPIN - 1) * PITCH / 2
    tip_l = legs & (hx < -W - REACH + 0.45) & (hz > z0 + (NPIN - 2.5) * PITCH) & (n_y > 0.6)
    tip_f = legs & (hz > W + REACH - 0.45) & (hx < z0 + 1.5 * PITCH) & (n_y > 0.6)
    tidy(pic, legs)
    pic.put(tip_l | tip_f, "cream")
    # the contact shadow each leg throws down and right onto the board
    pic.put(ak.shift(legs, 1, 1) & board & ~ak.shift(legs, 0, -1), "black")

    # ---- the play mark: a neon ring and the triangle, lit from inside
    ring = top & (ed > -2.0) & (ed <= 0.0)
    pic.put(ring, "cyan")
    pic.put(ring & (ed > -1.0) & (Y1 > ecy + eb * 0.55), "cream")      # its near arc, hottest
    tw, trh = max(TRIANGLE), len(TRIANGLE)
    tx0, ty0 = int(round(ecx - tw / 2 + 1)), int(round(ecy - trh / 2))           # a pixel right of centre: optical
    tri = np.zeros((128, 128), bool)
    for j, n in enumerate(TRIANGLE):
        tri[ty0 + j, tx0:tx0 + n] = True
    pic.put(ak.dilate(tri, 1, diag=True) & ~tri, "cyan")
    pic.put(tri, "cream")
    keep |= ring | ak.dilate(tri, 1, diag=True)

    # ---- the pulses: cream heads, cyan bodies, tails fading into the trace, racing into the legs
    heads = []
    for side, k, head, length in PULSES:
        pbody = np.zeros((128, 128), bool)
        lit_ = np.zeros((128, 128), bool)
        for x, y, i in tpx[(side, k)]:
            if not board[y, x]:
                continue
            u = (i - head) / length
            if 0 <= u < 1:
                c = "cream" if u < 0.12 else ("cyan" if u < 0.55 else "pcb3")
                pic.px(x, y, c)
                lit_[y, x] = True
                pbody[y, x] = u < 0.55
                if i == head:
                    heads.append((x, y))
        halo = ak.dilate(pbody, 1) & board & ~lit_ & ~traces_hot(pic)    # the light it throws on the mask
        pic.put(halo, "pcb3")
        keep |= lit_ | halo

    # ---- no lone pixels on the board and the chip (the mark, vias and pulses kept)
    ak.despeckle(pic, need=5, keep=keep, within=(Y1 > 28), passes=2)

    # ---- the frame: the outer two rows and columns dark, so the installed border frames the picture
    frame = (xx < 2) | (xx > 125) | (yy > 125)
    darker = {"cream": "cyan", "cyan": "pcb3", "pcb3": "pcb2", "pcb2": "pcb1", "silver": "grey", "grey": "chip2"}
    for _ in range(2):
        for a2, b2 in darker.items():
            pic.put(frame & pic.where(a2), b2)
    pic.put((frame & ((xx < 1) | (xx > 126) | (yy > 126))) & pic.where("pcb1"), "pcb0")

    # ---- the near corner's glint; the first pulse's head flares; motes in the dark
    gx, gy = cam.project((-W + 0.25, S + H, W - 0.25))
    ak.glint(pic, int(gx), int(gy), size=2)
    if heads:
        ak.glint(pic, *heads[0], size=1, core="cream", tip=None)
    for x_, y_, n_ in MOTES:
        ak.glint(pic, x_, y_, size=n_, core="cyan")

    # ---- the title
    m = np.array([[ch == "#" for ch in r_] for r_ in TITLE], bool)
    tx = ak.centred_x(m)
    rows = ["gold2"] * 9 + ["gold1", "gold0", "gold2"] + ["gold1"] * 6 + ["gold0"] * 3
    t = ak.title(pic, m, tx, TITLE_Y, fill=None, rows=rows, hi=None, lo=None,
                 extrude=TITLE_EXTRUDE, shadow=dict(dx=1, dy=2, colour="black"))
    # each letter's depth stops a pixel short of the next letter: black between them
    lab = ak.letters(t["face"])
    for i in range(1, lab.max() + 1):
        Li = lab == i
        Ei = np.zeros_like(Li)
        for k in range(1, TITLE_EXTRUDE["depth"] + 1):
            Ei |= ak.shift(Li, TITLE_EXTRUDE["dx"] * k, TITLE_EXTRUDE["dy"] * k)
        Ei &= t["extrude"]
        others = t["face"] & ~Li
        pic.put(Ei & ak.nbrs(others), "black")
    ak.bevel_runs(pic, t["face"], "cream", "gold0")
    for gx_, gy_, arms in TITLE_GLINTS:
        ak.glint(pic, tx + gx_, TITLE_Y + gy_, arms=arms, tip="gold2")

    # ---- the words
    f = ak.Font(SMALL)
    f.g["M"] = [5, 7, 0, 4, 6, ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"]]   # an M, not an H
    for line, y_ in WORDS:
        mt = f.mask(line)
        Mt = ak.place(mt, 64 - mt.shape[1] // 2, y_)
        pic.put(ak.dilate(Mt, 1, diag=True) & ~Mt, "black")
        pic.put(Mt, "silver")

    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), OUT))
