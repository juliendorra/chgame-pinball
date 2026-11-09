"""Checks a picture for the faults the house style rules out.

    python -m artkit.lint PICTURE.png ...

    colours     own colours (11 at most) and whether the rainbow colour is used
    edges       the outer rows and columns: the installed border is drawn
                there, so they should be dark
    doubled     8x8 tiles with detail that are a 2x enlargement (pixel doubling)
    specks      lone pixels unlike all eight neighbours that are not part of a
                dither (worth a look: they read as noise)
    bar         how busy the install bar's rows (110-119) are (a note only)
"""
from __future__ import annotations

import sys

import numpy as np

from . import color as C


def _load(p):
    from PIL import Image
    if hasattr(p, "rgb_array"):
        return p.rgb_array()
    return np.asarray(Image.open(p).convert("RGB"))


def lint(pic, title_mask=None, title_colours=None):
    a = _load(pic)
    flat = a.reshape(-1, 3)
    cols = {tuple(c) for c in np.unique(flat, axis=0)}
    fixed = set(C.FIXED.values())
    own = [c for c in cols if c not in fixed]
    notes, stats = [], {"own": len(own), "rainbow": C.RAINBOW in cols}
    if len(own) > 11:
        notes.append(f"ERROR {len(own)} own colours (11 at most)")
    lum = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114) / 255.0
    border = np.concatenate([lum[0], lum[-1], lum[:, 0], lum[:, -1]])
    stats["edge_luma"] = round(float(border.mean()), 3)
    if (border > 0.55).mean() > 0.05:
        notes.append(f"edges: {int((border > 0.55).sum())} bright pixels on the outer rows/columns (the border goes there)")
    # pixel doubling: an 8x8 tile with 3+ colours that is a 2x enlargement
    key = a[..., 0].astype(np.int32) << 16 | a[..., 1].astype(np.int32) << 8 | a[..., 2]
    doubled = []
    for ty in range(0, 128, 8):
        for tx in range(0, 128, 8):
            t = key[ty:ty + 8, tx:tx + 8]
            if len(np.unique(t)) < 3:
                continue
            for ox in (0, 1):
                for oy in (0, 1):
                    tt = key[ty + oy:ty + oy + 8, tx + ox:tx + ox + 8]
                    if tt.shape != (8, 8):
                        continue
                    small = tt[::2, ::2]
                    if np.array_equal(np.repeat(np.repeat(small, 2, 0), 2, 1), tt):
                        doubled.append((tx, ty))
                        break
                else:
                    continue
                break
    stats["doubled_tiles"] = len(doubled)
    if len(doubled) > 2:
        notes.append(f"doubled: {len(doubled)} detailed 8x8 tiles look like 2x enlargements, e.g. {doubled[:4]}")
    # specks
    k = key
    diff_all = np.ones((126, 126), dtype=bool)
    c = k[1:-1, 1:-1]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                diff_all &= k[1 + dy:127 + dy, 1 + dx:127 + dx] != c
    # part of a dither if the same colour sits two away (a checker or a grid)
    pad = np.pad(k, 2, mode="edge")
    two = np.zeros((126, 126), dtype=bool)
    for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        two |= pad[3 + dy:129 + dy, 3 + dx:129 + dx] == c
    specks = diff_all & ~two
    ys, xs = np.nonzero(specks)
    stats["specks"] = int(specks.sum())
    if specks.sum() > 6:
        notes.append(f"specks: {int(specks.sum())} lone pixels, e.g. {[(int(x) + 1, int(y) + 1) for x, y in zip(xs[:6], ys[:6])]}")
    bar = key[110:120, 8:120]
    stats["bar_colours"] = int(len(np.unique(bar)))
    if title_mask is not None and title_colours:
        from .pixel import dilate
        area = dilate(title_mask, 1, True)
        tc = {C.rgb(c) for c in title_colours}
        stray = np.zeros((128, 128), dtype=bool)
        for t in tc:
            stray |= (a == np.array(t)).all(-1)
        stray &= ~area
        stats["title_colour_strays"] = int(stray.sum())
        if stray.sum():
            notes.append(f"title colours used outside the title: {int(stray.sum())} pixels")
    return notes, stats


def main(argv):
    rc = 0
    for p in argv:
        notes, stats = lint(p)
        print(f"{p}: {stats}")
        for n in notes:
            print("   ", n)
            if n.startswith("ERROR"):
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
