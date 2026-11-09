"""A small ray marcher for the props that want real form: dice, chips,
balls, chess pieces, a roulette wheel. Scenes are signed distance trees;
every hit carries a material; the result is painted onto a Canvas like any
other shape, and the quantiser turns the shading into ramps and dither.

World: x right, y up, z toward the viewer. Units are free; the camera
frames them.

    from artkit import render3d as R
    mats = [R.Mat("#E8E0D0", spec=0.6, shin=40), R.Mat("#101010", spec=0.2)]
    die = R.Sub(R.prim(R.box((1, 1, 1), 0.18), 0),
                R.U(*[R.xf(R.prim(R.sphere(0.2), 1), p) for p in pips]))
    scene = R.xf(die, (0, 1, 0), R.rot_y(30) @ R.rot_x(-20))
    cam = R.Camera((0, 3, 6), (0, 1, 0), fov=30)
    out = R.render(cv, scene, cam, mats)
    R.paint(cv, out, {0: cv.new_id("die"), 1: cv.new_id("pips")})
"""
from __future__ import annotations

import numpy as np

from . import canvas as cvs
from . import color as C


# ---- materials ------------------------------------------------------------------

class Mat:
    """A surface: base colour (hex), specular strength and shininess, mirror
    reflection (0..1), rim light, emission, and an optional texture
    tex(p, n) -> (M, 3) colours in 0..1 that replaces the base colour."""

    def __init__(self, colour, spec=0.3, shin=24.0, refl=0.0, rim=0.0, rim_col="#FFFFFF", emit=0.0,
                 amb=1.0, tex=None, spec_col="#FFF8E8", shadow_col=None):
        self.col = C.to_float(colour)
        self.spec, self.shin, self.refl = spec, shin, refl
        self.rim, self.rim_col, self.emit, self.amb = rim, C.to_float(rim_col), emit, amb
        self.tex, self.spec_col = tex, C.to_float(spec_col)
        self.shadow_col = None if shadow_col is None else C.to_float(shadow_col)


# ---- distance primitives (p: (M, 3) points in the primitive's own frame) ----------------

def sphere(r):
    return lambda p: np.linalg.norm(p, axis=1) - r


def box(half, r=0.0):
    h = np.asarray(half, dtype=np.float64) - r

    def f(p):
        q = np.abs(p) - h
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - r
    return f


def cylinder(r, h, rr=0.0):
    """A cylinder along y: radius r, half height h, edges rounded by rr."""
    def f(p):
        d0 = np.hypot(p[:, 0], p[:, 2]) - r + rr
        d1 = np.abs(p[:, 1]) - h + rr
        return np.minimum(np.maximum(d0, d1), 0) + np.hypot(np.maximum(d0, 0), np.maximum(d1, 0)) - rr
    return f


def torus(R, r):
    """A ring in the xz plane."""
    return lambda p: np.hypot(np.hypot(p[:, 0], p[:, 2]) - R, p[:, 1]) - r


def plane(y=0.0):
    return lambda p: p[:, 1] - y


def capsule(a, b, r):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    ab = b - a

    def f(p):
        t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
        return np.linalg.norm(p - a - t[:, None] * ab, axis=1) - r
    return f


def lathe(profile):
    """A solid of revolution about y: `profile` is a closed outline of
    (radius, y) points (include the axis, radius 0, so it closes there)."""
    pts = [(float(r), float(y)) for r, y in profile]

    def f(p):
        q = (np.hypot(p[:, 0], p[:, 2]), p[:, 1])
        return cvs.polygon(q, pts)
    return f


def extrude(fn2d, h):
    """A 2D distance field fn2d(x, y) given depth 2h along z."""
    def f(p):
        d = fn2d(p[:, 0], p[:, 1])
        wz = np.abs(p[:, 2]) - h
        return np.minimum(np.maximum(d, wz), 0) + np.hypot(np.maximum(d, 0), np.maximum(wz, 0))
    return f


# ---- the tree: nodes take points and give (distance, material) -------------------------

def prim(fn, mat):
    return lambda p: (fn(p), np.full(len(p), mat, dtype=np.int16))


def U(*nodes):
    def f(p):
        d, m = nodes[0](p)
        for n in nodes[1:]:
            d2, m2 = n(p)
            s = d2 < d
            d, m = np.where(s, d2, d), np.where(s, m2, m)
        return d, m
    return f


def SU(a, b, k=0.1):
    """Smooth union (the material of whichever is nearer)."""
    def f(p):
        da, ma = a(p)
        db, mb = b(p)
        h = np.clip(0.5 + 0.5 * (db - da) / k, 0, 1)
        return db + (da - db) * h - k * h * (1 - h), np.where(da < db, ma, mb)
    return f


def Sub(a, b):
    """a with b cut out of it; the cut's surface has b's material."""
    def f(p):
        da, ma = a(p)
        db, mb = b(p)
        s = -db > da
        return np.where(s, -db, da), np.where(s, mb, ma)
    return f


def Inter(a, b):
    def f(p):
        da, ma = a(p)
        db, mb = b(p)
        s = db > da
        return np.where(s, db, da), np.where(s, mb, ma)
    return f


def xf(node, pos=(0, 0, 0), rot=None, scale=1.0):
    """The node moved to `pos`, turned by `rot` (a 3x3 matrix), scaled."""
    pos = np.asarray(pos, dtype=np.float64)
    R = np.eye(3) if rot is None else np.asarray(rot, dtype=np.float64)

    def f(p):
        q = ((p - pos) @ R) / scale                 # R^T (p - pos): into the node's frame
        d, m = node(q)
        return d * scale, m
    return f


def rot_x(deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# ---- camera --------------------------------------------------------------------------

class Camera:
    """A pinhole camera at `pos` looking at `target`; fov is the vertical
    field of view in degrees across the whole 128-pixel picture. ortho=H
    makes it orthographic, H world units tall. shift=(sx, sy) slides the
    picture (in pixels) without turning the camera (a lens shift)."""

    def __init__(self, pos, target, fov=35.0, up=(0, 1, 0), ortho=None, shift=(0, 0)):
        self.pos = np.asarray(pos, dtype=np.float64)
        f = np.asarray(target, dtype=np.float64) - self.pos
        self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, np.asarray(up, dtype=np.float64))
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.fov, self.ortho, self.shift = fov, ortho, shift

    def rays(self, X, Y):
        sx = (X - 64.0 - self.shift[0]) / 64.0
        sy = -(Y - 64.0 - self.shift[1]) / 64.0
        if self.ortho:
            h = self.ortho / 2
            o = self.pos + (sx[:, None] * h) * self.r + (sy[:, None] * h) * self.u
            d = np.broadcast_to(self.f, o.shape).copy()
        else:
            k = np.tan(np.radians(self.fov) / 2)
            d = self.f + (sx[:, None] * k) * self.r + (sy[:, None] * k) * self.u
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            o = np.broadcast_to(self.pos, d.shape).copy()
        return o, d

    def project(self, p):
        """Where the world point p lands on the picture (pixels)."""
        v = np.asarray(p, dtype=np.float64) - self.pos
        z = v @ self.f
        if self.ortho:
            sx, sy = (v @ self.r) / (self.ortho / 2), (v @ self.u) / (self.ortho / 2)
        else:
            k = np.tan(np.radians(self.fov) / 2)
            sx, sy = (v @ self.r) / z / k, (v @ self.u) / z / k
        return 64.0 + sx * 64.0 + self.shift[0], 64.0 - sy * 64.0 + self.shift[1]


def _grid(cv, region, ss):
    """The samples to trace: flat indices into a grid of ss samples a pixel
    (the canvas's own, or coarser to save time), their coordinates, and how
    to spread the results back over the canvas."""
    k = 1 if not ss or ss >= cv.s else cv.s // ss
    n = cv.N // k
    if region:
        x0, y0, x1, y1 = (int(round(v * cv.s / k)) for v in region)
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(n, x1), min(n, y1)
    else:
        x0, y0, x1, y1 = 0, 0, n, n
    ys, xs = np.mgrid[y0:y1, x0:x1]
    flat = (ys * n + xs).reshape(-1)
    X = (xs.reshape(-1) + 0.5) * k / cv.s
    Y = (ys.reshape(-1) + 0.5) * k / cv.s
    return flat, X.astype(np.float64), Y.astype(np.float64), n, k


def _spread(a, n, k):
    """A coarse grid's result (n*n, ...) back onto the canvas's (N, N, ...)."""
    a = a.reshape((n, n) + a.shape[1:])
    return np.repeat(np.repeat(a, k, 0), k, 1) if k > 1 else a


# ---- marching ------------------------------------------------------------------------

def _march(scene, o, d, steps, tmax, eps):
    M = len(o)
    t = np.zeros(M)
    hit = np.zeros(M, dtype=bool)
    mat = np.full(M, -1, dtype=np.int16)
    act = np.arange(M)
    for _ in range(steps):
        if not len(act):
            break
        p = o[act] + d[act] * t[act, None]
        dist, m = scene(p)
        done = dist < eps * (1 + t[act])
        hit[act[done]] = True
        mat[act[done]] = m[done]
        t[act] += np.where(done, 0, dist * 0.92)
        far = t[act] > tmax
        act = act[~done & ~far]
    return t, hit, mat


def _normal(scene, p, h=1e-3):
    k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], dtype=np.float64)
    n = np.zeros_like(p)
    for v in k:
        n += v * scene(p + v * h)[0][:, None]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def _shadow(scene, p, L, k=10.0, steps=40, tmax=20.0):
    res = np.ones(len(p))
    t = np.full(len(p), 0.02)
    for _ in range(steps):
        dist = scene(p + L * t[:, None])[0]
        res = np.minimum(res, np.clip(k * dist / t, 0, 1))
        t += np.clip(dist, 0.01, 0.5)
        if (t > tmax).all():
            break
    return np.clip(res, 0, 1)


def _ao(scene, p, n, k=1.5):
    occ = np.zeros(len(p))
    w = 1.0
    for i in range(1, 6):
        h = 0.04 * i
        occ += w * (h - scene(p + n * h)[0])
        w *= 0.7
    return np.clip(1 - k * occ, 0, 1)


def default_env(d):
    """Reflections: a warm ceiling glow above, the dark room around, felt
    green below."""
    y = d[:, 1]
    sky = np.array([1.0, 0.92, 0.72])
    room = np.array([0.08, 0.06, 0.06])
    floor = np.array([0.02, 0.18, 0.08])
    a = np.clip(y * 2.0, 0, 1)[:, None] ** 1.5
    b = np.clip(-y * 3.0, 0, 1)[:, None]
    return room + (sky - room) * a + (floor - room) * b


def render(cv, scene, cam, mats, lights=None, ambient="#3A3448", env=None, steps=160, tmax=60.0,
           eps=4e-4, shadows=True, ao=True, region=None, ss=None):
    """Marches a ray per canvas sample (within `region` = (x0, y0, x1, y1)
    in pixels, the whole picture by default) and shades the hits. ss=2
    traces 2x2 rays a pixel instead of the canvas's 4x4: a quarter of the
    time, still smooth edges.

    lights: [(direction toward the light, colour, strength)]; by default the
    house key light from the top left and a cool fill from the right.
    Returns {rgb (N, N, 3), alpha (N, N), mat (N, N; -1 where nothing),
    depth (N, N), normal (N, N, 3)}."""
    if lights is None:
        lights = [((-0.55, 0.75, 0.45), "#FFF0D8", 1.0), ((0.8, 0.2, 0.3), "#6080C0", 0.35)]
    L = [(np.asarray(v, dtype=np.float64) / np.linalg.norm(v), C.to_float(c).astype(np.float64), k) for v, c, k in lights]
    amb = C.to_float(ambient).astype(np.float64)
    env = env or default_env
    flat, X, Y, n, k = _grid(cv, region, ss)
    o, d = cam.rays(X, Y)
    t, hit, mat = _march(scene, o, d, steps, tmax, eps)
    rgb = np.zeros((len(flat), 3))
    nrm = np.zeros((len(flat), 3))
    hi = np.nonzero(hit)[0]
    if len(hi):
        p = o[hi] + d[hi] * t[hi, None]
        nh = _normal(scene, p)
        nrm[hi] = nh
        rgb[hi] = _shade(scene, p, nh, d[hi], mat[hi], mats, L, amb, env, shadows, ao, steps, tmax, eps)
    out_rgb = np.zeros((n * n, 3), dtype=np.float32)
    out_a = np.zeros(n * n, dtype=np.float32)
    out_m = np.full(n * n, -1, dtype=np.int16)
    out_z = np.full(n * n, np.inf, dtype=np.float32)
    out_n = np.zeros((n * n, 3), dtype=np.float32)
    out_rgb[flat] = rgb
    out_a[flat] = hit
    out_m[flat] = np.where(hit, mat, -1)
    out_z[flat] = np.where(hit, t, np.inf)
    out_n[flat] = nrm
    return {"rgb": _spread(out_rgb, n, k), "alpha": _spread(out_a, n, k), "mat": _spread(out_m, n, k),
            "depth": _spread(out_z, n, k), "normal": _spread(out_n, n, k)}


def _shade(scene, p, n, v, mat, mats, L, amb, env, shadows, ao, steps, tmax, eps, bounce=True):
    col = np.zeros((len(p), 3))
    occ = _ao(scene, p, n) if ao else np.ones(len(p))
    sh = []
    for Ld, Lc, Lk in L:
        sh.append(_shadow(scene, p + n * 2e-3, Ld) if shadows else np.ones(len(p)))
    for k, m in enumerate(mats):
        sel = mat == k
        if not sel.any():
            continue
        pp, nn, vv = p[sel], n[sel], v[sel]
        base = m.tex(pp, nn) if m.tex else np.broadcast_to(m.col, (len(pp), 3))
        if m.shadow_col is not None:                 # unlit is shadow_col, lit goes to base
            c = np.broadcast_to(m.shadow_col * m.amb, (len(pp), 3)) * occ[sel, None]
        else:
            c = base * amb * m.amb * occ[sel, None]
        for (Ld, Lc, Lk), s in zip(L, sh):
            dif = np.clip(nn @ Ld, 0, 1) * s[sel]
            if m.shadow_col is not None:
                c = c + (base - m.shadow_col) * (dif * Lk)[:, None] * Lc
            else:
                c = c + base * (dif * Lk)[:, None] * Lc
            h = Ld - vv
            h /= np.linalg.norm(h, axis=1, keepdims=True)
            spec = np.clip((nn * h).sum(1), 0, 1) ** m.shin * s[sel] * Lk
            c = c + m.spec * spec[:, None] * m.spec_col * Lc
        if m.rim:
            c = c + m.rim * ((1 - np.clip(-(nn * vv).sum(1), 0, 1)) ** 3)[:, None] * m.rim_col
        if m.emit:
            c = c + base * m.emit
        if m.refl and bounce:
            r = vv - 2 * (vv * nn).sum(1)[:, None] * nn
            ro = pp + nn * 4e-3
            t2, h2, m2 = _march(scene, ro, r, steps // 2, tmax, eps)
            rc = env(r)
            j = np.nonzero(h2)[0]
            if len(j):
                p2 = ro[j] + r[j] * t2[j, None]
                n2 = _normal(scene, p2)
                rc[j] = _shade(scene, p2, n2, r[j], m2[j], mats, L, amb, env, False, False, steps, tmax, eps, bounce=False)
            c = c * (1 - m.refl) + rc * m.refl
        col[sel] = c
    return np.clip(col, 0, 1)


def ground(cv, scene, cam, y=0.0, light=(-0.55, 0.75, 0.45), region=None, k=8.0, ao=True, ss=None):
    """The shadow the scene casts on the floor plane at height y (and the
    darkening where things stand on it), as an (N, N) darkness 0..1 to paint
    over a painted floor: cv.paint(dark * 0.8, '#000000')."""
    flat, X, Y, n, kk = _grid(cv, region, ss)
    o, d = cam.rays(X, Y)
    down = d[:, 1] < -1e-6
    t = np.where(down, (y - o[:, 1]) / np.where(down, d[:, 1], -1), np.inf)
    ok = np.isfinite(t) & (t > 0)
    dark = np.zeros(len(flat))
    idx = np.nonzero(ok)[0]
    if len(idx):
        p = o[idx] + d[idx] * t[idx, None]
        Ld = np.asarray(light, dtype=np.float64)
        Ld = Ld / np.linalg.norm(Ld)
        s = _shadow(scene, p + np.array([0, 2e-3, 0]), Ld, k=k)
        occ = _ao(scene, p, np.tile([0.0, 1.0, 0.0], (len(p), 1)), k=2.5) if ao else np.ones(len(p))
        dark[idx] = 1 - s * occ
    out = np.zeros(n * n, dtype=np.float32)
    out[flat] = dark
    return _spread(out, n, kk)


def majority(out, s):
    """Each pixel's material in a render: the one most of its s x s samples
    hit (-1: nothing), at picture size. For painting surfaces pixel by pixel
    (artkit.paint) instead of through the quantiser."""
    n = out["mat"].shape[0] // s
    m = out["mat"].reshape(n, s, n, s).transpose(0, 2, 1, 3).reshape(n, n, s * s)
    best = np.full((n, n), -1, np.int64)
    cnt = (m == -1).sum(-1)
    for k in np.unique(m):
        if k < 0:
            continue
        c = (m == k).sum(-1)
        best = np.where(c > cnt, k, best)
        cnt = np.maximum(c, cnt)
    return best


def paint(cv, out, oids=None, dither=None, mats_dither=None):
    """Paints a render onto the canvas: each material's pixels with its
    object id (oids {material: oid}; one id for all if an int)."""
    for k in np.unique(out["mat"]):
        if k < 0:
            continue
        sel = (out["mat"] == k).astype(np.float32) * out["alpha"]
        oid = oids.get(int(k)) if isinstance(oids, dict) else oids
        dk = (mats_dither or {}).get(int(k), dither)
        cv.paint(sel, out["rgb"], dither=dk, oid=oid)
