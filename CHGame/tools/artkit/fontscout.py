"""Find a title's lettering among thousands of pixel fonts, at their own
size (never enlarged), and commit the one chosen as text art.

The fonts are the ones Pixel Logo Lab collects: a separate tool, not part of
this repository, whose `logolab.py fetch` and `build` download the
collections and write its data/*.js. It is looked for beside this
repository (../PixelLogoLab) or at $CHG_LOGOLAB. TrueType pixel fonts in
../PixelFonts/Source Fonts (or $CHG_PIXELFONTS) are added when there are
any. Nothing of them is copied into this repository but the pixels of the
title itself, with the font's name, author, stated terms and source in the
text art's header, so the recipes need none of it.

    python -m artkit.fontscout scout "YACHT DICE" out/fontscout/CHYacht [--min 14] [--max 48]
            [--width 120] [--weight 1.8] [--clear] [--find NAME] [--per 40]
        contact sheets (sheet-01.png ...) and index.json: every face that sets
        the text within the box, numbered, with a quick gold treatment (faces
        drawn at twice their size or width, every row or every column paired,
        are left out: that is pixel doubling; --doubled shows them)
    python -m artkit.fontscout export "YACHT DICE" <font id> OUT.txt [--gap N]
        the text in that face as text art (lines split by '|', centred)
    python -m artkit.fontscout font <font id> OUT.json
        a whole face, for small lettering (pixel.Font reads it)
    python -m artkit.fontscout show <font id> "TEXT" OUT.png
"""
from __future__ import annotations

import json
import os
import pathlib
import pickle
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]          # the repository
LAB = pathlib.Path(os.environ.get("CHG_LOGOLAB", ROOT.parent / "PixelLogoLab"))
PIXELFONTS = pathlib.Path(os.environ.get("CHG_PIXELFONTS", ROOT.parent / "PixelFonts" / "Source Fonts"))
CACHE = ROOT / "out" / "fontscout" / "_fonts.pickle"

CLEAR = ("cc0", "public domain", "ofl", "100% free", "commercial", "free (her patreon")


def _unpack(g):
    w, h, x, y, adv, hx = g
    if not w or not h:
        return [w, h, x, y, adv, []]
    bits = bin(int(hx, 16))[2:].zfill(len(hx) * 4)
    rows = [bits[r * w:(r + 1) * w].replace("1", "#").replace("0", ".") for r in range(h)]
    return [w, h, x, y, adv, rows]


def load():
    """Every face: [{id, name, author, terms, url, tall, glyphs {ch: [w,h,x,y,adv,rows]}}]."""
    src = sorted((LAB / "data").glob("*.js")) if (LAB / "data").exists() else []
    stamp = [(p.name, p.stat().st_mtime) for p in src]
    if CACHE.exists():
        try:
            c = pickle.loads(CACHE.read_bytes())
            if c["stamp"] == stamp:
                return c["fonts"]
        except Exception:
            pass
    fonts = []
    for p in src:
        if p.name == "sources.js":
            continue
        t = p.read_text(encoding="utf-8")
        body = json.loads(t[t.index("LOGOLAB_LOAD(") + 13:t.rindex(");")])
        for f in body["fonts"]:
            fonts.append({"id": f["id"], "name": f["n"], "author": f.get("a", ""), "terms": f.get("l", ""),
                          "url": f.get("u", ""), "tall": f["t"], "g": f["g"]})
    if PIXELFONTS.exists() and (LAB / "logolab").exists():
        sys.path.insert(0, str(LAB))
        try:
            from logolab import formats
            for ttf in sorted(PIXELFONTS.glob("*.ttf")):
                try:
                    r = formats.ttf(str(ttf))
                except Exception:
                    r = None
                if not r:
                    continue
                g = r[1] if isinstance(r, tuple) else r
                packed = {}
                for ch, (rows, x, y, adv) in g.items():
                    bits = "".join(rows)
                    bits += "0" * (-len(bits) % 4)
                    packed[ch] = [len(rows[0]) if rows else 0, len(rows), x, y, adv,
                                  "%0*x" % (len(bits) // 4, int(bits, 2)) if bits else ""]
                tall = max((len(v[0]) for c, v in g.items() if c.isalnum() and v[0]), default=0)
                fonts.append({"id": f"pixelfonts/{ttf.stem}", "name": ttf.stem, "author": "", "terms": "",
                              "url": "", "tall": tall, "g": packed})
        finally:
            sys.path.pop(0)
    if not fonts:
        raise SystemExit(f"no fonts: Pixel Logo Lab's built data is not in {LAB / 'data'}. Run its "
                         "`python logolab.py fetch` and `build`, and put it beside this repository or set CHG_LOGOLAB.")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps({"stamp": stamp, "fonts": fonts}))
    return fonts


def glyphs(f):
    if "_u" not in f:
        f["_u"] = {c: _unpack(v) for c, v in f["g"].items()}
    return f["_u"]


def space(f):
    g = glyphs(f)
    s = g.get(" ")
    if s and s[4] > 0:
        return s[4]
    advs = [v[4] for v in g.values()]
    return max(2, round(sum(advs) / max(1, len(advs)) / 2))


def layout(f, text, gap=0):
    """The text in face f as a bool mask, or None if a letter is missing."""
    g = glyphs(f)
    pen, items = 0, []
    x0 = y0 = 10 ** 9
    x1 = y1 = -10 ** 9
    for ch in text:
        G = g.get(ch) or g.get(ch.lower() if ch == ch.upper() else ch.upper())
        if G is None:
            if ch == " ":
                pen += space(f) + gap
                continue
            return None
        w, h, gx, gy, adv, rows = G
        if w:
            items.append((pen + gx, gy, rows))
            x0, x1 = min(x0, pen + gx), max(x1, pen + gx + w)
            y0, y1 = min(y0, gy), max(y1, gy + h)
        pen += (adv if (w or ch != " ") else space(f)) + gap
    if not items:
        return None
    m = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for gx, gy, rows in items:
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#":
                    m[gy - y0 + j, gx - x0 + i] = True
    return m


def lines(f, text, gap=0, leading=2):
    """'A|B' as lines, each centred."""
    ms = [layout(f, t, gap) for t in text.split("|")]
    if any(m is None for m in ms):
        return None
    W = max(m.shape[1] for m in ms)
    H = sum(m.shape[0] for m in ms) + leading * (len(ms) - 1)
    out = np.zeros((H, W), dtype=bool)
    y = 0
    for m in ms:
        x = (W - m.shape[1]) // 2
        out[y:y + m.shape[0], x:x + m.shape[1]] = m
        y += m.shape[0] + leading
    return out


def weight(m):
    """Mean horizontal run of ink: how heavy the strokes are."""
    runs = []
    for row in m:
        r = 0
        for v in row:
            if v:
                r += 1
            elif r:
                runs.append(r)
                r = 0
        if r:
            runs.append(r)
    return float(np.mean(runs)) if runs else 0.0


def doubled(m):
    """True if every row, or every column, comes in identical pairs: a face
    drawn at twice its size or stretched to twice its width (pixel doubling,
    which the house look rules out)."""
    def paired(a):
        return any(all((a[i] == a[i + 1]).all() for i in range(off, a.shape[0] - 1, 2)) for off in (0, 1))
    return m.shape[0] > 3 and m.shape[1] > 3 and (paired(m) or paired(m.T))


def clear_terms(f):
    t = (f["terms"] or "").lower()
    src = f["id"].split("/")[0]
    return src in ("arcade", "zx", "castpixel") or any(k in t for k in CLEAR)


def treat(m, pad=3):
    """A quick look: gold face, dark red depth, black outline, on felt."""
    from .pixel import shift, ring
    h, w = m.shape
    H, W = h + 2 * pad + 2, w + 2 * pad + 2
    M = np.zeros((H, W), dtype=bool)
    M[pad:pad + h, pad:pad + w] = m
    E = (shift(M, 1, 1) | shift(M, 2, 2)) & ~M
    O = ring(M | E)
    img = np.zeros((H, W, 3), dtype=np.uint8)
    img[:] = (10, 52, 30)
    img[O] = (0, 0, 0)
    img[E] = (120, 20, 30)
    ys = np.nonzero(M.any(1))[0]
    t0, t1 = ys.min(), ys.max()
    for r in range(t0, t1 + 1):
        k = (r - t0) / max(1, t1 - t0)
        c = (255, 238, 150) if k < 0.3 else (255, 200, 40) if k < 0.7 else (220, 130, 20)
        img[r][M[r]] = c
    return img


def scout(text, out, lo=14, hi=48, width=120, min_weight=0.0, only_clear=False, find=None, per=40, gap=0,
          allow_doubled=False):
    from PIL import Image, ImageDraw
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("sheet-*.png"):
        old.unlink()
    cands = []
    for f in load():
        if not lo <= f["tall"] <= hi:
            continue
        if only_clear and not clear_terms(f):
            continue
        if find and find.lower() not in (f["name"] + " " + f["id"]).lower():
            continue
        m = lines(f, text, gap) if "|" in text else layout(f, text, gap)
        if m is None or m.shape[1] > width or not lo <= m.shape[0] <= hi * (text.count("|") + 1):
            continue
        wgt = weight(m)
        if wgt < min_weight:
            continue
        if not allow_doubled and doubled(m):
            continue
        cands.append((f, m, wgt))
    cands.sort(key=lambda c: (-c[1].shape[0], -c[2]))
    index = []
    cols = 4
    for s in range(0, len(cands), per):
        chunk = cands[s:s + per]
        cells = [treat(m) for _, m, _ in chunk]
        cw = max(c.shape[1] for c in cells) + 4
        ch = max(c.shape[0] for c in cells) + 12
        rows = (len(cells) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cw, rows * ch), (24, 24, 28))
        d = ImageDraw.Draw(sheet)
        for k, ((f, m, wgt), cell) in enumerate(zip(chunk, cells)):
            n = s + k + 1
            x, y = (k % cols) * cw, (k // cols) * ch
            sheet.paste(Image.fromarray(cell), (x + 2, y + 10))
            mark = "" if clear_terms(f) else " ?"
            d.text((x + 2, y), f"{n} {f['name'][:16]} {m.shape[0]}px{mark}", fill=(200, 200, 200))
            index.append({"n": n, "id": f["id"], "name": f["name"], "author": f["author"], "terms": f["terms"],
                          "url": f["url"], "w": m.shape[1], "h": m.shape[0], "weight": round(wgt, 2),
                          "clear": clear_terms(f)})
        sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
        sheet.save(out / f"sheet-{s // per + 1:02d}.png")
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8", newline="\n")
    print(f"{len(cands)} faces set '{text}' within {width} px, {lo}-{hi} px tall: {out}")
    return index


def find_font(fid):
    for f in load():
        if f["id"] == fid:
            return f
    raise SystemExit(f"no font {fid!r}")


def export(text, fid, path, gap=0, leading=2):
    f = find_font(fid)
    m = lines(f, text, gap, leading) if "|" in text else layout(f, text, gap)
    if m is None:
        raise SystemExit(f"{fid} lacks a letter of {text!r}")
    head = [f"// title: {text}", f"// font: {f['name']} ({f['id']})", f"// author: {f['author'] or 'not stated'}",
            f"// terms: {f['terms'] or 'not stated'}", f"// source: {f['url'] or 'not stated'}",
            "// set at the font's own size by tools/artkit/fontscout.py; pixels may be touched up by hand"]
    body = ["".join("#" if v else "." for v in row) for row in m]
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(head + body) + "\n", encoding="utf-8", newline="\n")
    print(f"{p}: {m.shape[1]}x{m.shape[0]}, {f['name']}")


def export_font(fid, path):
    f = find_font(fid)
    g = glyphs(f)
    d = {"name": f["name"], "id": f["id"], "author": f["author"], "terms": f["terms"], "source": f["url"],
         "space": space(f), "glyphs": {c: v for c, v in g.items() if 32 <= ord(c) < 127}}
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8", newline="\n")
    print(f"{p}: {f['name']}, {len(d['glyphs'])} glyphs, {f['tall']} px")


def show(fid, text, path):
    from PIL import Image
    f = find_font(fid)
    m = lines(f, text) if "|" in text else layout(f, text)
    im = Image.fromarray(treat(m))
    im = im.resize((im.width * 4, im.height * 4), Image.NEAREST)
    im.save(path)
    print(path)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("scout")
    p.add_argument("text")
    p.add_argument("out")
    p.add_argument("--min", type=int, default=14)
    p.add_argument("--max", type=int, default=48)
    p.add_argument("--width", type=int, default=120)
    p.add_argument("--weight", type=float, default=0.0)
    p.add_argument("--clear", action="store_true")
    p.add_argument("--find")
    p.add_argument("--per", type=int, default=40)
    p.add_argument("--gap", type=int, default=0)
    p.add_argument("--doubled", action="store_true", help="also faces drawn at twice their size (left out by default)")
    p = sub.add_parser("export")
    p.add_argument("text")
    p.add_argument("font")
    p.add_argument("out")
    p.add_argument("--gap", type=int, default=0)
    p.add_argument("--leading", type=int, default=2)
    p = sub.add_parser("font")
    p.add_argument("font")
    p.add_argument("out")
    p = sub.add_parser("show")
    p.add_argument("font")
    p.add_argument("text")
    p.add_argument("out")
    a = ap.parse_args(argv)
    if a.cmd == "scout":
        scout(a.text, a.out, a.min, a.max, a.width, a.weight, a.clear, a.find, a.per, a.gap, a.doubled)
    elif a.cmd == "export":
        export(a.text, a.font, a.out, a.gap, a.leading)
    elif a.cmd == "font":
        export_font(a.font, a.out)
    else:
        show(a.font, a.text, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
