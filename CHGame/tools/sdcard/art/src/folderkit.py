"""folderkit: the casino card's genre folders, one family (docs/cover-art.md).

A folder's cover is a sign over a door: its word, big, lit like a casino's
neon sign, over the one object that says what is inside, on the casino at
night. A folder must never pass for a game (the games are on felt), and
every folder must plainly belong with the others. This module is the
family's shared look; each folder's recipe (tools/sdcard/art/src/<name>.py)
paints its own object between the two calls that make it a folder:

    import pathlib, sys
    HERE = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(HERE))
    import folderkit as fk                 # puts the repository's tools/ on sys.path
    import artkit as ak

    def draw():
        P = fk.palette({"bone0": "#...", "bone1": "#...", ...})   # up to 5 own colours
        pic = ak.Picture.blank(P, "navy0")
        fk.put_sky(pic)                    # the night (fk.LOOK's defaults, or your own look=)
        ...paint the object (below fk.OBJECT_TOP), light from the top left...
        fk.word(pic, "dice")               # the sign: word_dice.txt, at fk.WORD_Y
        return pic.image()

  An object painted on an artkit Canvas instead: fk.sky(cv, P, **look) first
  (its edges then blend into the night), cv.quantize(P, exclude=fk.EXCLUDE),
  then fk.put_sky(pic, pic.obj("background"), **look) to lay the night back
  as clean levels. Surfaces come out cleanest painted pixel by pixel as
  levels on a ramp (ak.by_level with fk.terrace_px: flat bands, seams a
  pixel or two wide whatever the gradient); cards.py beside this file is a
  worked example: a hand of cards painted from their geometry (rounded
  corners, gilt edges, a card back's lattice of even 1-px lines, hand-turned
  index glyphs), a hero card turned out of the picture's plane and seen in
  perspective (a homography), a flash on its corner, a sunburst behind it
  (rays, ray_width, ray_top) and the hand's shadow on the backdrop
  (put_sky's shadow=).

  The words: word_cards, word_casino, word_dice, word_board, word_tiles,
  word_words and word_apps.txt, all BAZAR at its own size, letters 2 px
  apart, widths 54-93 px. Each folder's painter may touch its own word's
  pixels up by hand (WORDS' W already has thicker feet: its 1-px spikes
  broke up under the outline). BAZAR is from the bmf collection, terms
  "freeware; authors vary, few gave terms" (a `?` face, for the credits in
  docs/cover-art.md): no clear-terms face sets all seven words this tall
  and bold within 120 px.

THE LOOK
- The night. navy0 behind the sign, a glow of navy1 and navy2 behind the
  object (`centre`, `glow`; by default a broad dome rising from below the
  frame, the casino's light on the night), falling to black at the frame
  (a vignette a few pixels deep, in flat steps: the frame stays dark). Optionally a
  stage floor with a pool of light under the object (`floor`), a
  spotlight beam slanting in from the top left (`beam`: lighter toward its
  source, soft sides), a sunburst behind the object (`rays`). Everything
  is painted as levels on NIGHT_R, flat plateaus with seams a pixel or two
  wide (terrace_px), never wide 50% bands.
- The sign. The word, in BAZAR (a tall condensed marquee face, 35 px; one
  face for every folder word; word_<name>.txt here, set by the font scout),
  centred at the top (fk.WORD_Y = 6). Its face is ice chrome: ice2 sky,
  ice1, a 2-px ice0 horizon, ice1, ice2 ground; a cream bevel on the edges
  facing the key, ice0 on the others; a 3-px extrusion in navy2 and navy1;
  a black outline and drop shadow; a cream glint inside a letter's face.
  Round it, the sign's frame: a navy1 panel, a rectangle with its corners
  cut on even 1-1 steps, a pixel clear of the lettering; on its edge a
  1-px neon tube in the rainbow colour (#FF00FF: on the Rainbow bootloader
  it turns through the colour wheel, so every folder's sign is a living
  neon sign; magenta on the Static one); outside it the tube's glow, a ring
  of the rainbow colour on a 50% checker (so the glow turns with the
  tube), then navy1. The sign spans rows 1 to 48 (fk.OBJECT_TOP is 49),
  its tube on row 3, so rows 0-1 stay dark for the installed border;
  keep everything busy below that.
- The light. The house key from the top left, a warm spotlight on a cool
  night: the object's lit edges up and left (cream at the hottest), cast
  shadows down and right, a cream glint where it catches the lamp. Shadows
  fall to cool colours (a slate, navy2, navy1), not to black: the night
  air. Black is for outlines on the shadow side (fk.selout) and the
  deepest cracks; the lit side needs none against the night.
- THE FAMILY'S COLOUR RULE: the objects are warm, the sign alone is
  cool-bright. The sign owns the pale blues (ice) and the night owns the
  navies; an object's lit faces are warm (ivory, bone, gold, wine, felt,
  wood) and only its cast shadows go cool. Dice, dominoes, tiles, letter
  tiles and chessmen are all pale things: paint them on a warm ivory ramp
  (cream, a bone, a warm tan-grey), never on a lavender or ice-grey one, or
  the object takes the sign's colour and the whole picture goes blue.
  Bring in a casino accent (wine, gold, felt green) where it helps.
- The palette: 11 own colours, 6 of them the family's.
    navy0 navy1 navy2   the night (with black): sky, glow, the sign's panel
                        and extrusion, the far shadows. Use them freely.
    ice0 ice1 ice2      the sign's own (with cream): NOTHING else uses them
                        (quantise with exclude=fk.EXCLUDE).
    + 5 of your own     the object's colours (CARDS: card0 card1 the warm
                        stock, slate the cool shadow, wine, gold). Cream,
                        grey, black and red are free as ever.
  The rainbow colour is the sign's neon; nothing else in a folder uses it.

THE API
    palette(own, ramps=(), pairs=())        the family's 6 + yours (5 at most), with NIGHT_R and
                                            ICE_R as ramps
    LOOK                                    the default night: dict(centre, glow, floor, beam, rays...)
    sky_level(X, Y, **look)                 the night as a float level on NIGHT_R at points X, Y
    put_sky(pic, where=None, shadow=None, **look)
                                            paints it on the pixels (where: a mask; everywhere if None;
                                            shadow: a mask where the object's shadow falls on the
                                            backdrop: a level darker, flat)
    sky(cv, P, **look)                      paints it in true colour on an artkit Canvas (for objects
                                            painted on a canvas and quantised: edges blend into it)
    terrace_px(lv, px=1.5)                  ak.terrace with seams `px` pixels wide wherever the level
                                            changes slowly or fast (for by_level)
    edge_dark(X, Y)                         the vignette's darkening (levels) at X, Y: take it off an
                                            object's own levels where it runs off the frame
    word(pic, name_or_mask, y=WORD_Y, ...)  the sign; returns {'face', 'all' (the lettering's
                                            footprint), 'panel', 'halo' (everything the sign drew)}
    word_mask(name)                         a folder word's mask (word_<name>.txt)
    skyline(pic, base, tops, seed, near, windows, where, look)
                                            the Strip's towers in silhouette behind the object, one or
                                            two rows a level or two darker than the night (paint it
                                            after put_sky); returns their mask
    twinkle(pic, x, y, arm="grey", size=1)  a small four-pointed star: cream core, `arm` arms
    selout(pic, m, dark, light=None)        a selective outline: `dark` on the ring pixels facing down
                                            and right, chosen by the shape's smoothed normal, so the
                                            step corners of a slanted edge go with it and the line has
                                            no gaps (ak.selout, now fixed, picks by the neighbours
                                            above and left; either suits a folder)
    WORD_Y, OBJECT_TOP, EXCLUDE, NIGHT_R, ICE_R, NIGHT, ICE

look= keys (all optional; LOOK holds the defaults):
    centre=(x, y), glow=(rx, ry)    the glow behind the object: where, how wide
    floor=y or None                 a stage floor from row y down: darker than the backdrop, a pool
                                    of light under `centre` (pool=(rx, ry) its radii)
    beam=((sx, sy), (tx, ty), half_angle, strength)
                                    a spotlight beam from (sx, sy) (off the frame, up left) to
                                    (tx, ty), widening at half_angle degrees, brightest at its source
    rays=n, ray_reach=(r0, r1), ray_k, spin, ray_width, ray_top
                                    a sunburst of n rays round `centre`, from r0 to r1 px, ray_k
                                    levels bright, turned `spin` degrees; ray_width the share of
                                    the turn each ray fills (0.5: rays as wide as the gaps);
                                    ray_top a row: the rays fade out above it (clear of the sign)
    blooms=[(x, y, r, k)]           light caught in the air round a bright point (a flash, a
                                    glint): k levels at its middle, fading out at r px
    top                             the level behind the word (0.95: navy0)
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parents[2]                                   # the repository's tools/
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import numpy as np  # noqa: E402
import artkit as ak  # noqa: E402

NIGHT = {"navy0": "#060B22", "navy1": "#0D1B4A", "navy2": "#1B3779"}
ICE = {"ice0": "#2A62C4", "ice1": "#7EC4F6", "ice2": "#D6F0FF"}
NIGHT_R = ["black", "navy0", "navy1", "navy2"]
ICE_R = ["ice0", "ice1", "ice2", "cream"]
EXCLUDE = list(ICE)                                       # the sign's own: quantise with exclude=EXCLUDE
WORD_COLOURS = EXCLUDE
WORD_Y = 6                                                # the word's top row (its neon tube is on row 3)
OBJECT_TOP = 49                                           # the sign's glow ends above this row
YY, XX = np.mgrid[0:128, 0:128]

LOOK = dict(centre=(64, 132), glow=(100, 84), floor=None, pool=(54, 14), beam=None, rays=0,
            ray_reach=(24, 84), ray_k=0.7, spin=0.0, ray_width=0.5, ray_top=None, top=0.95, blooms=())


def palette(own, ramps=(), pairs=()):
    """The family's six colours and the folder's own (5 at most), named;
    NIGHT_R and ICE_R are ramps (neighbours may dither), plus yours."""
    if len(own) > 5:
        raise ValueError(f"{len(own)} colours of the folder's own; 5 at most")
    return ak.Palette({**NIGHT, **ICE, **own}, ramps=[NIGHT_R, ICE_R, *ramps], pairs=list(pairs))


def edge_dark(X, Y):
    """The vignette at the frame: how many levels the night loses there."""
    e = np.minimum(np.minimum(X, 128 - X), np.minimum(Y, 128 - Y))
    return np.clip((6 - e) / 6, 0, 1) ** 1.3 * 1.5


def terrace_px(lv, px=1.5):
    """ak.terrace with its seams about `px` pixels wide: the softness in
    levels follows the local gradient, so a slow gradient gets a narrow
    seam (not a wide 50% band) and a steep one still gets a step."""
    gy, gx = np.gradient(np.asarray(lv, dtype=np.float64))
    soft = np.clip(px * np.hypot(gx, gy), 0.02, 0.6)
    k = np.floor(lv)
    s = np.clip((lv - k - 0.5) / soft + 0.5, 0, 1)
    return k + s


def sky_level(X, Y, **look):
    """The night as a float level on NIGHT_R (0 black .. 3 navy2) at the
    points X, Y (pixel centres are x + 0.5)."""
    L = {**LOOK, **look}
    cx, cy = L["centre"]
    top = L["top"]
    base = np.interp(Y, [0, 44, 80, 128], [top, top + 0.05, 1.25, 1.35])
    gx, gy = L["glow"]
    r = np.hypot((X - cx) / gx, (Y - cy) / gy)
    lv = base + 1.0 * np.clip(1 - r, 0, 1) ** 1.4
    if L["floor"] is not None:
        fy = L["floor"]
        px, py = L["pool"]
        below = Y >= fy
        rp = np.hypot((X - cx) / px, (Y - max(cy, fy + py)) / py)
        t_ = np.clip(1 - rp, 0, 1)
        floor = 1.05 + np.clip((Y - fy) / 40.0, 0, 1) * 0.2 + 1.7 * t_ * t_ * (3 - 2 * t_)
        lv = np.where(below, floor, np.minimum(lv, 1.7))
    if L["beam"]:
        (sx, sy), (tx, ty), half, k = L["beam"][:4]
        ax_, ay_ = tx - sx, ty - sy
        n = np.hypot(ax_, ay_)
        ax_, ay_ = ax_ / n, ay_ / n
        dx, dy = X - sx, Y - sy
        along = dx * ax_ + dy * ay_
        across = np.abs(-dx * ay_ + dy * ax_)
        wdt = np.maximum(along, 1e-3) * np.tan(np.radians(half))
        edge = np.clip((wdt - across) / (1.0 + 0.25 * wdt), 0, 1)       # soft sides
        fade = np.clip(1.15 - along / n, 0, 1) ** 0.8                     # brightest at its source
        lv = lv + k * edge * edge * fade * (along > 0)
    if L["rays"]:
        nr = L["rays"]
        ang = np.arctan2(Y - cy, X - cx) + np.radians(L["spin"])
        rr = np.hypot(X - cx, Y - cy)
        f = np.cos(nr * ang) - np.cos(np.pi * L["ray_width"])
        e = np.clip(0.9 / np.maximum(rr * np.pi / nr, 1e-3), 0.02, 1)
        wedge = np.clip((f + e) / (2 * e), 0, 1)
        r0, r1 = L["ray_reach"]
        fade = np.clip((rr - r0) / 12.0, 0, 1) * np.clip(1 - (rr - r0) / (r1 - r0), 0, 1) ** 0.7
        if L["ray_top"] is not None:                                      # clear of the sign
            fade = fade * np.clip((Y - L["ray_top"]) / 10.0, 0, 1)
        lv = lv + L["ray_k"] * wedge * fade
    for bx, by, br, bk in L["blooms"]:
        t_ = np.clip(1 - np.hypot(X - bx, Y - by) / br, 0, 1)
        lv = lv + bk * t_ * t_
    lv = lv - edge_dark(X, Y)
    return np.clip(lv, 0, 3)


def sky(cv, P, **look):
    """The night in true colour on an artkit Canvas."""
    lv = sky_level(cv.X, cv.Y, **look)
    cv.paint(1.0, ak.ramp_map(lv / 3.0, [P.hex(n) for n in NIGHT_R]))


def put_sky(pic, where=None, shadow=None, **look):
    """The night on the pixels: flat plateaus of NIGHT_R, seams a pixel or
    two wide. shadow: a mask where the object's shadow falls on the
    backdrop (the object moved down and right a few px): the night a whole
    level darker there, flat, with no dither at its edge."""
    lv = sky_level(XX + 0.5, YY + 0.5, **look)
    if where is None:
        where = np.ones((128, 128), bool)
    if shadow is None:
        shadow = np.zeros((128, 128), bool)
    ak.by_level(pic, terrace_px(lv, 1.5), NIGHT_R, where & ~shadow)
    ak.put_levels(pic, where & shadow, np.clip(np.round(lv) - 1, 0, 3).astype(int), NIGHT_R)


def skyline(pic, base=100, tops=(60, 80), seed=7, near=True, windows="navy2", where=None, look=None):
    """The Strip at night behind the object, as on the cart's cover: towers
    standing on row `base`, their roofs between rows tops[0] and tops[1].
    The far row is the night one level darker (so the glow still shows
    through it); the near row (near=True), lower and wider apart, is two
    levels darker with a navy2 rim on its roofs. `windows`: a colour for a
    sparse grid of lit windows on the far row (None for none). Paint it
    after put_sky and before the object; `look` as given to put_sky.
    Returns the towers' mask."""
    look = look or {}
    lv = sky_level(XX + 0.5, YY + 0.5, **look)
    rng = np.random.default_rng(seed)
    out = np.zeros((128, 128), bool)
    layers = [("far", tops, 1.0)] + ([("near", (tops[0] + 10, tops[1] + 8), 2.0)] if near else [])
    for name, (t0, t1), drop in layers:
        m = np.zeros((128, 128), bool)
        x = -int(rng.integers(0, 6))
        while x < 128:
            bw = int(rng.integers(5, 12)) if name == "far" else int(rng.integers(8, 16))
            top = int(rng.integers(t0, t1))
            m[top:base, max(x, 0):max(x + bw, 0)] = True
            if bw >= 8 and rng.random() < 0.45:                  # a stepped crown
                inset = int(rng.integers(2, bw // 2))
                m[top - 3:top, max(x + inset, 0):max(x + bw - inset, 0)] = True
                top -= 3
            if rng.random() < 0.3:                               # a mast
                mx = x + bw // 2
                if 0 <= mx < 128:
                    m[top - int(rng.integers(3, 6)):top, mx] = True
            x += bw + (0 if name == "far" else int(rng.integers(4, 14)))
        if where is not None:
            m &= where
        ak.by_level(pic, terrace_px(np.clip(lv - drop, 0, 3), 1.5), NIGHT_R, m)
        if name == "far" and windows:
            g = m & ak.erode(m, 1) & (YY % 3 == 0) & (XX % 2 == 1) & (ak.ihash(XX * 131 + YY * 7, seed) < 0.16)
            pic.put(g & (YY < base - 2), windows)
        if name == "near":
            roof = m & ~ak.shift(m, 0, 1)
            pic.put(roof, "navy2")
        out |= m
    return out


def word_mask(name):
    """A folder word's mask: word_<name>.txt beside this module (a path or a mask passes through)."""
    if isinstance(name, np.ndarray):
        return name
    p = pathlib.Path(name)
    if not p.suffix:
        p = HERE / f"word_{str(name).lower()}.txt"
    return ak.load_mask(p)


def twinkle(pic, x, y, arm="grey", size=1, core="cream"):
    """A small four-pointed star: a `core` pixel, arms `size` long in `arm`."""
    pic.px(x, y, core)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            pic.px(x + dx, y + dy, arm if k == size else core)


def _blur(m, n=2):
    """A box blur (2n+1 square) of a mask, as floats."""
    a = np.pad(m.astype(np.float64), n, mode="edge")
    c = np.cumsum(np.cumsum(a, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    k = 2 * n + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s / (k * k)


def selout(pic, m, dark="black", light=None, diag=False, facing=0.15):
    """A selective outline round the mask m: `dark` on the ring pixels whose
    outward normal (from the smoothed shape) faces down or right (n . (1, 1)
    / sqrt 2 > -facing), `light` (or nothing) on the others. The step
    corners of a slanted edge go with their edge, so a shadow-side line has
    no gaps. Returns the shadow-side ring."""
    r = ak.dilate(m, 1, diag=diag) & ~m
    b = _blur(m, 2)
    gy, gx = np.gradient(b)
    nx, ny = -gx, -gy                                            # outward: away from the shape
    nn = np.hypot(nx, ny) + 1e-9
    face = (nx + ny) / (nn * np.sqrt(2))
    shade = r & (face > -facing)
    pic.put(shade, dark)
    if light:
        pic.put(r & ~shade, light)
    return shade


def sign_panel(foot, pad=1, cut=3):
    """The sign's panel: the bounding box of `foot`, `pad` px clear of it,
    its corners cut on even 1-1 steps (`cut` px)."""
    ys, xs = np.nonzero(foot)
    x0, x1 = xs.min() - pad, xs.max() + pad
    y0, y1 = ys.min() - pad, ys.max() + pad
    m = (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1)
    dx = np.minimum(XX - x0, x1 - XX)
    dy = np.minimum(YY - y0, y1 - YY)
    return m & ((dx + dy) >= cut)


def _extrude(M, steps):
    """The letters' depth, layer by layer: [(dx, dy, colour)]. A layer's
    lone stair-step pixels are left to the outline, unless they sit under a
    hairline (which would show a pinhole)."""
    acc = M.copy()
    layers = []
    for dx, dy, c in steps:
        L0 = ak.shift(M, dx, dy) & ~acc
        L = L0 & ak.nbrs(L0)
        L |= L0 & ak.shift(M, 0, 1) & ak.shift(acc, 1, 0)
        layers.append((L, c))
        acc |= L
    return acc, layers


FACE = [(0.42, "ice2"), (0.54, "ice1"), (0.60, "ice0"), (0.86, "ice1"), (1.01, "ice2")]
EXTRUDE = ["navy2", "navy1", "navy1", "navy1"]
# the rings outside the panel: the tube, its glow (the tube's colour on a
# checker, so it turns with it), the night's glow
HALO = [("rainbow", None), ("rainbow", "checker"), ("navy1", None)]


def word(pic, name, y=WORD_Y, x=None, depth=3, glints=(), neon=True, face=None, extrude=None, halo=None,
         bevel=("cream", "ice0"), seams=5, pad=1, cut=3):
    """The folder's sign: its word in ice chrome on its panel, framed by the
    family's neon.

    name: 'cards' (word_cards.txt), a path, or a mask. x: its left column
    (centred if None). glints: [(dx, dy, size)] cream stars on the face,
    from its top-left corner (each moved to the nearest spot wholly inside a
    letter's face, so it never breaks the outline). neon=False makes the
    tube navy2 (a plain glow). face: [(up to this fraction of the height,
    colour or (colour, seam colour))]; extrude: a colour per depth step;
    halo: the rings round the panel [(colour, None | 'checker')]; pad: the
    panel's margin round the lettering; cut: its corners. Returns {'face',
    'all' (lettering, extrusion, outline, shadow), 'panel', 'halo' (all it
    drew)}."""
    m = word_mask(name)
    if x is None:
        x = ak.centred_x(m)
    face = face or FACE
    extrude = extrude or EXTRUDE
    halo = HALO if halo is None else halo
    if not neon:
        halo = [(("navy2" if c == "rainbow" else c), (None if c == "rainbow" else p)) for c, p in halo]
    M = ak.place(m, x, y)
    ys = np.nonzero(M.any(1))[0]
    top, h = int(ys.min()), int(ys.max() - ys.min() + 1)
    steps = [(k, k, c) for k, c in zip(range(1, depth + 1), extrude)]
    body, layers = _extrude(M, steps)
    sh = ak.shift(body, 1, 1) & ~body
    O = ak.dilate(body, 1) & ~body
    foot = body | O | sh
    # notches between letters: one-pixel gaps of the ground shut in by outlines
    notch = ~foot & ak.shift(foot, 1, 0) & ak.shift(foot, -1, 0)
    notch |= ~foot & ak.shift(foot, 0, 1) & ak.shift(foot, 0, -1)
    foot |= notch
    panel = sign_panel(foot, pad, cut) | foot
    pic.put(panel & ~foot, "navy1")
    acc = panel.copy()
    drawn = panel.copy()
    for c, pat in halo:
        r = ak.dilate(acc, 1) & ~acc                             # 4-way: a clean 1-px ring, 1-1 corners
        if pat == "checker":
            pic.put(r & ak.checker(), c)
            pic.put(r & ~ak.checker(), "navy1")
        elif c:
            pic.put(r, c)
        drawn |= r
        acc |= r
    pic.put(sh | O | notch, "black")
    for L, c in layers:
        pic.put(L, c)
    wide = M & (ak.runs(M, 1) >= seams)
    for j in range(h):
        f = (j + 0.5) / h
        c = next(cc for lim, cc in face if f < lim)
        row = M & (YY == top + j)
        if isinstance(c, tuple):
            pic.put(row, c[0])
            pic.put(row & wide & ~ak.checker(), c[1])
        else:
            pic.put(row, c)
    if bevel:
        cls = ak.bevel_runs(pic.copy(), M, "cream", "black")
        if bevel[1]:
            pic.put(M & (cls == -1), bevel[1])
        if bevel[0]:
            pic.put(M & (cls == 1), bevel[0])
    for g in glints:
        size = g[2] if len(g) > 2 else 2
        gx, gy = ak.glint_in(M, x + g[0], y + g[1], size=size, reach=6)
        ak.glint(pic, gx, gy, size, tip="ice2")
    return {"face": M, "all": foot, "panel": panel, "halo": drawn}
