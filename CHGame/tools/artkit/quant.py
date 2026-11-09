"""From the canvas's true colour to the picture's 16 colours.

The palette is the picture's own colours (11 at most, named) plus the menu's
fixed four (cream, grey, black, red), which count against nothing, and the
rainbow colour (index 15), which the quantiser never picks: paint it on
purpose (pixel.py).

The quantiser is a positional ordered dither in the manner of Joel
Yliluoma's: each pixel takes the best "plan", either one colour or two
colours mixed at a fixed ratio, and a Bayer matrix decides which of the two
each pixel shows. Only pairs the palette allows can mix: neighbours in a ramp
(ramps=) or colours close enough to each other (auto). That keeps the dither
clean: a gradient goes dark-to-mid-to-light, never through a stray colour.

Each pixel's dither strength (the canvas's dith) limits the ratios: below
0.25 a pixel is the nearest colour, below 0.75 a 50% checker at most, above
that quarters too. Object edges get none by default (Canvas.downsample),
so outlines and anti-aliasing come out clean.
"""
from __future__ import annotations

import numpy as np

from . import color as C

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)
THRESH = {"bayer4": (BAYER4 + 0.5) / 16.0,
          "checker": np.array([[0.25, 0.75], [0.75, 0.25]], dtype=np.float32)}


class Palette:
    """The picture's colours by name.

        P = Palette({"felt0": "#06301C", "felt1": "#0E5A30", ...},
                    ramps=[["black", "felt0", "felt1", "felt2"], ...])

    own: up to 11 named colours (snapped to RGB565 unless snap=False).
    ramps: lists of names, dark to light; neighbours in a ramp may dither.
    pairs: more name pairs that may dither.
    auto: without ramps, any two colours closer than this (OKLab) may dither.
    fixed: which of the menu's four the quantiser may use (all by default).
    """

    def __init__(self, own, ramps=None, pairs=None, auto=0.16, fixed=("black", "cream", "grey", "red"), snap=True):
        if len(own) > 11:
            raise ValueError(f"{len(own)} own colours; 11 at most")
        self.names = list(own)
        self.rgb = [None] * 16
        self.index = {}
        for k, (name, hexc) in enumerate(own.items()):
            if name in C.FIXED:
                raise ValueError(f"{name!r} is one of the fixed colours' names")
            self.rgb[k] = C.snap565(hexc) if snap else C.rgb(hexc)
            self.index[name] = k
        for name, k in C.FIXED_INDEX.items():
            self.rgb[k] = C.FIXED[name]
            self.index[name] = k
        for k in range(16):
            if self.rgb[k] is None:
                self.rgb[k] = (0, 0, 0)
        own_set = {self.rgb[self.index[n]] for n in self.names}
        clash = own_set & set(C.FIXED.values())
        if clash:
            raise ValueError(f"own colours equal to fixed ones: {clash}; use the fixed name instead")
        self.usable = [self.index[n] for n in self.names] + [C.FIXED_INDEX[f] for f in fixed]
        self.lab = C.srgb_to_oklab(np.array(self.rgb, dtype=np.float64) / 255.0)
        pr = set()
        for r in ramps or []:
            ids = [self[n] for n in r]
            for a, b in zip(ids, ids[1:]):
                pr.add((min(a, b), max(a, b)))
        for a, b in pairs or []:
            a, b = self[a], self[b]
            pr.add((min(a, b), max(a, b)))
        if not ramps and auto:
            for i in self.usable:
                for j in self.usable:
                    if i < j and np.linalg.norm(self.lab[i] - self.lab[j]) < auto:
                        pr.add((i, j))
        self.pairs = sorted(pr)

    def __getitem__(self, name):
        if isinstance(name, (int, np.integer)):
            return int(name)
        return self.index[name]

    def hex(self, name):
        return C.hexs(self.rgb[self[name]])

    def sheet(self):
        """The palette as text, for a look."""
        return "\n".join(f"{k:2d} {n:10s} {C.hexs(self.rgb[k])}" for n, k in sorted(self.index.items(), key=lambda x: x[1]))


def quantize(cv, palette, exclude=(), allow=None, edge_dither=0.0, matrix="bayer4", penalty=0.5, phase=(0, 0)):
    """The canvas as a Picture in `palette`.

    exclude: names the art may not use (a title's own colours, say).
    allow: {object id or name: [names]}: what an object's pixels may use.
    penalty: how much a mix of two distant colours is avoided (Yliluoma's
    psychovisual term): higher is cleaner, lower is closer in colour.
    matrix: bayer4 (quarters and halves) or checker (halves only).
    phase: shifts the dither pattern (x, y)."""
    rgb, dith, oid = cv.downsample(edge_dither)
    rgb = np.round(rgb * 1024.0) / 1024.0                    # the same on every machine
    n = rgb.shape[0]
    px = C.srgb_to_oklab(rgb.reshape(-1, 3).astype(np.float64))
    d = dith.reshape(-1)
    P = px.shape[0]
    pal = palette.lab
    usable = [k for k in palette.usable if k not in {palette[e] for e in exclude}]
    ok = np.zeros((P, 16), dtype=bool)
    ok[:, usable] = True
    if allow:
        o = oid.reshape(-1)
        for key, names in allow.items():
            k = cv.id_of(key) if isinstance(key, str) else key
            m = o == k
            row = np.zeros(16, dtype=bool)
            row[[palette[nm] for nm in names]] = True
            ok[m] = row & ok[m]
    # one colour
    e1 = ((px[:, None, :] - pal[None, :, :]) ** 2).sum(-1)
    e1 = np.where(ok, e1, np.inf)
    best1 = np.argmin(e1, axis=1)
    err = e1[np.arange(P), best1]
    ca = best1.copy()
    cb = best1.copy()
    tq = np.zeros(P)
    # two colours mixed
    steps = 4 if matrix == "bayer4" else 2
    for a, b in palette.pairs:
        if a not in usable or b not in usable:
            continue
        both = ok[:, a] & ok[:, b] & (d >= 0.25)
        if not both.any():
            continue
        va, vb = pal[a], pal[b]
        ab = vb - va
        L2 = float((ab * ab).sum())
        if L2 < 1e-12:
            continue
        t = np.clip(((px - va) * ab).sum(-1) / L2, 0, 1)
        st = np.where(d >= 0.75, steps, 2)
        t = np.round(t * st) / st
        mixc = va[None, :] + t[:, None] * ab[None, :]
        e = ((px - mixc) ** 2).sum(-1) + penalty * t * (1 - t) * L2
        better = both & (e < err - 1e-12) & (t > 0) & (t < 1)
        err = np.where(better, e, err)
        ca = np.where(better, a, ca)
        cb = np.where(better, b, cb)
        tq = np.where(better, t, tq)
    th = THRESH[matrix]
    yy, xx = np.mgrid[0:n, 0:n]
    thr = th[(yy + phase[1]) % th.shape[0], (xx + phase[0]) % th.shape[1]].reshape(-1)
    idx = np.where(thr < tq, cb, ca).reshape(n, n).astype(np.uint8)
    return Picture(idx, palette, oid=oid, dith=dith, names=dict(cv.names))


class Picture:
    """A picture as palette indices (128 x 128, uint8) with its palette, and
    the canvas's object map at pixel size (for outlines and masks)."""

    def __init__(self, idx, palette, oid=None, dith=None, names=None):
        self.idx = idx
        self.pal = palette
        self.oid = oid if oid is not None else np.zeros_like(idx, dtype=np.int16)
        self.dith = dith
        self.names = names or {0: "background"}

    @classmethod
    def blank(cls, palette, colour="black"):
        return cls(np.full((128, 128), palette[colour], dtype=np.uint8), palette)

    def copy(self):
        return Picture(self.idx.copy(), self.pal, self.oid.copy(), None if self.dith is None else self.dith.copy(), dict(self.names))

    def obj(self, name_or_id):
        """Pixels whose majority object is this one."""
        k = name_or_id
        if isinstance(k, str):
            k = next(i for i, v in self.names.items() if v == k)
        return self.oid == k

    def put(self, mask, colour):
        self.idx[mask] = self.pal[colour]

    def px(self, x, y, colour):
        if 0 <= x < self.idx.shape[1] and 0 <= y < self.idx.shape[0]:
            self.idx[y, x] = self.pal[colour]

    def where(self, *colours):
        ids = [self.pal[c] for c in colours]
        return np.isin(self.idx, ids)

    def rgb_array(self):
        lut = np.array(self.pal.rgb, dtype=np.uint8)
        return lut[self.idx]

    def image(self):
        from PIL import Image
        return Image.fromarray(self.rgb_array(), "RGB")

    def png(self):
        import boxart
        return boxart.png(self.image())

    def preview(self, path, scale=4):
        """A nearest-neighbour enlargement, for looking at."""
        from PIL import Image
        im = self.image()
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        im.save(path)
        return path

    def used(self):
        return sorted(set(np.unique(self.idx).tolist()))

    def own_count(self):
        return sum(1 for k in self.used() if k < 11)


def from_png(path, palette=None):
    """A Picture from a PNG that follows the rule (for touching up)."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    cols = {}
    idx = np.zeros(a.shape[:2], dtype=np.uint8)
    if palette is None:
        uniq = [tuple(c) for c in np.unique(a.reshape(-1, 3), axis=0)]
        own = {}
        for c in uniq:
            if c not in C.FIXED.values():
                own[f"c{len(own)}"] = C.hexs(c)
        palette = Palette(own, snap=False)
    for k, c in enumerate(palette.rgb):
        cols.setdefault(c, k)
    flat = a.reshape(-1, 3)
    idx = np.array([cols[tuple(c)] for c in flat], dtype=np.uint8).reshape(a.shape[:2])
    return Picture(idx, palette)


def save_png(pic, path):
    """Checks the picture rule and writes the PNG (only if it changed)."""
    import boxart
    return boxart.save(pic.image(), path)
