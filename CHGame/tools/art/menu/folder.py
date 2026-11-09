"""spec/assets/system/folder.png: the menu's default FOLDER screen, shown for
a folder on the card that has no cover of its own (docs/visual-menu.md; A
opens it). tools/menuart.py draws it from draw(); edit this, not the PNG
(docs/cover-art.md).

THE BRIEF (revision 2, the owner's: the default cover's look, generic, the
title FOLDER and nothing else in words)
  Message: a folder: open it to see what's inside. It is shared by every
  cart, so nothing here is the casino's: it is the default cover's scene
  (tools/art/menu/sdscene.py) with a folder rising out of the console's
  slot where the cover raises its SD card, and FOLDER where the cover has
  the CHGAME logo, in the same dress.

  Composition: the night, the burst of rays out of the slot, its light
  rising to the hero, sparks, stars and the dark frame, as on the default
  cover. The hero: a manila folder (about 62 x 50 px), leaning with the
  card's lean (one pixel in eight, top to the right), a sheet of paper
  standing out of it (cream, its lines of print in grey), the front flap
  with a thumb notch, lit by the key from the top left (manila2 along its
  top and left edges, manila1 the face, manila0 toward the lower right and
  its crease), its foot in the slot's light (azure), its card-thin side
  showing to the left, a black outline, a cream glint on the flap's corner.
  The title: FOLDER flat in the rainbow colour (#FF00FF, index 15: the
  Rainbow menu turns it through the colour wheel, the Static one shows
  magenta) with a black outline, low in the top band like the cover's logo.

  Palette: sdscene's eight and the folder's own manila0 manila1 manila2;
  the fixed four; the rainbow is the title's alone.

  Lettering: DyslexicPixel by ladyliefy (free for commercial use,
  https://ladyliefy.itch.io/dyslexic-lief), at its own size: folder_title.txt.
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

OUT = TOOLS.parent / "spec" / "assets" / "system" / "folder.png"
TITLE = HERE / "folder_title.txt"
TITLE_Y = 13                                  # as the cover's logo
YY, XX = S.YY, S.XX
MANILA = {"manila0": "#8A5418", "manila1": "#DCA24A", "manila2": "#F8D88A"}

# the folder, drawn upright in its own pixels (local x, y), then leaned like the card
FW, FH = 62, 50
FTOP, FX = 42, 64                             # its top row and middle on the picture
TAB = 8                                       # the tab's height (the back panel starts below it)
FRONT = 15                                    # the front flap's top row
NOTCH = (24, 38, 4)                           # the flap's thumb notch: from, to (x), depth
PAPER = (6, 3, 54, 21)                        # the sheet of paper: x0, y0, x1, y1 (exclusive)
LINES = [(10, 7, 36), (10, 10, 46), (10, 13, 30)]   # its print: x0, y, x1
CREASE = FH - 6                               # the flap's crease near its foot
THICK = [(-1, 0), (-2, 1)]                    # its side: card thin


def folder_local():
    """The folder's parts on its own pixels: name -> bool (FH, FW)."""
    y, x = np.mgrid[0:FH, 0:FW]
    back = (y >= TAB) & (x < FW)
    tab = (y < TAB + 1) & (x >= (y == 0) * 2 + (y == 1) * 1) & (x <= 21 + y)
    paper = (x >= PAPER[0]) & (x < PAPER[2]) & (y >= PAPER[1]) & (y < PAPER[3])
    notch = (x >= NOTCH[0]) & (x < NOTCH[1]) & (y < FRONT + NOTCH[2])
    notch &= ((x - (NOTCH[0] + NOTCH[1] - 1) / 2) / ((NOTCH[1] - NOTCH[0]) / 2)) ** 2 + ((y - FRONT) / NOTCH[2]) ** 2 < 1.0
    front = (y >= FRONT) & ~notch
    return dict(back=back | tab, tab=tab & ~back, paper=paper, front=front, notch=notch)


def draw():
    P = ak.Palette({**S.PAL, **MANILA}, ramps=S.RAMPS + [["black", "manila0", "manila1", "manila2", "cream"]])
    pic = ak.Picture.blank(P, "navy0")
    keep = np.zeros((128, 128), bool)

    parts = folder_local()
    L = S.Lean(FW, FH, FTOP, FX, S.LEAN, FRONT, (NOTCH[0] + NOTCH[1]) // 2)
    on = {k: L.mask(v) for k, v in parts.items()}
    F = on["back"] | on["front"] | on["paper"]
    body = F.copy()
    for dx, dy in THICK:
        body |= ak.shift(F, dx, dy)
    S.stage(pic, body, keep)

    # ---- the folder
    pic.put(ak.dilate(body, 1) & ~body, "black")
    pic.put(body, "black")
    side = body & ~F
    pic.put(side, "manila0")
    pic.put(side & (YY > FTOP + FH - 12), "violet")
    # the back panel and its tab, in the folder's shade; the tab's top lit
    pic.put(on["back"], "manila0")
    pic.put(on["back"] & ~ak.shift(on["back"], 0, 1), "manila1")
    # the paper: cream, its far edge grey, its print
    pic.put(on["paper"], "cream")
    pic.put(on["paper"] & ~ak.shift(on["paper"], -1, 0), "grey")
    for x0, y0, x1 in LINES:
        ln = np.zeros((FH, FW), bool)
        ln[y0, x0:x1] = True
        pic.put(L.mask(ln) & on["paper"], "grey")
    # the front flap: lit from the top left, falling to the lower right; its crease; its foot in the slot's light
    fr = on["front"]
    # the key's light: manila2 near the top-left corner, manila1 across the
    # face, manila0 toward the lower right; flat bands, short dithered seams
    i, j = np.meshgrid(np.arange(FW), np.arange(FH))
    t = np.hypot(i / FW, (j - FRONT) / (FH - FRONT) * 0.8)
    lv = 3.0 - np.clip((t - 0.28) / 0.08, 0, 1) - np.clip((t - 0.86) / 0.1, 0, 1)
    lv_on = np.zeros((128, 128))
    sel = L.ok & parts["front"]
    lv_on[L.y[sel], L.x[sel]] = lv[sel]
    ak.by_level(pic, lv_on, ["black", "manila0", "manila1", "manila2"], fr)
    top = fr & ~ak.shift(fr, 0, 1)
    left = fr & ~ak.shift(fr, 1, 0)
    pic.put(top | left, "manila2")
    cr = np.zeros((FH, FW), bool)
    cr[CREASE, 2:FW - 2] = True
    pic.put(L.mask(cr) & fr, "manila0")
    bottom = fr & ~ak.shift(fr, 0, -1)
    pic.put(bottom, "azure")
    right = fr & ~ak.shift(fr, -1, 0)
    pic.put(right & ~bottom, "manila0")
    gx, gy = L.at(1, FRONT + 1)
    ak.glint(pic, gx, gy, arms=(2, 2, 2, 2), tip="manila2")
    keep[gy - 3:gy + 4, gx - 3:gx + 4] = True

    S.finish(pic, body, keep)

    # ---- the title: FOLDER flat in the rainbow colour, a black outline
    m = ak.load_mask(TITLE)
    M = ak.place(m, (128 - m.shape[1]) // 2, TITLE_Y)
    ring = ak.dilate(M, 1, diag=True) & ~M
    S.calm_title(pic, M | ring, body, keep)
    pic.put(ring, "black")
    pic.put(M, "rainbow")
    S.frame(pic, dict(S.DARKER, manila2="manila1", manila1="manila0", manila0="black"))
    return pic.image()


if __name__ == "__main__":
    import boxart
    print(boxart.save(draw(), OUT))
