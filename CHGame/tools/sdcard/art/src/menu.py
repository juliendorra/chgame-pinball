"""tools/sdcard/menu.png: the CHGame CASINO card's TEXT MENU picture, the
background the list menu bootloader draws its list over (docs/menu-image.md,
docs/cover-art.md). `python tools/sdcard/covers.py` redraws it (and
`python tools/sdcard/art/src/menu.py` alone); edit this, not the PNG.

THE BRIEF (revision 1)
  Message: the CHGame Casino, in a list. The same night as the splash (the
  cart's cover, art/src/cover.py): the gold CHGAME mark and a neon CASINO
  sign over the lobby's games, the list readable before anything else.

  Composition (a thumbnail in words; the menu's layout is fixed):
    rows 0-19    THE MARQUEE, a sign board lit by its own neon. Black at the
                 frame (row 0, columns 0 and 127), the board navy0 (dark at
                 its top, where nothing lights it), and on it the light,
                 every glow a falloff onto the board, never a hard outline:
                 - left, the CHGAME logo in the family's gold chrome
                   (tools/art/chglogo.py, depth 1, no shadow, at its own 72 x
                   17 pixels), its outline from x 2 and row 1, a navy1 hug
                   round its sides and foot so the black outline reads;
                 - right, CASINO as a bare neon sign, the splash's sign
                   shrunk: the letters a cream white-hot core, the tube a
                   pixel round them in the rainbow colour (#FF00FF, index 15:
                   the Rainbow menu turns it with the selection bar; the
                   Static one shows magenta), a black ring keeping it crisp
                   in every phase of the wheel, the night shut in between the
                   tubes closed with black. Round it the air it lights: an
                   even band of violet (the bays between the letters filled,
                   so its contour is one smooth line), then the tube's own
                   light blurred onto the board in flat plateaus, plum, then
                   navy1, with narrow dithered seams: a glow, not a plaque.
                   3 px of lit board between AME and the sign, 3 px to the
                   right edge (the glow fading into the frame);
                 - row 18, the marquee's neon trim (x 2-125), its light rising
                   onto the board in three flat rows (violet, plum, navy1)
                   and meeting the sign's: the foot of the board is lit. Row
                   19 black, the trim's shade;
                 - the logo's drip hangs in front of the trim: gold1 on its
                   lit left, gold0 on its right, the logo's cream bevel at
                   its root, tapering to a 1 px gold1 tip that crosses the
                   tube with no black beside it (the tube runs on round it).
    rows 20-119  THE LIST, dark and plain: a quilted panel (the booths and
                 card backs of a casino), a diamond lattice every 8 px whose
                 seams step evenly (1-1-1), each diamond one flat level of the
                 night, lit from the trim above in a band, not a cone: navy1
                 edge to edge for the first five rows of diamonds (rows
                 20-40), navy0 through the middle, black from row 108, the
                 lower corners first. Each change of level is one row of
                 diamonds in which every other diamond takes the lower level
                 (a harlequin, 16 px teeth): a soft, near-horizontal edge,
                 no shape. Every change of level sits on a seam (a seam is a
                 step below the darker diamond it parts): nothing is dithered
                 under the titles, and the brightest ground is navy1, so the
                 cream titles, the grey ones, the red chip and the rainbow
                 bar all read on it.
    rows 120-127 THE KEYS, on black: two round buttons 7 px across (rows
                 120-126, row 127 left black), as the about page draws them:
                 A red with a rose arc toward the key and a wine shade and
                 rim, B felt2 with a felt1 shade and rim (both rims show on
                 black), each letter cream; PLAY and BACK beside them in grey
                 (rows 121-125), quieter than the list.
  The eye: CHGAME and CASINO, the lit foot of the marquee, the lit top of
  the list, the rainbow bar.
  Light: the house key from the top left on the buttons and the logo; the
  neon lights the board round it and the panel under it.

  Palette (11 own + cream, grey, black, red; the rainbow colour on purpose):
    gold0 gold1 gold2            the logo's own: nothing else uses them
    navy0 navy1 plum violet      the night: the board (navy0), the neon's
                                 air in steps (violet, plum, navy1), the
                                 panel's levels (black, navy0, navy1)
    wine rose                    the A button's shade and light (red its body)
    felt1 felt2                  the B button
    fixed: cream (the neon's core, the letters on the buttons), black
    (outlines, the shade, the frame, the void), red (the A button), grey
    (the keys' words; the menu's own colour for titles of files that are
    not games). The rainbow colour: the neon CASINO and its trim, turning
    with the selection bar.

  The list's panel and the keys are tools/art/menu/listbg.py's, shared
  with the default picture (spec/assets/menu-default.png).

  Lettering: CASINO is Lanky Git Variable by 2bitcrook ("44 Game Boy
  fonts", itch.io: free for commercial work, editing encouraged), set at its
  own size with 3 px between letters so each is its own tube
  (menu_casino.txt); its round C and O, pointed A and diagonal S are the
  splash's Pee Wee shapes at a third of the size. The keys are RotorCap Neue
  Bold by David Lindecrantz (dafont: 100% free;
  tools/art/fonts/casino-menu-rotorcap.json). The CHGAME logo is the owner's.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent             # tools/sdcard/art/src
TOOLS = HERE.parents[2]                                     # the repository's tools/
for p in (TOOLS, TOOLS / "art", TOOLS / "art" / "menu", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402
import chglogo as cl  # noqa: E402
import listbg as LB  # noqa: E402   (the text menu's panel and keys, shared with the default picture)

WORD = HERE / "menu_casino.txt"
YY, XX = LB.YY, LB.XX

PAL = {**LB.PAL, **cl.GOLD}       # the night and the buttons (listbg), and the logo's own gold
NIGHT = LB.NIGHT                   # levels 0-4

LIST = LB.LIST                     # the menu's list: rows 20-119
LOGO_X, LOGO_Y, DEPTH = 3, 2, 1    # gold, no shadow: x 2-76, rows 1-17 (the drip to 18)
WORD_X, WORD_Y = 81, 6             # CASINO's core, top left (x 81-122, rows 6-13): ring x 79-124
TRIM_Y, TRIM = LB.TRIM_Y, LB.TRIM   # the marquee's neon trim

# the light on the board, a level of NIGHT (1 navy0 .. 4 violet; a fraction
# is an ordered 25/50/75% dither, in narrow seams): the trim's, row by row
# above it (1 = the row just above); the sign's: its body (tube, ring and
# the night shut between them) with its bays closed (BAYS px) and grown by
# HALO px is the violet air, an even band round the word; beyond it the
# tube's own light, blurred (GLOW: sigma sideways, up and down, gain) and
# read through GLOW_LEVELS ((light, level) stops) onto flat plateaus with
# narrow seams (GLOW_SOFT, artkit.paint.terrace): plum, navy1, the board
TRIM_GLOW = LB.TRIM_GLOW
BAYS, HALO = 3, 1
GLOW = (2.4, 3.0, 4.0)
GLOW_LEVELS = [(0.0, 1.0), (0.1, 1.0), (0.25, 2.0), (0.45, 3.0), (0.7, 4.0)]
GLOW_SOFT = 0.5
HUG = 2                            # the logo's hug (a level), on its sides and foot

def board(pic, body, logo, tube):
    """The marquee: a navy0 board in a black frame, lit by its neon: the
    trim's light rising from its foot in flat rows; round the sign an even
    band of violet air, then the tube's light falling off in plateaus of
    plum and navy1 with narrow dithered seams; a navy1 hug round the logo's
    sides and foot, so its black outline reads on the board. Then the trim
    (rainbow) and the black row of shade under it. Returns the levels."""
    head = (YY < TRIM_Y) & (YY > 0) & (XX > 0) & (XX < 127)
    lv = np.ones((128, 128))
    for k, v in TRIM_GLOW.items():
        lv = np.where(YY == TRIM_Y - k, np.maximum(lv, v), lv)
    sx, sy, gain = GLOW
    ls, vs = zip(*GLOW_LEVELS)
    lv = np.maximum(lv, ak.terrace(np.interp(LB.blur(tube, sx, sy) * gain, ls, vs), GLOW_SOFT))
    lv = np.where(ak.dilate(LB.closing(body, BAYS), HALO, diag=True), 4, lv)
    hug = ak.dilate(logo, 1, diag=True) & ~logo & ak.outside_of(logo) & (YY > LOGO_Y + 2)
    lv = np.where(hug, np.maximum(lv, HUG), lv)
    lv = np.where((YY == 1) | (XX == 1) | (XX == 126), np.floor(lv), lv)    # no dither against the frame
    pic.put(~head & (YY < TRIM_Y), "black")
    ak.by_level(pic, lv, NIGHT, head)
    pic.put(logo, "black")                                                  # (the logo covers it)
    ak.despeckle(pic, need=4, within=head & ~ak.dilate(body, 1) & ~logo)    # no lone dot on the board
    # a step of plum shut in by violet (in a bay between letters) goes violet
    v = pic.where("violet") | body
    lone = pic.where("plum") & ((ak.shift(v, 1, 0) & ak.shift(v, -1, 0)) | (ak.shift(v, 0, 1) & ak.shift(v, 0, -1)))
    pic.put(lone & head, "violet")
    pic.put(YY == TRIM_Y + 1, "black")
    pic.put((YY == TRIM_Y) & (XX >= TRIM[0]) & (XX <= TRIM[1]), "rainbow")
    return lv


def neon(pic, W):
    """CASINO as a neon sign: the letters are the white-hot core (cream), the
    tube a pixel round them (rainbow), a black ring; a pixel of night shut
    in between the tubes closed with black. Returns the sign's body (tube,
    ring and the closed night), for the light round it."""
    T = ak.dilate(W, 1)
    n = cl.neon(pic, T, core=False, ring="black", air=None)
    body = n["tube"] | n["ring"]
    shut = cl.pockets(body, 1) & ~body
    pic.put(shut, "black")
    pic.put(W, "cream")
    return body | shut


def drip(pic):
    """The logo's drip in front of the trim: lit gold1 on its left column,
    gold0 on its right, a cream glint at its root, tapering to a 1 px gold1
    tip on the tube's row with no black beside it."""
    x0 = LOGO_X + 26                         # the drip's left column (logo columns 26-27)
    y0 = LOGO_Y + 14                         # its first row (logo rows 14-16)
    # the tube runs on under it; the black row of shade under the tube
    row = (YY == TRIM_Y) & (XX >= x0 - 2) & (XX <= x0 + 3)
    pic.put(row, "rainbow")
    pic.put((YY >= TRIM_Y + 1) & (YY < LIST[0]) & (XX >= x0 - 2) & (XX <= x0 + 3), "black")
    for y in (y0, y0 + 1):
        pic.px(x0, y, "gold1")
        pic.px(x0 + 1, y, "gold0")
    pic.px(x0, y0 + 2, "gold1")              # the tip, over the tube


def draw(word=None):
    P = ak.Palette(PAL, ramps=LB.RAMPS + [cl.GOLD_RAMP])
    pic = ak.Picture.blank(P, "black")
    W = ak.place(ak.load_mask(WORD) if word is None else word, WORD_X, WORD_Y)
    T = ak.dilate(W, 1)
    body = ak.dilate(T, 1)
    body |= cl.pockets(body, 1)
    logo = cl.footprint(LOGO_X, LOGO_Y, "gold", depth=DEPTH, shadow=None)

    board(pic, body, logo, T)
    LB.panel(pic, (YY >= LIST[0]) & (YY < LIST[1]))
    LB.hints(pic, ak.Font(LB.KEYS))

    # ---- the titles last: the sign, then the logo and its drip (kept out
    # of the list's rows)
    neon(pic, W)
    keep = pic.idx[LIST[0]:].copy()
    cl.dress(pic, LOGO_X, LOGO_Y, "gold", depth=DEPTH, shadow=None)
    drip(pic)
    pic.idx[LIST[0]:] = keep
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), TOOLS / "sdcard" / "menu.png"))
