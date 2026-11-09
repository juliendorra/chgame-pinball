"""What the text menu's pictures share (docs/menu-image.md): the list's
ground, a quilted panel of diamonds lit from the header above and falling
into the night, and the keys at the foot (A PLAY, B BACK). The default
picture (menu.py: spec/assets/menu-default.png) and the casino card's
(tools/sdcard/art/src/menu.py) are drawn with it; each paints its own
header in rows 0-19.

    import listbg as LB
    P = ak.Palette({**LB.PAL, ...the header's own...}, ramps=LB.RAMPS + [...])
    pic = ak.Picture.blank(P, "black")
    ...the header (rows 0-19)...
    LB.panel(pic, (LB.YY >= LB.LIST[0]) & (LB.YY < LB.LIST[1]))
    LB.hints(pic, ak.Font(LB.KEYS))
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

KEYS = TOOLS / "art" / "fonts" / "casino-menu-rotorcap.json"   # RotorCap Neue Bold (dafont: 100% free)
YY, XX = np.mgrid[0:128, 0:128]

PAL = {
    "navy0": "#0A0C26", "navy1": "#1C1E52", "plum": "#302066", "violet": "#46267A",   # the night
    "wine": "#640E22", "rose": "#F2644A",                                            # A, the red button
    "felt1": "#0C5A34", "felt2": "#2EA45A",                                          # B, the green button
}
NIGHT = ["black", "navy0", "navy1", "plum", "violet"]      # levels 0-4
RAMPS = [NIGHT, ["black", "wine", "red", "rose", "cream"], ["black", "felt1", "felt2", "cream"],
         ["black", "grey", "cream"]]

LIST = (20, 120)                   # the menu's list: rows 20-119
TRIM_Y, TRIM = LIST[0] - 2, (2, 125)   # the header's neon trim
TRIM_GLOW = {1: 4, 2: 3, 3: 2}     # the trim's light on the board, row by row above it (1 = the row just above)

QUILT = 8                          # the panel's diamonds: a seam every QUILT px
# the panel's light by a diamond's middle row: (row, level) stops, a level 0
# (black) to 2 (navy1); toward the foot it falls by up to FALL_X at the sides
PANEL = [(20, 2.0), (36, 2.0), (40, 1.5), (44, 1.0), (100, 1.0), (104, 0.5), (108, 0.0)]
FALL_X = 0.5

# the buttons, 7 x 7 (as the about page draws them: A red, B green, the
# letter cream): 'h' the key's light on its shoulder, 'b' its body, 'd' its
# shade and rim, 'c' the letter
BUTTON = {
    "A": ["..hhb..",
          ".hbcbb.",
          "hbcbcbd",
          "hbcccbd",
          "bbcbcbd",
          ".bcbcd.",
          "..ddd.."],
    "B": ["..bhb..",
          ".hccbb.",
          "bbcbcbd",
          "bbccbbd",
          "bbcbcbd",
          ".bccbd.",
          "..ddd.."],
}
BUTTON_COLS = {"A": {"h": "rose", "b": "red", "d": "wine", "c": "cream"},
               "B": {"h": "felt2", "b": "felt2", "d": "felt1", "c": "cream"}}
HINTS = [("A", "PLAY"), ("B", "BACK")]
HINT_Y = 120
HINT_GAP = 12                      # px between the PLAY pair and the BACK pair


def closing(M, n):
    """M with its bays and gaps up to 2n px filled (kept off the picture's edge)."""
    if not n:
        return M
    k = n + 1
    Mp = np.pad(M, k)                                  # room round it, so the edge closes nothing
    return ak.erode(ak.dilate(Mp, n, diag=True), n, diag=True)[k:-k, k:-k]


def blur(M, sx, sy):
    """A mask blurred (a separable Gaussian): the light a tube throws."""
    def k(sg):
        r = int(np.ceil(3 * sg))
        t = np.arange(-r, r + 1)
        g = np.exp(-t * t / (2 * sg * sg))
        return g / g.sum()
    a = M.astype(float)
    a = np.apply_along_axis(lambda v: np.convolve(v, k(sx), "same"), 1, a)
    return np.apply_along_axis(lambda v: np.convolve(v, k(sy), "same"), 0, a)


def panel(pic, where):
    """The list's ground: a quilted panel, each diamond one flat level of the
    night, lit from the header above in a band: the light falls off
    downward in whole diamonds, each change of level one row in which every
    other diamond takes the lower level (a harlequin), so every change sits
    on a seam and nothing is dithered under the titles. A seam is the shade
    between two diamonds, a step below the darker one."""
    P = QUILT
    a, b = XX + YY, XX - YY
    i, j = np.floor(a / P).astype(int), np.floor(b / P).astype(int)
    xc, yc = ((i + 0.5) * P + (j + 0.5) * P) / 2, ((i + 0.5) * P - (j + 0.5) * P) / 2
    ys, vs = zip(*PANEL)
    v = np.interp(yc, ys, vs) - FALL_X * np.clip((yc - 88) / 20.0, 0, 1) * ((xc - 63.5) / 64.0) ** 4
    th = np.where(i % 2 == 0, 0.25, 0.75)              # a half step: every other diamond along the row
    lvl = np.clip(np.floor(v) + ((v - np.floor(v)) >= th), 0, 2).astype(int)
    seam = ((XX + YY) % P == 0) | ((XX - YY) % P == 0)
    big = np.where(seam, 99, lvl)
    lo = big.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        lo = np.minimum(lo, np.roll(np.roll(big, dy, 0), dx, 1))
    lvl = np.where(seam, np.clip(lo - 1, 0, 2), lvl)
    for k, nm in enumerate(NIGHT[:3]):
        pic.put(where & (lvl == k), nm)
    return lvl


def hints(pic, F):
    """The keys at the foot: a round button and its word, the pairs centred."""
    items = [(key, word, F.mask(word)) for key, word in HINTS]
    bw = len(BUTTON["A"][0])
    total = sum(bw + 3 + m.shape[1] for _, _, m in items) + HINT_GAP * (len(items) - 1)
    x = (128 - total) // 2
    for key, word, m in items:
        cols = BUTTON_COLS[key]
        for j, row in enumerate(BUTTON[key]):
            for i, ch in enumerate(row):
                if ch != ".":
                    pic.px(x + i, HINT_Y + j, cols[ch])
        x += bw + 3
        F.text(pic, word, x, HINT_Y + 1, "grey")
        x += m.shape[1] + HINT_GAP


def trim_levels():
    """The trim's light on the header board, as levels of NIGHT (1 the board)."""
    lv = np.ones((128, 128))
    for k, v in TRIM_GLOW.items():
        lv = np.where(YY == TRIM_Y - k, np.maximum(lv, v), lv)
    return lv
