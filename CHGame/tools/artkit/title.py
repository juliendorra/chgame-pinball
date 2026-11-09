"""Titles: a 1-bit mask (a pixel font at its own size, set by fontscout.py
and committed as text art) dressed as box-art lettering, pixel by pixel.

From the back:
    shadow      the whole title's drop shadow (solid or a 50% checker)
    outline2    an outer rim round everything (optional)
    outline     the black outline round the letters and their extrusion
    extrude     the letters' depth: `depth` pixels toward (dx, dy), with a
                side colour and a bottom colour (or one per depth step)
    fill        the face: colour bands top to bottom (seams dithered, if
                asked), e.g. a chrome sky / horizon / ground
    bevel       a light edge on the top and left of each stroke, a dark one
                on the bottom and right (only where strokes are 3 px thick)
    glints      four-pointed sparkles

    m = load_mask(HERE / "art" / "title.txt")
    title(pic, m, x=8, y=6, fill=["gold3", "gold2", "gold1"], hi="cream",
          lo="gold0", extrude=dict(dx=1, dy=1, depth=3, side="wine", bottom="black"),
          shadow=dict(dx=2, dy=2, colour="black"), glints=[(12, 8)])

Returns the masks it drew ({'face', 'extrude', 'outline', 'all'}), so the
art can keep clear of them.
"""
from __future__ import annotations

import numpy as np

from .pixel import dilate, ring, shift, place, checker, sparkle, edge


def title(pic, m, x, y, fill, hi=None, lo=None, outline="black", outline2=None,
          extrude=None, shadow=None, glints=(), seam_dither=True, diag_outline=False,
          bevel_min=3, rows=None):
    M = place(m, x, y) if m.shape != pic.idx.shape else m.copy()
    ys = np.nonzero(M.any(axis=1))[0]
    top, bot = int(ys.min()), int(ys.max())
    # extrusion
    E = np.zeros_like(M)
    layers = []
    if extrude:
        dx, dy, depth = extrude.get("dx", 1), extrude.get("dy", 1), extrude.get("depth", 2)
        acc = M.copy()
        for k in range(1, depth + 1):
            L = shift(M, dx * k, dy * k) & ~acc
            layers.append(L)
            acc |= L
        E = acc & ~M
    body = M | E
    O = ring(body, diag_outline) if outline else np.zeros_like(M)
    O2 = ring(body | O, False) if outline2 else np.zeros_like(M)
    everything = body | O | O2
    # shadow
    if shadow:
        sdx, sdy = shadow.get("dx", 2), shadow.get("dy", 2)
        S = np.zeros_like(M)
        for k in range(1, max(abs(sdx), abs(sdy)) + 1):
            S |= shift(everything, int(round(sdx * k / max(abs(sdx), abs(sdy)))),
                       int(round(sdy * k / max(abs(sdx), abs(sdy)))))
        S &= ~everything
        if shadow.get("pattern") == "checker":
            S &= checker()
        pic.put(S, shadow.get("colour", "black"))
    if outline2:
        pic.put(O2, outline2)
    if outline:
        pic.put(O, outline)
    # extrusion colours
    if extrude:
        per = extrude.get("colours")
        if per:
            for k, L in enumerate(layers):
                pic.put(L, per[min(k, len(per) - 1)])
        else:
            side, bottom = extrude.get("side", "black"), extrude.get("bottom", extrude.get("side", "black"))
            dx, dy = extrude.get("dx", 1), extrude.get("dy", 1)
            # a pixel of the extrusion right under the face (or under more
            # extrusion that is) is the bottom face; the rest the side
            under = np.zeros_like(M)
            src = M.copy()
            for _ in range(extrude.get("depth", 2) + 1):
                nxt = shift(src, 0, 1) & E
                under |= nxt
                src = nxt
            pic.put(E & ~under, side)
            pic.put(E & under, bottom)
            if extrude.get("edge"):
                pic.put(ring(M, False) & E & (shift(M, 0, 1) | shift(M, 1, 0)), extrude["edge"])
    # the face
    if rows is not None:
        for j, c in enumerate(rows):
            r = top + j
            if r > bot:
                break
            pic.put(M & _row(M, r), c)
    else:
        n = len(fill)
        h = bot - top + 1
        band = [min(n - 1, int((r - top) * n / h)) for r in range(top, bot + 1)]
        ck = checker()
        for j, r in enumerate(range(top, bot + 1)):
            b = band[j]
            row = M & _row(M, r)
            pic.put(row, fill[b])
            if seam_dither and j > 0 and band[j - 1] != b:
                pic.put(row & ck, fill[band[j - 1]])
    # bevel
    if hi or lo:
        thick_v = M & shift(M, 0, 1) & shift(M, 0, -1)
        thick_h = M & shift(M, 1, 0) & shift(M, -1, 0)
        if lo:
            low = (edge(M, "bottom") & shift(thick_v, 0, 1)) | (edge(M, "right") & shift(thick_h, 1, 0))
            if bevel_min <= 2:
                low = edge(M, "bottom") | edge(M, "right")
            pic.put(low, lo)
        if hi:
            high = (edge(M, "top") & shift(thick_v, 0, -1)) | (edge(M, "left") & shift(thick_h, -1, 0))
            if bevel_min <= 2:
                high = edge(M, "top") | edge(M, "left")
            pic.put(high, hi)
    for g in glints:
        gx, gy = g[0], g[1]
        size = g[2] if len(g) > 2 else 2
        sparkle(pic, gx, gy, size, "cream")
    return {"face": M, "extrude": E, "outline": O | O2, "all": everything}


def _row(M, r):
    out = np.zeros_like(M)
    out[r, :] = True
    return out


def centred_x(m, width=128):
    return (width - m.shape[1]) // 2


def embolden(m, dx=1):
    """A heavier face: every stroke one pixel wider to the right."""
    return m | shift(m, dx, 0)


def glow(pic, m, colours, pattern="checker"):
    """A halo round a mask: one ring per colour, outermost last, each ring
    after the first a 50% checker (a dithered fall-off)."""
    acc = m.copy()
    ck = checker()
    for k, c in enumerate(colours):
        r = dilate(acc, 1, diag=k > 0) & ~acc
        if k > 0 and pattern == "checker":
            pic.put(r & ck, c)
        else:
            pic.put(r, c)
        acc |= r
    return acc
