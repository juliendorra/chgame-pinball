"""Work on the finished pixels (a quant.Picture): masks, outlines, shadows,
clean-up, bitmap text and hand-placed pixels.

Masks are (128, 128) bool arrays. Colours are palette names ('black',
'cream', 'rainbow', or the picture's own).
"""
from __future__ import annotations

import json
import pathlib

import numpy as np


def shift(m, dx, dy):
    """The mask moved by (dx, dy) pixels (what falls off is lost)."""
    out = np.zeros_like(m)
    h, w = m.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs1 > xs0 and ys1 > ys0:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return out


def dilate(m, n=1, diag=False):
    out = m.copy()
    for _ in range(n):
        g = out.copy()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g |= shift(out, dx, dy)
        if diag:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                g |= shift(out, dx, dy)
        out = g
    return out


def erode(m, n=1, diag=False):
    return ~dilate(~m, n, diag)


def ring(m, diag=False):
    """The pixels just outside the mask."""
    return dilate(m, 1, diag) & ~m


def edge(m, side):
    """Pixels of the mask whose neighbour on `side` (top, bottom, left,
    right) is outside it."""
    d = {"top": (0, 1), "bottom": (0, -1), "left": (1, 0), "right": (-1, 0)}[side]
    return m & ~shift(m, *d)


def checker(shape=(128, 128), phase=0):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return (xx + yy + phase) % 2 == 0


def outline(pic, m, colour="black", diag=False, where=None):
    """Draws a 1 px outline round the mask (4-connected, or 8 with diag)."""
    r = ring(m, diag)
    if where is not None:
        r &= where
    pic.put(r, colour)
    return r


def selout(pic, m, dark, light=None, diag=False):
    """A selective outline: `dark` on the shadow side (bottom, right) and
    `light` (or nothing) on the lit side (top, left)."""
    r = ring(m, diag)
    lit = r & (shift(m, 0, -1) | shift(m, -1, 0))    # the ring above or left of the shape
    if light is not None:
        pic.put(lit, light)
        pic.put(r & ~lit, dark)
    else:
        pic.put(r & ~lit, dark)
    return r


def drop_shadow(pic, m, dx=1, dy=1, colour="black", pattern=None):
    """The mask's shadow, moved by (dx, dy), where the mask is not.
    pattern='checker' makes it a 50% shadow."""
    s = shift(m, dx, dy) & ~m
    if pattern == "checker":
        s &= checker()
    pic.put(s, colour)
    return s


def clean_orphans(pic, protect=None, max_dither=0.25):
    """Single pixels whose four neighbours all share one other colour take
    that colour, except where the quantiser was dithering (pic.dith above
    max_dither) or `protect` says so. Returns how many changed."""
    a = pic.idx
    up, dn = np.roll(a, 1, 0), np.roll(a, -1, 0)
    lf, rt = np.roll(a, 1, 1), np.roll(a, -1, 1)
    lone = (up == dn) & (lf == rt) & (up == lf) & (up != a)
    lone[0, :] = lone[-1, :] = lone[:, 0] = lone[:, -1] = False
    if pic.dith is not None:
        lone &= pic.dith <= max_dither
    if protect is not None:
        lone &= ~protect
    a[lone] = up[lone]
    return int(lone.sum())


def patch(pic, x, y, rows, key):
    """Hand-placed pixels: `rows` of characters, `key` {char: colour}; any
    character not in key is left alone."""
    if isinstance(rows, str):
        rows = [r for r in rows.strip("\n").split("\n")]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in key:
                pic.px(x + i, y + j, key[ch])


def sparkle(pic, x, y, size=2, colour="cream", centre=None):
    """A four-pointed glint: a centre pixel and arms `size` long."""
    pic.px(x, y, centre or colour)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            pic.px(x + dx, y + dy, colour)


# ---- bitmap masks and fonts ------------------------------------------------------------

def load_mask(path):
    """A 1-bit mask from text art: '#' (or 'X', '1') ink, anything else none.
    Lines starting with '//' are comments (the font's credit)."""
    rows = [ln.rstrip("\n") for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if not r.startswith("//") and r.strip() != ""]
    w = max(len(r) for r in rows)
    return np.array([[ch in "#X1" for ch in r.ljust(w)] for r in rows], dtype=bool)


def mask_rows(m):
    return ["".join("#" if v else "." for v in row) for row in m]


def place(m, x, y, size=(128, 128)):
    """A small mask on a picture-sized one, its top-left corner at (x, y)."""
    out = np.zeros(size, dtype=bool)
    h, w = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(size[1], x + w), min(size[0], y + h)
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = m[y0 - y:y1 - y, x0 - x:x1 - x]
    return out


class Font:
    """A bitmap font from a JSON file (fontscout.py exports them): glyphs as
    [w, h, x, y, adv, rows] with y measured from the font's top line."""

    def __init__(self, path):
        d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        self.meta = {k: v for k, v in d.items() if k != "glyphs"}
        self.g = d["glyphs"]
        self.space = d.get("space") or max(2, round(sum(g[4] for g in self.g.values()) / max(1, len(self.g)) / 2))

    def glyph(self, ch):
        g = self.g.get(ch) or self.g.get(ch.upper()) or self.g.get(ch.lower())
        return g

    def mask(self, text, gap=0):
        items, pen = [], 0
        x0 = y0 = 10 ** 9
        x1 = y1 = -10 ** 9
        for ch in text:
            g = self.glyph(ch)
            if g is None or (ch == " " and not g[0]):
                pen += (g[4] if g and g[4] else self.space) + gap
                continue
            w, h, gx, gy, adv, rows = g
            if w:
                items.append((pen + gx, gy, rows))
                x0, x1 = min(x0, pen + gx), max(x1, pen + gx + w)
                y0, y1 = min(y0, gy), max(y1, gy + h)
            pen += adv + gap
        if not items:
            return np.zeros((1, 1), dtype=bool)
        m = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        for gx, gy, rows in items:
            for j, r in enumerate(rows):
                for i, ch in enumerate(r):
                    if ch in "#1":
                        m[gy - y0 + j, gx - x0 + i] = True
        return m

    def text(self, pic, s, x, y, colour, gap=0, align="left", shadow=None):
        """Draws s; align: left (x is the left edge), centre (x the middle),
        right. shadow: a colour drawn 1 px down and right first."""
        m = self.mask(s, gap)
        if align == "centre":
            x = x - m.shape[1] // 2
        elif align == "right":
            x = x - m.shape[1]
        M = place(m, x, y)
        if shadow:
            pic.put(shift(M, 1, 1) & ~M, shadow)
        pic.put(M, colour)
        return M
