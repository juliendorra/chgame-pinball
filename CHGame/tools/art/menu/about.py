"""spec/assets/about-default.png: the visual menu's ABOUT page, how the menu
works (docs/visual-menu.md; B or SELECT on the card's cover shows it).
tools/menuart.py draws it from draw(); edit this, not the PNG
(docs/cover-art.md).

THE BRIEF
  Message: here's how to drive this thing. Clear, friendly, premium: the
  casino console's own face, its controls lit like a slot machine's at
  night, every instruction printed beside the control it belongs to, every
  word legible at 1x.

  The key map (docs/visual-menu.md), said briefly, a bold keyword and a
  thin line to finish it:
    UP / DOWN     GAMES          IN A FOLDER
    LEFT / RIGHT  FOLDERS        SIDE BY SIDE
    A             PLAY           OR OPEN
    B             BACK           ONE STEP
    SELECT        TO THE COVER   THEN THIS PAGE   (B on the cover too)
    START         HOLD 3 SECONDS IN A GAME: BACK HERE

  Composition (a thumbnail in words): a product shot of the console's face,
  straight on, filling the frame, so the picture is the device in your
  hands.
  - Top: the bottom of its screen, a black glass with rounded corners sunk
    in the face, showing the title, the first read. The bezel's slope into
    the glass catches the key along the bottom and right (a steel L, kept
    whole round the title), falls into shade on the left and fades into the
    frame at the top.
  - Under it, four bands down the face, each control on the left and its
    words beside it:
      the D-pad (34 px, the focal point) with GAMES / FOLDERS to its right,
      each keyed by a pair of glowing arrows like the D-pad's own (two
      separate arrows, each in its own black cut, their right edges lined
      up);
      A and B side by side with PLAY and BACK (7 px clear of the frame);
      SELECT, then START, rubber pills with their names moulded on them.
  - Top right, under the bezel's corner: the speaker, four slots slanting
    up to the right in even 3-row steps, each a black cut with its far wall
    lit indigo: the one wordless detail that says "device".
  - The D-pad: violet plastic sitting in a round recess centred on it (the
    recess's floor a step down in shade, its wall black on the near side
    and lit steel on the far side, a clear ring of floor all round), so the
    cross reads light on dark, the brightest form under the title. Each arm
    is a rocker: the near ones (up, left) steel, the far ones (right, down)
    indigo; each edge that faces the key a step lighter (cream on the near
    arms' tops) and each edge turning away a step darker; a dished hub (its
    near wall in shade, its far wall lit); cream glints on the two corners
    nearest the key; four arrow windows lit from under the plastic in the
    rainbow colour (they turn through the colour wheel on a Rainbow
    bootloader, with the arrow pairs by the words; magenta on a Static
    one), each with a black cut round it and its lower lip lit. Navy and
    ink only on its front walls.
  - A and B: slot-machine buttons, a 1-px chrome bezel in clean 8-connected
    steps (steel where it faces the key, indigo, navy round to the far
    side), a black gap, a glossy dome (red A, jade B; A's thin rose arc on
    its rim up toward the key with a cream heart, B's a short cream
    specular, both clear of the letter; the shade down and right), the
    letter moulded in cream.
  - SELECT and START: moulded rubber pills, indigo on top and navy below,
    the near end's rim steel with a cream specular on its shoulder, the rim
    fading toward the far end, the far end and the underside ink.
  - Every control stands proud of the face on a short front wall, in a
    black seam, and casts a clean shadow, its own silhouette moved down and
    right, one step darker than what it falls on: the D-pad's onto the
    recess's floor.
  - Light: the house key from the top left. The face is violet lacquer,
    navy, with an indigo heart round the recess on the key's side, falling
    to ink in the bottom-right corner (an ellipse leaning down the light's
    way, its seam narrow and dithered, stepping without a dither behind the
    words), and black only in a 4-px dithered vignette at the frame, in the
    seams and in the shadows.
  - The words: the keywords cream (Bitrimus), the lines under them steel
    (Thintel), both with a black drop shadow: two levels in weight and in
    value, so the D-pad and the keywords lead. The eye runs title, D-pad,
    then the keywords down the page.
  - Title: HOW IT WORKS in Round9x13 (word spaces narrowed by a pixel, so
    the glass frames it evenly), chrome gold in bands (gold2 sky, gold1, a
    gold0 horizon, a gold2 reflection under it, gold1 ground), a cream
    bevel on its outer contour's top and left edges and a gold0 one on its
    bottoms (no dark right edge, so the stems stay gold), a 3 px
    red-and-wine extrusion, black outline and shadow on the black glass
    (no glow: the word gaps and pockets stay clean black), two cream glints
    clear of the counters (one on H's left stem, one on the O of WORKS).

PALETTE (11 own + cream, grey, black, red)
  ink navy indigo steel   the face, the D-pad, the bezels and pills: one
                          ramp from black to cream, hue-shifted (blue-black
                          shadows, a violet indigo, a lavender steel), the
                          violet night of the family
  wine rose               A's shade and highlight (A itself is red); wine
                          is also the title's depth under its red lip
  jade0 jade1             B (its specular cream)
  gold0 gold1 gold2       the title's own: nothing else uses them
  cream                   the keywords, glints, letters, chrome's hot spots
  rainbow (#FF00FF)       the D-pad's lit arrows and the arrow pairs by the
                          words, on purpose: the LEDs

FONTS
  Title: Round9x13 by heraldod (OFL; heraldod.itch.io/bitmap-fonts), at its
  own size (the text art below keeps its header).
  Keywords: Bitrimus by ggbot (CC0; ggbot.itch.io/bitrimus-font),
  tools/art/fonts/about-bitrimus.json, the family's key-hint face (A: PLAY
  on the NO PICTURE and INSTALLED screens).
  The lines under them: Thintel by Skeddles (100% free;
  dafont.com/thintel.font), tools/art/fonts/about-thintel.json.
  The buttons' letters and the pills' names are drawn here (5 x 7 bold and
  3 x 5).
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parents[1]
sys.path.insert(0, str(TOOLS))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

FONTS = TOOLS / "art" / "fonts"
THIN = FONTS / "about-thintel.json"
BOLD = FONTS / "about-bitrimus.json"
OUT = TOOLS.parent / "spec" / "assets" / "about-default.png"

TITLE_ART = """
// title: HOW IT WORKS
// font: Round9x13 (itch/Round9x13)
// author: heraldod
// terms: ofl
// source: https://heraldod.itch.io/bitmap-fonts
// set at the font's own size by tools/artkit/fontscout.py
###...###..#######..###...###......#########.#########......###...###..#######..########..###...###..########
###...###.#########.###...###......#########.#########......###...###.#########.#########.###...###.#########
###...###.#########.###...###......#########.#########......###...###.#########.#########.###...###.#########
###...###.###...###.###...###.........###.......###.........###...###.###...###.###...###.###..####.###......
###...###.###...###.###...###.........###.......###.........###...###.###...###.###...###.###.#####.###......
#########.###...###.###...###.........###.......###.........###...###.###...###.#########.########..########.
#########.###...###.###...###.........###.......###.........###...###.###...###.#########.#######...#########
#########.###...###.###.#.###.........###.......###.........###.#.###.###...###.########..########...########
###...###.###...###.#########.........###.......###.........#########.###...###.###.#####.###.#####.......###
###...###.###...###.#########.........###.......###.........#########.###...###.###..####.###..####.......###
###...###.#########.#########......#########....###.........#########.#########.###...###.###...###.#########
###...###.#########.####.####......#########....###.........####.####.#########.###...###.###...###.#########
###...###..#######..###...###......#########....###.........###...###..#######..###...###.###...###.########.
"""

# ---- the layout (pixels) -------------------------------------------------------------

TITLE_Y = 3
TITLE_X = 9                                     # the face's left edge (the extrusion runs 3 px right of it)
WORD_GAP = 5                                    # the title's word spaces (the font's are 6)
GLASS = (64, 21, 60, 7)                         # the screen's glass: centre x, bottom edge, half width, corners
TITLE_GLINTS = [(1, 1, (2, 1, 2, 2)), (69, 1, (1, 1, 1, 1))]   # from the title's corner: x, y, arms (l, r, u, d)
TITLE_ROWS = ["gold2"] * 4 + ["gold1"] * 2 + ["gold0"] + ["gold2"] * 2 + ["gold1"] * 4   # sky, horizon, ground
DPAD = (24, 46, 34, 12)                         # centre x, y, span, arm width
WELL = (24, 47.5, 21.6)                         # the round recess round the D-pad: centre, radius
BTN_R = 8.2                                     # the buttons' caps
BUTTONS = [(12.5, 78.5, "A"), (72.5, 78.5, "B")]
PILL_W, PILL_H = 29, 9
PILLS = [(4, 93, "SELECT"), (4, 113, "START")]  # top-left of each pill
GLYPHS = [("updown", 53, 27), ("leftright", 49, 49)]
LABELS = [("GAMES", 61, 28, "bold"), ("IN A FOLDER", 61, 37, "thin"),
          ("FOLDERS", 61, 48, "bold"), ("SIDE BY SIDE", 61, 57, "thin"),
          ("PLAY", 25, 70, "bold"), ("OR OPEN", 25, 79, "thin"),
          ("BACK", 85, 70, "bold"), ("ONE STEP", 85, 79, "thin"),
          ("TO THE COVER", 37, 90, "bold"), ("THEN THIS PAGE", 37, 99, "thin"),
          ("HOLD 3 SECONDS", 37, 110, "bold"), ("IN A GAME: BACK HERE", 37, 119, "thin")]
COLOURS = {"bold": "cream", "thin": "steel"}
WALL = {"dpad": 3, "button": 2, "pill": 2}
GRILLE = (107, 35, 12, 4, 4, 3)                 # the speaker: first slot's foot (x, y), rows, slots, spacing, rows a step
POOL = (0, 10, 150, 120, 38, 0.1)               # the key's pool: centre, radii (along, across), tilt (degrees), seam
HEART = (20, 40, 27.0)                          # its indigo heart round the recess, toward the key: centre, radius
VIGNETTE = 4.5                                  # px of the frame that fall to black
DISH = (4.6, 3.0)                               # the D-pad's dish: radius, where its walls begin
DP_SHADE = 0.0                                  # the D-pad's hub: near up to this diagonal (x + y from its centre)
NEAR_CREAM = 0.7                                # the near arms' edges cream where they face the key this squarely
DP_GLINTS = [(19, 30), (8, 42)]                 # the key's glints on its corners

GRAPH = ["black", "ink", "navy", "indigo", "steel", "cream"]
PLATE = ["black", "ink", "navy", "indigo"]
LKEY = np.array([-0.6, -0.8])                   # toward the key, on the picture

S = 4
_c = (np.arange(128 * S) + 0.5) / S
X, Y = np.meshgrid(_c, _c)
PP = (X, Y)
_p = np.arange(128) + 0.5
XP, YP = np.meshgrid(_p, _p)
PX = (XP, YP)
yy, xx = np.mgrid[0:128, 0:128]


def stamp(rows):
    return np.array([[ch == "#" for ch in r] for r in rows], dtype=bool)


LETTER = {"A": stamp([".###.", "##.##", "##.##", "#####", "##.##", "##.##", "##.##"]),
          "B": stamp(["####.", "##.##", "##.##", "####.", "##.##", "##.##", "####."])}
SMALL = {"S": ["###", "#..", "###", "..#", "###"], "E": ["###", "#..", "##.", "#..", "###"],
         "L": ["#..", "#..", "#..", "#..", "###"], "C": ["###", "#..", "#..", "#..", "###"],
         "T": ["###", ".#.", ".#.", ".#.", ".#."], "A": ["###", "#.#", "###", "#.#", "#.#"],
         "R": ["##.", "#.#", "##.", "#.#", "#.#"]}
TRI = {"up": stamp(["...#...", "..###..", ".#####.", "#######"])}
TRI["down"] = TRI["up"][::-1]
TRI["left"] = TRI["up"].T
TRI["right"] = TRI["up"].T[:, ::-1]
GLYPH = {"updown": stamp(["..#..", ".###.", "#####", ".....", ".....", ".....", "#####", ".###.", "..#.."]),
         "leftright": stamp(["..#...#..", ".##...##.", "###...###", ".##...##.", "..#...#.."])}


def text_mask(art):
    rows = [r for r in art.strip("\n").splitlines() if r and not r.startswith("//")]
    w = max(len(r) for r in rows)
    return np.array([[ch == "#" for ch in r.ljust(w)] for r in rows], dtype=bool)


def narrow_spaces(m, gap):
    """The title's word spaces (runs of 4 or more empty columns) cut to `gap`."""
    empty = ~m.any(0)
    keep, x = [], 0
    while x < m.shape[1]:
        e = x
        while e < m.shape[1] and empty[e] == empty[x]:
            e += 1
        n = e - x
        keep += list(range(x, e)) if not empty[x] or n < 4 else list(range(x, x + gap))
        x = e
    return m[:, keep]


def word35(s):
    m = np.zeros((5, 4 * len(s) - 1), bool)
    for k, ch in enumerate(s):
        m[:, 4 * k:4 * k + 3] = stamp(SMALL[ch])
    return m


def cov(d):
    """A shape's pixels: those at least half covered (4 x 4 samples)."""
    return ak.px_mean((d < 0).astype(np.float32), S) >= 0.5


def edge_rank(m):
    """0 on a mask's outermost pixels, 1 on the next ring in, ... (8-way)."""
    r = np.full(m.shape, 99, int)
    cur = m.copy()
    k = 0
    while cur.any() and k < 20:
        inner = ak.erode(cur, 1, diag=True)
        r[cur & ~inner] = k
        cur = inner
        k += 1
    return r


def facing(dpx):
    """How much each pixel's nearest edge faces the key (-1..1), from a
    distance field at the pixel centres."""
    gy, gx = np.gradient(dpx)
    n = np.hypot(gx, gy)
    return (gx * LKEY[0] + gy * LKEY[1]) / np.linalg.norm(LKEY) / np.maximum(n, 1e-6)


def toward_key(cx, cy):
    rr = np.hypot(XP - cx, YP - cy)
    return ((XP - cx) * LKEY[0] + (YP - cy) * LKEY[1]) / np.linalg.norm(LKEY) / np.maximum(rr, 1e-6), rr


def smooth(v, a, b):
    """0 at a, 1 at b, a smooth step between."""
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def proud(cap, depth):
    """A control standing proud of the face: its cap, the front wall `depth`
    px under it, the black seam round both, and the shadow it casts: its
    own silhouette moved `depth` px down and right."""
    wall = np.zeros_like(cap)
    for k in range(1, depth + 1):
        wall |= ak.shift(cap, 0, k)
    wall &= ~cap
    body = cap | wall
    seam = ak.dilate(body, 1, diag=True) & ~body
    shadow = ak.shift(body, depth, depth) & ~body & ~seam
    return dict(cap=cap, wall=wall, body=body, seam=seam, shadow=shadow)


def darken(pic, mask, ramp, steps=1):
    """Pixels of `mask` one step (or more) down `ramp`, whatever they are:
    a shadow that keeps the pattern under it."""
    a = pic.idx
    ids = [pic.pal[n] for n in ramp]
    for k in range(len(ids) - 1, 0, -1):
        m = mask & (a == ids[k])
        a[m] = ids[max(0, k - steps)]


def walls(pic, c, side, foot):
    pic.put(c["wall"], side)
    pic.put(c["wall"] & ~ak.shift(c["wall"], 0, -1), foot)
    pic.put(c["seam"], "black")


def dpad_sdf(P):
    cx, cy, span, arm = DPAD
    return ak.smin(ak.box(P, cx, cy, span / 2, arm / 2, 2.5), ak.box(P, cx, cy, arm / 2, span / 2, 2.5), 1.5)


def pill_sdf(x0, y0):
    return lambda P: ak.box(P, x0 + PILL_W / 2, y0 + PILL_H / 2, PILL_W / 2, PILL_H / 2, PILL_H / 2)


def glass_sdf(P):
    cx, bot, hw, r = GLASS
    return ak.box(P, cx, bot - 40, hw, 40, r)


# ---- the controls ---------------------------------------------------------------------------

def dpad(pic, c):
    """Violet plastic, lit from the top left: the tops a plateau (steel on
    the near arms, indigo on the far), each edge facing the key a step up,
    each turning away a step down, a dished centre, glints on the corners
    nearest the key, LED arrows."""
    cx, cy, span, arm = DPAD
    cap = c["cap"]
    walls(pic, c, "ink", "black")
    pic.put(c["wall"] & ak.shift(cap, 0, 1), "navy")            # the wall's top row, just under the lip
    f = facing(dpad_sdf(PX))
    er = edge_rank(cap)
    dx, dy = XP - cx, YP - cy
    hub = (np.abs(dx) < arm / 2) & (np.abs(dy) < arm / 2)
    farh = (dx > arm / 2) | (dy > arm / 2) | (hub & (dx + dy > DP_SHADE))
    top = np.where(farh, 3, 4)                                   # each arm a rocker: up and left steel, right and down indigo
    lv = top.copy()
    near, away = np.where(farh, f > 0.55, f > NEAR_CREAM), f < -0.3
    lv = np.where(near & (er == 0), top + 1, lv)                 # the edge facing the key, a step up
    lv = np.where(away & (er == 0), top - 1, lv)                 # the edge turning away, a step down
    lv = np.where((er == 0) & ~near & ~away, top, lv)
    df, rr = toward_key(cx, cy)
    dish = rr < DISH[0]
    lv = np.where(dish, 3, lv)
    lv = np.where(dish & (rr > DISH[1]) & (df > 0.2), 2, lv)           # its near wall, in shade
    lv = np.where(dish & (rr > DISH[1]) & (df < -0.2), 4, lv)          # its far wall, lit
    ak.put_levels(pic, cap, lv, GRAPH)
    for gx, gy in DP_GLINTS:
        ak.glint(pic, gx, gy, 1)
    h = span / 2
    for k, (ax, ay) in {"up": (cx - 3.5, cy - h + 3), "down": (cx - 3.5, cy + h - 7),
                        "left": (cx - h + 3, cy - 3.5), "right": (cx + h - 7, cy - 3.5)}.items():
        M = ak.place(TRI[k], int(round(ax)), int(round(ay)))
        ring = ak.dilate(M, 1) & ~M & cap
        lip = ring & (ak.shift(M, 1, 0) | ak.shift(M, 0, 1)) & ~(ak.shift(M, -1, 0) | ak.shift(M, 0, -1))
        pic.put(ring, "black")
        pic.put(lip, "indigo" if k in ("right", "down") else "steel")    # the window's lower lip, lit
        pic.put(M, "rainbow")


def button(pic, c, cx, cy, ramp, letter):
    """A slot machine's button: a 1-px chrome bezel, a black gap, a glossy
    dome (its highlight up toward the key, its shade down and right), the
    letter moulded in cream."""
    lo, base, hi = ramp
    walls(pic, c, "navy", "ink")
    a, rr = toward_key(cx, cy)
    cap = c["cap"]
    c1 = ak.erode(cap, 1)
    bez = cap & ~c1                                              # an 8-connected ring
    dome = ak.erode(c1, 1)
    lb = np.full((128, 128), 2)
    lb = np.where(a > -0.35, 3, lb)
    lb = np.where(a > 0.25, 4, lb)
    ak.put_levels(pic, bez, lb, GRAPH)
    pic.put(c1 & ~dome, "black")
    L = LETTER[letter]
    lx, ly = int(cx - L.shape[1] / 2 + 0.5), int(cy - L.shape[0] / 2 + 0.5)
    LM = ak.place(L, lx, ly)
    clear = ~ak.dilate(LM, 1, diag=True)
    rim = dome & ~ak.erode(dome, 1)
    pic.put(dome, base)
    pic.put(dome & (rr > DOME_SHADE) & (a < -0.3), lo)
    if hi == "cream":                                           # a short specular, clear of the letter
        pic.put(rim & (a > 0.9) & clear, "cream")
    else:                                                       # an arc toward the key, its middle cream
        hl = rim & (a > 0.3) & clear
        pic.put(hl, hi)
        pic.put(hl & (a > 0.9), "cream")
    pic.put(ak.shift(LM, 1, 1) & dome & ~LM, lo)
    pic.put(LM, "cream")
    ak.despeckle(pic, need=4, within=dome & ~LM & ~(rim & (a > 0.3)))      # no lone dots of red in the shade


DOME_SHADE = 4.3                                                 # the domes' shade: from this radius out


def pill(pic, c, x0, y0, word):
    """SELECT / START: a rubber pill, its name moulded on it: indigo on top,
    navy below, the near end's rim steel with a cream specular, the far
    end's ink."""
    walls(pic, c, "ink", "black")
    cap = c["cap"]
    f = facing(pill_sdf(x0, y0)(PX))
    er = edge_rank(cap)
    lv = np.where(YP < y0 + 4, 3, 2)
    lit = (er == 0) & (f > 0.3)
    lv = np.where(lit, np.where(XP < x0 + PILL_W * 0.62, 4, 3), lv)   # the top rim steel, fading toward the far end
    lv = np.where((er == 0) & ((f < -0.3) | ((YP > y0 + PILL_H / 2) & ~lit)), 1, lv)   # the far end and the underside, ink
    ak.put_levels(pic, cap, lv, GRAPH)
    pic.put(lit & (yy == y0) & (xx >= x0 + 4) & (xx <= x0 + 6), "cream")   # the specular on the near shoulder
    W = word35(word)
    pic.put(ak.place(W, int(x0 + (PILL_W - W.shape[1]) / 2 + 0.5), y0 + 2), "cream")


def well(pic):
    """The round recess the D-pad sits in: its floor a step down in shade,
    its wall dark on the near side and lit on the far side."""
    cx, cy, R = WELL
    a, rr = toward_key(cx, cy)
    W = cov(np.hypot(X - cx, Y - cy) - R)
    rim = W & ~ak.erode(W, 1)
    rim2 = ak.erode(W, 1) & ~ak.erode(W, 2)
    floor = W & ~rim
    lv = np.where(rr < R - 6, 1.6, 1.4) - 0.6 * np.clip(-a, 0, 1)
    ak.by_level(pic, ak.terrace(lv, 0.15), PLATE, where=floor)
    pic.put(rim, "ink")
    pic.put(rim & (a > 0.35), "black")
    pic.put(rim & (a < -0.3), "indigo")
    pic.put(rim & (a < -0.75), "steel")
    pic.put(rim2 & (a > 0.35), "ink")
    pic.put(rim2 & (a < -0.5), "navy")
    return W, floor


def face_levels():
    """The face's light, a level on PLATE per pixel: the key's pool from the
    top left over most of the face (navy, an ellipse leaning down the light's
    way, so the bottom-right corner falls to ink) and an indigo heart round
    the recess, toward the key. The frame's vignette comes off it after."""
    cx, cy, ra, rc, tilt, w = POOL
    px_, py_ = XP - cx, YP - cy
    ca, sa = np.cos(np.radians(tilt)), np.sin(np.radians(tilt))
    pd = np.hypot((px_ * ca + py_ * sa) / ra, (-px_ * sa + py_ * ca) / rc)
    lv = 1.0 + smooth(-pd, -1.0, -1.0 + w)
    rh = np.hypot(XP - HEART[0], YP - HEART[1])
    lv += smooth(-rh, -HEART[2], -HEART[2] + 2.5)
    return lv


def vignette():
    """How far the frame pulls the face down (levels), a soft ramp dithered
    over its whole width: ink, then black at the very edge."""
    de = np.minimum(np.minimum(XP, 128 - XP), np.minimum(YP, 128 - YP))
    return np.clip((VIGNETTE - de) / (VIGNETTE - 1.0) * 2.0, 0, 2.0)  # 2 levels over the rim


# ---- the picture ----------------------------------------------------------------------------

def bezel(pic, gm):
    """The bezel round the glass: its slope into the screen lit on the
    bottom and right, in shade on the left, fading out at the frame's top."""
    fg = facing(glass_sdf(PX))
    r1 = ak.dilate(gm, 1, diag=True) & ~gm
    r2 = ak.dilate(gm, 2, diag=True) & ~gm & ~r1
    pic.put(r1, "indigo")
    pic.put(r1 & (fg < -0.3), "steel")
    pic.put(r1 & (fg > 0.3), "ink")
    pic.put(r2 & (fg < -0.5), "indigo")
    pic.put(r2 & (fg > 0.3), "navy")
    fade = yy < 3
    pic.put((r1 | r2) & fade, "ink")
    pic.put((r1 | r2) & fade & (yy == 2) & (fg < -0.3), "navy")


def grille(pic):
    """The speaker: slots slanting up to the right (one pixel across every
    GRILLE[5] rows, clean even steps), cut in the face: a black slot, its far
    wall (down and right, facing the key) lit indigo just beside it."""
    x0, y0, rows, n, step, rise = GRILLE
    for k in range(n):
        for r in range(rows):
            x, y = x0 + step * k + r // rise, y0 - r
            pic.px(x, y, "black")
            pic.px(x + 1, y, "indigo")


def draw():
    P = ak.Palette({
        "ink": "#0A0A26", "navy": "#1B1D58", "indigo": "#3C3A96", "steel": "#8E8CDC",
        "wine": "#5A0A1E", "rose": "#FF8C70",
        "jade0": "#0A5040", "jade1": "#1FA06C",
        "gold0": "#94500E", "gold1": "#EAA622", "gold2": "#FFEA8C",
    }, ramps=[GRAPH, ["black", "wine", "red", "rose", "cream"], ["black", "jade0", "jade1", "cream"],
              ["gold0", "gold1", "gold2", "cream"]])
    pic = ak.Picture.blank(P, "black")
    thin, bold = ak.Font(THIN), ak.Font(BOLD)

    # ---- the screen's glass at the top, black
    gm = cov(glass_sdf(PP))

    # ---- the controls' geometry
    ctl = {"dpad": proud(cov(dpad_sdf(PP)), WALL["dpad"])}
    for bx, by, letter in BUTTONS:
        ctl[letter] = proud(cov(np.hypot(X - bx, Y - by) - BTN_R), WALL["button"])
    for x0, y0, word in PILLS:
        ctl[word] = proud(cov(pill_sdf(x0, y0)(PP)), WALL["pill"])

    # ---- the face: violet lacquer, lit from the top left
    bm = ~gm
    words = np.zeros((128, 128), bool)                            # behind the words the seams step without a dither
    for s_, lx, ly, kind in LABELS:
        mw = (bold if kind == "bold" else thin).mask(s_)
        words |= ak.dilate(ak.place(np.ones((mw.shape[0] + 1, mw.shape[1] + 1), bool), lx, ly), 1)
    ak.put_levels(pic, bm, ak.levels(ak.terrace(face_levels(), 0.3) - vignette(), ~words), PLATE)
    W, floor = well(pic)
    for k, c in ctl.items():
        darken(pic, c["shadow"] & (floor if k == "dpad" else ~W), PLATE)
    bezel(pic, gm)
    grille(pic)
    dpad(pic, ctl["dpad"])
    for (bx, by, letter), ramp in zip(BUTTONS, (("wine", "red", "rose"), ("jade0", "jade1", "cream"))):
        button(pic, ctl[letter], bx, by, ramp, letter)
    for x0, y0, word in PILLS:
        pill(pic, ctl[word], x0, y0, word)

    # lone pixels on the face (the seams' odd dots) take their neighbours' colour
    used = gm.copy()
    for c in ctl.values():
        used |= c["body"] | c["seam"]
    ak.despeckle(pic, need=5, within=~used)

    # ---- the words
    for name, gx, gy in GLYPHS:
        M = ak.place(GLYPH[name], gx, gy)
        pic.put(ak.dilate(M, 1) & ~M, "black")
        pic.put(M, "rainbow")
    for s, lx, ly, kind in LABELS:
        (bold if kind == "bold" else thin).text(pic, s, lx, ly, COLOURS[kind], shadow="black")

    # ---- the title
    m1 = narrow_spaces(text_mask(TITLE_ART), WORD_GAP)
    x1 = TITLE_X
    keep = pic.idx.copy()
    t1 = ak.title(pic, m1, x1, TITLE_Y, fill=None, rows=TITLE_ROWS, hi=None, lo=None,
                  extrude=dict(dx=1, dy=1, depth=3, colours=["red", "wine", "wine"]),
                  shadow=dict(dx=1, dy=1, colour="black"))
    face = t1["face"]
    out = ak.outside_of(face)
    thick_v = face & ak.shift(face, 0, 1) & ak.shift(face, 0, -1)
    thick_h = face & ak.shift(face, 1, 0) & ak.shift(face, -1, 0)
    top_e = face & ak.shift(out, 0, 1) & ak.shift(thick_v, 0, -1)
    left_e = face & ak.shift(out, 1, 0) & ak.shift(thick_h, -1, 0)
    bot_e = face & ak.shift(out, 0, -1) & ak.shift(thick_v, 0, 1)
    pic.put(bot_e, "gold0")
    pic.put((top_e | left_e) & ~bot_e, "cream")
    for gx, gy, arms in TITLE_GLINTS:
        ak.glint(pic, x1 + gx, TITLE_Y + gy, max(arms), tip="gold2", arms=arms)
    pic.idx[~gm] = keep[~gm]                                      # the bezel stays whole round the title
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), OUT))
