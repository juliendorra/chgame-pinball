"""tools/sdcard/art/cover.png: the CHGame CASINO cart's cover, the splash at
power-on and the top of the visual menu (docs/cover-art.md,
docs/visual-menu.md). `python tools/sdcard/covers.py` redraws it; edit
this, not the PNG.

THE BRIEF (revision 3)
  Message: welcome to the CHGame Casino. The lights are on, the games are
  waiting: the first thing anyone sees when the console switches on, so it
  is the whole collection's identity, a night in Vegas in one picture.

  Composition (a thumbnail in words):
  - The top half is the marquee. The CHGAME logo (the owner's mark, at its
    own 72 x 17 pixels) crowns it in gold chrome (tools/art/chglogo.py, the
    family's mark), on calm flat navy, a navy1 halo hugging its sides and
    foot (none above it: no shelf under the frame). Under it CASINO, the
    biggest thing in the picture, as a sign maker's channel letters
    (chglogo.channel): a neon tube in the rainbow colour (#FF00FF, index
    15: the Rainbow menu turns it through the colour wheel, the Static one
    shows magenta) with a white-hot cream core down every stroke's middle,
    inside a can whose face glows violet round the tube, a black lip, navy
    returns two pixels deep down-right and a black drop shadow: a sign with
    mass, crisp in every phase of the wheel (blue included). The glow is
    the night itself: the air the sign lights is an ellipse of navy1 round
    the word, its edge one narrow seam that curves (no dots, no straight
    shelf); between the letters the night is one flat level, so no seam
    crosses a counter or a gap, and a pixel of night shut in by the cans is
    closed with their black. Two small stars in the top corners.
  - The middle band is the Strip: a skyline in two layers against the
    violet glow on the horizon, far towers navy1 with a few dim and warm
    windows, near ones black with navy1 roof rims, their windows violet,
    ivory and a few burning cream, a red light on each spire. It frames the
    sign's foot and says "Vegas" at a glance.
  - The bottom half is the table, seen low and close (a wide lens): its
    padded rail (wine leather, lit red along its top, the sign's colour on
    the lip under the sign: the neon lighting the table, one continuous run)
    arcs across under the skyline and throws a band of shade on the felt
    under it; the felt sits in the key's pool of light, its plateau on the
    open felt left of the fan and above it, falling to felt1, navy and
    black toward the sides and the front, every seam one narrow step
    following the table's perspective. The games spill toward us:
    - the hero, a fan of three cards dead centre under the sign: the ace of
      spades upright in front (cream with an ivory sheen falling to its lower
      right along one diagonal seam; the A and a small spade in its corner;
      a big spade drawn on the pixels, 17 x 19, its sides even 1-1-1 steps,
      a grey gloss tapering to navy along its upper left edge; no index at
      the bottom, as on the games' own cards), two red backs with a wine
      lattice fanned behind it, each turned an even 1-in-3, both showing;
    - a pair of red dice tumbling in from the upper right: a far one in the
      air over the right back's corner and the rail, showing 3 on top (2
      and 1 on its sides), a near one bigger at the lower right, showing 4
      (1 and 2): a seven. Each is an exact cube in perspective with rounded
      corners and three flat values so it reads at a glance: the top the
      key lights rose (falling to red in its far corner, one seam), the
      face below it red, the face turned away wine; the edge between the
      top and the red face a continuous cream specular run tapering to rose,
      the edge to the dark face a red lip; round pips (cream, ivory on the
      dark face) kept a pixel clear of those edges. Two speed lines each,
      rooted just behind the trailing edge, run back up and to the right and
      bend level (the top of the throw's arc), tapering cream to ivory to
      grey, a black edge under them on the felt and the rail;
    - a stack of five red clay chips on the left, in front of the left
      card's corner (it overlaps the card decisively), drawn on the pixels:
      each chip's edge in three flat values by how it turns from the key
      (rose, red, wine), six cream edge spots that narrow as they turn away
      (ivory in the shade), an unbroken black seam under each chip; the top
      chip's face red with a wine inlay ring, six cream rim spots and its
      rim rose toward the key; its shadow down right on the felt.
  - The eye: CASINO, the logo, down through the sign's glow to the ace (the
    biggest cream shape, its big black spade), then out to the dice and
    the chips.
  - Light: the house key from the top left: the dice's tops, the chips'
    left sides and the felt's pool toward it, the ace's sheen on its lower
    right, the props' shadows down right. Black outlines round every prop;
    the felt falls to black toward us and the outer two rows and columns
    step down, so the menu's border frames a dark edge and the install bar
    sits on dark.
  - The titles are alone in their colours: gold0-2 is the logo's and
    nothing else's; the rainbow colour is the sign's (and its light on the
    rail's lip under it). Their ground is the calm navy night.

  Palette (11 own + cream, grey, black, red; the rainbow colour on purpose):
    navy0 navy1 violet     the night, dark to the horizon's glow; the air
                           the sign lights; the sign's can (violet face,
                           navy0 returns); the skyline; the felt's shade;
                           the spade's gloss's tail
    rose                   red in the light: the dice's tops, the chips'
                           lit side and rim
    gold0 gold1 gold2      the logo's own: nothing else uses them
    wine                   red in shade: the dice's dark faces, the card
                           backs' lattice, the chips' inlay and shade, the
                           rail
    felt1 felt2            the table (navy0 and black below them)
    ivory                  the ace's sheen and the cards' edges, pips and
                           chip spots in shade, warm windows, the speed
                           lines' middle
    fixed: cream (the neon's core, cards, pips, spots, the dice's
    specular, windows), red (dice, backs, chips, the rail, the spire
    lights), black (outlines, seams, the void), grey (the spade's gloss,
    the speed lines' tails, the stars' tips)

  How it is painted: the sky, the sign's air and the felt are levels on
  their ramps (artkit.paint: by_level, terrace: flat bands, dithered only at
  narrow seams); the dice are exact cubes in perspective (render3d's camera
  projects their faces; the silhouette rounded), each face one flat level,
  their lit edges picked one pixel per column off the face's lip; the chips
  are ellipses and bands on the pixels; the cards are drawn on the pixels
  (their glyphs from tools/art/common: ranks, suits; the big spade here).
  Lone pixels on the table are cleaned (the props and their lines kept),
  then the sign, then the logo, then the frame.

  Lettering: CASINO is Pee Wee by Complex (the bmf collection: freeware,
  author's terms not stated; a `?` face, chosen because its round geometric
  monoline caps, three pixels thick, are a neon tube's own shape), spaced
  by hand so each letter is its own tube, its arcs thickened to three
  pixels so the white-hot core runs down every stroke's middle
  (cover_neon.txt). The CHGAME logo is the owner's.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent             # tools/sdcard/art/src
TOOLS = HERE.parents[2]                                     # the repository's tools/
for p in (TOOLS, TOOLS / "art", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402
from artkit import render3d as R  # noqa: E402
import chglogo as cl  # noqa: E402

NEON = HERE / "cover_neon.txt"
YY, XX = np.mgrid[0:128, 0:128]
X1, Y1 = XX + 0.5, YY + 0.5

PAL = {
    "navy0": "#0A0C26", "navy1": "#1C1E52", "violet": "#46267A",     # the night, dark to the horizon's glow
    "rose": "#F2644A",                                                 # red in the light
    **cl.GOLD,                                                         # the logo's own
    "wine": "#640E22",                                                 # red in shade
    "felt1": "#0C5A34", "felt2": "#1E8C4C",                            # the table
    "ivory": "#C4B49A",                                                # the cards' sheen, pips in shade
}
SKY = ["black", "navy0", "navy1", "violet"]
FELT = ["black", "navy0", "felt1", "felt2"]
REDS = ["black", "wine", "red", "rose", "cream"]

LOGO_Y = 4
NEON_Y = 30
SKY_ROWS = ([0, 36, 48, 58], [1.0, 1.0, 1.9, 3.2])     # the sky's level by row: flat navy, rising to violet at the horizon
SIGN_AIR = (64, 41, 74, 24, 1.25, 0.32)   # the sign's light in the air: an ellipse (centre, radii), its lift, its edge's width
LOGO_HALO = 2                      # px of navy1 hugging the logo
RAIL = (65, 8)                     # the table's far rail: its top at the middle, how far it falls at the sides
POOL = (40, 86, 56, 26)            # the key's pool of light on the felt: centre, radii (its plateau is the inner 55%)
FRONT = (104, 12, 2.4)             # the felt falls into the dark toward us: from this row, over these rows, by this much
RAIL_SHADE = 4                     # rows of shade the rail throws on the felt under it
STARS = [(9, 8, (1, 1, 1, 1)), (117, 12, (2, 2, 2, 2))]       # x, y, arms
# the skyline: (left, width, top row, roof); roof: flat, step, spire
FAR_TOWERS = [(4, 8, 54, "flat"), (18, 7, 52, "step"), (36, 8, 57, "flat"), (46, 6, 59, "flat"),
              (78, 7, 59, "flat"), (86, 9, 56, "step"), (100, 6, 53, "flat"), (114, 8, 55, "step")]
TOWERS = [(0, 9, 57, "flat"), (7, 6, 54, "spire"), (14, 10, 59, "step"), (26, 5, 56, "flat"),
          (34, 9, 61, "flat"), (93, 10, 60, "step"), (103, 5, 54, "spire"), (108, 12, 57, "flat"),
          (119, 9, 59, "step")]
FAR_WINDOWS = (0.3, 0.1)           # the far towers' window slots lit: violet, ivory
WINDOWS = (0.42, 0.2, 0.06)        # the near towers' window slots lit: violet (dim), ivory (warm), cream (bright)

# ---- the props --------------------------------------------------------------------------
CAM = R.Camera((0.0, 4.0, 9.5), (0.0, 0.0, 0.0), fov=42, shift=(0, 30))     # low and close, a wide lens
KEY = np.array([-0.55, 0.78, 0.42])
KEY = KEY / np.linalg.norm(KEY)
# the dice, in the air: where on the picture, the height of the centre, size,
# show: (a face, the way it looks (x right, y up, z toward us), a spin about
# that), the silhouette's corner radius (px), the shadow's offset (px)
DICE = [dict(scr=(95, 79), h=1.7, show=(3, (-0.15, 0.85, 0.3), 330), size=0.72, rnd=1.6, sh=(4, 2)),
        dict(scr=(101, 104), h=0.9, show=(4, (-0.3, 0.85, 0.2), 30), size=0.98, rnd=2.2, sh=(3, 2))]
TOP_FALL = (0.22, 0.3)             # the lit top: rose to here (from its middle, away from the key), then red
# speed lines: the way the dice came (up and to the right, on the picture),
# how far behind the die each starts, and per die: (offset across the path
# from the die's middle, length, how far it bends level (degrees), radius at
# the root), px
TRAIL_DIR = (1.0, -1.0)
TRAIL_GAP = 2.0
TRAILS = [[(-4, 19, 40, 1.3), (5, 14, 40, 1.1)],
          [(-5, 16, 40, 1.4), (5, 12, 40, 1.2)]]
# the chip stack, drawn on the pixels: its middle, the bottom of its lowest
# chip, chips, half width and half height of a chip's face, a chip's edge
# (px), each chip's nudge sideways and the turn of its edge spots (degrees)
STACK = dict(cx=21.5, base=119.0, n=5, rx=11.5, ry=4.5, t=4.0, nudge=(0, 0, 0, 1, 1),
             turn=(5, 33, 18, 47, 26), spot=8)
STACK_SHADOW = (7, -2, 4, 1.5)     # its shadow on the felt: offset from its foot, extra radius, depth
# the cards, back to front: rank ("back" face down), suit, centre on the picture, tilt (-1, 0, 1)
SLOPE = 1 / 3                      # the fan's tilt: an even 1-in-3 step on every edge
CARDS = [("back", "", (44, 95), -1), ("back", "", (76, 95), 1), ("A", "s", (60, 92), 0)]
CARD_W, CARD_H = 25, 35
# the ace's spade, drawn on the pixels (17 x 19: the house 13 x 13 pip grown,
# its sides even 1-1-1 steps), and where it sits (from the card's middle);
# 'g' the gloss along its upper left edge (grey), 'n' its tail (navy1)
ACE_SPADE = [
    "........#........",
    "........#........",
    ".......###.......",
    "......#g###......",
    ".....#g#####.....",
    "....#g#######....",
    "...#g#########...",
    "..#n###########..",
    ".##n############.",
    ".###############.",
    "#################",
    "#################",
    "#################",
    "#################",
    ".#####.###.#####.",
    "..###...#...###..",
    ".......###.......",
    "......#####......",
    ".....#######.....",
]
ACE_SPADE_AT = (0, 2)
SHEEN = 0.62                       # the ace's ivory sheen: where it starts along its diagonal (0 the top-left corner, 1 the bottom-right)
# a shade darker, for the frame's edge
DARKER = {"cream": "ivory", "ivory": "grey", "grey": "navy1", "rose": "red", "red": "wine", "wine": "black",
          "felt2": "felt1", "felt1": "navy0", "navy0": "black", "navy1": "navy0", "violet": "navy1",
          "rainbow": "violet", "gold2": "gold1", "gold1": "gold0", "gold0": "black"}

# a die's faces: pips -> (outward normal, u, v) in its own frame
FACES = {6: ((0, 1, 0), (1, 0, 0), (0, 0, 1)), 1: ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
         2: ((0, 0, 1), (1, 0, 0), (0, 1, 0)), 5: ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
         3: ((1, 0, 0), (0, 0, 1), (0, 1, 0)), 4: ((-1, 0, 0), (0, 0, 1), (0, 1, 0))}
PIP_S, PIP_R = 0.25, 0.1


def facing(face, toward, spin=0.0):
    """A die's turn (its own frame -> the world) that shows `face` toward
    `toward`, spun `spin` degrees about it."""
    n = np.array(FACES[face][0], float)
    d = np.asarray(toward, float)
    d = d / np.linalg.norm(d)

    def rodrigues(axis, c, s_):
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + s_ * K + (1 - c) * K @ K
    v = np.cross(n, d)
    sv = np.linalg.norm(v)
    Rm = rodrigues(v / sv, float(n @ d), sv) if sv > 1e-9 else np.eye(3)
    a = np.radians(spin)
    return rodrigues(d, np.cos(a), np.sin(a)) @ Rm


def rail_y(x):
    return RAIL[0] + RAIL[1] * ((np.asarray(x, float) + 0.5 - 64) / 64) ** 2


def at(sx, sy, h):
    """The world point at height h that lands on (sx, sy)."""
    o, d = CAM.rays(np.array([sx], float), np.array([sy], float))
    return o[0] + d[0] * (h - o[0, 1]) / d[0, 1]


def mask_of(d, s=4):
    """A distance field on the picture's own samples (s x s a pixel) to pixel coverage >= 0.5."""
    return (d < 0).reshape(128, s, 128, s).mean(axis=(1, 3)) >= 0.5


def grid(s=4):
    c = (np.arange(128 * s) + 0.5) / s
    return np.meshgrid(c, c)


# ---- the night --------------------------------------------------------------------------

def night(pic, sign, sign_front, logo, ry):
    """The sky as levels on navy: flat behind the logo, deepening to a
    violet glow on the horizon, lifted in terraces round the sign and a
    little round the logo; the corners darker. Then the skyline."""
    sky = np.interp(Y1, *SKY_ROWS)
    sky -= 1.2 * np.clip(np.abs(X1 - 64) / 64, 0, 1) ** 2.2 * np.clip((Y1 - 36) / 26, 0, 1)
    ex, ey, rx, ry_, lift, edge = SIGN_AIR
    e = np.hypot((X1 - ex) / rx, (Y1 - ey) / ry_)
    sky += lift * np.clip((1 - e) / edge, 0, 1)
    sky = ak.terrace(np.clip(sky, 0, 3), 0.22)
    # between the letters the night is one flat level: no seam through a
    # counter or a gap
    span = np.zeros((128, 128), bool)
    front = ak.dilate(sign_front, 2, diag=True)
    for y in range(128):
        xs = np.nonzero(front[y])[0]
        if len(xs):
            span[y, xs.min():xs.max() + 1] = True
    sky = np.where(span, 2.0, sky)
    # a navy halo hugging the logo (not above it: no shelf under the frame)
    sky = np.maximum(sky, np.where(ak.dilate(logo, LOGO_HALO, diag=True) & (YY >= LOGO_Y), 2.0, 0.0))
    skyp = Y1 < ry + 1
    ak.by_level(pic, sky, SKY, skyp)

    def towers(spec):
        c = np.zeros((128, 128), bool)
        for x0, w, top, roof in spec:
            b = (XX >= x0) & (XX < x0 + w) & (YY >= top)
            if roof == "step":
                b |= (XX >= x0 + 2) & (XX < x0 + w - 2) & (YY >= top - 2)
            if roof == "spire":
                b |= (XX == x0 + w // 2) & (YY >= top - 5)
            c |= b
        return c & skyp
    far = towers(FAR_TOWERS)
    pic.put(far, "navy1")
    fslot = far & (XX % 2 == 1) & (YY % 3 == 1) & ak.erode(far, 1, diag=True)
    fh = ak.paint.ihash(XX * 57 + YY * 11, 4)
    pic.put(fslot & (fh < FAR_WINDOWS[0]), "violet")
    pic.put(fslot & (fh < FAR_WINDOWS[1]), "ivory")
    city = towers(TOWERS)
    pic.put(city, "black")
    pic.put(city & ~ak.shift(city, 0, 1) & ~ak.shift(city, 1, 0), "navy1")
    slot = city & (XX % 2 == 0) & (YY % 3 == 1) & ak.erode(city, 1, diag=True)
    h = ak.paint.ihash(XX * 131 + YY * 7, 3)
    for frac, col in zip(WINDOWS, ("violet", "ivory", "cream")):
        pic.put(slot & (h < frac), col)
    # a red light on each spire's tip
    for x0, w, top, roof in TOWERS:
        if roof == "spire":
            pic.px(x0 + w // 2, top - 5, "red")
    return skyp


# ---- the dice ---------------------------------------------------------------------------

def face_uv(c, n, u, v, size):
    """Per pixel, where its ray meets the face's plane, in face units (-0.5..0.5)."""
    o, d = CAM.rays(X1.reshape(-1).astype(np.float64), Y1.reshape(-1).astype(np.float64))
    dn = d @ n
    t = ((c - o) @ n) / np.where(np.abs(dn) < 1e-9, 1e-9, dn)
    q = o + d * t[:, None] - c
    return ((q @ u) / size).reshape(128, 128), ((q @ v) / size).reshape(128, 128)


def rounded(pts, r):
    """The pixels inside a convex polygon whose corners are rounded by r px:
    the polygon inset by r (each edge moved in, neighbours intersected),
    then grown by r."""
    P = np.asarray(pts, float)
    c = P.mean(axis=0)
    lines = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        t = (b - a) / np.linalg.norm(b - a)
        n = np.array([-t[1], t[0]])
        if n @ (c - a) < 0:
            n = -n
        lines.append((n, n @ a + r))                  # n . x = k: the edge moved in by r
    ins = []
    for i in range(len(lines)):
        (n0, k0), (n1, k1) = lines[i - 1], lines[i]
        A = np.array([n0, n1])
        ins.append(np.linalg.solve(A, [k0, k1]))
    return ak.polygon((X1, Y1), [tuple(p) for p in ins]) < r


def cube(d):
    """A die as an exact cube in perspective: its visible faces (quad, pixel
    mask, normal, axes, where each pixel lies on it), ranked by how lit they
    are; its silhouette with rounded corners; each silhouette pixel's face."""
    size = d["size"]
    pos = at(*d["scr"], d["h"])
    rot = facing(*d["show"])
    faces = {}
    corners = []
    for f, (nl, ul, vl) in FACES.items():
        n, u, v = (rot @ np.array(a, float) for a in (nl, ul, vl))
        c = pos + n * 0.5 * size
        if n @ (CAM.pos - c) <= 0:
            continue
        q = [CAM.project(c + (su * u + sv * v) * 0.5 * size) for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        uu, vv = face_uv(c, n, u, v, size)
        faces[f] = dict(q=q, n=n, u=u, v=v, c=c, sd=ak.polygon((X1, Y1), q), lit=float(n @ KEY), uu=uu, vv=vv)
        corners += q
    sil = rounded(ak.paint.hull(corners), d["rnd"])
    ids = list(faces)
    own = np.array(ids)[np.argmin(np.stack([faces[f]["sd"] for f in ids]), axis=0)]
    for f in ids:
        faces[f]["m"] = sil & (own == f)
    rank = sorted(ids, key=lambda f: -faces[f]["lit"])
    return dict(pos=pos, rot=rot, size=size, faces=faces, rank=rank, sil=sil, own=own)


def stamp_pips(pic, C, f, col, avoid=None):
    """A face's pips, one round template each, the size the perspective
    gives them (smaller if they would touch), a pixel of face kept round
    each; none on a face too thin for 2 x 2 dots."""
    F = C["faces"][f]
    inner = F["m"] & ~avoid if avoid is not None else F["m"]
    if inner.sum() < 9:
        return 0
    cs, ws, hs = [], [], []
    for a, b in ak.PIPS[f]:
        cc = F["c"] + (F["u"] * a * PIP_S + F["v"] * b * PIP_S) * C["size"]
        ring = np.array([CAM.project(cc + PIP_R * C["size"] * (np.cos(t) * F["u"] + np.sin(t) * F["v"]))
                         for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)])
        cs.append(CAM.project(cc))
        ws.append(np.ptp(ring[:, 0]))
        hs.append(np.ptp(ring[:, 1]))
    w, h = int(round(np.mean(ws))), int(round(np.mean(hs)))
    w, h = max(1, min(w, h + 1, 4)), max(1, min(h, w + 1, 4))
    ys, xs = np.nonzero(inner)
    mx, my = xs.mean(), ys.mean()
    while w >= 2 and h >= 2:
        tpl = ak.pip_template(w, h)
        placed = []
        for cx, cy in cs:
            x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
            for _ in range(4):
                m = ak.place(tpl, x0, y0)
                if m.any() and (ak.dilate(m, 1) & ~inner).sum() == 0:
                    placed.append(m)
                    break
                ex, ey = mx - (x0 + w / 2), my - (y0 + h / 2)
                x0 += int(np.sign(ex)) if abs(ex) > 0.5 else 0
                y0 += int(np.sign(ey)) if abs(ey) > 0.5 else 0
        clash = any((ak.dilate(a, 1) & b).any() for i, a in enumerate(placed) for b in placed[i + 1:])
        if len(placed) == len(cs) and not clash:
            for m in placed:
                if pic is not None:
                    pic.put(m, col)
            return w
        w, h = w - 1, h - 1
    return 0


def shared_edge(C, fa, fb):
    """The two corners faces fa and fb share, on the picture."""
    A, B = C["faces"][fa], C["faces"][fb]
    h = 0.5 * C["size"]
    ca = [A["c"] + (su * A["u"] + sv * A["v"]) * h for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    cb = [B["c"] + (su * B["u"] + sv * B["v"]) * h for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    common = [p for p in ca if min(np.linalg.norm(p - q) for q in cb) < 1e-6]
    return [np.array(CAM.project(p), float) for p in common]


def paint_die(pic, C):
    """A red die face by face, three flat values so the cube reads at a
    glance: the face the key lights most rose (falling to red in its far
    corner, one narrow seam), the next red, the one turned away wine. The
    edge between the two lit faces is the specular: one continuous cream run
    on the red face's lip, tapering to rose at both ends; the edge between
    the lit top and the dark face a red lip on the dark one. Pips round,
    cream on the lit faces, ivory on the dark one."""
    faces, rank = C["faces"], C["rank"]
    lvl = np.zeros((128, 128))
    for i, f in enumerate(rank):
        F = faces[f]
        if i == 0:
            e = KEY - (KEY @ F["n"]) * F["n"]
            e /= np.linalg.norm(e) or 1.0
            s = F["uu"] * (F["u"] @ e) + F["vv"] * (F["v"] @ e)            # toward the key, across the face
            lv = np.where(s > -TOP_FALL[0], 3.0, np.where(s > -TOP_FALL[1], 2.5, 2.0))
        else:
            lv = np.full((128, 128), 2.0 if i == 1 else 1.0)
        lvl[F["m"]] = lv[F["m"]]
    ak.by_level(pic, lvl, REDS, C["sil"], q=2)
    inner = ak.erode(C["sil"], 1)
    lines = np.zeros((128, 128), bool)
    # the lit edges: on the lip of the face below the top, one pixel per
    # column (or per row, for a steep edge), unbroken
    for fb, cols in ((rank[1], [("rose", 0.18), ("cream", 0.82), ("rose", 1.0)]),
                     (rank[2], [("red", 1.0)])):
        ends = shared_edge(C, rank[0], fb)
        if len(ends) != 2:
            continue
        a, b = ends
        Fb = faces[fb]
        seam = Fb["m"] & inner & ak.dilate(faces[rank[0]]["m"], 1)
        ys, xs = np.nonzero(seam)
        if not len(xs):
            continue
        t = (b - a) / np.linalg.norm(b - a)
        axis = 0 if abs(t[0]) >= abs(t[1]) else 1
        n = np.array([-t[1], t[0]])
        d = np.abs((xs + 0.5 - a[0]) * n[0] + (ys + 0.5 - a[1]) * n[1])     # off the edge's line
        line = np.zeros((128, 128), bool)
        key = xs if axis == 0 else ys
        for k_ in np.unique(key):
            sel = np.nonzero(key == k_)[0]
            j = sel[np.argmin(d[sel])]
            line[ys[j], xs[j]] = True
        lines |= line
        ly, lx = np.nonzero(line)
        u = ((lx + 0.5 - a[0]) * t[0] + (ly + 0.5 - a[1]) * t[1]) / np.linalg.norm(b - a)
        u = (u - u.min()) / max(u.max() - u.min(), 1e-6)
        lo = 0.0
        for name, hi in cols:
            sel = (u >= lo) & (u <= hi)
            pic.idx[ly[sel], lx[sel]] = pic.pal[name]
            lo = hi
    # pips by the face's light
    for i, f in enumerate(rank):
        stamp_pips(pic, C, f, "cream" if i < 2 else "ivory", avoid=ak.dilate(lines, 1, diag=True))
    return C["sil"]


def trails(pic, C, spec, ok):
    """Speed lines streaming back the way a die came: each starts a little
    behind its trailing edge and runs back up and to the right, bending
    level as it goes (the top of the throw's arc); parallel, tapering, cream
    to ivory to grey, a black edge under each. Returns their mask."""
    ys, xs = np.nonzero(C["sil"])
    bk = np.array(TRAIL_DIR, float)
    bk /= np.linalg.norm(bk)
    pp = np.array([-bk[1], bk[0]])                                       # across the path (down right)
    body = ak.dilate(C["sil"], 1)
    c0 = np.array([xs.mean() + 0.5, ys.mean() + 0.5])
    out = np.zeros((128, 128), bool)
    for off, ln, bend, r0 in spec:
        # from far behind, march toward the die to find its trailing edge
        start = c0 + pp * off + bk * 40
        hit = None
        for t in np.arange(0, 60, 0.25):
            q = start - bk * t
            x_, y_ = int(q[0]), int(q[1])
            if 0 <= x_ < 128 and 0 <= y_ < 128 and body[y_, x_]:
                hit = q
                break
        if hit is None:
            continue
        root = hit + bk * TRAIL_GAP
        th = np.radians(bend)
        rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        ctrl = root + bk * ln * 0.55
        end = ctrl + (rot @ bk) * ln * 0.5
        tmp = pic.copy()
        sm = ak.streak(tmp, tuple(root), tuple(ctrl), tuple(end), r0, 0.3, ok,
                       cols=(("cream", 0.3), ("ivory", 0.62), ("grey", 1.0)))
        sm &= ak.paint.nbrs(sm, diag=True)                               # no lone crumb where it is cut
        pic.idx[sm] = tmp.idx[sm]
        out |= sm
    under = ak.shift(out, 0, 1) & ~out & ok & (pic.where("felt1") | pic.where("felt2") | pic.where("red"))
    pic.put(under, "black")
    return out


# ---- the chips --------------------------------------------------------------------------

def stack_geom(st):
    """Each chip of the stack, bottom up: its middle, its face (the top
    ellipse) and its whole shape (face, edge band, bottom ellipse)."""
    X, Y = grid()
    out = []
    for j in range(st["n"]):
        cx = st["cx"] + st["nudge"][j]
        cy = st["base"] - st["ry"] - st["t"] * (j + 1)
        top = ak.ellipse((X, Y), cx, cy, st["rx"], st["ry"])
        bot = ak.ellipse((X, Y), cx, cy + st["t"], st["rx"], st["ry"])
        band = ak.box((X, Y), cx, cy + st["t"] / 2, st["rx"], st["t"] / 2)
        out.append(dict(cx=cx, cy=cy, face=mask_of(top), whole=mask_of(np.minimum(np.minimum(top, bot), band))))
    return out


def paint_stack(pic, st):
    """A stack of red clay chips, bottom up, each over the one below. Its
    edge band in three flat values by how it turns from the key (rose on the
    left, red, wine on the right), six cream edge spots round it, narrowed
    as they turn away (ivory in the shade), a black seam under each chip.
    The top chip's face: red, a wine inlay ring, six cream spots round its
    rim, the rim toward the key rose. Returns the stack's mask."""
    chips = stack_geom(st)
    allm = np.zeros((128, 128), bool)
    for j, c in enumerate(chips):
        m = c["whole"]
        sx = (X1 - c["cx"]) / st["rx"]
        side = m & ~c["face"]
        lv = np.where(sx < -0.55, 3, np.where(sx < 0.38, 2, 1))
        for k_, nm in enumerate(REDS):
            pic.put(side & (lv == k_), nm)
        for k_ in range(6):
            th = (st["turn"][j] + 60 * k_ + 90) % 360 - 180
            if abs(th) > 80:
                continue
            xa = c["cx"] + st["rx"] * np.sin(np.radians(max(th - st["spot"], -90)))
            xb = c["cx"] + st["rx"] * np.sin(np.radians(min(th + st["spot"], 90)))
            sp = side & (X1 >= xa) & (X1 < max(xb, xa + 1.0))
            pic.put(sp, "cream" if np.sin(np.radians(th)) < 0.38 else "ivory")
        pic.put(side & ~ak.shift(m, 0, -1), "black")                    # the seam under it
        pic.put(c["face"], "rose")                                       # its face: only a lit sliver shows past the next
        if j == st["n"] - 1:
            F = c["face"]
            u, v = (X1 - c["cx"]) / st["rx"], (Y1 - c["cy"]) / st["ry"]
            rad = np.hypot(u, v)
            ang = np.degrees(np.arctan2(v, u))
            pic.put(F, "red")
            pic.put(F & (rad > 0.74) & (u < -0.25) & (v < 0.35), "rose")
            spot = (((ang - st["turn"][j]) % 60) < 16) & (rad > 0.7)
            pic.put(F & spot, "cream")
            pic.put(F & (np.abs(rad - 0.5) < 0.1), "wine")
        allm |= m
    pic.put(ak.dilate(allm, 1) & ~allm, "black")
    return allm


# ---- the cards --------------------------------------------------------------------------

def card_geom(cx, cy, tilt, inset=0.0):
    """A card turned by atan(SLOPE) (tilt -1, 0, 1): a function from its own
    frame (pixels from its centre) to the picture, and its corners (`inset`
    pixels in). Its long edges step one pixel across every 1/SLOPE rows."""
    k = tilt * SLOPE
    hw, hh = CARD_W / 2 - inset, CARD_H / 2 - inset

    def pt(dx, dy):
        n = 1 / np.sqrt(1 + k * k)
        return cx + (dx - dy * k) * n, cy + (dy + dx * k) * n
    return pt, [pt(-hw, -hh), pt(hw, -hh), pt(hw, hh), pt(-hw, hh)]


def stamp(pic, rows, x, y, col, where=None):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != "." and 0 <= x + i < 128 and 0 <= y + j < 128 and (where is None or where[y + j, x + i]):
                pic.px(x + i, y + j, col)


def lattice(tilt, P=6):
    """A diamond lattice drawn in the card's own frame: on a card turned by
    atan(1/3) its diagonals land on the picture at slopes 2 and 1/2, so
    every line steps evenly (2-2-2)."""
    if tilt > 0:
        a = (XX - np.floor((YY + 1) / 2)) % P == 0
        b = (YY + np.floor((XX + 1) / 2)) % P == 0
    elif tilt < 0:
        a = (XX + np.floor((YY + 1) / 2)) % P == 0
        b = (YY - np.floor((XX + 1) / 2)) % P == 0
    else:
        a = (XX + YY) % P == 0
        b = (XX - YY) % P == 0
    return a | b


def card_masks():
    X, Y = grid()
    geo = []
    for rank, suit, (cx, cy), tilt in CARDS:
        pt, quad = card_geom(cx, cy, tilt)
        M = mask_of(ak.polygon((X, Y), quad))
        _, inner = card_geom(cx, cy, tilt, inset=2.5)
        geo.append((pt, M, mask_of(ak.polygon((X, Y), inner))))
    return geo


def paint_cards(pic, geo):
    """The fan: two backs behind (red, a cream border, a wine lattice), the
    ace of spades in front, upright: cream with an ivory sheen falling to
    its lower right (one clean diagonal seam), an ivory edge on its shadow
    sides. Outlined in black; the cards in front shade the ones behind."""
    import boxart as bx
    art = bx.card_art()
    drawn = np.zeros((128, 128), bool)
    for i, ((rank, suit, (cx, cy), tilt), (pt, M, IN)) in enumerate(zip(CARDS, geo)):
        pic.put(M, "cream")
        k_ = tilt * SLOPE
        n_ = 1 / np.sqrt(1 + k_ * k_)
        dx_, dy_ = X1 - cx, Y1 - cy
        u_, v_ = n_ * (dx_ + k_ * dy_), n_ * (-k_ * dx_ + dy_)
        if rank == "back":
            pic.put(IN, "red")
            pic.put(IN & lattice(tilt), "wine")
            pic.put(IN & ~ak.erode(IN, 1), "wine")
            rb = M & ~IN & ((u_ > CARD_W / 2 - 1.1) | (v_ > CARD_H / 2 - 1.1))
            pic.put(rb, "ivory")
        else:
            # the sheen: its lower right falls to ivory along one diagonal,
            # a 50% seam a pixel wide where they meet
            t = (u_ / CARD_W + v_ / CARD_H) + 0.5                              # 0 top-left .. 1 bottom-right
            pic.put(M & (t > SHEEN), "ivory")
            pic.put(M & (t > SHEEN - 0.035) & (t <= SHEEN) & ak.checker(), "ivory")
            rb = M & ((u_ > CARD_W / 2 - 1.1) | (v_ > CARD_H / 2 - 1.1))
            pic.put(rb, "ivory")
            col = "red" if suit in "dh" else "black"
            r_i, s_i = bx.RANKS.index(rank), bx.SUITS.index(suit)
            ix, iy = pt(-(CARD_W / 2 - 4.5), -(CARD_H / 2 - 5.0))
            g = art["ranks"][r_i]
            stamp(pic, g, int(round(ix - len(g[0]) / 2)), int(round(iy - 3.5)), col, M)
            sx2, sy2 = pt(-(CARD_W / 2 - 4.5), -(CARD_H / 2 - 12.5))
            stamp(pic, art["suits"][s_i], int(round(sx2 - 2.5)), int(round(sy2 - 3)), col, M)
            # the big spade, black, a grey gloss along its upper left
            # edges (no index at the bottom: the games' cards have none)
            gx_, gy_ = int(round(cx - len(ACE_SPADE[0]) / 2 + ACE_SPADE_AT[0])), int(round(cy - len(ACE_SPADE) / 2 + ACE_SPADE_AT[1]))
            stamp(pic, [r.replace("g", "#").replace("n", "#") for r in ACE_SPADE], gx_, gy_, col, M)
            stamp(pic, [r.replace("#", ".").replace("n", ".") for r in ACE_SPADE], gx_, gy_, "grey", M)
            stamp(pic, [r.replace("#", ".").replace("g", ".") for r in ACE_SPADE], gx_, gy_, "navy1", M)
        for _, M2, _ in geo[i + 1:]:                       # the cards in front shade this one
            cs = (ak.shift(M2, 2, 2) | ak.shift(M2, 1, 2)) & M & ~M2
            pic.put(cs & pic.where("cream"), "ivory")
            pic.put(cs & pic.where("red"), "wine")
        ring = ak.dilate(M, 1) & ~M
        pic.put(ring, "black")
        drawn |= M
    return drawn


# ---- the picture ------------------------------------------------------------------------

def draw():
    P = ak.Palette(PAL, ramps=[SKY, FELT, REDS, ["black", "grey", "ivory", "cream"], cl.GOLD_RAMP])
    pic = ak.Picture.blank(P, "black")
    ry = rail_y(XX)

    # ---- where the titles will be, to light the air round them
    m = ak.load_mask(NEON)
    N = ak.place(m, ak.centred_x(m), NEON_Y)
    sign = cl.channel(None, N)["all"]
    logo = cl.footprint(cl.centred(), LOGO_Y, "gold", depth=1)

    # ---- the night and the Strip
    skyp = night(pic, sign, N, logo, ry)

    # ---- the props' geometry
    dice = [cube(d) for d in DICE]
    geo = card_masks()
    cards_m = np.zeros((128, 128), bool)
    for _, M, _ in geo:
        cards_m |= M

    # ---- the table: a padded rail, the felt in a pool of light, the props' shadows
    felt = Y1 >= ry + 4
    rail = (Y1 >= ry) & ~felt
    pool = np.hypot((X1 - POOL[0]) / POOL[2], (Y1 - POOL[1]) / POOL[3])
    fl = 3.35 - 2.2 * pool ** 1.6
    fl = np.minimum(fl, 1.6 + (Y1 - ry - RAIL_SHADE) * 0.45)          # the rail's shade on the felt under it
    fl -= FRONT[2] * np.clip((Y1 - FRONT[0]) / FRONT[1], 0, 1)          # the front edge into the dark
    # the stack's shadow: down right of its foot
    st = STACK
    ox, oy, grow, depth = STACK_SHADOW
    e = np.hypot((X1 - st["cx"] - ox) / (st["rx"] + grow), (Y1 - st["base"] + st["ry"] - oy) / (st["ry"] + grow * 0.5))
    fl -= depth * np.clip((1.15 - e) / 0.3, 0, 1)
    # the cards' shadow: the fan's footprint, down right
    csh = (ak.shift(cards_m, 3, 2) | ak.shift(cards_m, 2, 3)) & ~cards_m
    fl -= 1.0 * csh
    # the dice's shadows: straight under them on the felt, down right, a
    # little softer for the higher one
    for C, d in zip(dice, DICE):
        gx, gy = CAM.project((C["pos"][0], 0.0, C["pos"][2]))
        xs_ = np.nonzero(C["sil"])[1]
        wd = xs_.max() - xs_.min()
        e = np.hypot((X1 - gx - d["sh"][0]) / (0.5 * wd), (Y1 - gy - d["sh"][1]) / (0.2 * wd))
        fl -= 1.4 * np.clip(1.3 - e, 0, 1) ** 0.7
    ak.by_level(pic, ak.terrace(np.clip(fl, 0, 3), 0.12), FELT, felt)
    # under the far rail: one solid row of shade
    pic.put(felt & (Y1 < ry + 5), "navy0")
    # the rail: padded wine leather, lit red along its top toward the key, a
    # black shadow line under it
    rr_ = Y1 - ry
    pic.put(rail, "wine")
    pic.put(rail & (rr_ >= 3), "black")
    pic.put(rail & (rr_ < 1) & (X1 > 6) & (X1 < 122), "red")

    # ---- the cards
    paint_cards(pic, geo)

    # ---- the chips; a pixel of felt shut in by them (or between them and
    # the card) is closed with the outline's black
    objs = paint_stack(pic, STACK)
    both = objs | cards_m
    shut = ak.erode(ak.dilate(both, 2, diag=True), 2, diag=True) & ~both & ak.dilate(objs, 3) & (YY > STACK["base"] - 30)
    pic.put(shut, "black")

    # ---- the dice in the air (the far one first): speed lines back along
    # their arc first, so each die covers their roots
    keep = np.zeros((128, 128), bool)
    dmask = np.zeros((128, 128), bool)
    for C, spec in zip(dice, TRAILS):
        ok = (YY >= 54) & (XX <= 125) & (YY <= 125) & ~ak.dilate(cards_m | objs | dmask, 1) & ~sign
        keep |= trails(pic, C, spec, ok)
    for C in dice:
        sil = paint_die(pic, C)
        pic.put(ak.dilate(sil, 1) & ~sil & ~dmask, "black")
        dmask |= sil
    keep &= ~dmask
    objs |= dmask

    # ---- the sign's light on the table: the rail's lip under it catches the
    # neon (the rainbow colour: it turns with the sign), one continuous run
    lip = rail & (rr_ < 1) & (np.abs(X1 - 64) < 24) & ~ak.dilate(objs | cards_m, 1)
    pic.put(lip, "rainbow")

    # ---- the stars: two twinkles in the top corners, clear of the titles
    for x_, y_, arms in STARS:
        ak.glint(pic, x_, y_, arms=arms, tip="grey" if max(arms) > 1 else None, core="cream")
        keep[y_ - 3:y_ + 4, x_ - 3:x_ + 4] = True

    # ---- lone pixels in the props and the table (the glints and the lines kept)
    ak.despeckle(pic, 5, keep=keep, within=(YY >= 50) & ~ak.dilate(objs | cards_m, 1), passes=2)

    # ---- the sign: channel letters; a pixel of night shut in by them is
    # closed with their black
    signm = cl.channel(pic, N)["all"]
    near = ak.dilate(signm, 2) & ~signm
    for _ in range(2):
        cnt = sum(ak.shift(signm, dx, dy).astype(int) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
        shut = near & (cnt >= 5)
        pic.put(shut, "black")
        signm |= shut

    # ---- the logo
    cl.dress(pic, cl.centred(), LOGO_Y, "gold", depth=1)

    # ---- the frame: the outer two pixels all round step down (the outermost
    # three times, the next twice), so the menu's border frames a dark edge
    edge2 = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))
    for steps, where in ((3, edge2 == 0), (2, edge2 == 1)):
        for _ in range(steps):
            idx = pic.idx.copy()
            for a_, b_ in DARKER.items():
                pic.put(where & (idx == P[a_]), b_)
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), TOOLS / "sdcard" / "art" / "cover.png"))
