"""The CHGAME logo, dressed: one treatment shared by every picture that
carries the console's own mark (the casino cart's cover, which is the
power-on splash; the default cover; the text menu's header). The house look
is docs/cover-art.md; tools/sdcard/art/src/cover.py is the worked example.

The logo is the owner's (it came from the list menu's first default
picture, spec/assets/menu-default.png): LOGO_ROWS below is its master, 72 x
17 pixels: the brush letters CHG, the small AME at the top right, the H's
drip below. It is always drawn at that native size, never enlarged; only its
dress changes. (menuart.chg_logo() hands out the same rows.)

THE CASINO'S MARK IS GOLD; THE CONSOLE'S IS THE RAINBOW. Gold chrome is
the logo on the casino card's own pictures (its splash and its text menu's
header). The defaults every cart falls back on (the default cover, the
default text-menu picture) wear it plain: flat in the rainbow colour, as
the menu has always shown it. Neon is for a picture that wants the mark lit
in the rainbow colour on a dark ground; it is clean (no dotted halo) but
quieter than gold: choose it on purpose.

USE (from a recipe; it needs the repository's tools/ and tools/art/ on sys.path)

    import chglogo as cl
    P = ak.Palette({**cl.GOLD, ...up to 8 more of the picture's own...},
                   ramps=[..., cl.GOLD_RAMP])            # gold0 gold1 gold2 cream
    pic = cv.quantize(P, exclude=list(cl.GOLD))         # keep the logo's gold its own
    ...paint the picture...
    cl.dress(pic, cl.centred(), 4)                      # gold chrome, the default
    cl.dress(pic, x, y, style="neon", air="violet")     # lit tubes in the rainbow colour
    cl.dress(pic, x, y, style="plain")                  # the list menu's flat logo

    Plan round it first: cl.footprint(x, y, style, **same options) is the
    mask of every pixel dress() will touch (for a halo hugging it, as the
    casino cover's sky does, or to keep busy detail away from it).

    Any lettering as a neon sign (the casino cover's CASINO):
    cl.channel(pic, M, body="violet")                   # channel letters
    cl.neon(pic, M)                                     # a bare tube

STYLES
    gold   Gold chrome (the default). The face in bands like a chrome sky:
           gold2 above, gold1 falling to a hard gold0 horizon at the logo's
           row 7, gold2 again under it (the ground's light), gold1, gold0
           down the drip; the small AME light above and mid below, with no
           horizon through its two-pixel strokes. A bevel on the big
           letters (artkit.paint.bevel_runs: cream on the edges that face
           the key, top and left, gold0 on the others, 1-2 px strokes left
           plain), an extrusion `depth` pixels down-right (gold0), a black
           outline round it all (the notches between the letters and in the
           m closed with it), a black drop shadow, and two cream glints
           (the C's shoulder, the G's spur), clipped to the letters so they
           never break the outline. Costs three own colours, GOLD, plus the
           fixed cream and black. Pass ramp=(dark, mid, light) to dress it
           in another metal (a silver chrome of the picture's own).
    neon   The logo lit in the rainbow colour (#FF00FF, index 15: the
           Rainbow menu turns it through the colour wheel, the Static one
           shows magenta): the strokes rainbow, a cream (white-hot) line
           down the middle of the big brush strokes (where they are 5 px or
           more), the small AME plain rainbow (its 2 px strokes can't hold a
           core), a black outline so the tube stays crisp in every phase of
           the wheel (blue on navy would vanish), and, with air=, a ring of
           that colour `air_px` wide hugging the outline outside (never in
           the counters): the night lit round the sign. No dotted halo.
           Costs no own colour (air is the picture's own).
    plain  The console's own mark as the menu has always shown it: flat
           rainbow, a black outline and a black drop shadow (shadow=None:
           the outline alone, as the default cover, the default text-menu
           picture and FOLDER wear it; outline=None too for the bare shape).
           Costs no own colour.

FUNCTIONS
    mask()                      the logo, a (17, 72) bool array
    W, H                        72, 17
    centred(width=128)          the x that centres it (28)
    place(x, y)                 the logo itself on a 128 x 128 mask
    dress(pic, x, y, style="gold", **options) -> {name: mask}
        paints it on an artkit Picture (None: only measure); returns the
        masks: 'face' (the logo), 'depth', 'outline', 'shadow', 'glow',
        'core', 'glints' and 'all' (everything it touched)
    footprint(x, y, style="gold", **options)
        dress(...)['all'] without painting
    channel(pic, M, body="violet", edge="black", depth=2, returns="navy0",
            shadow=(1, 1), core="ridge") -> {name: mask}
        any lettering as channel letters, the sign maker's neon: the tube
        (M, rainbow) with a white-hot core, inside a can whose face is a
        `body` ring a pixel wide (lit by the tube), its lip an `edge`
        outline, `depth` pixels of `returns` (its sides) down-right, and a
        drop shadow. Letters set 3 px apart share one edge pixel between
        their bodies. Masks: 'tube', 'core', 'body', 'edge', 'returns',
        'shadow', 'all'.
    neon(pic, M, core="ridge"|"inline"|False, ring="black", air=None, air_px=1)
        any mask as a bare neon tube: the tube, its core, a `ring` outline
        (None for none) and an `air` ring outside it (never in a counter or
        a pocket between letters). Masks: 'tube', 'core', 'ring', 'glow', 'all'.
    ridge(M), thin(M)           a stroke's middle line (Zhang-Suen thinning)
    pockets(M, n=2)             the counters and the gaps between letters
                                up to 2n px wide: where a halo must not go

    Options (each style takes the ones that make sense to it):
    ramp=("gold0", "gold1", "gold2")   gold: the metal, dark to light
    depth=1                             gold: extrusion pixels (0 for none)
    depth_colours=None                  gold: one colour per extrusion step
                                        (default: the ramp's dark one)
    outline="black"                     gold, neon, plain: None for none
    shadow=(1, 1)                       gold, plain: the drop shadow's
                                        offset, None for none
    shadow_colour="black"
    glints=True                         gold: the two cream stars
    bevel=True                          gold ("contour": only the outer
                                        contour, the counters flat)
    horizon=True                        gold: False fills the big letters
                                        light to mid with no chrome band
    hi="cream"                          gold: the bevel's light colour
    notches=True                        gold, plain: close the notches with
                                        the outline colour
    core=True                           neon: the white-hot line
    air=None, air_px=1                  neon: the lit night round it

SIZES (the footprint, from the logo's top-left corner at x, y)
    gold, depth 1, shadow (1, 1):   x-1 .. x+74, y-1 .. y+19 (21 rows)
    gold, depth 1, no shadow:       x-1 .. x+73, y-1 .. y+18 (20 rows)
    gold, depth 0, no shadow:       x-1 .. x+72, y-1 .. y+17 (19 rows)
    neon (outline, no air):         x-1 .. x+72, y-1 .. y+17
    neon, air_px n:                 n more all round
    plain (outline, shadow):        x-1 .. x+73, y-1 .. y+18
    The text menu's header (rows 0-19) takes gold with depth 1 and no
    shadow at y=1 (rows 0-19), or depth 0 and no shadow at y=1 or 2.

PALETTE NAMES
    GOLD = {"gold0", "gold1", "gold2"}: the same names the pilot covers give
    their titles' gold, so a picture whose own title is gold can share them
    with the logo (both are titles; nothing else may use them). GOLD_RAMP is
    the ramp for the quantiser: gold0 gold1 gold2 cream. The neon styles
    use the fixed colours and the rainbow colour, plus whatever the caller
    names for `air` / `body` / `returns` (the casino cover: violet, navy0).
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

W, H = 72, 17
GOLD = {"gold0": "#8E4A06", "gold1": "#E8A018", "gold2": "#FFE77A"}
GOLD_RAMP = ["gold0", "gold1", "gold2", "cream"]

# the logo: the master (the owner's mark, from the list menu's first default picture)
LOGO_ROWS = [
    "....#######..##...#####....#####.....#######..##........................",
    "...############....####.....####....############........................",
    "..#####....####.....###.....####...#############....####..#.....#.######",
    ".#####......###.....###.....####..######....###....######.##...##.######",
    ".####.......##......###......###..#####......#......#..##..##.###..#....",
    "#####........#.#################.#####.............##..##.#######.#####.",
    "####............################.#####..##########.######.#######.####..",
    "####................############.####.....########.###.##.##.#.##.##....",
    "####...........#...###...######..####........####..##..##.##...##.######",
    "#####.........##...###.....####..#####.........##..##..##.##...##.######",
    ".######...######...##......####...######...######...............#.......",
    "..#############....##......###.....#############........................",
    "....##########.....##.....###........##########.........................",
    ".....#######.......#......###.........#######...........................",
    "..........................##............................................",
    "..........................##............................................",
    "..........................#.............................................",
]

# the face's bands, row by row (0 the logo's top): a light sky, a seam, the
# mid tone, the hard dark horizon, the light ground, falling to the drip.
# Each entry: a ramp step (0 dark, 1 mid, 2 light) or (a, b) for a seam: a,
# with a 50% checker of b where the stroke is 5 px or wider.
ROWS = [2, 2, 2, 2, 1, 1, 1, 0, 2, 2, 2, 1, 1, 1, 0, 0, 0]
ROWS_FLAT = [2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
# the small AME (logo columns from SMALL_X): light above, mid below, no
# horizon through letters two pixels thin
SMALL_X = 51
ROWS_SMALL = [2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
# where the glints go on the logo (x, y, arms (left, right, up, down)): the
# C's shoulder and the G's spur; arms are clipped to the letters
GLINTS = [(9, 1, (2, 2, 2, 2)), (47, 1, (2, 1, 1, 1))]

_MASK = None


def mask():
    """The logo as a (17, 72) bool array."""
    global _MASK
    if _MASK is None:
        _MASK = np.array([[c == "#" for c in r] for r in LOGO_ROWS], dtype=bool)
        assert _MASK.shape == (H, W), _MASK.shape
    return _MASK.copy()


def centred(width=128):
    return (width - W) // 2


def place(x, y):
    from artkit.pixel import place as _place
    return _place(mask(), x, y)


def footprint(x, y, style="gold", **kw):
    return dress(None, x, y, style, **kw)["all"]


# ---- the pieces ----------------------------------------------------------------------

def _shift(m, dx, dy):
    from artkit.pixel import shift
    return shift(m, dx, dy)


def _dilate(m, n=1, diag=False):
    from artkit.pixel import dilate
    return dilate(m, n, diag)


def _erode(m, n=1, diag=False):
    from artkit.pixel import erode
    return erode(m, n, diag)


def _ring(m, diag=False):
    return _dilate(m, 1, diag) & ~m


def _wide(M):
    from artkit.paint import runs
    return M & (runs(M, 1) >= 5) & _shift(M, 1, 0) & _shift(M, -1, 0)


def _put(pic, m, colour):
    if pic is not None and colour and m.any():
        pic.put(m, colour)


def _face(pic, M, y, ramp, rows, cols=None):
    from artkit.pixel import checker
    ck = checker()
    wide = _wide(M)
    for j, c in enumerate(rows):
        row = np.zeros_like(M)
        if 0 <= y + j < 128:
            row[y + j, :] = True
        row &= M
        if cols is not None:
            row &= cols
        if isinstance(c, tuple):
            _put(pic, row, ramp[c[0]])
            _put(pic, row & wide & ~ck, ramp[c[1]])
        else:
            _put(pic, row, ramp[c])


def _bevel(pic, M, hi, lo):
    """Light on the outer contour's edges that face the key (top, left),
    dark on the others, where the stroke is 3 px thick; the counters and
    the small AME (2 px strokes) keep their face. A light run is unbroken:
    a bevel pixel with no neighbour of its kind is dropped."""
    from artkit.paint import outside_of, nbrs
    out = outside_of(M)
    tv = M & _shift(M, 0, 1) & _shift(M, 0, -1)
    th = M & _shift(M, 1, 0) & _shift(M, -1, 0)
    top = M & _shift(out, 0, 1)
    bot = M & _shift(out, 0, -1)
    left = M & _shift(out, 1, 0)
    right = M & _shift(out, -1, 0)
    low = (bot & _shift(tv, 0, 1)) | (right & _shift(th, 1, 0))
    high = ((top & _shift(tv, 0, -1)) | (left & _shift(th, -1, 0))) & ~bot & ~right
    high &= nbrs(high, diag=True)
    low &= nbrs(low, diag=True)
    _put(pic, low, lo)
    _put(pic, high, hi)
    return high, low


def _bevel_runs(pic, M, hi, lo):
    """artkit.paint.bevel_runs, measuring only: straight edges by their side
    (top and left light, bottom and right dark), diagonals by the blurred
    letter's normal against the key, 1-2 px strokes left as they are."""
    from artkit.paint import bevel_runs

    class _Null:
        def put(self, m, c):
            pass
    cls = bevel_runs(_Null(), M, hi, lo)
    _put(pic, cls == -1, lo)
    _put(pic, cls == 1, hi)
    return cls == 1, cls == -1


def _glint(pic, x, y, arms, core="cream", tip=None, clip=None):
    """A four-pointed star; with `clip`, only its pixels on that mask (so it
    never pokes out of a letter into its outline or a counter)."""
    m = np.zeros((128, 128), bool)
    pts = [(x, y, core)]
    for (dx, dy), n in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for k in range(1, n + 1):
            pts.append((x + dx * k, y + dy * k, tip if (tip and k == n and n > 1) else core))
    for px, py, c in pts:
        if 0 <= px < 128 and 0 <= py < 128 and (clip is None or clip[py, px]):
            m[py, px] = True
            if pic is not None:
                pic.px(px, py, c)
    return m


def _notches(body, n=2):
    """Background shut in by `body` on both sides (left and right, or above
    and below) within n*2+1 px and on a third side: the notches between
    letters and in the m's humps, which want the outline colour."""
    from artkit.paint import outside_of
    closed = _erode(_dilate(body, n, diag=True), n, diag=True)
    gap = closed & ~body
    # keep only what is open to the outside (a notch), not a whole counter
    return gap & _dilate(outside_of(body), 1)


def thin(M):
    """Zhang-Suen thinning: M worn down to one-pixel lines through its
    middle (8-connected), its topology kept."""
    A = np.pad(M.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            P2, P3, P4 = A[:-2, 1:-1], A[:-2, 2:], A[1:-1, 2:]
            P5, P6, P7 = A[2:, 2:], A[2:, 1:-1], A[2:, :-2]
            P8, P9 = A[1:-1, :-2], A[:-2, :-2]
            ring = [P2, P3, P4, P5, P6, P7, P8, P9, P2]
            B = sum(ring[:8])
            T = sum(((ring[i] == 0) & (ring[i + 1] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                c = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
            else:
                c = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
            kill = (A[1:-1, 1:-1] == 1) & (B >= 2) & (B <= 6) & (T == 1) & c
            if kill.any():
                A[1:-1, 1:-1][kill] = 0
                changed = True
        if not changed:
            return A[1:-1, 1:-1].astype(bool)


def ridge(M, min_d=2):
    """The middle line of M's strokes, for a neon tube's white-hot core: M
    thinned to one pixel, kept where the stroke is at least 2*min_d-1 wide
    (a 3 px stroke: rainbow, cream, rainbow); a bar two pixels high and four
    or more long gets its core on its upper row (the A's crossbar); crumbs
    (a pixel with no neighbour of its own) are dropped."""
    from artkit.paint import nbrs, runs
    deep = _erode(M, min_d - 1) if min_d > 1 else M.copy()
    R = thin(M) & deep
    if min_d == 2:
        bar = M & (runs(M, 0) == 2) & ~_shift(M, 0, 1) & (runs(M, 1) >= 4)    # the top row of a 2-high bar
        R |= bar & ~(_shift(~M, 1, 0) | _shift(~M, -1, 0))                     # short of its ends
    return R & nbrs(R, diag=True)


def pockets(M, n=2):
    """The counters and the gaps between letters up to 2n px wide: the
    closing of M less M, and every enclosed counter."""
    from artkit.paint import outside_of
    closed = _erode(_dilate(M, n, diag=True), n, diag=True)
    return (closed | ~outside_of(M)) & ~M


def neon(pic, M, core="ridge", ring="black", air=None, air_px=1, core_min=2, tube="rainbow", hot="cream",
         glow=0, dens=(0.0, 0.125)):
    """Any mask dressed as a bare neon tube: `tube` (the rainbow colour)
    with a `hot` (cream) white-hot core, a `ring` outline (so the tube stays
    crisp in every phase of the wheel; None for none), and with `air` a ring
    of that colour `air_px` wide outside it, hugging the word's outer
    contour: never in a counter or a pocket between letters (pockets()).
    core: "ridge", the middle line of strokes at least 2*core_min-1 px wide
    (a 3 px stroke: rainbow, cream, rainbow); "inline", a line two pixels in
    from every edge of the wide strokes; False for none.
    glow > 0 adds the old dotted halo of the tube's colour (Bayer, `dens`
    per ring), also kept out of the pockets; the house look prefers air.
    Returns {'tube', 'core', 'ring', 'glow', 'all'}."""
    from artkit.paint import BAYER, distance_px, nbrs
    z = np.zeros_like(M)
    Rg = _ring(M) if ring else z
    body = M | Rg
    free = ~pockets(body) & ~body
    G = z.copy()
    if air:
        G = _dilate(body, air_px, diag=True) & free
    D = z.copy()
    dd = list(dens)[:max(0, min(len(dens), glow))]
    if dd:
        d = distance_px(body, len(dd) + 1)
        for k, a in enumerate(dd):
            D |= (d == k + 1) & free & (BAYER < a)
    if core == "inline":
        C = _erode(M, 1) & ~_erode(M, 2)
        C &= nbrs(C, diag=True)
    elif core:
        C = ridge(M, core_min)
    else:
        C = z
    _put(pic, G, air)
    _put(pic, D, tube)
    _put(pic, Rg, ring)
    _put(pic, M, tube)
    _put(pic, C, hot)
    return dict(tube=M, core=C, ring=Rg, glow=G | D, all=body | G | D)


def channel(pic, M, body="violet", edge="black", depth=2, returns="navy0", shadow=(1, 1), shadow_colour="black",
            core="ridge", core_min=2, tube="rainbow", hot="cream"):
    """Channel letters, the sign maker's neon: M is the tube (`tube`, the
    rainbow colour, with a `hot` white-hot core down its middle), inside a
    can: a `body` ring a pixel wide round the tube (the can's face, lit by
    it), an `edge` outline (its lip), `depth` pixels of `returns` (its sides)
    down-right, outlined in `edge` too, and a drop shadow. Letters set 3 px
    apart share one edge pixel between their bodies. Returns {'tube',
    'core', 'body', 'edge', 'returns', 'shadow', 'all'}."""
    z = np.zeros_like(M)
    B = _dilate(M, 1) & ~M if body else z
    can = M | B
    E = _ring(can, diag=True) if edge else z
    front = can | E
    ret = z.copy()
    for k in range(1, depth + 1):
        ret |= _shift(front, k, k)
    ret &= ~front
    Er = _ring(ret | front) & ~(ret | front) if edge and depth else z
    Er &= _shift(ret, -1, -1) | _shift(ret, -1, 0) | _shift(ret, 0, -1) | _shift(ret, 1, 0) | _shift(ret, 0, 1)
    whole = front | ret | Er
    S = (_shift(whole, *shadow) & ~whole) if shadow else z
    _put(pic, S, shadow_colour)
    _put(pic, Er, edge)
    _put(pic, ret, returns)
    _put(pic, E, edge)
    _put(pic, B, body)
    _put(pic, M, tube)
    C = ridge(M, core_min) if core else z
    _put(pic, C, hot)
    return dict(tube=M, core=C, body=B, edge=E | Er, returns=ret, shadow=S, all=whole | S)


# ---- the styles ----------------------------------------------------------------------

def dress(pic, x, y, style="gold", ramp=("gold0", "gold1", "gold2"), depth=1, depth_colours=None,
          outline="black", shadow=(1, 1), shadow_colour="black", glints=True, bevel=True, horizon=True,
          core=True, air=None, air_px=1, hi="cream", notches=True, glow=None, where=None):
    """Paints the logo with its top-left corner at (x, y) on `pic` (an
    artkit Picture; None only measures). Returns its masks. (glow= and
    where= are accepted for older callers and ignored.)"""
    M = place(x, y)
    z = np.zeros_like(M)
    res = dict(face=M, depth=z, outline=z, shadow=z, glow=z, core=z, glints=z)
    if style == "neon":
        big = M & ~((np.arange(128)[None, :] >= x + SMALL_X) & np.ones((128, 1), bool))
        n = neon(None, M, core=False, ring=outline, air=air, air_px=air_px)
        C = ridge(big, 2) if core else z
        if notches and outline:
            Nn = _notches(M | n["ring"], 1) & ~n["glow"]
        else:
            Nn = z
        _put(pic, n["glow"], air)
        _put(pic, n["ring"] | Nn, outline)
        _put(pic, M, "rainbow")
        _put(pic, C, "cream")
        res.update(outline=n["ring"] | Nn, glow=n["glow"], core=C, all=n["all"] | Nn)
        return res
    if style == "plain":
        O = _ring(M) if outline else z
        if notches and outline:
            O |= _notches(M | O, 1)
        S = _shift(M | O, *shadow) & ~(M | O) if shadow else z
        _put(pic, S, shadow_colour)
        _put(pic, O, outline)
        _put(pic, M, "rainbow")
        res.update(shadow=S, outline=O, all=M | S | O)
        return res
    if style != "gold":
        raise ValueError(f"style {style!r}: gold, neon or plain")
    # gold chrome: shadow, outline, extrusion, face, bevel, glints
    cols = list(depth_colours) if depth_colours else [ramp[0]] * depth
    acc = M.copy()
    layers = []
    for k in range(1, depth + 1):
        L = _shift(M, k, k) & ~acc
        layers.append((L, cols[min(k - 1, len(cols) - 1)]))
        acc |= L
    D = acc & ~M
    O = _ring(acc) if outline else z
    if notches and outline:
        O |= _notches(acc | O, 1)
    body = acc | O
    S = (_shift(body, *shadow) & ~body) if shadow else z
    _put(pic, S, shadow_colour)
    _put(pic, O, outline)
    for L, c in layers:
        _put(pic, L, c)
    small = (np.arange(128)[None, :] >= x + SMALL_X) & np.ones((128, 1), bool)
    _face(pic, M, y, ramp, ROWS if horizon else ROWS_FLAT, ~small)
    _face(pic, M, y, ramp, ROWS_SMALL, small)
    if bevel:
        big = M & ~small
        if bevel == "contour":
            _bevel(pic, big, hi, ramp[0])
        else:
            _bevel_runs(pic, big, hi, ramp[0])
    Gm = z.copy()
    if glints:
        for gx, gy, arms in GLINTS:
            Gm |= _glint(pic, x + gx, y + gy, arms, tip=ramp[2], clip=M)
    res.update(depth=D, outline=O, shadow=S, glints=Gm, all=body | S | Gm)
    return res
