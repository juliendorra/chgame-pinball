"""spec/assets/menu-default.png: the text menu's DEFAULT picture, the
background the list menu bootloader draws its list over when a cart brings
none of its own (docs/menu-image.md, docs/cover-art.md). tools/menuart.py
draws it from draw(); edit this, not the PNG. (`chgame background
--template` hands it out as the starting point for a picture of one's own.)

THE BRIEF (the owner's: the casino's text menu made generic)
  Message: CHGame, a list of games. The casino card's text menu
  (tools/sdcard/art/src/menu.py) without the casino: its quilted panel and
  its keys, and in the header the CHGAME logo alone, flat in the rainbow
  colour and centred, as the menu has always shown it.

  The layout is the menu's own (docs/menu-image.md):
    rows 0-19    the header: a dark board in a black frame, lit from below
                 by a rule in the rainbow colour on row 18 (#FF00FF, index
                 15: the Rainbow menu turns it with the selection bar, the
                 Static one shows magenta), its light rising onto the board
                 in three flat rows (violet, plum, navy1); on it the CHGAME
                 logo, centred, flat rainbow with a black outline (the
                 owner's logo at its own 72 x 17 pixels, rows 1-17), its drip
                 touching the rule; row 19 black.
    rows 20-119  the list: the quilted panel, dark and plain (listbg.py).
    rows 120-127 the keys: A PLAY, B BACK (listbg.py).

  Palette: listbg's eight (the night, the A and B buttons) and the fixed
  four; the rainbow colour for the logo and the rule.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent             # tools/art/menu
TOOLS = HERE.parents[1]                                     # the repository's tools/
for p in (TOOLS, TOOLS / "art", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import artkit as ak  # noqa: E402
import chglogo as cl  # noqa: E402
import listbg as LB  # noqa: E402

OUT = TOOLS.parent / "spec" / "assets" / "menu-default.png"
YY, XX = LB.YY, LB.XX
LOGO_Y = 1                                    # the logo's rows 1-17: its drip touches the rule on row 18


def draw():
    P = ak.Palette(LB.PAL, ramps=LB.RAMPS)
    pic = ak.Picture.blank(P, "black")
    # ---- the header: the board lit by the rule under it
    head = (YY < LB.TRIM_Y) & (YY > 0) & (XX > 0) & (XX < 127)
    ak.by_level(pic, LB.trim_levels(), LB.NIGHT, head)
    pic.put((YY == LB.TRIM_Y) & (XX >= LB.TRIM[0]) & (XX <= LB.TRIM[1]), "rainbow")
    # ---- the logo: flat rainbow, centred, a black outline (the rule runs on under its drip)
    cl.dress(pic, cl.centred(), LOGO_Y, "plain", shadow=None)
    pic.put((YY == LB.TRIM_Y) & (XX >= LB.TRIM[0]) & (XX <= LB.TRIM[1]), "rainbow")
    pic.put(YY == LB.TRIM_Y + 1, "black")
    # ---- the list's panel and the keys
    LB.panel(pic, (YY >= LB.LIST[0]) & (YY < LB.LIST[1]))
    LB.hints(pic, ak.Font(LB.KEYS))
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), OUT))
