"""Painting on the pixels: the hand-finishing tools the pilot covers grew
(CHYacht, CHRoulette, CHSnakes: their tools/cart.py are worked examples).

The method that gave the cleanest results: let the canvas and render3d
work out the geometry and the light, then paint each surface pixel by pixel
as a *level* on one of the palette's ramps (0 = the ramp's first colour,
1 the next, ...), with an ordered dither only where a band is wide enough
and only between neighbours in the ramp:

    lv = ak.at_px(light, cv.s) * 3                     # a level per pixel, 0..3
    ak.by_level(pic, ak.terrace(lv), ["black", "felt0", "felt1", "felt2"], where=felt)

Levels:  by_level, levels, put_levels, terrace, cel
Masks:   nbrs, thick, runs, outside_of, distance_px, letters
Lines:   raster, line_px, ink, streak
Clean:   despeckle, lonely
Sparkle: glint, glint_in
Shapes:  pip_template, PIPS, tube, path, hull
Arrays:  px_mean, at_px, up, ihash
Titles:  bevel_contour, bevel_runs
"""
from __future__ import annotations

import numpy as np

from . import color as C
from .canvas import bezier, polyline
from .pixel import shift, dilate, erode
from .quant import BAYER4

BAYER = np.tile((BAYER4 + 0.5) / 16.0, (32, 32))         # the 4x4 thresholds over the picture


# ---- levels ---------------------------------------------------------------------------

def by_level(pic, level, ramp, where, q=4, phase=(0, 0)):
    """Paints `where` from a float level per pixel on the named ramp (0 is
    ramp[0], 1 the next, ...): an ordered Bayer dither in steps of 1/q (q=4:
    25/50/75%, no lone dots; q=2: a 50% checker at most; q=1: plain bands)."""
    th = np.roll(BAYER, phase, axis=(1, 0)) if phase != (0, 0) else BAYER
    level = np.asarray(level, dtype=np.float64)
    b = np.floor(level)
    f = np.round((level - b) * q) / q
    i = np.clip(b + (f > th), 0, len(ramp) - 1).astype(int)
    for k, nm in enumerate(ramp):
        pic.put(where & (i == k), nm)
    return i


def levels(v, dither, steps=4):
    """Float levels to whole ones: a Bayer dither in `steps` steps where
    `dither` (a mask or a bool), plain rounding elsewhere."""
    fl = np.floor(v)
    fr = np.round((v - fl) * steps) / steps
    d = fl + (fr > BAYER)
    return np.where(dither, d, np.round(v)).astype(np.int64)


def put_levels(pic, mask, lv, names):
    """Whole levels (an int array) painted on the named ramp over `mask`."""
    lv = np.clip(lv, 0, len(names) - 1)
    lut = np.array([pic.pal[n] for n in names], np.uint8)
    pic.idx[mask] = lut[lv[mask]]


def terrace(v, soft=0.4):
    """Levels pushed onto whole-level plateaus with short ramps between: flat
    bands, dithered only at their seams (wide 50% bands read as a screen
    door; this keeps them narrow)."""
    k = np.floor(v)
    s = np.clip((v - k - 0.5) / soft + 0.5, 0, 1)
    return k + s


def cel(v, colours, edges, soft=0.05, P=None):
    """Toon shading in true colour: v (0..1) through flat tones `colours`
    (hex, or names with P), changing at `edges`, each change `soft` wide
    (the quantiser then dithers just the seam). Returns an (..., 3) array."""
    cols = [C.to_float(P.hex(c) if P is not None and not str(c).startswith("#") else c) for c in colours]
    v = np.asarray(v, dtype=np.float32)
    out = np.broadcast_to(cols[0], v.shape + (3,)).copy()
    for k, e in enumerate(edges):
        t = np.clip((v - (e - soft)) / (2 * soft), 0, 1)
        w = (t * t * (3 - 2 * t))[..., None]
        out += w * (cols[k + 1] - cols[k])
    return out


# ---- masks ----------------------------------------------------------------------------

def nbrs(m, diag=False):
    """Pixels next to the mask (4-way, or 8 with diag), the mask's own excluded only if not next to itself."""
    out = np.zeros_like(m)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ()):
        out |= shift(m, dx, dy)
    return out


def thick(m, n=2):
    """The parts of a mask at least 2n+1 pixels thick (and a pixel round them)."""
    return dilate(erode(m, n), n) & m


def runs(m, axis):
    """For each True pixel, the length of the run it is in: along rows
    (axis 1) or columns (axis 0)."""
    out = np.zeros(m.shape, int)
    a = m if axis == 1 else m.T
    o = out if axis == 1 else out.T
    for r in range(a.shape[0]):
        row, x = a[r], 0
        while x < len(row):
            if row[x]:
                e = x
                while e < len(row) and row[e]:
                    e += 1
                o[r, x:e] = e - x
                x = e
            else:
                x += 1
    return out


def outside_of(M):
    """The background connected to the picture's border (so a letter's
    enclosed counters are not in it)."""
    out = np.zeros_like(M)
    out[0, :] = ~M[0, :]
    out[-1, :] = ~M[-1, :]
    out[:, 0] |= ~M[:, 0]
    out[:, -1] |= ~M[:, -1]
    while True:
        g = dilate(out, 1) & ~M
        if (g == out).all():
            return out
        out = g


def distance_px(M, n):
    """Pixel distance (0..n, n = farther) from mask M, octagonal."""
    d = np.full(M.shape, float(n), np.float32)
    acc = M.copy()
    d[acc] = 0
    for k in range(1, n):
        acc = dilate(acc, 1, diag=k % 2 == 0)
        d[acc & (d == n)] = k
    return d


def letters(M):
    """The 4-connected parts of a mask (a title's letters), labelled 1..n."""
    lab = np.zeros(M.shape, np.int32)
    n = 0
    for y0, x0 in zip(*np.nonzero(M)):
        if lab[y0, x0]:
            continue
        n += 1
        stack = [(y0, x0)]
        lab[y0, x0] = n
        while stack:
            y, x = stack.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < M.shape[0] and 0 <= xx < M.shape[1] and M[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
    return lab


# ---- lines ----------------------------------------------------------------------------

def raster(pts, closed=False):
    """A polyline (picture coordinates) as pixels, 8-connected and one pixel
    thick, with no L-shaped corners: [(x, y, t)], t the position along it."""
    if closed:
        pts = list(pts) + [pts[0]]
    out = []
    n = len(pts) - 1
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        k = int(max(abs(x1 - x0), abs(y1 - y0)) * 6) + 1
        for s in np.arange(k) / k:
            q = (int(np.floor(x0 + (x1 - x0) * s)), int(np.floor(y0 + (y1 - y0) * s)), (i + s) / n)
            if out and out[-1][:2] == q[:2]:
                continue
            out.append(q)
            while len(out) >= 3:
                a, b, c = out[-3], out[-2], out[-1]
                if a[:2] == c[:2]:
                    out.pop()
                    out.pop()
                    continue
                if abs(a[0] - c[0]) <= 1 and abs(a[1] - c[1]) <= 1:
                    out.pop(-2)                        # b is an L corner (or a doubled step)
                    continue
                break
    return out


def line_px(pts):
    """The pixels [(x, y)] of a clean 1-pixel line through the points."""
    return [(x, y) for x, y, _ in raster(pts)]


def ink(pic, pts, colour, where=None, colours=None):
    """Draws a clean 1-pixel line through the points. colours: [(name, up
    to t)] to step its colour along it instead. Returns its pixels."""
    out = raster(pts)
    for x, y, t in out:
        if 0 <= x < 128 and 0 <= y < 128 and (where is None or where[y, x]):
            c = colour
            if colours:
                c = next((nm for nm, hi in colours if t <= hi), colours[-1][0])
            if c:
                pic.px(x, y, c)
    return [(x, y) for x, y, _ in out]


def streak(pic, root, ctrl, end, r0, r1, ok=None, cols=(("cream", 0.3), ("grey", 1.0)), ss=4, cut=0.5):
    """A speed line or swoosh: a quadratic curve from `root` through `ctrl`
    to `end`, r0 px in radius at the root tapering to r1, painted where `ok`
    is (a pixel is in when `cut` of it is covered). Its colour steps along
    it: cols [(name, up to t)] (a None name leaves that part unpainted).
    Returns its mask."""
    pts = bezier(root, ctrl, end, n=40)
    c = (np.arange(128 * ss) + 0.5) / ss
    X, Y = np.meshgrid(c, c)
    d = polyline((X, Y), pts, r0, r1)
    cov = (d < 0).reshape(128, ss, 128, ss).mean(axis=(1, 3))
    m = cov >= cut
    if ok is not None:
        m &= ok
    ys, xs = np.nonzero(m)
    Pt = np.array(pts)
    t = ((xs[:, None] + 0.5 - Pt[None, :, 0]) ** 2 + (ys[:, None] + 0.5 - Pt[None, :, 1]) ** 2).argmin(1) / (len(pts) - 1)
    lo = 0.0
    for name, hi in cols:
        sel = (t >= lo) & (t <= hi)
        if name:
            pic.idx[ys[sel], xs[sel]] = pic.pal[name]
        lo = hi
    return m


# ---- clean-up ---------------------------------------------------------------------------

def despeckle(pic, need=5, keep=None, within=None, passes=1):
    """Lone pixels (unlike all eight neighbours, and not part of a dither: no
    pixel of their colour two steps away) take the colour most of their
    neighbours share, when at least `need` of the eight do. keep: pixels to
    leave alone (glints); within: where to look. Returns how many changed."""
    a = pic.idx
    total = 0
    for _ in range(passes):
        pad = np.pad(a, 2, mode="edge")
        nb = [pad[2 + dy:130 + dy, 2 + dx:130 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
        lone = np.ones_like(a, dtype=bool)
        for q in nb:
            lone &= q != a
        two = np.zeros_like(lone)
        for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            two |= pad[2 + dy:130 + dy, 2 + dx:130 + dx] == a
        lone &= ~two
        if keep is not None:
            lone &= ~keep
        if within is not None:
            lone &= within
        stack = np.stack(nb, -1)
        best = np.zeros_like(a)
        cnt = np.zeros(a.shape, dtype=np.int32)
        for k in np.unique(stack):
            n = (stack == k).sum(-1)
            better = n > cnt
            best = np.where(better, k, best)
            cnt = np.where(better, n, cnt)
        fix = lone & (cnt >= need)
        a[fix] = best[fix]
        total += int(fix.sum())
        if not fix.any():
            break
    return total


def lonely(pic, colour, within, into=None):
    """Pixels of `colour` inside `within` with no 4-neighbour of their colour
    take the colour most of their 4 neighbours share (or `into`)."""
    a = pic.idx
    k = pic.pal[colour]
    m = a == k
    has = shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)
    lone = m & ~has & within
    if into is not None:
        a[lone] = pic.pal[into]
        return int(lone.sum())
    pad = np.pad(a, 1, mode="edge")
    nb = np.stack([pad[1:129, 2:130], pad[1:129, 0:128], pad[2:130, 1:129], pad[0:128, 1:129]], -1)
    best = nb[..., 0].copy()
    cnt = np.zeros(a.shape, np.int32)
    for v in np.unique(nb):
        n = (nb == v).sum(-1)
        better = n > cnt
        best = np.where(better, v, best)
        cnt = np.where(better, n, cnt)
    a[lone] = best[lone]
    return int(lone.sum())


# ---- sparkle ----------------------------------------------------------------------------

def glint(pic, x, y, size=2, tip=None, arms=None, core="cream"):
    """A four-pointed star: `core` in the middle and along the arms, each
    arm's last pixel `tip` (a taper, when given). arms: (left, right, up,
    down) lengths, when they differ."""
    pic.px(x, y, core)
    arms = arms or (size,) * 4
    for (dx, dy), n in zip(((-1, 0), (1, 0), (0, -1), (0, 1)), arms):
        for k in range(1, n + 1):
            pic.px(x + dx * k, y + dy * k, tip if (tip and k == n and n > 1) else core)


def glint_in(face, x, y, size=1, reach=4):
    """The nearest spot to (x, y) where a glint of `size` lies wholly on
    `face`, a pixel clear of its edge (so it never breaks an outline)."""
    inner = erode(face, 1, diag=True)
    best = None
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            px, py = x + dx, y + dy
            pts = [(px, py)] + [(px + k * a, py + k * b) for k in range(1, size + 1)
                                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(0 <= u < 128 and 0 <= v < 128 and inner[v, u] for u, v in pts):
                d = dx * dx + dy * dy
                if best is None or d < best[0]:
                    best = (d, px, py)
    return best[1:] if best else (x, y)


# ---- shapes -----------------------------------------------------------------------------

# Where a die face's pips sit, in face units (-1..1 across): six faces.
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
        4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
        6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}


def pip_template(w, h):
    """A round dot w x h pixels: a square up to 3, an ellipse's pixels from 4
    (4 x 4 loses its corners, 5 x 5 is 3-5-5-5-3)."""
    if min(w, h) < 3 or max(w, h) < 4:
        return np.ones((h, w), bool)
    j, i = np.meshgrid((np.arange(w) + 0.5 - w / 2) / (w / 2), (np.arange(h) + 0.5 - h / 2) / (h / 2))
    return i * i + j * j < 0.98


def tube(P, pts, radii, s0=0.0):
    """A tube along a polyline (a snake, a rope, a cable, a pipe): its
    distance field, its round normal (a cylinder seen side on), the arc
    length along it, its direction and radius at each sample."""
    X, Y = P
    pts = np.asarray(pts, dtype=np.float64)
    radii = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(radii)), radii)
    best = np.full(X.shape, 1e9, np.float32)
    nx, ny, s, tx, ty, rr = (np.zeros(X.shape, np.float32) for _ in range(6))
    cum = s0
    for k in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        dx, dy = x1 - x0, y1 - y0
        L = float(np.hypot(dx, dy)) or 1e-6
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / (L * L), 0, 1)
        r = radii[k] + (radii[k + 1] - radii[k]) * t
        ox, oy = X - (x0 + t * dx), Y - (y0 + t * dy)
        d = np.hypot(ox, oy) - r
        m = d < best
        best = np.where(m, d, best)
        nx = np.where(m, ox / r, nx)
        ny = np.where(m, oy / r, ny)
        s = np.where(m, cum + t * L, s)
        tx = np.where(m, dx / L, tx)
        ty = np.where(m, dy / L, ty)
        rr = np.where(m, r, rr)
        cum += L
    nx, ny = np.clip(nx, -1, 1), np.clip(ny, -1, 1)
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    return {"d": best, "n": np.stack([nx, ny, nz], -1).astype(np.float32), "s": s, "t": (tx, ty),
            "r": rr, "len": cum}


def path(*segs, n=14):
    """Bezier segments (each 3 or 4 points) joined into one list of points."""
    out = []
    for sg in segs:
        pts = bezier(*sg, n=n)
        out += pts if not out else pts[1:]
    return out


def hull(pts):
    """Convex hull of points, counter-clockwise (monotone chain)."""
    pts = sorted(map(tuple, pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


# ---- arrays -----------------------------------------------------------------------------

def px_mean(a, s):
    """A canvas-sized array (128*s square) averaged down to pixels."""
    return a.reshape((128, s, 128, s) + a.shape[2:]).mean(axis=(1, 3))


def at_px(a, s):
    """A canvas-sized array sampled at the pixels' centres."""
    return a[s // 2::s, s // 2::s]


def up(a, s):
    """A pixel-sized array blown up to the canvas's samples."""
    return np.repeat(np.repeat(a, s, 0), s, 1)


def ihash(k, seed=1):
    """A fixed random number in 0..1 per integer k (arrays welcome): the same
    on every machine."""
    k = np.asarray(k, dtype=np.int64)
    h = (k * 374761393 + seed * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


# ---- title bevels -----------------------------------------------------------------------

def bevel_contour(pic, M, hi, lo):
    """A title's bevel on its outer contour only: `hi` on top- and
    left-facing edges, `lo` on every bottom- and right-facing edge (it wins
    at corners), where the stroke is 3 px thick; enclosed counters get none,
    so small letters stay clean. (Draw after ak.title(..., hi=None, lo=None).)"""
    out = outside_of(M)
    thick_v = M & shift(M, 0, 1) & shift(M, 0, -1)
    thick_h = M & shift(M, 1, 0) & shift(M, -1, 0)
    top = M & shift(out, 0, 1)
    bot = M & shift(out, 0, -1)
    left = M & shift(out, 1, 0)
    right = M & shift(out, -1, 0)
    low = (bot & shift(thick_v, 0, 1)) | (right & shift(thick_h, 1, 0))
    high = ((top & shift(thick_v, 0, -1)) | (left & shift(thick_h, -1, 0))) & ~bot & ~right
    pic.put(low, lo)
    pic.put(high, hi)
    return high, low


def bevel_runs(pic, M, hi, lo, L=(-1.0, -0.3), t=0.1, long=3):
    """A title's bevel by edge runs: straight edges (runs of `long` px or
    more) by their side, the whole run one colour; diagonals by the outward
    normal of the blurred letter against the light L; 1-px bars and strokes
    2 px wide or less keep their face; a bevel pixel with no neighbour of its
    kind is dropped. Returns the class map (1 light, -1 dark)."""
    up_, dn = M & ~shift(M, 0, 1), M & ~shift(M, 0, -1)
    lf, rt = M & ~shift(M, 1, 0), M & ~shift(M, -1, 0)
    ru, rd, rl, rr = runs(up_, 1), runs(dn, 1), runs(lf, 0), runs(rt, 0)
    cls = np.zeros(M.shape, int)
    best = np.zeros(M.shape, int)
    for r, c in ((ru, 1), (rd, -1), (rl, 1), (rr, -1)):
        take = (r >= long) & (r > best)
        cls[take] = c
        best[take] = r[take]
    k = np.array([1, 4, 6, 4, 1], float) / 16
    B = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 1, M.astype(float))
    B = np.apply_along_axis(lambda v: np.convolve(v, k, "same"), 0, B)
    gy, gx = np.gradient(B)
    d = (-gx * L[0] - gy * L[1]) / np.hypot(*L) / np.maximum(np.hypot(gx, gy), 1e-6)
    rest = (up_ | dn | lf | rt) & (best == 0) & ~((up_ & dn) | (lf & rt))
    cls[rest & (d > t)] = 1
    cls[rest & (d < -t)] = -1
    cls[(up_ & dn) & (ru >= 5) & (rd >= 5)] = 0
    cls[(lf & rt) & (rl >= 5) & (rr >= 5)] = 0
    cls[(runs(M, 1) <= 2) & (ru < long) & (rd < long)] = 0
    for c in (1, -1):
        m = cls == c
        cls[m & ~nbrs(m, diag=True)] = 0
    pic.put(cls == -1, lo)
    pic.put(cls == 1, hi)
    return cls
