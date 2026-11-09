"""Anti-aliased serif lettering from DejaVu Serif Bold, as the games' tile
and heading fonts use it (CHCrossword's and CHWords' tools/tilefont.py,
CHDominoes' tools/aafont.py share this; each keeps its character set,
header and output file).

Each glyph is rows of '#' (ink), '+' (half ink: drawn in a tone between the
letter's colour and what it is on) and '.' (clear), from the capitals' top
row. The ink is the typeface's own hinted one-bit rendering, so stems stay
crisp; the half tones are where its smooth rendering covers at least
`half` of 255 of a pixel the one-bit one left clear: the curves and
diagonals. J's hook is brought up to stand on the baseline.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIRS = ["C:/Windows/Fonts/", "/usr/share/fonts/truetype/dejavu/", "/Library/Fonts/"]


def find_ttf(name="DejaVuSerif-Bold.ttf", explicit=None):
    """The system's copy of a DejaVu face, or the path given."""
    if explicit:
        return explicit
    for d in FONT_DIRS:
        if Path(d + name).exists():
            return d + name
    raise SystemExit(f"{name} not found: pass --ttf (DejaVu is freely redistributable)")


def rasterize(chars, size=12, half=80, ttf=None, narrow_ttf=None, narrow_chars="", drop_first_col="",
              j_to_baseline=True, max_below_baseline=None, base=20, canvas=40):
    """{char: rows} and the baseline's row. `narrow_ttf` draws `narrow_chars`
    (CHWords' M and W from the Condensed face); `drop_first_col` loses a
    glyph's first column; `max_below_baseline` cuts anything further below
    the baseline (CHDominoes: Q's tail, two rows at most). `base`/`canvas`
    are the drawing position and image size, kept per game so the output is
    byte for byte what each game's own tool wrote."""
    regular = ImageFont.truetype(ttf, size)
    narrow = ImageFont.truetype(narrow_ttf, size) if narrow_ttf else None

    def ink(ch, mode):
        im = Image.new("L", (canvas, canvas), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = mode
        d.text((10, base), ch, font=narrow if (narrow and ch in narrow_chars) else regular, fill=255, anchor="ls")
        return im

    top = ink("H", "1").getbbox()[1]                 # the capitals' top row
    out = {}
    for ch in chars:
        hard, soft = ink(ch, "1"), ink(ch, "L")
        x0, y0, x1, y1 = hard.getbbox()
        if ch in drop_first_col:
            x0 += 1
        y_end = max(y1, top + 1) if max_below_baseline is not None else y1
        rows = ["".join("#" if hard.getpixel((x, y)) else "+" if soft.getpixel((x, y)) >= half else "."
                        for x in range(x0, x1)) for y in range(top, y_end)]
        if ch == "J" and j_to_baseline:              # its hook brought up to stand on the baseline
            rows = rows[:base - top - 2] + rows[-2:]
        if max_below_baseline is not None:
            rows = rows[:base - top + max_below_baseline]
        out[ch] = rows
    return out, base - top


def write_txt(path, header_lines, glyphs, chars):
    out = list(header_lines) + [""]
    for ch in chars:
        out.append(f"= {ch}")
        out += glyphs[ch]
        out.append("")
    Path(path).write_text("\n".join(out), newline="\n")
