"""spec/assets/system/game.png: the menu's NO PICTURE screen, shown for a
game on the card that has no picture of its own (docs/visual-menu.md; A
plays it). tools/menuart.py draws it from draw(); edit this, not the PNG
(docs/cover-art.md).

THE BRIEF (revision 2, the owner's: generic, a question mark, no words)
  Message: a game is here, its picture isn't: a mystery, not an error. It is
  shared by every cart, so nothing here is the casino's: it is the default
  cover's scene (tools/art/menu/sdscene.py) with a question mark rising out
  of the console's slot where the cover raises its SD card. No title, no
  subtitle, no key hint: the picture says it.

  Composition: the night and the burst of rays out of the slot, its sheet
  of light rising to the hero, sparks, stars, the dark frame, all as on the
  default cover. The hero: a big question mark (about 50 x 76 px), leaning
  with the card's lean (one pixel in eight, top to the right: it is turning
  as it rises), its face flat in the rainbow colour (#FF00FF, index 15: the
  Rainbow menu turns it through the colour wheel, the Static one shows
  magenta), the colour the console's own marks wear (the CHGAME logo on the
  default cover). It is a solid thing, in the card's material: the face sits
  on black gloss that shows as its thickness to the left and below (lit by
  the key at the top, steel, falling through grey and navy to the slot's
  violet, its foot ice in the slot's light), a black outline round it, a
  cream glint where the key catches the hook's shoulder.

  Palette: sdscene's eight (the night, the slot's light, the metal, the
  label's reds) and the fixed four; the rainbow is the hero's alone.
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
import sdscene as S  # noqa: E402

OUT = TOOLS.parent / "spec" / "assets" / "system" / "game.png"
YY, XX = S.YY, S.XX

# the question mark: its hook round a circle (centre, radius of the stroke's middle), from the lower
# left over the top to the right (degrees, y down), then a curve down into the stem; the stroke's
# half width; the dot (centre, radius); the lean's pivot (the dot's foot stays put)
HOOK_C, HOOK_R = (63.0, 41.0), 17.0
HOOK_A = (156.0, 398.0)
STEM = [(64.0, 63.0), (63.0, 68.0), (63.0, 71.0)]
HALF = 6.6
DOT_C, DOT_R = (63.0, 89.5), 6.8
PIVOT_Y = 96.0
THICK = [(-1, 0), (-2, 1), (-3, 1), (-4, 2)]   # the card's thickness: the left side and the foot show
GLINT = (52, 30)                                # where the key catches the hook's shoulder


def question():
    """The question mark's face on the picture (a bool mask), leaned."""
    cv = ak.Canvas()
    X, Y = cv.P
    Xs = X - (PIVOT_Y - Y) * S.LEAN                          # lean: the top to the right
    a = np.radians(np.linspace(HOOK_A[0], HOOK_A[1], 64))
    hook = [(HOOK_C[0] + HOOK_R * np.cos(t), HOOK_C[1] + HOOK_R * np.sin(t)) for t in a]
    end = hook[-1]
    tail = ak.bezier(end, (end[0] - 2.0, end[1] + 6.0), STEM[0], n=12)[1:] + STEM[1:]
    d = ak.polyline((Xs, Y), hook + tail, HALF)
    d = np.minimum(d, ak.circle((Xs, Y), DOT_C[0], DOT_C[1], DOT_R))
    return ak.px_mean((d < 0).astype(np.float32), cv.s) >= 0.5


def draw():
    P = ak.Palette(S.PAL, ramps=S.RAMPS)
    pic = ak.Picture.blank(P, "navy0")
    keep = np.zeros((128, 128), bool)
    F = question()
    body = F.copy()
    for dx, dy in THICK:
        body |= ak.shift(F, dx, dy)
    S.stage(pic, body, keep, sheet_top=int(np.nonzero(F[:, 63])[0].max()) - 14)   # the light rises to the dot

    # ---- the question mark: black gloss under a flat rainbow face
    pic.put(ak.dilate(body, 1) & ~body, "black")
    pic.put(body, "black")
    side = body & ~F
    foot = side & (ak.shift(F, 0, 1) | ak.shift(F, 0, 2))      # the faces turned down: the slot's light
    ys = np.nonzero(F.any(axis=1))[0]
    t0 = ys.min()
    for (a, b), c in (((0, 18), "steel"), ((18, 36), "grey"), ((36, 54), "navy1"), ((54, 99), "violet")):
        pic.put(side & ~foot & (YY >= t0 + a) & (YY < t0 + b), c)
    pic.put(foot & (YY < t0 + 40), "navy1")
    pic.put(foot & (YY >= t0 + 40), "ice")
    pic.put(F, "rainbow")
    ak.glint(pic, GLINT[0], GLINT[1], arms=(2, 2, 2, 2), tip="steel")
    keep[GLINT[1] - 3:GLINT[1] + 4, GLINT[0] - 3:GLINT[0] + 4] = True

    S.finish(pic, body, keep)
    S.frame(pic)
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), OUT))
