"""The scene the menu's generic screens share (docs/cover-art.md): the night,
the burst of rays out of the console's card slot, the slot's light, sparks
and stars. The default cover (cover.py) raises the SD card out of the slot;
the no-picture screen (game.py) and the default folder (folder.py) raise
their own heroes into the same light, so the defaults every cart falls back
on look like one console's own.

    import sdscene as S
    P = ak.Palette({**S.PAL, ...more own colours...}, ramps=S.RAMPS + [...])
    pic = ak.Picture.blank(P, "navy0")
    keep = np.zeros((128, 128), bool)          # deliberate lone pixels
    body = ...the hero's mask on the picture...
    S.stage(pic, body, keep)                   # night, rays, console, slot, its light up to the hero
    ...paint the hero...
    S.finish(pic, body, keep)                  # sparks, motes, stars, clean-up
    ...the title...
    S.frame(pic)                               # the outer pixels step down to the dark

    S.card() / S.paint_card(pic, c, keep)      # the SD card (the cover's hero)
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent             # tools/art/menu
TOOLS = HERE.parents[1]                                     # the repository's tools/
for p in (TOOLS, TOOLS / "art"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

YY, XX = np.mgrid[0:128, 0:128]
X1, Y1 = XX + 0.5, YY + 0.5

PAL = {
    "navy0": "#0A0C26", "navy1": "#1C1E52", "violet": "#3A2A8A",     # the night
    "azure": "#3A86DA", "ice": "#92E2F2",                             # the slot's light
    "steel": "#A8B4D6",                                               # the card's metal
    "wine": "#640E22", "rose": "#F2644A",                             # the label
}
SKY = ["black", "navy0", "navy1", "violet", "azure", "ice", "cream"]
REDS = ["black", "wine", "red", "rose", "cream"]
METAL = ["black", "navy1", "grey", "steel", "cream"]
RAMPS = [SKY, REDS, METAL]
DARKER = {"cream": "ice", "ice": "azure", "azure": "violet", "violet": "navy1", "navy1": "navy0", "navy0": "black",
          "steel": "grey", "grey": "navy1", "rose": "red", "red": "wine", "wine": "black", "rainbow": "violet"}

# ---- the layout -------------------------------------------------------------------------

# the card, drawn upright in its own pixels, then leaned by two integer shears
CARD_W, CARD_H = 41, 54
CARD_TOP, CARD_X = 37, 66                     # its face's top row and middle on the picture
CARD_CUT = 10                                 # the cut corner (a 45-degree line on the picture), px
LEAN = 1 / 8                                  # the lean: one pixel in eight (7 degrees), top to the right
THICK = [(-1, 0), (-2, 1), (-3, 1), (-4, 2)]  # its thickness on the picture: the left side and the foot show
LABEL = (4, 15, 38, 50)                       # the label on the face (local x0, y0, x1, y1, exclusive)
MARK_AT = (5, 5)                              # the SD mark on the grip (local)
SHEEN = ((-16, -20), 38.0, 62.0)              # the label's light: centre (from its top-left), rose within, wine beyond
GLOSS = (31, 3, 36)                           # the gloss band on the black: where it starts (x + y from the
                                              # card's corner), its width, and a thin second one
SLOT_Y = 107                                  # the slot's opening (top row of three)
FAR_Y = SLOT_Y - 5                            # the console's far edge
FRONT_Y = 121                                 # its front edge
SLOT_X = (44, 85)                             # its ends (exclusive)
SRC = (64.0, SLOT_Y + 8.0)                    # where the fan of light springs from (under the slot)
# the rays, mirrored left and right: their sides as slopes (px across per px up, from SRC: whole
# ratios, so every edge steps evenly), then where azure ends, violet, navy1 (px from SRC)
RAYS = [((3, 4), (1, 1), 54, 72, 88), ((4, 3), (2, 1), 56, 84, 102), ((5, 2), (7, 2), 52, 78, 94),
        ((5, 1), (8, 1), 48, 70, 84)]
RAY_SEAM = 2.0                                # the rays' steps: a seam this many pixels deep (25/50/75%)
CALM_Y = 42                                   # nothing bright above this row: the title's band
SHEET_ARCH = (12, 7, 20)                      # the sheet's azure: how high it reaches in the middle, how much
                                              # lower 20 px out (it is brightest over the slot's middle)
FLOOR_RAYS = (2.2, 22, 46)                    # the rays' reflection in the console's gloss: squash, violet to, navy1 to
# the splash of light out of the slot's ends: root, bend, head (x, y from the slot's top row);
# radius at the root, at the head
SPLASH = [((45, -3), (31, -19), (16, -34), 0.3, 1.3), ((44, -2), (26, -10), (12, -16), 0.3, 1.1),
          ((84, -3), (98, -19), (113, -34), 0.3, 1.3), ((85, -2), (103, -10), (117, -16), 0.3, 1.1)]
# sparks out of the slot's ends: (end -1/1, angle out from upright (deg), speed (px/s), time (s))
SPARKS = [(-1, 48, 62, 0.34), (-1, 66, 56, 0.3), (1, 50, 62, 0.33), (1, 64, 58, 0.3)]
GRAVITY = 80.0
SPARK_TAIL = 4.0
STARS = [(11, 10, 2), (117, 13, 1), (4, 38, 0), (123, 35, 0), (8, 52, 0), (119, 56, 0)]
MOTES = [(35, 66), (95, 76), (30, 84), (100, 62), (38, 48), (92, 44)]


# ---- the card's print, drawn on its own pixels -----------------------------------------

GAMEPAD = [
    ".....####################.....",
    "...########################...",
    "..##########################..",
    ".############################.",
    "##############################",
    "##############################",
    "##############################",
    "##############################",
    "##########..........##########",
    ".########............########.",
    "..######..............######..",
    "...####................####...",
]
DPAD = [(x, y) for x in (5, 6) for y in range(2, 8)] + [(x, y) for x in (3, 4, 7, 8) for y in (4, 5)]  # wine
BUTTONS = [(21, 4), (20, 5), (21, 5), (22, 5), (21, 6), (24, 2), (23, 3), (24, 3), (25, 3), (24, 4)]  # red
PILLS = [(12, 5), (13, 5), (16, 5), (17, 5)]                                         # grey
PAD_SEAM = 10                                 # the lean's column step falls before this column of the pad
SD_MARK = ["###.###.", "#...#..#", "###.#..#", "..#.#..#", "###.###."]


# ---- helpers ----------------------------------------------------------------------------

def rows_mask(rows):
    return np.array([[c == "#" for c in r] for r in rows])


def ramp(v, a, w=2.0):
    """0 below a, 1 above a + w: a short seam."""
    return np.clip((v - a) / w, 0, 1)


class Lean:
    """A flat drawing's own pixels onto the picture: a row shear (up is
    right) then a column shear (right is down), each by whole pixels, so
    every pixel of the upright drawing lands on exactly one of the
    picture's: nothing is doubled or lost, and straight edges step evenly
    (one in s). The steps are placed so a new row band starts at local row
    `row0` and a new column band at local column `col0` (in the band
    starting at row0): between the drawing's parts, not through them. The
    drawing's top row lands on `top`, its middle on `mid_x`."""

    def __init__(self, w, h, top, mid_x, s, row0, col0):
        i, j = np.meshgrid(np.arange(w), np.arange(h))
        ic, jc = (w - 1) / 2, (h - 1) / 2
        p0 = 1.0 - (jc - (row0 - 1)) * s                  # value(row0 - 1) whole: the band changes there
        x1 = i + np.floor((jc - j) * s + p0 + 1e-9).astype(int)
        shift0 = int(np.floor((jc - row0) * s + p0 + 1e-9))
        p1 = -((col0 + shift0) - ic) * s                  # value(col0) whole
        y1 = j + np.floor((x1 - ic) * s + p1 + 1e-9).astype(int)
        self.x = x1 - int(round((x1.min() + x1.max()) / 2 - mid_x))
        self.y = y1 - (y1.min() - top)
        self.ok = (self.x >= 0) & (self.x < 128) & (self.y >= 0) & (self.y < 128)
        self.shape = (h, w)

    def mask(self, local):
        out = np.zeros((128, 128), bool)
        sel = local & self.ok
        out[self.y[sel], self.x[sel]] = True
        return out

    def paint(self, pic, local_names):
        """local_names: an object array of colour names (0/None: leave)."""
        for name in {n for n in local_names.ravel() if n}:
            pic.put(self.mask(local_names == name), name)

    def at(self, i, j):
        return int(self.x[j, i]), int(self.y[j, i])

    def blank(self):
        return np.zeros(self.shape, object)


def rays_in(dx, dy):
    """For each ray (both sides), the pixels inside it, given each pixel's
    offset from the fan's source (dx across, dy along, dy > 0 toward the rays)."""
    out = []
    ax = np.abs(dx)
    for ray in RAYS:
        (p0, q0), (p1, q1) = ray[0], ray[1]
        inw = (dy > 0) & (ax * q0 > dy * p0) & (ax * q1 < dy * p1)
        out.append((inw, ray))
    return out


# ---- the stage ----------------------------------------------------------------------------

def stage(pic, body, keep, sheet_top=None):
    """The night, the fan of rays, the console's top with its slot, the
    sheet of light from the slot up to the hero (`body`, its mask: up to its
    lowest pixels, and no higher than `sheet_top` when given, for a hero
    that overhangs) and the splash of light out of the slot's ends (behind
    the hero)."""
    # ---- the night: navy0 falling to black in the corners; the fan of rays
    # from the slot, azure near it, then violet, then navy1 (flat bands, hard
    # steps, every side a whole-ratio slope); nothing bright near the title
    vig = np.hypot((X1 - 64) / 70, (Y1 - 62) / 76)
    lv = 1.0 - (vig > 0.93)
    r = np.hypot(X1 - SRC[0], Y1 - SRC[1])
    for inw, (_, _, ra, rv, rn) in rays_in(X1 - SRC[0], SRC[1] - Y1):
        rl = 4.0 - ramp(r, ra, RAY_SEAM) - ramp(r, rv, RAY_SEAM) - 2.0 * (r > rn)
        lv = np.maximum(lv, np.where(inw, rl, -9))
    lv = np.minimum(lv, np.where(YY < CALM_Y, 1.0, 9.0))
    ak.by_level(pic, np.clip(lv, 0, 4), SKY, YY < FAR_Y)

    # ---- the console's top: dark gloss, a pool of light round the slot
    topm = (YY >= FAR_Y) & (YY < FRONT_Y)
    pool = np.hypot((X1 - 64) / 46, (Y1 - (SLOT_Y + 3)) / 10)
    pl = 1.0 + (1.0 - ramp(pool, 0.86, 0.05)) + (1.0 - ramp(pool, 0.56, 0.05))
    pl -= ramp(np.hypot((X1 - 64) / 64, (Y1 - 104) / 20), 0.95, 0.1)
    # the fan's reflection in the gloss: dim wedges spreading toward us from the slot
    fr = np.hypot(X1 - 64, (Y1 - SLOT_Y) * FLOOR_RAYS[0])
    for inw, _ in rays_in(X1 - 64, (Y1 - SLOT_Y) * FLOOR_RAYS[0]):
        inw &= Y1 > SLOT_Y
        pl = np.maximum(pl, np.where(inw, 3.0 - (fr > FLOOR_RAYS[1]) - (fr > FLOOR_RAYS[2]), -9))
    ak.by_level(pic, ak.terrace(np.clip(pl, 0, 4), 0.3), SKY, topm)
    far = YY == FAR_Y
    fx = np.abs(X1 - 64)
    pic.put(far & (fx < 62), "navy1")
    pic.put(far & (fx < 46), "violet")
    pic.put(far & (fx < 30), "azure")
    front = YY == FRONT_Y
    pic.put(front & (fx < 56), "navy1")
    pic.put(front & (fx < 34), "violet")
    pic.put(YY > FRONT_Y, "black")
    # the recess round the slot: rows of (x0, x1)
    rec = np.zeros((128, 128), bool)
    for k, y in enumerate(range(SLOT_Y - 3, SLOT_Y + 6)):
        rec[y, SLOT_X[0] - 4 - k // 2:SLOT_X[1] + 4 + k // 2] = True
    pic.put(rec, "black")
    pic.put(rec & ~ak.shift(rec, 0, -1), "azure")                        # its near lip
    # the slot: the hot opening
    slot = (XX >= SLOT_X[0]) & (XX < SLOT_X[1]) & (YY >= SLOT_Y) & (YY < SLOT_Y + 3)
    pic.put(slot, "azure")
    pic.put(slot & (YY == SLOT_Y), "ice")
    pic.put(slot & (YY == SLOT_Y + 1) & (XX >= SLOT_X[0] + 3) & (XX < SLOT_X[1] - 3), "cream")

    # ---- the sheet of light from the slot up to the hero's foot
    half = (SLOT_X[1] - SLOT_X[0]) / 2 + (SLOT_Y - Y1) * 0.12
    under = np.flipud(np.cumsum(np.flipud(body), axis=0)) == 0    # nothing of the hero at or below
    below = under & body.any(axis=0)[None, :]                    # under the hero, in its columns
    if sheet_top is not None:                                    # only under the hero's lowest part
        low = np.where(body.any(axis=0), 127 - np.argmax(np.flipud(body), axis=0), -1)
        below &= (YY >= sheet_top) & (low >= sheet_top)[None, :]
    sheet = (np.abs(X1 - (SLOT_X[0] + SLOT_X[1]) / 2) < half) & (YY < SLOT_Y) & below & ~body
    pic.put(sheet, "violet")
    arch = SLOT_Y - SHEET_ARCH[0] + SHEET_ARCH[1] * ((X1 - 64.5) / SHEET_ARCH[2]) ** 2
    pic.put(sheet & (Y1 > arch), "azure")

    # ---- the splash of light out of the slot's ends, behind the hero
    ok_sw = ~ak.dilate(body, 1) & (YY < FAR_Y)
    for root, ctrl, head, r0, r1 in SPLASH:
        root, ctrl, head = [(x, SLOT_Y + y) for x, y in (root, ctrl, head)]
        m = ak.streak(pic, root, ctrl, head, r0, r1, ok=ok_sw,
                      cols=(("azure", 0.4), ("ice", 0.8), ("cream", 1.0)))
        keep |= m


def finish(pic, body, keep):
    """Sparks out of the slot's ends, motes rising, stars, and the lone
    pixels cleaned (the deliberate ones in `keep` kept)."""
    for end, ang_, spd, t in SPARKS:
        x0 = SLOT_X[0] + 1 if end < 0 else SLOT_X[1] - 2
        y0 = SLOT_Y - 1
        vx, vy = end * spd * np.sin(np.radians(ang_)), -spd * np.cos(np.radians(ang_))
        hx, hy = x0 + vx * t, y0 + vy * t + 0.5 * GRAVITY * t * t
        dx_, dy_ = vx, vy + GRAVITY * t
        n_ = np.hypot(dx_, dy_)
        pts = [(hx - dx_ / n_ * SPARK_TAIL, hy - dy_ / n_ * SPARK_TAIL), (hx, hy)]
        for x, y in ak.ink(pic, pts, None, where=~ak.dilate(body, 1),
                           colours=[("azure", 0.4), ("ice", 0.75), ("cream", 1.0)]):
            if 0 <= x < 128 and 0 <= y < 128:
                keep[y, x] = True
    for x, y in MOTES:
        if body[y, x] or body[min(127, y + 1), x]:
            continue
        pic.px(x, y, "cream")
        pic.px(x, y + 1, "ice")
        keep[y:y + 2, x] = True
    for x, y, s_ in STARS:
        if s_ == 0:
            pic.px(x, y, "grey")
        else:
            ak.glint(pic, x, y, size=s_, tip="grey" if s_ > 1 else None)
        keep[max(0, y - 2):y + 3, max(0, x - 2):x + 3] = True
    ak.despeckle(pic, 4, keep=keep, within=~ak.dilate(body, 1), passes=2)


def frame(pic, darker=None):
    """The outer two pixels step down into the dark (the outermost twice),
    so the menu's border frames a dark edge."""
    darker = darker or DARKER
    edge2 = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))
    for steps, where in ((2, edge2 == 0), (1, edge2 == 1)):
        for _ in range(steps):
            idx = pic.idx.copy()
            for a_, b_ in darker.items():
                pic.put(where & (idx == pic.pal[a_]), b_)


def calm_title(pic, M, body, keep, pad=2):
    """Calm flat navy round a title's footprint `M`."""
    pic.put(ak.dilate(M, pad, diag=True) & ~body & ~keep, "navy0")


# ---- the SD card (the cover's hero) --------------------------------------------------

def card():
    """The card's shape: its Lean, face, body (with its thickness), edges."""
    G = rows_mask(GAMEPAD)
    gx0 = (LABEL[0] + LABEL[2] - G.shape[1]) // 2
    gy0 = (LABEL[1] + LABEL[3] - G.shape[0]) // 2 + 1
    L = Lean(CARD_W, CARD_H, CARD_TOP, CARD_X, LEAN, gy0, gx0 + PAD_SEAM)
    F = L.mask(np.ones((CARD_H, CARD_W), bool))
    tr_x, tr_y = L.at(CARD_W - 1, 0)
    F &= ~((XX - tr_x) - (YY - tr_y) > -CARD_CUT)            # the cut corner: a clean 45-degree line
    ys, xs = np.nonzero(F)
    body = F.copy()
    for dx, dy in THICK:
        body |= ak.shift(F, dx, dy)

    # the face's edges, from its own rows and columns (so a step in one edge
    # never takes another's colour), the cut corner's diagonal from the picture
    def local(sel):
        a = np.zeros((CARD_H, CARD_W), bool)
        a[sel] = True
        return L.mask(a) & F
    cutd = F & ~ak.shift(F, -1, 1) & ((XX - tr_x) - (YY - tr_y) > -CARD_CUT - 2)
    E = dict(top=local(np.s_[0, :]) & ~cutd, bottom=local(np.s_[CARD_H - 1, :]), left=local(np.s_[:, 0]),
             right=local(np.s_[:, CARD_W - 1]) & ~cutd, cut=cutd)
    foot = body & ~F & (ak.shift(F, 0, 1) | ak.shift(F, 0, 2) | ak.shift(F, 0, 3))
    lside = body & ~F & ~foot
    return dict(G=G, gx0=gx0, gy0=gy0, L=L, F=F, xs=xs, ys=ys, body=body, local=local, E=E, foot=foot,
                lside=lside)


def paint_card(pic, c, keep, label=None):
    """The card: black gloss, its lit side with a lock slider, its bevels,
    a gloss band, the red label (lit from the key's side) and its print: the
    gamepad, or label(pic, c) to print something else on the label, and the
    SD mark; the key's glint on its corner."""
    L, F, E, body, foot, lside, local = c["L"], c["F"], c["E"], c["body"], c["foot"], c["lside"], c["local"]
    xs, ys, G, gx0, gy0 = c["xs"], c["ys"], c["G"], c["gx0"], c["gy0"]
    pic.put(ak.dilate(body, 1) & ~body, "black")
    pic.put(body, "black")
    # its left side: the key lights its top, the slot its foot; a lock slider on it.
    # The face's left bevel a step lighter than the side all the way down, so the corner reads
    t0 = ys.min()
    for (a, b), side_c, bev_c in (((0, 15), "steel", "cream"), ((15, 30), "grey", "steel"),
                                  ((30, 44), "navy1", "grey"), ((44, 99), "violet", "azure")):
        band = (YY >= t0 + a) & (YY < t0 + b)
        pic.put(lside & band, side_c)
        pic.put(E["left"] & band, bev_c)
    sv = lside & ak.shift(lside, 1, 0) & ak.shift(lside, -1, 0)
    groove = sv & (YY > t0 + 8) & (YY < t0 + 21)
    pic.put(groove, "black")
    pic.put(groove & (YY > t0 + 10) & (YY < t0 + 14), "cream")
    pic.put(foot, "ice")
    # the face's bevels: grey along the top (steel near the key's corner), the
    # light behind and below grazing the far edge, the slot's light along the foot
    pic.put(E["top"], "grey")
    pic.put(E["top"] & (XX < xs.min() + 18), "steel")
    pic.put(E["right"], "navy1")
    pic.put(E["right"] & (YY > ys.min() + 14), "violet")
    pic.put(E["right"] & (YY > ys.max() - 14), "azure")
    pic.put(E["bottom"], "azure")
    pic.put(E["cut"], "grey")
    # the gloss: a band of the night's light across the black, toward the key
    gs = (XX + YY) - (xs.min() + ys.min())
    grip = local(np.s_[1:LABEL[1] - 1, 1:CARD_W - 1]) & ~E["cut"]
    pic.put(grip & (gs >= GLOSS[0]) & (gs < GLOSS[0] + GLOSS[1]), "navy1")
    pic.put(grip & (gs >= GLOSS[2]) & (gs < GLOSS[2] + 1), "navy1")
    # the label: red, lit from the key's side, falling to wine in the far corner
    lab = np.zeros((CARD_H, CARD_W), bool)
    lab[LABEL[1]:LABEL[3], LABEL[0]:LABEL[2]] = True
    LB = L.mask(lab)
    lx0, ly0 = L.at(LABEL[0], LABEL[1])
    d0 = np.hypot(X1 - (lx0 + SHEEN[0][0]), Y1 - (ly0 + SHEEN[0][1]))
    ll = 2 + (d0 < SHEEN[1]).astype(int) - (d0 > SHEEN[2]).astype(int)
    ak.put_levels(pic, LB, ll, REDS)
    c["LB"] = LB
    if label is not None:
        label(pic, c)
    else:
        # the gamepad printed on it
        gp = L.blank()
        sub = gp[gy0:gy0 + G.shape[0], gx0:gx0 + G.shape[1]]
        sub[G] = "cream"
        lowr = G & ~np.vstack([G[1:], np.zeros((1, G.shape[1]), bool)])
        sub[lowr] = "steel"
        for pts, col in ((DPAD, "wine"), (BUTTONS, "red"), (PILLS, "grey")):
            for i, j in pts:
                sub[j, i] = col
        GP = L.mask(gp != 0)
        pic.put(ak.shift(GP, 1, 1) & ~GP & LB, "wine")
        L.paint(pic, gp)
    # the mark on the grip, silver print
    mk = L.blank()
    S = rows_mask(SD_MARK)
    mx, my = MARK_AT
    mk[my:my + S.shape[0], mx:mx + S.shape[1]][S] = "steel"
    mk[my, mx:mx + S.shape[1]][S[0]] = "cream"
    MK = L.mask(mk != 0)
    pic.put(ak.shift(MK, 1, 1) & ~MK & F & ~E["top"] & ak.outside_of(MK), "navy1")
    L.paint(pic, mk)
    # the key's glint on the corner nearest it
    gx_, gy_ = L.at(0, 0)
    ak.glint(pic, gx_ + 1, gy_ + 1, arms=(2, 3, 2, 3), tip="steel")
    keep[gy_ - 3:gy_ + 5, gx_ - 3:gx_ + 5] = True
