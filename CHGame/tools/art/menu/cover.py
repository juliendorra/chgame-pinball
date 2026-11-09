"""spec/assets/cover-default.png: the default cover, the splash a card
shows when its cart brings no cover of its own (docs/visual-menu.md: the
cart's cover, the top level's first picture). tools/menuart.py draws it from
draw(); edit this, not the PNG (docs/cover-art.md).

THE BRIEF
  Message: CHGame. The games are on the SD card. Any cart, anyone's games:
  so nothing here is the casino's, only the console's own mark and the
  family's night. (Revision 2, the owner's: no subtitle; the logo lower,
  flat in the rainbow colour as the menu has always shown it.) The card is the hero, caught the instant it comes alive:
  it shoots up out of the console's slot on a burst of light, like the
  power-up on a 16-bit box.

  Composition (a thumbnail in words):
  - Top band: the CHGAME logo flat in the rainbow colour (#FF00FF, index
    15: the Rainbow menu turns it through the colour wheel, the Static one
    shows magenta), a black outline keeping it crisp in every phase
    (tools/art/chglogo.py's plain style, at its own 72 x 17 pixels, the
    first read), set low in the band so it sits close over the card, on
    calm flat navy; two star glints in the top corners. Nothing bright above
    row 42.
  - Middle: the SD card, big (about 50 x 62 px with its sides), leaning 7
    degrees (one pixel in eight, top to the right: it is turning as it
    rises), seen from a low camera so its left side and its foot show. It is
    drawn upright in its own pixels and leaned by two whole-pixel shears
    (Lean): no pixel doubled or lost, every straight edge stepping evenly
    every eight, the steps placed between the print's parts (the D-pad, the
    pills, the buttons and the SD mark are each whole). Its corner cut
    off on a clean 45-degree line. Black gloss plastic, the darkest, most
    contrasty shape: the key lights its left side (steel at the top, a
    lock slider's groove with a cream tab, grey, navy, violet where the
    slot's light reaches) and its top bevel (grey, steel near the key's
    corner, a cream glint on that corner); the face's left bevel a step
    lighter than the side all the way down, so the corner reads; the cut
    grey; the far edge dark at the top, then violet (the burst behind it),
    azure near the slot;
    the foot ice, lit from below. A 45-degree gloss band (navy1, three
    pixels and one) across the grip. The SD mark in silver print (a cream
    top over steel, a navy shadow). The label: red, a rose sheen toward the
    key and wine falling into the far corner, both curved (arcs about a
    point off its top-left corner, hard edges). Printed on it a cream
    gamepad (30 x 12) on the label's own plane: a chunky wine D-pad, grey
    pills, two round red buttons, a steel underside, a wine shadow down and
    right on the label: the games.
  - Behind it the burst: four rays a side fanning out of the slot, narrow
    there and widening to the corners, azure near the slot, violet, then
    navy: flat bands with a short dithered seam (two pixels, 25/50/75%) at
    each step, every side a whole-ratio slope (3:4, 1:1, 4:3, 2:1, 5:2,
    7:2, 5:1, 8:1) so it steps evenly; dark navy between them and above the
    card's shoulders; the corners falling to black on a clean curve. A splash of light out of each end of the slot: two tapered
    streaks curling out, azure to ice to a cream head, their heads in the
    dark between the rays. Sparks and two-pixel motes.
  - Bottom: the console's top, dark gloss: its far edge a clean line
    behind the light (azure in the middle, violet, navy), the burst
    reflected in it as dim wedges spreading toward us, a pool of light round
    the slot. The slot (the card's width) in a black recess with slanted
    ends and an azure near lip: an ice lip, one cream row, azure. A sheet
    of light rises from it to the card's foot: an azure dome over the
    slot's middle, violet at its sides, so the ice foot shows against it.
    The hot core sits above the install bar.
  - The eye: the logo, down to the card (the cream gamepad on
    red: the strongest contrast under the titles), down its light to the
    slot, and out along the rays.

  Palette (8 own + cream, grey, black, red, and the rainbow: the logo's alone):
    navy0 navy1 violet  the night (the family's), the rays as they fade, the
                        floor, the card's gloss and far edge
    azure ice           the slot's light: the rays near it, the sheet, the
                        splash, the card's foot, sparks
    steel               the card's lit side and bevels, the mark
    wine rose           the label's shade and sheen (red itself is fixed)
    fixed: cream (the slot's core, the gamepad, glints, heads), red (the
    label, the buttons), grey (the bevels, the side, the pills, dim stars),
    black (the card, outlines, the recess, the void, the logo's outline)

  The scene (the night, the rays, the console's slot and its light, the
  sparks and stars) is tools/art/menu/sdscene.py, which the no-picture and
  folder screens share; the card is its hero, sdscene.card().

  How it is painted: no quantiser. The card is a flat drawing in its own
  pixels leaned onto the picture (Lean); its edges are its own rows and
  columns (so a step in one edge never takes another's colour); the sides
  are the face swept along its thickness. The sky, the floor and the label
  are painted as levels on their ramps (hard steps; two-pixel seams on the
  rays); the lines are clean
  one-pixel rasters; lone pixels are cleaned (the stars, glints, motes,
  sparks and streaks kept); the logo goes on last, and the outer two pixels
  all round step down (the outermost twice), so the menu's border frames a
  dark edge.

  Lettering: none but the CHGAME logo, the owner's.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent             # tools/art/menu
TOOLS = HERE.parents[1]                                     # the repository's tools/
for p in (TOOLS, TOOLS / "art", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402
import chglogo as cl  # noqa: E402
import sdscene as S  # noqa: E402

OUT = TOOLS.parent / "spec" / "assets" / "cover-default.png"
LOGO_Y = 13                                   # the logo's top row: low in the band, close over the card


def draw():
    P = ak.Palette(S.PAL, ramps=S.RAMPS)
    pic = ak.Picture.blank(P, "navy0")
    keep = np.zeros((128, 128), bool)                         # deliberate lone pixels
    c = S.card()                                              # the card's shape first: all else round it
    S.stage(pic, c["body"], keep)
    S.paint_card(pic, c, keep)
    S.finish(pic, c["body"], keep)
    # ---- the logo: flat rainbow on calm navy, a black outline round it
    logo = cl.footprint(cl.centred(), LOGO_Y, "plain", shadow=None)
    S.calm_title(pic, logo, c["body"], keep)
    cl.dress(pic, cl.centred(), LOGO_Y, "plain", shadow=None)
    S.frame(pic)
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), OUT))
