"""spec/assets/system/error-1.png .. error-5.png: the visual menu's five
install errors (tools/menuart.py ERRORS, docs/sd-menu.md). draw(n) paints
error n; `python tools/menuart.py` (or this file, run from anywhere) writes
them. Edit this, not the PNGs (docs/cover-art.md).

THE BRIEF (revision 2, the owner's: no bulbs round the title, no coin
door, and emblems any cart's errors can wear: these are spec defaults)
  Message: this machine is out of order; here is what went wrong and what to
  do. Calm, not alarming: nothing is on fire, a lamp says why. Red lacquer,
  chrome, gold lettering. Read order at 1x: ERROR n, the lamp with the error's name, the
  emblem beside the lines (each error's own picture: it is what tells the
  five apart at a glance), the lines, the key that takes you back.

  Composition: the front of a casino cabinet, square on (it is a notice and
  must read like one), in three tiers that every error shares; only the
  number, the lamp's words, the lines and the emblem change.

      +==========================+   the topper: chrome, lacquer
      |   E R R O R   n          |   gold on the dark face, a red halo
      +==========================+
      | [==== ERROR'S NAME ====] |   the TILT lamp
      |  .--.   line one ......  |
      | (emblem) line two .....  |   the glass: the emblem, big and lit,
      |  '--'   line three ....  |   the lines beside it
      +--------------------------+
      (o) ANY KEY: BACK              the deck: button, key

  - The topper (y 1-41): a sign. Two strips of red lacquer between chrome
    lips run along its top and bottom. On the near-black face, ERROR n
    blazes in gold, the only light in the sign and the first read: Oberon's
    bold 24 at its own size, black outline, a red and wine extrusion to the
    lower right, a gold face (light, a dark horizon band, light again;
    seams dithered on the wide bars only), a cream bevel on the edges
    facing the key (only where it runs: no lone dots), amber0 on the
    others, two cream glints, and a red halo hugging the whole word (the
    pockets between letters filled flat wine2, a wine1 ring round it; the
    strip's shadow stays above the letters, so no shelf).
  - The glass (y 43-106): smoked glass in a chrome bezel, flat wine1 (calm
    under the text: no dither behind letters, no glare), the bezel's shadow
    along its top and left, a darker foot. Across its top the TILT lamp: a
    red lens lit from within, rose along its top with a cream gleam, the
    error's name in cream on it (the second read), its light blooming onto
    the glass round it. Under it the lines in cream, left-aligned, the block
    flush to the right margin (its longest line ends at x 116) and centred
    in the rows y 61-98; the emblem takes all the room the lines leave on
    the left (30-36 px wide, about 40 tall): a little picture with its own
    action, outlined in black, lit from the top left (three tones on each
    surface's ramp and a cream specular), casting a shadow (black, a wine0
    penumbra) to the lower right on the glass:
      1 CARD ERROR      an SD card (dark slate, its cut corner, faint
                        contacts, the lock switch, a cream label with a bold
                        SD), knocked a little askew by a bolt striking its
                        cut corner from the upper right: an electric-blue
                        bolt, sparks flying off into the glass
      2 FILE DAMAGED    a document (a page with its corner dog-eared and
                        lines of print) torn in two, the halves pulled apart
                        and turning away (the torn edge in shade on the left)
      3 NOT A GAME      a game controller (grey, a D-pad, two red buttons)
                        under a red no sign, a ring and its bar
      4 INSTALL FAILED  a microchip cracked in two (no half program runs):
                        dark epoxy on steel legs, the halves turned apart
                        about the crack's foot, its edges lit electric blue
                        by a spark at its top
      5 CAN'T INSTALL   a polished steel padlock, shut: a round shackle, a
                        body lit like a drum, a keyhole in its plate
  - The deck (y 107-125): a chrome lip, a red arcade button in a chrome
    ring, ANY KEY: BACK in steel beside it.
  Light: the house key from the top left: lips and bevels lit on their tops
  and lefts, cream speculars streaking the left ends of the chrome lips.
  The edges are the cabinet's lacquer falling to black.

  Palette (11 own + cream, grey, black, red):
    wine0 wine1 wine2     the lacquer and the smoked glass (with black, red)
    rose                  light: the lamp's edge, the button, the no sign
    steel0 steel1 steel2  chrome, the SD card, the padlock (grey, cream)
    amber0 amber1 amber2  the title's own: nothing else uses them
    + one per error, for its emblem:
      1 volt   the bolt's electric blue and its sparks
      2 paper  the torn page's shade between cream and grey
      3 silver the controller's lit edge
      4 volt   the spark and the crack's edges
      5 silver the padlock's polish between steel2 and cream

  Lettering:
  - ERROR n: Oberon24b.Scn.Fnt, the Oberon system's bold 24 (hoard of
    bitfonts, oberon; terms: a system's font, its vendor's), set at its own
    size from the glyphs below (the 1's flag joined to its stem); the
    number set 7 px after ERROR.
  - The error's name and ANY KEY: BACK: Gamer by memesbruh03 (dafont,
    "100% Free"): tools/art/fonts/error-key-gamer.json.
  - The lines: Pizel by surrealember (itch.io, CC0):
    tools/art/fonts/error-body-pizel.json.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

FONTS = TOOLS / "art" / "fonts"
BODY_FONT = FONTS / "error-body-pizel.json"      # Pizel by surrealember, CC0
HEAD_FONT = FONTS / "error-key-gamer.json"       # Gamer by memesbruh03, 100% free

# ---- the title: Oberon24b (the Oberon system's bold 24) at its own size ----------------
# font: Oberon24b.Scn.Fnt (hoard/Oberon24b.Scn.Fnt (oberon)), author: oberon,
# terms: a system's font; its vendor's,
# source: https://github.com/robhagemans/hoard-of-bitfonts/tree/master/oberon
# (the 1: its flag joined to the stem, the slit and the lone tip filled)
GLYPHS = {
    "E": """
#############
#############
#############
#############
#####........
#####........
#####........
#############
#############
#############
#############
#####........
#####........
#####........
#####........
#############
#############
#############
#############""",
    "R": """
###########....
#############..
#############..
#####...######.
#####....#####.
#####....#####.
#####....#####.
#####...#####..
#############..
###########....
#########......
#####.#####....
#####..#####...
#####..######..
#####...#####..
#####...######.
#####....#####.
#####....######
#####.....#####""",
    "O": """
......######......
....##########....
..##############..
..#####....#####..
.#####......#####.
.#####......#####.
#####........#####
#####........#####
#####........#####
#####........#####
#####........#####
#####........#####
#####........#####
.#####......#####.
.#####......#####.
..#####....#####..
..##############..
....##########....
......######......""",
    "1": """
......#####
.....######
....#######
..#########
.##########
###########
.##########
...########
......#####
......#####
......#####
......#####
......#####
......#####
......#####
......#####
......#####
......#####
......#####""",
    "2": """
...########...
#############.
#############.
.###....######
.........#####
.........#####
.........#####
........#####.
........#####.
.......#####..
......######..
.....#####....
....######....
...#####......
..#####.......
.####.........
##############
##############
##############""",
    "3": """
...#######...
############.
############.
.##....######
........#####
........#####
........#####
.......#####.
..#########..
..#######....
..#########..
.......#####.
........#####
........#####
........#####
.##....######
############.
############.
...#######...""",
    "4": """
.......######...
......#######...
.....########...
.....########...
....###.#####...
...####.#####...
..####..#####...
..###...#####...
.####...#####...
####....#####...
###.....#####...
################
################
################
........#####...
........#####...
........#####...
........#####...
........#####...""",
    "5": """
.############.
.############.
.############.
.####.........
.####.........
#####.........
##########....
############..
#############.
###.....#####.
.........#####
.........#####
.........#####
.........#####
........#####.
.##....######.
############..
###########...
..#######.....""",
}


def glyph(ch):
    rows = [r for r in GLYPHS[ch].strip("\n").split("\n")]
    return np.array([[c == "#" for c in r] for r in rows], bool)


def title_mask(n, gap=2, space=7):
    """ERROR n as one mask: the letters `gap` apart, the number `space` after."""
    parts = [glyph(c) for c in "ERROR"] + [glyph(str(n))]
    w = sum(p.shape[1] for p in parts) + gap * 4 + space
    m = np.zeros((19, w), bool)
    x = 0
    for k, p in enumerate(parts):
        m[:, x:x + p.shape[1]] = p
        x += p.shape[1] + (gap if k < 4 else space)
    return m


def errors():
    import menuart
    return menuart.ERRORS


# ---- the palette -----------------------------------------------------------------------

COLOURS = {
    "wine0": "#1A0610", "wine1": "#3E0C1C", "wine2": "#741628",
    "rose": "#FF7A5E",
    "steel0": "#232A3E", "steel1": "#56627C", "steel2": "#AAB8CA",
    "amber0": "#A03C08", "amber1": "#F59C20", "amber2": "#FFE36C",
}
# each error's own colour, for its emblem (the 11th)
ACCENT = {1: ("volt", "#52C4F4"), 2: ("paper", "#D4BC98"), 3: ("silver", "#D8E0EA"),
          4: ("volt", "#52C4F4"), 5: ("silver", "#D8E0EA")}
LAQ = ["black", "wine0", "wine1", "wine2", "red"]
MET = ["black", "steel0", "steel1", "grey", "steel2", "cream"]
TTL = ["amber0", "amber1", "amber2", "cream"]

MQ = (2, 2, 125, 40)            # the marquee, x0 y0 x1 y1 (inclusive): columns 0-1 and 126-127 stay dark
STRIP = 7                       # its bulb strips, top and bottom
CAP = 3                         # its chrome end caps
TITLE_Y = 12
WIN = (4, 44, 123, 105)         # the glass
LENS = (9, 48, 118, 57)         # the TILT lamp
TY = 61                         # the text column's first row
TX_END = 116                    # its lines end by this column (the glass's face ends at 120)
BLOCK = 38                      # the rows it may fill (y 61-98)
EM_X0 = 7                       # the emblem's column starts here and ends 3 px before the text
TX, EX = 39, 21.5               # the text's left edge, the emblem's centre line: set per error by draw()
PITCH, GAP = 8, 4               # the lines' pitch; a blank line's
DECK = 107                      # the button deck's lip

YY, XX = np.mgrid[0:128, 0:128]


def palette(n):
    nm, hx = ACCENT[n]
    cols = dict(COLOURS)
    cols[nm] = hx
    ramps = [LAQ, MET, TTL, ["red", "rose", "cream"],
             {"volt": ["steel1", "volt", "cream"], "paper": ["grey", "paper", "cream"],
              "silver": ["steel2", "silver", "cream"]}[nm]]
    return ak.Palette(cols, ramps=ramps)


def rect_mask(x0, y0, x1, y1):
    m = np.zeros((128, 128), bool)
    m[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True
    return m


def rounded(x0, y0, x1, y1, r):
    """A rounded rectangle's pixels (inclusive corners)."""
    m = (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        cxm = (XX < cx) if cx == x0 + r else (XX > cx)
        cym = (YY < cy) if cy == y0 + r else (YY > cy)
        m &= ~(cxm & cym & ((XX - cx) ** 2 + (YY - cy) ** 2 > r * r + r * 0.6))
    return m


def side_of(x0, y0, x1, y1):
    """Each pixel's nearest edge of a box (0 top, 1 left, 2 bottom, 3 right) and its distance."""
    dt, db, dl, dr = YY - y0, y1 - YY, XX - x0, x1 - XX
    st = np.stack([dt, dl, db, dr])
    return np.argmin(st, 0), st.min(0)


# ---- the cabinet -----------------------------------------------------------------------

def cabinet(pic):
    """The cabinet's lacquer behind everything, falling to black at the frame:
    the outermost ring black, the next wine0."""
    ring = np.minimum(np.minimum(XX, 127 - XX), np.minimum(YY, 127 - YY))
    pic.put(ring >= 0, "wine1")
    pic.put(ring == 1, "wine0")
    pic.put(ring == 0, "black")
    pic.put((YY == MQ[3] + 2) & (ring > 0), "black")


def chrome_frame(pic, x0, y0, x1, y1, r=3, w=2):
    """A chrome frame `w` px wide round a box, lit on its top and left, a black
    line outside it and inside it. Returns the face inside."""
    outer = rounded(x0, y0, x1, y1, r)
    inner = rounded(x0 + w, y0 + w, x1 - w, y1 - w, max(1, r - w))
    band = outer & ~inner
    ak.outline(pic, outer, "black")
    side, k = side_of(x0, y0, x1, y1)
    cols = {0: ["steel2", "grey"], 1: ["steel2", "grey"], 2: ["steel1", "steel0"], 3: ["steel1", "steel0"]}
    pic.put(band, "black")                                 # the corners' inner pixels
    for s, cs in cols.items():
        for j, c in enumerate(cs):
            pic.put(band & (side == s) & (k == j), c)
    # a lit corner's outer pixel takes the lit chrome, not the grey under it
    oc = band & ~ak.shift(outer, 1, 0) & ~ak.shift(outer, 0, 1) & ((side == 0) | (side == 1))
    pic.put(oc, "steel2")
    face = ak.erode(inner, 1)
    pic.put(inner & ~face, "black")
    return face


# ---- the topper ------------------------------------------------------------------------

# the title's face, row by row: a colour, or (a, b): a with a checker of b
# where the stroke runs SEAM_RUN px or more (the bars: the stems step cleanly)
SEAM_RUN = 8
FACE_ROWS = (["amber2"] * 6 + [("amber2", "amber1")] + ["amber1"] * 5 + [("amber1", "amber0")] + ["amber0"] * 2
             + [("amber0", "amber1")] + ["amber1"] * 3)


def gold_face(pic, M, top, rows):
    ck = ak.checker()
    wide = M & (ak.runs(M, 1) >= SEAM_RUN) & ak.shift(M, 1, 0) & ak.shift(M, -1, 0)
    for j, c in enumerate(rows):
        row = M & (YY == top + j)
        if isinstance(c, tuple):
            pic.put(row, c[0])
            pic.put(row & wide & ~ck, c[1])
        else:
            pic.put(row, c)


def extrude(M, steps):
    """The title's depth: `steps` [(dx, dy, colour)] from the face back. A
    layer's lone pixels (no 4-way neighbour in it: the stair steps of a
    diagonal) are left to the outline. Returns everything drawn (face
    included), the outline, and the layers."""
    acc = M.copy()
    layers = []
    for dx, dy, c in steps:
        L0 = ak.shift(M, dx, dy) & ~acc
        L = L0 & ak.nbrs(L0)
        layers.append((L, c))
        acc |= L
    return acc, ak.dilate(acc, 1) & ~acc, layers


def marquee(pic, n):
    x0, y0, x1, y1 = MQ
    outer = rounded(x0, y0, x1, y1, 3)
    ak.outline(pic, outer, "black", diag=True)
    top = outer & (YY < y0 + STRIP)
    bot = outer & (YY > y1 - STRIP)
    caps = outer & ~top & ~bot & ((XX < x0 + CAP) | (XX > x1 - CAP))
    # the strips: red lacquer between chrome lips, lit from above
    for strip, ya in ((top, y0), (bot, y1 - STRIP + 1)):
        pic.put(strip, "wine2")
        pic.put(strip & (YY == ya + 1), "red")
        pic.put(strip & (YY == ya + STRIP - 2), "wine1")
        pic.put(strip & (YY == ya), "steel2")
        pic.put(strip & (YY == ya + STRIP - 1), "steel1")
    pic.put(caps, "grey")
    pic.put(caps & (XX == x0), "steel2")
    pic.put(caps & (XX == x1), "steel1")
    pic.put(caps & ((XX == x0 + CAP - 1) | (XX == x1 - CAP + 1)), "steel0")
    face = outer & ~top & ~bot & ~caps
    edge = face & ~ak.erode(face, 1)
    face &= ~edge
    pic.put(edge, "black")
    pic.put(face, "wine0")
    # the top strip's shadow on the face
    shade_row = y0 + STRIP + 1
    pic.put(face & (YY == shade_row), "black")
    pic.put(face & (YY == shade_row + 1) & ak.checker(), "black")
    # the title: lit amber, the only light in the sign, a red halo hugging it
    m = title_mask(n)
    tx, ty = 64 - (m.shape[1] + 2) // 2, TITLE_Y
    M = ak.place(m, tx, ty)
    allm, O, layers = extrude(M, [(1, 1, "red"), (2, 2, "wine2")])
    foot = allm | O
    sh = ak.shift(foot, 1, 1) & ~foot
    F = foot | sh
    out = ak.outside_of(F)                                 # the halo stays out of the counters
    # the halo hugs the word, not each letter: the pockets between letters
    # (narrower than 11 px) are filled flat, then two rings round the whole
    C = ak.erode(ak.dilate(F, 5, diag=True), 5, diag=True) | F
    h1 = ak.dilate(C, 1, diag=True) & ~C
    h2 = ak.dilate(C | h1, 1) & ~(C | h1)
    halo = face & out & (YY > shade_row + 1)               # and under the strip's shadow: no shelf
    pic.put(h2 & halo, "wine1")
    pic.put((h1 | (C & ~F)) & halo, "wine2")
    pic.put(sh & face, "black")
    pic.put(face & ~out & ~foot, "black")
    pic.put(O, "black")
    for L, c in layers:
        pic.put(L, c)
    for L, c in layers:                                    # depth pixels alone in a cramped counter: outline
        here = pic.where(c) & L
        pic.put(here & ~ak.nbrs(here, diag=True), "black")
    gold_face(pic, M, ty, FACE_ROWS)
    ak.bevel_runs(pic, M, "cream", "amber0")
    # pinholes shut in by the outline go black
    blk = pic.where("black")
    hole = ~blk & ak.shift(blk, 1, 0) & ak.shift(blk, -1, 0) & ak.shift(blk, 0, 1) & ak.shift(blk, 0, -1) & face & ~M
    pic.put(hole, "black")
    # glints: the E's top corner, the number's crown (cream on the bevel row,
    # its arms kept on the face)
    ak.glint(pic, tx + 1, ty + 1, 2, tip="amber2", arms=(1, 3, 1, 2))
    nx = tx + m.shape[1] - glyph(str(n)).shape[1]
    top_ = np.nonzero(M[ty, nx:])[0]
    gx = nx + int(top_[len(top_) // 2]) if len(top_) else nx + 4
    pic.px(gx, ty, "cream")
    for k in (1, 2):
        for xx in (gx - k, gx + k):
            if M[ty, xx]:
                pic.px(xx, ty, "cream")
    if M[ty + 1, gx]:
        pic.px(gx, ty + 1, "cream")
    if M[ty + 2, gx] and M[ty + 3, gx]:
        pic.px(gx, ty + 2, "amber2")
    return M


# ---- the glass, the lamp, the deck -----------------------------------------------------

def glass(pic):
    """Smoked glass: flat wine1, the bezel's shadow along its top and left,
    a darker foot."""
    x0, y0, x1, y1 = WIN
    face = chrome_frame(pic, x0, y0, x1, y1, r=3, w=2)
    pic.put(face, "wine1")
    top = face & ~ak.shift(face, 0, 1)
    pic.put(top, "black")
    pic.put(ak.shift(top, 0, 1) & face, "wine0")
    left = face & ~ak.shift(face, 1, 0)
    pic.put(left & ~top, "wine0")
    bottom = face & ~ak.shift(face, 0, -1)
    pic.put(bottom, "wine0")
    pic.put(ak.shift(bottom, 0, -1) & face & ak.checker(), "wine0")
    return face


def lens(pic, head, glass_m):
    """The TILT lamp: a red lens lit from within, the error's name on it, its
    light blooming onto the glass round it."""
    x0, y0, x1, y1 = LENS
    m = rounded(x0, y0, x1, y1, 3)
    o = ak.dilate(m, 1) & ~m
    g1 = ak.dilate(m | o, 1, diag=True) & ~(m | o)
    g2 = ak.dilate(m | o | g1, 1) & ~(m | o | g1)
    pic.put(g1 & glass_m, "wine2")
    pic.put(g2 & glass_m & ak.checker() & (YY > y1), "wine2")
    pic.put(o, "black")
    pic.put(m, "red")
    pic.put(m & (YY == y0), "rose")
    pic.put(m & (YY == y0 + 1) & ak.checker(), "rose")
    pic.put(m & (YY >= y1 - 1), "wine2")
    f = ak.Font(HEAD_FONT)
    mk = f.mask(head)
    tx = 64 - mk.shape[1] // 2
    ty = y0 + 2
    T = ak.place(mk, tx, ty)
    pic.put(ak.shift(T, 1, 1) & ~T & m, "wine2")
    pic.put(T, "cream")
    # the lens's gloss: a cream gleam along its top near the left
    pic.put(m & (YY == y0) & (XX >= x0 + 7) & (XX <= x0 + 20), "cream")
    pic.put(m & (YY == y0) & (XX >= x0 + 23) & (XX <= x0 + 25), "cream")
    # the lamp's chrome end caps, a screw in each
    for a0 in (x0, x1 - 3):
        cap = m & (XX >= a0) & (XX <= a0 + 3)
        pic.put(cap, "grey")
        pic.put(cap & (YY >= y0 + 6), "steel1")
        pic.put(cap & (YY == y1), "steel0")
        pic.put(cap & ((YY == y0) | (XX == a0)) & (YY < y1), "steel2")
        pic.put(cap & (XX == a0 + 3) & (YY > y0), "steel0")
        pic.px(a0 + 1, y0 + 4, "steel0")
        pic.px(a0 + 2, y0 + 4, "steel0")
        pic.px(a0 + 1, y0 + 3, "cream")
    pic.put(m & ((XX == x0 + 4) | (XX == x1 - 4)), "black")


def block_height(lines):
    return sum(GAP if not ln else PITCH for ln in lines) - (PITCH - 6)


def body(pic, lines, y):
    bf = ak.Font(BODY_FONT)
    for ln in lines:
        if not ln:
            y += GAP
            continue
        bf.text(pic, ln, TX, y, "cream")
        y += PITCH


def chrome_glints(pic):
    """Speculars on the chrome: a streak along each top lip near its left
    end, where the key light catches it."""
    x0, y0, x1, y1 = MQ
    for x in range(x0 + 4, x0 + 17):
        pic.px(x, y0, "cream")
    for x in range(x0 + 20, x0 + 23):
        pic.px(x, y0, "cream")
    wx0, wy0, wx1, wy1 = WIN
    for x in range(wx0 + 4, wx0 + 14):
        pic.px(x, wy0, "cream")
    pic.px(wx0, wy0 + 3, "cream")
    pic.px(wx0, wy0 + 4, "cream")
    for x in range(6, 16):
        pic.px(x, DECK, "cream")


def button(pic, cx, cy):
    """The red arcade button in its chrome ring, lit from the top left: a
    rose crescent on the dome, a cream spark, its lower right in shade."""
    dx, dy = XX + 0.5 - cx, YY + 0.5 - cy
    r = np.hypot(dx, dy)
    lam = (dx * KEYL[0] + dy * KEYL[1]) / np.maximum(r, 1e-3)      # 1 facing the key, -1 away
    ring = r < 6.7
    ak.outline(pic, ring, "black")
    tones(pic, ring, lam, ["steel0", "steel1", "grey", "steel2"], [-0.45, 0.05, 0.6])
    pic.put(ring & (r < 5.2), "black")
    dome = r < 4.4
    pic.put(dome, "red")
    pic.put(dome & (lam < -0.3) & (r > 2.7), "wine2")
    pic.put(dome & (lam > 0.45) & (r > 2.3), "rose")
    pic.px(int(cx) - 2, int(cy) - 2, "cream")
    pic.px(int(cx) - 1, int(cy) - 2, "cream")
    pic.px(int(cx) - 2, int(cy) - 1, "cream")


def deck(pic):
    """The button deck: lacquer curving away under a chrome lip (a sheen just
    under the lip, falling to black at the frame), the button, the key."""
    top = DECK + 3
    d = rounded(1, DECK, 126, 130, 3) & (YY >= top)
    # a sheen under the lip, the key's row flat wine1 (calm under the letters),
    # falling to black below it and towards the ends
    lv = np.interp(YY + 0.0, [top, top + 1, top + 2, top + 11, top + 12, top + 13, 125, 127],
                   [3.0, 2.5, 2.0, 2.0, 1.5, 1.0, 1.0, 0.25])
    lv = lv - np.clip((np.abs(XX + 0.5 - 64) - 58) / 4, 0, 1) * 1.0
    ak.by_level(pic, lv, LAQ, d, q=2)
    pic.put(rect_mask(3, DECK, 124, DECK), "steel2")
    pic.put(rect_mask(3, DECK + 1, 124, DECK + 1), "steel1")
    pic.put(rect_mask(3, DECK + 2, 124, DECK + 2), "black")
    button(pic, 20.5, 118.5)
    f = ak.Font(HEAD_FONT)
    f.text(pic, "ANY KEY: BACK", 32, 115, "steel2", shadow="black")


# ---- the emblems -----------------------------------------------------------------------
# Small things are drawn at the pixel: shapes tested at the pixels' centres,
# each surface in flat tones on its ramp by how it faces the key (three
# levels and a cream specular), a black outline, hand-placed details, a
# shadow cast on the glass to the lower right.

XC = (XX + 0.5).astype(np.float32)
YC = (YY + 0.5).astype(np.float32)
PC = (XC, YC)
KEYL = np.array([-0.64, -0.77])          # the key light's direction in the picture's plane


def at(d):
    """A shape's pixels: those whose centre falls inside it."""
    return d < 0


def cast(pic, m, where, dx=2, dy=2):
    """The emblem's shadow on the glass: black, a wine0 penumbra beyond it."""
    s = ak.shift(m, dx, dy) & ~m & where
    s2 = ak.shift(m, dx + 1, dy + 1) & ~m & ~s & where & ak.dilate(s, 1)
    pic.put(s2, "wine0")
    pic.put(s, "black")
    return s | s2


def edges(m):
    """A mask's edge pixels facing up, left, down and right."""
    return (m & ~ak.shift(m, 0, 1), m & ~ak.shift(m, 1, 0), m & ~ak.shift(m, 0, -1), m & ~ak.shift(m, -1, 0))


def tones(pic, m, val, cols, cuts):
    """Flat tones over m by a value: cols[k] where val passes k of the cuts."""
    i = np.zeros(m.shape, int)
    for c in cuts:
        i += (val > c)
    for k, c in enumerate(cols):
        pic.put(m & (i == k), c)


def facing(d):
    """How each pixel's outward normal (from a distance field) faces the key: 1 toward, -1 away."""
    gy, gx = np.gradient(np.asarray(d, np.float64))
    L = np.hypot(gx, gy) + 1e-9
    return (gx * KEYL[0] + gy * KEYL[1]) / L


def rim(m):
    """A mask's edge pixels (a 4-neighbour outside it)."""
    return m & ~ak.erode(m, 1)


def frame_at(cx, cy, turn=0.0, dx=0.0, dy=0.0):
    """Pixel centres in a piece's own frame: the piece drawn about (cx, cy)
    appears turned `turn` degrees (clockwise) and moved (dx, dy)."""
    return ak.rotate((XC - dx, YC - dy), cx, cy, -turn)


def to_screen(px, py, cx, cy, turn=0.0, dx=0.0, dy=0.0):
    """Where a point of a piece's own frame lands on the picture."""
    a = np.radians(turn)
    x, y = px - cx, py - cy
    return cx + np.cos(a) * x - np.sin(a) * y + dx, cy + np.sin(a) * x + np.cos(a) * y + dy


def stamp(pic, x, y, rows, key, where=None):
    """Hand-placed pixels, kept to `where` when given."""
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in key and 0 <= x + i < 128 and 0 <= y + j < 128 and (where is None or where[y + j, x + i]):
                pic.px(x + i, y + j, key[ch])


def mask_of(x, y, rows, chars):
    """A stamp's pixels (those whose character is in `chars`) as a mask."""
    m = np.zeros((128, 128), bool)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in chars and 0 <= x + i < 128 and 0 <= y + j < 128:
                m[y + j, x + i] = True
    return m


def shadow_side(m):
    """The pixels of m on its shadow side: a neighbour below or to the right outside it."""
    _, _, dn, rt = edges(m)
    return dn | rt


# ---- 1: CARD ERROR ----------------------------------------------------------------------

SD = dict(w=22.0, h=28.0, cut=6.5, turn=-6.0)
SD_S = [".####", "##...", "##...", ".###.", "...##", "...##", "####."]
SD_D = ["####.", "##.##", "##.##", "##.##", "##.##", "##.##", "####."]
# the bolt's core, drawn at the pixel: two legs stepping 2 down, 1 left, a jog
# between them, tapering to the tip (its last row's '#')
BOLT = ["...#####",
        "..#####.",
        "..####..",
        ".#####..",
        ".####...",
        "########",
        "....###.",
        "...####.",
        "...###..",
        "..###...",
        "..##....",
        ".##.....",
        ".#......",
        "#......."]


def emblem_sd(pic, glass_m, yc):
    """CARD ERROR: an SD card knocked askew, a bolt striking its cut corner
    from the upper right, sparks flying off into the glass."""
    cx, cy = EX - 3.5, float(round(yc)) + 6.0
    hw, hh, C, turn = SD["w"] / 2, SD["h"] / 2, SD["cut"], SD["turn"]
    Q = frame_at(cx, cy, turn)
    u, v = Q[0] - cx, Q[1] - cy
    poly = [(cx - hw, cy - hh), (cx + hw - C, cy - hh), (cx + hw, cy - hh + C), (cx + hw, cy + hh), (cx - hw, cy + hh)]
    dcard = ak.polygon(Q, poly)
    notch = (u < -hw + 1.0) & (v > -hh + 8.0) & (v < -hh + 13.0)    # the lock switch's slot
    card = at(dcard) & ~notch
    # the bolt, coming down from the upper right, its tip on the cut corner
    kx, ky = to_screen(hw - C / 2 + 1.2, -hh + C / 2 - 1.2, 0, 0, turn)
    tx_, ty_ = int(np.floor(cx + kx)), int(np.floor(cy + ky))
    bx0, by0 = tx_, ty_ - len(BOLT) + 1
    core = mask_of(bx0, by0, BOLT, "#")
    halo = ak.dilate(core, 1) & ~core
    bolt = core | halo
    every = card | bolt
    cast(pic, every, glass_m)
    ak.outline(pic, every, "black")
    # the card: dark slate, lit along its top and left, a gleam at the corner
    lam = facing(dcard)
    pic.put(card, "steel0")
    rc = rim(card)
    pic.put(rc & (lam > 0.25), "steel1")
    pic.put(rc & (lam > 0.25) & (u < -hw + 5.0) & (v < -hh + 4.0), "steel2")
    pic.put(card & ~rc & ak.shift(rc & (lam > 0.25), 1, 1) & (u + v < -hw - hh + 6.0), "steel1")
    # the lock switch in its slot
    pic.put(at(dcard) & notch & (v > -hh + 10.5) & ak.dilate(card, 1), "grey")
    # its contacts, faint under the top edge
    for k in range(4):
        ct = card & ~rc & (np.abs(u - (-6.5 + 3.0 * k)) < 0.5) & (v > -hh + 1.6) & (v < -hh + 5.4)
        pic.put(ct, "steel1")
    # the label: cream, its shadow side in steel2, a bold SD on it
    dl = ak.box(Q, cx, cy + 4.6, hw - 2.8, hh - 7.2, 1.0)
    lab = at(dl)
    pic.put(lab, "cream")
    pic.put(rim(lab) & (facing(dl) < -0.25), "steel2")
    lx, ly = to_screen(0.0, 4.6, 0, 0, turn)
    sx0, sy0 = int(round(cx + lx)) - 5, int(round(cy + ly)) - 3
    rise = int(round(6 * np.tan(np.radians(-turn))))
    stamp(pic, sx0, sy0 + rise // 2, SD_S, {"#": "steel0"})
    stamp(pic, sx0 + 6, sy0 + rise // 2 - rise, SD_D, {"#": "steel0"})
    # the bolt: a cream core, electric blue round it, its tip white hot
    pic.put(halo, "volt")
    pic.put(core, "cream")
    # sparks flying off the strike into the glass: short streaks, hot at the head
    sx, sy = tx_, ty_
    near = ak.dilate(every, 1)
    for (ax_, ay_), (bx_, by_) in (((sx - 3, sy - 3), (sx - 6, sy - 7)), ((sx - 4, sy - 1), (sx - 9, sy - 2)),
                                   ((sx + 2, sy + 3), (sx + 5, sy + 7)), ((sx + 4, sy + 1), (sx + 9, sy + 2))):
        pts = ak.line_px([(ax_ + 0.5, ay_ + 0.5), (bx_ + 0.5, by_ + 0.5)])
        for j, (px_, py_) in enumerate(pts):
            if glass_m[py_, px_] and not near[py_, px_] and px_ < TX - 3:
                pic.px(px_, py_, "cream" if j == len(pts) - 1 else "volt")


# ---- 2: FILE DAMAGED --------------------------------------------------------------------

def tear_line(x0, y0, x1, y1, n, amp, seed):
    """A torn edge from (x0, y0) to (x1, y1): n points, each pushed aside by
    up to `amp` (a deterministic scatter, so the edge looks torn, not cut)."""
    pts = []
    for k in range(n + 1):
        t = k / n
        off = 0.0 if k in (0, n) else (ak.ihash(k, seed) * 2 - 1) * amp
        pts.append((x0 + (x1 - x0) * t + off, y0 + (y1 - y0) * t))
    return pts


# the page: its size and dog-eared corner; each half's turn and move once torn
DOC = dict(w=22.0, h=30.0, ear=7.0, turns=(-7.0, 8.0), moves=((-2.0, -0.5), (2.0, 1.0)))
# its print: lines from u0 to u1 at v (in the page's own frame, from its centre)
DOC_LINES = [(-7.5, 3.5, -10.5), (-7.5, 7.5, -6.5), (-7.5, 5.5, -3.5), (-7.5, 7.5, -0.5), (-7.5, 2.5, 2.5),
             (-7.5, 7.5, 6.5), (-7.5, 6.5, 9.5)]


def page_d(Q, cx, cy, w, h, ear):
    """The page with its top right corner cut off (the dog-ear's fold)."""
    hw, hh = w / 2, h / 2
    return ak.polygon(Q, [(cx - hw, cy - hh), (cx + hw - ear, cy - hh), (cx + hw, cy - hh + ear),
                          (cx + hw, cy + hh), (cx - hw, cy + hh)])


def emblem_doc(pic, glass_m, yc):
    """FILE DAMAGED: a document (a page with its corner dog-eared and lines
    of print) torn in two, the halves pulled apart and turning away from
    each other. Generic: any cart's file."""
    cx, cy = EX + 1.0, float(round(yc)) + 0.5
    w, h, ear = DOC["w"], DOC["h"], DOC["ear"]
    tear = tear_line(cx + 1.4, cy - h / 2 - 2, cx - 1.4, cy + h / 2 + 2, 12, 1.5, 7)
    left = [(cx - 30, cy - h / 2 - 2)] + tear + [(cx - 30, cy + h / 2 + 2)]
    pieces = []
    for k in range(2):
        turn, (dx, dy) = DOC["turns"][k], DOC["moves"][k]
        Q = ak.rotate((XC - dx, YC - dy), cx, cy, -turn)
        dp = page_d(Q, cx, cy, w, h, ear)
        side = at(ak.polygon(Q, left))
        m = at(dp) & (side if k == 0 else ~side)
        pieces.append(dict(m=m, Q=Q, dp=dp, left=k == 0))
    for pc in pieces:
        cast(pic, pc["m"], glass_m)
    for pc in pieces:
        m, Q = pc["m"], pc["Q"]
        u, v = Q[0] - cx, Q[1] - cy
        ak.outline(pic, m, "black")
        # the page: cream, a paper shade along its shadow sides, the torn
        # edge in shade on the left half (it faces away from the key)
        lam = facing(pc["dp"])
        pic.put(m, "cream")
        rm = rim(m)
        shd = rm & (lam < -0.3) & (pc["dp"] > -1.6)
        pic.put(shd, "paper")
        if pc["left"]:
            pic.put(m & ~ak.shift(m, -1, 0) & (u > -5), "paper")
        else:
            # the dog-ear: the corner folded down, its back in shade, a crease along the fold
            hw, hh = w / 2, h / 2
            fold = at(ak.polygon(Q, [(cx + hw - ear, cy - hh), (cx + hw - ear, cy - hh + ear),
                                     (cx + hw, cy - hh + ear)])) & m
            pic.put(fold, "paper")
            pic.put(fold & (~ak.shift(fold, 1, 0) | ~ak.shift(fold, 0, -1)), "steel1")
        ak.lonely(pic, "paper", m, into="cream")
        # the print
        for u0, u1, vv in DOC_LINES:
            pic.put(m & ~rm & (np.abs(v - vv) < 0.5) & (u >= u0) & (u <= u1), "steel1")


# ---- 3: NOT A GAME ----------------------------------------------------------------------

def emblem_nogame(pic, glass_m, yc):
    """NOT A GAME: a game controller under a red no sign (a ring and its
    bar): the file is something else. Generic: any cart's."""
    cx, cy = EX + 0.5, float(round(yc)) + 0.5
    # the controller: a rounded body and two grips
    dbody = ak.union(ak.box(PC, cx, cy - 1.0, 12.5, 5.5, 4.5),
                     ak.circle(PC, cx - 8.0, cy + 3.5, 4.8), ak.circle(PC, cx + 8.0, cy + 3.5, 4.8))
    pad = at(dbody)
    # the no sign: a ring and its bar, top left to bottom right
    R, t = 15.5, 2.2
    dring = np.abs(np.hypot(XC - cx, YC - cy) - R) - t
    dbar = ak.segment(PC, cx - R * 0.72, cy - R * 0.72, cx + R * 0.72, cy + R * 0.72, t)
    dsign = ak.union(dring, dbar)
    sign = at(dsign)
    cast(pic, pad | sign, glass_m)
    ak.outline(pic, pad, "black")
    # the controller: grey plastic lit from the top left, a D-pad, two buttons, two pills
    pic.put(pad, "grey")
    up_, lf_, dn_, rt_ = edges(pad)
    pic.put(up_ | lf_, "silver")
    pic.put((dn_ | rt_) & ~(up_ | lf_), "steel1")
    px_, py_ = int(np.floor(cx - 7.0)), int(np.floor(cy - 2.0))
    stamp(pic, px_ - 2, py_ - 2, ["..k..", "..k..", "kkkkk", "..k..", "..k.."], {"k": "black"})
    bx_, by_ = int(np.floor(cx + 4.0)), int(np.floor(cy - 4.0))
    stamp(pic, bx_, by_, [".kk...", "krrk..", "krrkk.", ".kkrrk", "...rrk", "...kk."], {"k": "black", "r": "red"})
    pic.px(bx_ + 1, by_ + 1, "rose")
    pic.px(bx_ + 3, by_ + 3, "rose")
    stamp(pic, int(cx) - 3, int(cy) + 2, ["kk.kk"], {"k": "steel1"})
    # the sign over it: red, its lit side rose, its shaded side wine2, a black rim
    ak.outline(pic, sign, "black")
    tones(pic, sign, facing(dsign), ["wine2", "red", "red", "rose"], [-0.4, 0.1, 0.6])
    ys_, xs_ = np.nonzero(sign & (facing(dsign) > 0.6))
    if len(xs_):
        k_ = int(np.argmin(xs_ + ys_))
        pic.px(int(xs_[k_]) + 1, int(ys_[k_]) + 1, "cream")


# ---- 4: INSTALL FAILED ------------------------------------------------------------------

IC_HALF, IC_LEGS = 10.0, 4                     # the chip's half width, and its legs a side
# the halves once cracked: how far each moved and turned about the foot of the crack (left, right)
IC_PART = ((-1.0, 0.5, -6.0), (1.0, -0.5, 6.0))


def emblem_ic(pic, glass_m, yc):
    """INSTALL FAILED: a microchip cracked in two (the install stopped
    partway: no half program runs), the halves turned apart, the crack's
    edges lit by an electric spark. Generic: any cart's."""
    hb = IC_HALF
    cx, cy = EX + 0.5, float(round(yc)) + 0.5
    crack = [(cx + 0.5, cy - hb - 6), (cx - 1.5, cy - 5.0), (cx + 1.5, cy - 1.0), (cx - 1.0, cy + 3.0),
             (cx + 1.0, cy + 6.5), (cx + 0.5, cy + hb + 6)]
    left = [(cx - 40, cy - hb - 6)] + crack + [(cx - 40, cy + hb + 6)]
    hx, hy = cx, cy + hb + 3
    parts = []
    pitch = 2 * hb / IC_LEGS
    for k, (dx, dy, turn) in enumerate(IC_PART):
        Q = ak.rotate((XC - dx, YC - dy), hx, hy, -turn)
        inl = at(ak.polygon(Q, left))
        side = inl if k == 0 else ~inl
        dbody = ak.box(Q, cx, cy, hb, hb, 1.2)
        body = at(dbody) & side
        legs = np.zeros((128, 128), bool)
        for i in range(IC_LEGS):
            off = -hb + (i + 0.5) * pitch
            for ax, ay, w_, h_ in ((cx - hb - 1.6, cy + off, 1.7, 0.9), (cx + hb + 1.6, cy + off, 1.7, 0.9),
                                   (cx + off, cy - hb - 1.6, 0.9, 1.7), (cx + off, cy + hb + 1.6, 0.9, 1.7)):
                legs |= at(ak.box(Q, ax, ay, w_, h_, 0.0)) & side
        legs &= ~body
        parts.append(dict(body=body, legs=legs, Q=Q, dbody=dbody, left=k == 0))
    for pc in parts:
        cast(pic, pc["body"] | pc["legs"], glass_m)
    for pc in parts:
        body, legs, Q = pc["body"], pc["legs"], pc["Q"]
        u, v = Q[0] - cx, Q[1] - cy
        ak.outline(pic, body | legs, "black")
        # the legs: bright steel, their ends a step darker
        pic.put(legs, "steel2")
        pic.put(legs & ~ak.dilate(body, 2), "grey")
        # the body: dark epoxy, its rim lit on the key's side, a pin-1 dimple, a printed line
        pic.put(body, "steel0")
        lam = facing(pc["dbody"])
        pic.put(rim(body) & (lam > 0.3), "steel1")
        if pc["left"]:
            pic.put(body & (np.hypot(u + hb - 3.5, v + hb - 3.5) < 1.6), "steel1")
            pic.put(body & ~rim(body) & (np.abs(v - 3.5) < 0.5) & (u > -hb + 3) & (u < -2.5), "steel1")
        else:
            pic.put(body & ~rim(body) & (np.abs(v - 3.5) < 0.5) & (u > 2.5) & (u < hb - 4), "steel1")
        # the crack's edges: the spark's light along them
        open_side = ~ak.shift(body, -1, 0) if pc["left"] else ~ak.shift(body, 1, 0)
        pic.put(body & open_side & (np.abs(u) < 3.5), "volt")
    # the spark at the top of the crack, a few bits flying
    gx, gy = int(round(cx)), int(round(cy - hb - 3))
    ak.glint(pic, gx, gy, 2, arms=(2, 2, 2, 1), tip="volt")
    for x, y, c in ((gx - 4, gy - 1, "volt"), (gx + 4, gy - 2, "cream"), (gx + 4, gy + 2, "volt")):
        if glass_m[y, x]:
            pic.px(x, y, c)


# ---- 5: CAN'T INSTALL -------------------------------------------------------------------

def emblem_lock(pic, glass_m, yc):
    """CAN'T INSTALL: a polished steel padlock, shut."""
    cx = EX + 0.5
    by0 = int(round(yc)) - 2
    bx0, bx1, by1 = int(cx) - 12, int(cx) + 11, by0 + 18
    body = rounded(bx0, by0, bx1, by1, 3)
    # the shackle: a round tube, its legs into the body
    R, hw = 7.0, 2.3
    ya = by0 - 4.0
    pts = [(cx - R, by0 + 2.0), (cx - R, ya)] + [(cx - R * np.cos(t), ya - R * np.sin(t))
                                                 for t in np.linspace(0, np.pi, 15)[1:-1]] + [(cx + R, ya), (cx + R, by0 + 2.0)]
    T = ak.tube(PC, pts, [hw])
    sh = at(T["d"]) & ~body
    every = sh | body
    cast(pic, every, glass_m)
    ak.outline(pic, every, "black")
    val = T["n"][..., 0] * KEYL[0] + T["n"][..., 1] * KEYL[1]
    tones(pic, sh, val, ["steel0", "steel1", "grey", "steel2", "silver"], [-0.55, -0.15, 0.2, 0.55])
    # the tube's specular: cream along the crown's lit side
    spec = sh & (val > 0.55) & (T["n"][..., 2] < 0.95) & (YC < ya - 2.0) & (XC < cx + 1.0)
    pic.put(spec, "cream")
    pic.put(ak.dilate(body, 1) & ~body & sh, "black")
    # the body: polished steel lit like a drum, bright on the left
    u = (XC - bx0) / (bx1 + 1 - bx0)
    tones(pic, body, -np.abs(u - 0.3), ["steel1", "grey", "steel2", "silver"], [-0.52, -0.33, -0.14])
    pic.put(body & (u < 0.07), "steel2")
    up, lf, dn, rt = edges(body)
    pic.put(up, "silver")
    pic.put(up & (u > 0.2) & (u < 0.45), "cream")
    pic.put(up & (u > 0.75), "steel2")
    pic.put(lf, "steel2")
    pic.put(dn | rt, "steel0")
    pic.put(body & ~(dn | rt) & (ak.shift(dn, 0, -1) | ak.shift(rt, -1, 0)), "steel1")
    # a gleam down the bright band
    gl = body & ((XX - bx0) == 7) & (YY > by0 + 2) & (YY < by1 - 3)
    pic.put(gl, "cream")
    # the keyhole in its plate
    kx, ky = int(cx), by0 + 9
    pd = ak.circle(PC, cx, ky + 0.5, 4.3)
    plate = at(pd)
    pic.put(plate, "steel1")
    pl = facing(pd)
    pic.put(rim(plate) & (pl < -0.2), "steel2")             # a recess: lit on its far side
    pic.put(rim(plate) & (pl > 0.2), "steel0")
    stamp(pic, kx - 2, ky - 2, [".kk.", "kkkk", "kkkk", ".kk.", ".kk.", ".kk."], {"k": "black"})


EMBLEMS = {1: emblem_sd, 2: emblem_doc, 3: emblem_nogame, 4: emblem_ic, 5: emblem_lock}


def layout(lines):
    """The text column's left edge (the block flush to the right margin, so
    the emblem gets all the room the lines leave) and the emblem's centre."""
    bf = ak.Font(BODY_FONT)
    w = max(bf.mask(ln).shape[1] for ln in lines if ln)
    tx = TX_END + 1 - w
    return tx, (EM_X0 + tx - 3) / 2.0


def draw(n=1):
    global TX, EX
    head, lines = errors()[n]
    TX, EX = layout(lines)
    pic = ak.Picture.blank(palette(n), "black")
    cabinet(pic)
    marquee(pic, n)
    glass_m = glass(pic)
    lens(pic, head, glass_m)
    h = block_height(lines)
    y = TY + (BLOCK - h + 1) // 2
    free = glass_m & pic.where("wine1", "wine0")
    EMBLEMS[n](pic, glass_m & free, y + h / 2)
    body(pic, lines, y)
    deck(pic)
    chrome_glints(pic)
    # lone pixels left by the stacks (the extrusion's stair steps, the
    # frames' corners, the button's rim) take their neighbours' colour; the
    # lettering and the emblem are left as drawn
    wx0, wy0, wx1, wy1 = WIN
    bezel = rounded(wx0 - 1, wy0 - 1, wx1 + 1, wy1 + 1, 4) & ~rounded(wx0 + 3, wy0 + 3, wx1 - 3, wy1 - 3, 1)
    zone = ((YY > MQ[1] + STRIP) & (YY < MQ[3] - STRIP)) | bezel | ((YY >= DECK) & (XX < 30))
    ak.despeckle(pic, need=5, within=zone)
    return pic.image()


def e1():
    return draw(1)


def e2():
    return draw(2)


def e3():
    return draw(3)


def e4():
    return draw(4)


def e5():
    return draw(5)


if __name__ == "__main__":
    import boxart
    out = TOOLS.parent / "spec" / "assets" / "system"
    for k in sorted(errors()):
        print(boxart.save(draw(k), out / f"error-{k}.png"))
