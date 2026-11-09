"""Preview of a game's display font (tools/art/font.txt, or the common one),
drawn as the games draw their lettering: gradient fill, ink outline, a
shadow a pixel down and right. CHBackgammon's and CHFour's
tools/font_preview.py call `render()` with their own sample lines and
their assets.py's palette.
"""
from pathlib import Path

from PIL import Image


def text_mask(font, s, gap=1):
    w = sum(font[c]["w"] + gap if c in font else 4 if c == " " else 10 for c in s)
    h = 13
    m = [[0] * (w + 2) for _ in range(h + 2)]
    x = 1
    for c in s:
        if c not in font:
            x += 4 if c == " " else 10
            continue
        g = font[c]
        for r, row in enumerate(g["rows"]):
            for i, v in enumerate(row):
                if v:
                    m[1 + g["top"] + r][x + i] = 1
        x += g["w"] + gap
    return m


def draw(img, m, x0, y0, ramp, rgb, outline=0, shadow=7):
    h, w = len(m), len(m[0])
    grown = [[any(m[yy][xx] for yy in range(max(0, y - 1), min(h, y + 2)) for xx in range(max(0, x - 1), min(w, x + 2)))
              for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if grown[y][x]:
                img.putpixel((x0 + x + 1, y0 + y + 1), rgb(shadow))
    for y in range(h):
        for x in range(w):
            if grown[y][x]:
                img.putpixel((x0 + x, y0 + y), rgb(outline))
    for y in range(h):
        for x in range(w):
            if m[y][x]:
                img.putpixel((x0 + x, y0 + y), rgb(ramp[min(y, len(ramp) - 1)]))


def render(samples, font, rgb, out, width=150, row_height=20, background=3):
    """One line per sample, centred, 4x, to `out`. Prints each line's width."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, row_height * len(samples) + 4), rgb(background))
    gold = [1] * 3 + [8] * 7 + [9] * 6        # FX_B shows as gold here: white top rows instead
    for k, s in enumerate(samples):
        m = text_mask(font, s)
        draw(img, m, (width - len(m[0])) // 2, 2 + k * row_height, gold, rgb)
        print(f"{s!r}: {len(m[0]) - 2} px")
    img.resize((width * 4, img.height * 4), Image.NEAREST).save(out)
    print(out)
    return out
