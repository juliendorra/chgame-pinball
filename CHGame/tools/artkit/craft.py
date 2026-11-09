"""The pixel-art conventions a program can check, on a sprite or picture of
any size (docs/pixel-art.md is the whole guide).

    python -m artkit.craft IMAGE.png ...        orphans and jaggies, per colour cluster and silhouette

orphans   pixels none of whose eight neighbours share their colour, and no
          pixel two away does either (so not part of a dither): noise,
          unless a deliberate glint
jaggies   kinks in a curve's staircase. Along one quarter of an edge, the
          runs of a curve going from flat to steep must only shorten
          (3, 2, 2, 1) and then the vertical runs only lengthen (1, 2, 3);
          a run that breaks that order (3, 1, 3) is a jaggie. Checked on
          the silhouette (opaque vs transparent) and on each colour's
          clusters of at least `min_size` pixels.

From Python: craft.orphans(idx), craft.jaggies(mask), craft.report(idx).
idx is a 2D array of colour indices (or RGB, which is keyed), with
`transparent` for the background.
"""
from __future__ import annotations

import sys

import numpy as np


def _key(a):
    a = np.asarray(a)
    if a.ndim == 3:
        a = a.astype(np.int64)
        return a[..., 0] << 16 | a[..., 1] << 8 | a[..., 2]
    return a.astype(np.int64)


def orphans(idx, transparent=None):
    """[(x, y)] of lone pixels (not counting a regular dither)."""
    k = _key(idx)
    h, w = k.shape
    pad = np.pad(k, 2, constant_values=-1)
    c = pad[2:-2, 2:-2]
    alone = np.ones_like(c, dtype=bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                alone &= pad[2 + dy:2 + dy + h, 2 + dx:2 + dx + w] != c
    two = np.zeros_like(alone)
    for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        two |= pad[2 + dy:2 + dy + h, 2 + dx:2 + dx + w] == c
    m = alone & ~two
    if transparent is not None:
        m &= k != transparent
    ys, xs = np.nonzero(m)
    return list(zip(xs.tolist(), ys.tolist()))


def _profile_kinks(p):
    """Kinks in a monotone edge profile p (one value per row, or per column).
    Returns the indices where the staircase order breaks."""
    p = np.asarray(p)
    if len(p) < 3:
        return []
    d = np.abs(np.diff(p))
    # The curve as runs: a step of d>0 is a flat run of length d; a stretch of
    # zeros is a steep run of (zeros + 1) rows.
    runs = []                         # (kind, length, index)
    i = 0
    while i < len(d):
        if d[i] > 0:
            runs.append(("flat", int(d[i]), i))
            i += 1
        else:
            j = i
            while j < len(d) and d[j] == 0:
                j += 1
            runs.append(("steep", j - i + 1, i))
            i = j
    kinks = []
    # flat runs (with a 1 between steep runs counting as flat 1) shorten, then steep runs lengthen
    seq = [(1 if k == "steep" else 0, n, at) for k, n, at in runs]
    for a, b, c in zip(seq, seq[1:], seq[2:]):
        # a run shorter than both neighbours of the same kind, or longer than both: a kink
        if a[0] == b[0] == c[0]:
            if (b[1] < a[1] and b[1] < c[1]) or (b[1] > a[1] and b[1] > c[1]):
                if abs(b[1] - a[1]) + abs(b[1] - c[1]) >= 2:
                    kinks.append(b[2])
    return kinks


def _monotone_pieces(p):
    """Split a profile into pieces where it only grows or only shrinks."""
    pieces, start, sign = [], 0, 0
    for i in range(1, len(p)):
        s = np.sign(p[i] - p[i - 1])
        if s and sign and s != sign:
            pieces.append((start, i))
            start = i - 1
        if s:
            sign = s
    pieces.append((start, len(p)))
    return pieces


def jaggies(mask, min_rows=4):
    """[(x, y)] near kinks on the edge of a boolean shape: its left and right
    edges row by row, its top and bottom column by column."""
    m = np.asarray(mask, dtype=bool)
    out = []
    for transpose in (False, True):
        mm = m.T if transpose else m
        rows = [r for r in range(mm.shape[0]) if mm[r].any()]
        if len(rows) < min_rows:
            continue
        for side in ("lo", "hi"):
            prof = []
            for r in rows:
                xs = np.nonzero(mm[r])[0]
                prof.append(xs[0] if side == "lo" else xs[-1])
            prof = np.array(prof)
            for a, b in _monotone_pieces(prof):
                seg = prof[a:b]
                for k in _profile_kinks(seg):
                    r, c = rows[a + k], int(seg[k])
                    out.append((r, c) if transpose else (c, r))
    return sorted(set(out))


def clusters(idx, colour, min_size=6):
    """Boolean masks of the 4-connected clusters of one colour."""
    from collections import deque
    k = _key(idx)
    m = k == colour
    seen = np.zeros_like(m)
    out = []
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        q, cl = deque([(y, x)]), []
        seen[y, x] = True
        while q:
            cy, cx = q.popleft()
            cl.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(cl) >= min_size:
            cm = np.zeros_like(m)
            for cy, cx in cl:
                cm[cy, cx] = True
            out.append(cm)
    return out


def report(idx, transparent=None, min_size=6):
    """{'orphans': [...], 'jaggies': {'silhouette': [...], colour: [...]}}."""
    k = _key(idx)
    res = {"orphans": orphans(k, transparent), "jaggies": {}}
    if transparent is not None:
        j = jaggies(k != transparent)
        if j:
            res["jaggies"]["silhouette"] = j
    for col in np.unique(k):
        if col == transparent:
            continue
        found = []
        for cm in clusters(k, col, min_size):
            found += jaggies(cm)
        if found:
            res["jaggies"][int(col)] = sorted(set(found))
    return res


def main(argv):
    from PIL import Image
    for p in argv:
        im = Image.open(p).convert("RGBA")
        a = np.asarray(im)
        key = _key(a[..., :3])
        key = np.where(a[..., 3] == 0, -2, key)
        r = report(key, transparent=-2)
        print(f"{p}: {len(r['orphans'])} orphans {r['orphans'][:8]}")
        for c, pts in r["jaggies"].items():
            name = c if c == "silhouette" else f"#{c:06X}"
            print(f"   jaggies ({name}): {pts[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
