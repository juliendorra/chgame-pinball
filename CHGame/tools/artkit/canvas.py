"""The painting surface: a supersampled float RGB canvas, shapes as signed
distance fields, gradients, noise and 2D lighting.

Coordinates are the picture's pixels as floats: (0, 0) is the top-left
corner of the top-left pixel and (128, 128) the far corner; a pixel's centre
is (x + 0.5, y + 0.5). The canvas keeps `ss` x `ss` samples a pixel (4 by
default), so shapes come out smooth and the quantiser (quant.py) decides how
their edges become pixels.

Shapes are distance fields: a function of the sample coordinates (P = (X, Y))
that is negative inside. cover(cv, d) turns one into coverage, cv.paint()
composites a colour (a constant, or an array from a gradient or a lighting
function) through it. Besides colour each sample carries:

    dith   how much the quantiser may dither there (0: nearest colour only,
           0.5: a checker at most, 1: every level)
    oid    an object id (cv.new_id()), for outlines and clean edges later

    cv = Canvas("#081008")
    P = cv.P
    d = circle(P, 64, 70, 30)
    n = sphere_normal(P, 64, 70, 30)
    dif, spec = light(n)
    cv.paint(cover(cv, d), shade("#C02020", dif, spec), oid=cv.new_id("ball"))
"""
from __future__ import annotations

import numpy as np

from . import color as C

SIZE = 128


class Canvas:
    def __init__(self, bg="#000000", ss=4, size=SIZE):
        self.n, self.s = size, ss
        N = size * ss
        self.N = N
        self.rgb = np.empty((N, N, 3), dtype=np.float32)
        self.rgb[:] = C.to_float(bg)
        self.dith = np.ones((N, N), dtype=np.float32)
        self.oid = np.zeros((N, N), dtype=np.int16)
        c = (np.arange(N, dtype=np.float32) + 0.5) / ss
        self.X, self.Y = np.meshgrid(c, c)
        self.P = (self.X, self.Y)
        self.names = {0: "background"}

    # ---- objects ------------------------------------------------------------------

    def new_id(self, name=None):
        k = max(self.names) + 1
        self.names[k] = name or f"obj{k}"
        return k

    def id_of(self, name):
        for k, v in self.names.items():
            if v == name:
                return k
        raise KeyError(name)

    # ---- painting -----------------------------------------------------------------

    def paint(self, alpha, colour, dither=None, oid=None, blend="normal", where=0.5):
        """Composite `colour` (hex, an (r, g, b) in 0..1 floats, or an (N, N, 3)
        array) through `alpha` (a scalar or an (N, N) array in 0..1).

        blend: normal; add (light: colour * alpha added); multiply (colour
        multiplies, alpha its strength); screen. Samples with alpha above
        `where` take `dither` and `oid` when given."""
        col = _colour(colour)
        a = np.asarray(alpha, dtype=np.float32)
        if a.ndim == 0:
            a = np.full((self.N, self.N), float(a), dtype=np.float32)
        a3 = a[..., None]
        if blend == "normal":
            self.rgb += (col - self.rgb) * a3
        elif blend == "add":
            self.rgb += col * a3
        elif blend == "multiply":
            self.rgb *= 1 + (col - 1) * a3
        elif blend == "screen":
            self.rgb = 1 - (1 - self.rgb) * (1 - col * a3)
        else:
            raise ValueError(blend)
        np.clip(self.rgb, 0, 1, out=self.rgb)
        m = a > where
        if dither is not None:
            self.dith[m] = dither
        if oid is not None:
            self.oid[m] = oid
        return m

    def fill(self, colour, dither=None):
        self.paint(1.0, colour, dither=dither)

    def tag(self, mask, dither=None, oid=None):
        """Set dither and/or oid where `mask` (an (N, N) bool array) is true."""
        if dither is not None:
            self.dith[mask] = dither
        if oid is not None:
            self.oid[mask] = oid

    def blit(self, other, alpha=None, x=0, y=0):
        """Paint another canvas (same ss) on this one at pixel offset (x, y)
        (integers), through its own coverage `alpha` (N', N') or fully."""
        s = self.s
        h, w = other.rgb.shape[:2]
        ox, oy = int(x * s), int(y * s)
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(self.N, ox + w), min(self.N, oy + h)
        if x1 <= x0 or y1 <= y0:
            return
        src = other.rgb[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        a = np.ones(src.shape[:2], np.float32) if alpha is None else alpha[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        self.rgb[y0:y1, x0:x1] += (src - self.rgb[y0:y1, x0:x1]) * a[..., None]

    # ---- to pixels ----------------------------------------------------------------

    def downsample(self, edge_dither=0.0):
        """(rgb (128, 128, 3) float, dith (128, 128), oid (128, 128)): the mean
        colour and dither of each pixel's samples and its majority object.
        Pixels on an object's edge get at most `edge_dither` (0: an edge pixel
        is the nearest colour, so edges come out as hand anti-aliasing, not
        noise)."""
        n, s = self.n, self.s
        rgb = self.rgb.reshape(n, s, n, s, 3).mean(axis=(1, 3))
        dith = self.dith.reshape(n, s, n, s).mean(axis=(1, 3))
        blk = self.oid.reshape(n, s, n, s).transpose(0, 2, 1, 3).reshape(n, n, s * s)
        ids = np.unique(blk)
        counts = np.stack([(blk == u).sum(-1) for u in ids], axis=-1)
        oid = ids[np.argmax(counts, axis=-1)].astype(np.int16)
        if edge_dither is not None:
            edge = np.zeros((n, n), bool)
            edge[1:, :] |= oid[1:, :] != oid[:-1, :]
            edge[:-1, :] |= oid[:-1, :] != oid[1:, :]
            edge[:, 1:] |= oid[:, 1:] != oid[:, :-1]
            edge[:, :-1] |= oid[:, :-1] != oid[:, 1:]
            dith = np.where(edge, np.minimum(dith, edge_dither), dith)
        return rgb, dith, oid

    def quantize(self, palette, **kw):
        from .quant import quantize
        return quantize(self, palette, **kw)

    def mask(self, oid):
        """The samples of object `oid` (an id or a name) as a bool array."""
        if isinstance(oid, str):
            oid = self.id_of(oid)
        return self.oid == oid


def _colour(colour):
    if isinstance(colour, np.ndarray) and colour.ndim == 3:
        return colour.astype(np.float32)
    if isinstance(colour, (str,)) or (isinstance(colour, tuple) and len(colour) == 3 and max(colour) > 1.0001):
        return C.to_float(colour)
    return np.asarray(colour, dtype=np.float32)


# ---- distance fields (P = (X, Y) sample coordinates) -------------------------------

def circle(P, cx, cy, r):
    X, Y = P
    return np.hypot(X - cx, Y - cy) - r


def ellipse(P, cx, cy, rx, ry, angle=0.0):
    """An ellipse (Inigo Quilez's approximation: exact on the axes, close elsewhere)."""
    X, Y = rotate(P, cx, cy, -angle) if angle else P
    px, py = (X - cx) / rx, (Y - cy) / ry
    k0 = np.hypot(px, py)
    k1 = np.hypot(px / rx, py / ry)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def box(P, cx, cy, hw, hh, r=0.0, angle=0.0):
    """A box centred at (cx, cy), half sizes hw, hh, corners rounded by r."""
    X, Y = rotate(P, cx, cy, -angle) if angle else P
    qx = np.abs(X - cx) - hw + r
    qy = np.abs(Y - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def rect(P, x, y, w, h, r=0.0):
    """A box from its top-left corner and size."""
    return box(P, x + w / 2, y + h / 2, w / 2, h / 2, r)


def segment(P, x0, y0, x1, y1, r=0.0):
    """A capsule from (x0, y0) to (x1, y1), radius r."""
    X, Y = P
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = np.clip(((X - x0) * dx + (Y - y0) * dy) / (L2 if L2 else 1), 0, 1)
    return np.hypot(X - x0 - t * dx, Y - y0 - t * dy) - r


def polyline(P, pts, r=0.0, r1=None):
    """Capsules along pts; the radius goes from r to r1 (tapered) when given."""
    d = None
    n = len(pts) - 1
    for k in range(n):
        ra = r if r1 is None else r + (r1 - r) * k / n
        rb = r if r1 is None else r + (r1 - r) * (k + 1) / n
        X, Y = P
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / (L2 if L2 else 1), 0, 1)
        dk = np.hypot(X - x0 - t * dx, Y - y0 - t * dy) - (ra + (rb - ra) * t)
        d = dk if d is None else np.minimum(d, dk)
    return d


def polygon(P, pts):
    """A closed polygon (any winding), exact distance."""
    X, Y = P
    v = np.asarray(pts, dtype=np.float32)
    d = (X - v[0, 0]) ** 2 + (Y - v[0, 1]) ** 2
    s = np.ones_like(X)
    j = len(v) - 1
    for i in range(len(v)):
        ex, ey = v[j, 0] - v[i, 0], v[j, 1] - v[i, 1]
        wx, wy = X - v[i, 0], Y - v[i, 1]
        L2 = ex * ex + ey * ey
        t = np.clip((wx * ex + wy * ey) / (L2 if L2 else 1), 0, 1)
        bx, by = wx - ex * t, wy - ey * t
        d = np.minimum(d, bx * bx + by * by)
        c1 = Y >= v[i, 1]
        c2 = Y < v[j, 1]
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
        j = i
    return s * np.sqrt(d)


def star(P, cx, cy, r_out, r_in, n=5, angle=-90.0):
    pts = []
    for k in range(2 * n):
        a = np.radians(angle + k * 180.0 / n)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + r * np.cos(a), cy + r * np.sin(a)))
    return polygon(P, pts)


def ring(P, cx, cy, r, w):
    return np.abs(circle(P, cx, cy, r)) - w


def halfplane(P, x0, y0, nx, ny):
    """Negative on the side the normal (nx, ny) points away from."""
    X, Y = P
    L = np.hypot(nx, ny)
    return ((X - x0) * nx + (Y - y0) * ny) / L


def union(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.minimum(out, d)
    return out


def inter(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.maximum(out, d)
    return out


def sub(a, b):
    return np.maximum(a, -b)


def smin(a, b, k=4.0):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def cover(cv, d, soft=1.0):
    """Coverage of a distance field: 1 inside, 0 outside, a sample wide
    (`soft` samples) between."""
    return np.clip(0.5 - d * cv.s / soft, 0, 1).astype(np.float32)


# ---- curves --------------------------------------------------------------------------

def bezier(p0, p1, p2, p3=None, n=24):
    """Points along a quadratic (p0, p1, p2) or cubic (p0..p3) Bezier curve."""
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.array(p, dtype=np.float64) for p in (p0, p1, p2))
    if p3 is None:
        pts = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    else:
        p3 = np.array(p3, dtype=np.float64)
        pts = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return [tuple(p) for p in pts]


# ---- coordinate transforms -------------------------------------------------------------

def rotate(P, cx, cy, deg):
    """The sample coordinates turned by `deg` about (cx, cy). A shape drawn in
    the returned frame appears turned by -deg on the picture (shapes that take
    angle= do this for you, the right way round)."""
    X, Y = P
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    x, y = X - cx, Y - cy
    return (cx + c * x - s * y, cy + s * x + c * y)


def scale(P, cx, cy, sx, sy=None):
    X, Y = P
    sy = sx if sy is None else sy
    return (cx + (X - cx) / sx, cy + (Y - cy) / sy)


def homography(src, dst):
    """The 3x3 matrix taking the four points src to the four points dst."""
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(A, dtype=np.float64))
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]


def quad_uv(P, quad, w=1.0, h=1.0):
    """Coordinates (U, V) of a flat w x h rectangle seen as the screen quad
    `quad` (its corners: top-left, top-right, bottom-right, bottom-left), for
    drawing on a table, a card or a board in perspective. Points outside the
    quad get U, V outside 0..w, 0..h."""
    X, Y = P
    H = homography(quad, [(0, 0), (w, 0), (w, h), (0, h)])
    d = H[2, 0] * X + H[2, 1] * Y + H[2, 2]
    return ((H[0, 0] * X + H[0, 1] * Y + H[0, 2]) / d, (H[1, 0] * X + H[1, 1] * Y + H[1, 2]) / d)


def inside_uv(U, V, w=1.0, h=1.0):
    """Distance-like field of the rectangle in (U, V) (negative inside); in UV
    units, so only its sign (and cover()) is to be trusted."""
    return np.maximum(np.maximum(-U, U - w), np.maximum(-V, V - h))


def sample(img, U, V, w=1.0, h=1.0):
    """Look up an image ((H, W, 3) float array, or a Canvas's rgb) at (U, V)
    spanning w x h, bilinear, clamped at the edges."""
    a = img.rgb if hasattr(img, "rgb") else img
    H, W = a.shape[:2]
    x = np.clip(U / w * W - 0.5, 0, W - 1)
    y = np.clip(V / h * H - 0.5, 0, H - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, W - 1), np.minimum(y0 + 1, H - 1)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy)
            + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy).astype(np.float32)


# ---- gradients and colour maps ----------------------------------------------------------

def linear(P, x0, y0, x1, y1):
    """0 at (x0, y0), 1 at (x1, y1), along that line (clamped)."""
    X, Y = P
    dx, dy = x1 - x0, y1 - y0
    return np.clip(((X - x0) * dx + (Y - y0) * dy) / (dx * dx + dy * dy), 0, 1).astype(np.float32)


def radial(P, cx, cy, r, ry=None):
    X, Y = P
    ry = r if ry is None else ry
    return np.clip(np.hypot((X - cx) / r, (Y - cy) / ry), 0, 1).astype(np.float32)


def stops(t, pairs, space="srgb"):
    """A colour per sample from t (0..1): `pairs` are (position, colour) in
    order, interpolated in sRGB (or 'oklab')."""
    t = np.asarray(t, dtype=np.float32)
    pos = np.array([p for p, _ in pairs], dtype=np.float32)
    cols = np.stack([C.to_float(c) for _, c in pairs])
    if space == "oklab":
        cols = C.srgb_to_oklab(cols)
    out = np.empty(t.shape + (3,), dtype=np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(t, pos, cols[:, ch])
    if space == "oklab":
        out = C.oklab_to_srgb(out).astype(np.float32)
    return out


def lerp(a, b, t):
    """Mix two colours (hex or arrays) by t (scalar or array)."""
    a, b = _colour(a), _colour(b)
    t = np.asarray(t, dtype=np.float32)
    if t.ndim:
        t = t[..., None]
    return (a + (b - a) * t).astype(np.float32)


# ---- noise -------------------------------------------------------------------------------

def _hash(ix, iy, seed):
    h = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF).astype(np.float32) / 65535.0


def noise(P, scale=8.0, seed=1, octaves=1, gain=0.5):
    """Smooth value noise in 0..1 (fractal with octaves > 1). Integer hashing,
    so it is the same on every machine."""
    X, Y = P
    out = np.zeros_like(X)
    amp, tot, sc = 1.0, 0.0, float(scale)
    for o in range(octaves):
        x, y = X / sc, Y / sc
        ix, iy = np.floor(x), np.floor(y)
        fx, fy = x - ix, y - iy
        ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        ix, iy = ix.astype(np.int64), iy.astype(np.int64)
        a = _hash(ix, iy, seed + o)
        b = _hash(ix + 1, iy, seed + o)
        c = _hash(ix, iy + 1, seed + o)
        d = _hash(ix + 1, iy + 1, seed + o)
        out += amp * (a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy)
        tot += amp
        amp *= gain
        sc /= 2.0
    return (out / tot).astype(np.float32)


# ---- lighting ----------------------------------------------------------------------------

KEY = np.array([-0.55, -0.65, 0.52])          # the house key light: top left, in front
KEY = KEY / np.linalg.norm(KEY)


def sphere_normal(P, cx, cy, r):
    """Normals of a sphere seen head on (zero outside it)."""
    X, Y = P
    nx, ny = (X - cx) / r, (Y - cy) / r
    nz2 = 1 - nx * nx - ny * ny
    inside = nz2 > 0
    nz = np.sqrt(np.clip(nz2, 0, 1))
    return np.stack([np.where(inside, nx, 0), np.where(inside, ny, 0), np.where(inside, nz, 1)], -1).astype(np.float32)


def dome(cv, d, width=3.0, profile="round"):
    """Normals of a 2D shape (its distance field d) puffed up near its edge:
    flat in the middle, rounding over `width` pixels to the edge, like a
    pillow, a coin's rim or bevelled lettering. profile: round, bevel
    (straight 45-degree chamfer) or soft."""
    t = np.clip(-d / width, 0, 1)
    if profile == "round":
        h = np.sqrt(1 - (1 - t) ** 2)
    elif profile == "bevel":
        h = t
    else:
        h = t * t * (3 - 2 * t)
    h = h * width
    gy, gx = np.gradient(h, 1.0 / cv.s)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    return (n / np.linalg.norm(n, axis=-1, keepdims=True)).astype(np.float32)


def height_normal(cv, h, strength=1.0):
    """Normals of a height field (in pixels), e.g. noise for a bumpy surface."""
    gy, gx = np.gradient(h * strength, 1.0 / cv.s)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    return (n / np.linalg.norm(n, axis=-1, keepdims=True)).astype(np.float32)


def light(n, L=None, shininess=24.0, view=(0, 0, 1)):
    """(diffuse, specular) for normals n (..., 3) under the light L (default:
    the house key light). Diffuse is Lambert 0..1, specular Blinn-Phong."""
    L = KEY if L is None else np.asarray(L, dtype=np.float32) / np.linalg.norm(L)
    v = np.asarray(view, dtype=np.float32)
    hv = (L + v) / np.linalg.norm(L + v)
    dif = np.clip((n * L).sum(-1), 0, 1)
    spec = np.clip((n * hv).sum(-1), 0, 1) ** shininess
    return dif.astype(np.float32), spec.astype(np.float32)


def rim(n, power=3.0):
    """Light grazing the edge of a shape (from behind): 0 face on, 1 edge on."""
    return (1 - np.clip(n[..., 2], 0, 1)) ** power


def shade(base, dif, spec=None, amb=0.28, spec_col="#FFF6E0", spec_k=1.0, shadow_col=None):
    """A lit colour: `base` (hex or array) darkened toward `shadow_col` (by
    default base itself at ambient) where unlit, plus specular."""
    b = _colour(base)
    dif = np.asarray(dif, dtype=np.float32)[..., None]
    if shadow_col is None:
        out = b * (amb + (1 - amb) * dif)
    else:
        out = _colour(shadow_col) + (b - _colour(shadow_col)) * dif
    if spec is not None:
        out = out + _colour(spec_col) * (np.asarray(spec, dtype=np.float32)[..., None] * spec_k)
    return np.clip(out, 0, 1).astype(np.float32)


def ramp_map(t, colours):
    """t (0..1) through a list of colours, evenly spaced (a toon or a ramp)."""
    n = len(colours)
    return stops(t, [(k / (n - 1), c) for k, c in enumerate(colours)])
