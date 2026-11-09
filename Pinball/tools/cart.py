#!/usr/bin/env python3
"""MIDNIGHT PINBALL bootloader cover, drawn at the panel's native resolution.

Original lettering and pixel artwork; no external fonts or image assets.
Eleven RGB565 inks plus the menu's fixed inks. The animated ink is confined
to the bumper lamps; the ball, lettering and table keep their own colours.
Rows 110–119 are the empty apron beneath the flippers (the install bar).
Regenerate with: python3 pinball.py boxart
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "CHGame" / "tools"))
import artkit as ak
import boxart


def lettering(word):
    """Original 12×17 chamfered arcade capitals, sheared three pixels."""
    glyphs = {
        "P": [(0, 0, 3, 16), (3, 0, 9, 2), (9, 2, 11, 7), (3, 7, 9, 9)],
        "I": [(1, 0, 10, 2), (4, 3, 7, 13), (1, 14, 10, 16)],
        "N": [(0, 0, 2, 16), (9, 0, 11, 16)],
        "B": [(0, 0, 3, 16), (3, 0, 8, 2), (9, 2, 11, 6),
              (3, 7, 9, 9), (9, 10, 11, 14), (3, 14, 8, 16)],
        "A": [(0, 3, 2, 16), (3, 0, 8, 2), (9, 3, 11, 16), (3, 9, 8, 11)],
        "L": [(0, 0, 3, 16), (4, 14, 11, 16)],
    }
    mask = Image.new("1", (len(word) * 14 + 2, 17))
    for i, ch in enumerate(word):
        g = Image.new("1", (12, 17))
        d = ImageDraw.Draw(g)
        for rect in glyphs[ch]:
            d.rectangle(rect, fill=1)
        if ch == "N":
            d.polygon([(2, 0), (4, 0), (9, 12), (9, 16), (7, 16), (2, 4)], fill=1)
        for y in range(17):
            mask.paste(g.crop((0, y, 12, y + 1)), (i * 14 + (16 - y) // 5, y))
    return np.asarray(mask, dtype=bool)


def draw():
    pal = ak.Palette({
        "night": "#080C20", "blue": "#18284A", "teal": "#18566B",
        "cyan": "#62D6DF", "wine": "#481C48", "pink": "#F05C99",
        "steel": "#526B8C", "silver": "#B5CED6",
        "gold0": "#99512A", "gold1": "#EFAD49", "gold2": "#FFE39C",
    })
    im = Image.new("P", (128, 128), pal["black"])
    im.putpalette([c for rgb in pal.rgb for c in rgb])
    d = ImageDraw.Draw(im)

    def polygon(points, colour):
        d.polygon(points, fill=pal[colour])

    def line(points, colour, width=1):
        d.line(points, fill=pal[colour], width=width)

    def ellipse(box, colour):
        d.ellipse(box, fill=pal[colour])

    # Quiet night behind the sign, then a foreshortened, asymmetric cabinet.
    d.rectangle((3, 3, 124, 124), fill=pal["night"])
    polygon([(32, 45), (93, 45), (126, 124), (2, 124)], "black")
    polygon([(35, 46), (90, 46), (115, 109), (8, 109)], "blue")
    polygon([(39, 49), (87, 49), (106, 106), (17, 106)], "night")
    # The pool of light on the playfield fades into the near apron.
    for y in range(50, 106):
        half = 19 + (y - 50) * 0.40
        for x in range(18, 107):
            r = ((x - 61) / half) ** 2 + ((y - 73) / 38) ** 2
            if r < 0.65 or r < 1 and (x + y) % 4 == 0:
                im.putpixel((x, y), pal["blue"])
    polygon([(32, 47), (35, 46), (10, 110), (4, 121)], "steel")
    polygon([(35, 48), (37, 49), (15, 108), (10, 110)], "cyan")
    polygon([(90, 46), (94, 48), (123, 120), (115, 110)], "teal")
    line([(90, 49), (113, 108)], "silver")
    line([(39, 46), (86, 46)], "steel")
    # Wire ramp and rollover lanes behind the hero ball.
    line([(33, 86), (42, 71), (62, 64), (77, 54), (82, 48)], "black", 5)
    line([(32, 85), (41, 70), (61, 63), (76, 53), (81, 48)], "teal", 3)
    line([(32, 83), (41, 68), (61, 61), (75, 51)], "cyan")
    line([(36, 87), (44, 73), (64, 66), (79, 55)], "steel")
    for x in (48, 59, 70):
        line([(x, 49), (x - 2, 55)], "steel", 2)
        line([(x + 3, 50), (x + 2, 53)], "pink")

    def bumper(x, y, r):
        ellipse((x - r + 3, y - r + 5, x + r + 4, y + r + 5), "night")
        ellipse((x - r, y - r, x + r, y + r), "black")
        ellipse((x - r, y - r + 2, x + r, y + r - 1), "wine")
        ellipse((x - r + 1, y - r, x + r - 1, y + r - 4), "pink")
        ellipse((x - r + 3, y - r + 1, x + r - 3, y + r - 5), "cream")
        line([(x - 2, y - 2), (x + 1, y - 2)], "rainbow")

    bumper(48, 60, 8)
    bumper(35, 76, 10)
    bumper(78, 58, 7)
    # Slings, return guides and large tapered bats in the near ground.
    polygon([(23, 88), (19, 100), (45, 103)], "black")
    polygon([(24, 88), (23, 98), (42, 100)], "wine")
    line([(24, 88), (24, 96), (41, 99)], "pink", 2)
    polygon([(98, 89), (105, 101), (82, 104)], "wine")
    line([(98, 89), (102, 99), (84, 102)], "pink", 2)
    for points in ([(18, 95), (15, 103), (29, 108)], [(109, 96), (112, 104), (97, 109)]):
        line(points, "black", 5)
        line(points, "steel", 2)

    def flipper(points):
        polygon([(x + 2, y + 3) for x, y in points], "black")
        polygon(points, "wine")
        polygon([(x, y - 2) for x, y in points], "pink")
        line([(points[0][0], points[0][1] - 3),
              (points[1][0], points[1][1] - 3)], "cream", 2)

    flipper([(31, 103), (53, 107), (56, 105), (54, 102), (33, 97), (29, 99)])
    flipper([(96, 103), (74, 107), (71, 105), (73, 102), (94, 97), (98, 99)])
    # A curling wake leads to a chrome sphere, lit from the upper left.
    line([(89, 51), (99, 59), (102, 69), (98, 80)], "teal", 4)
    line([(90, 53), (98, 61), (100, 69), (97, 76)], "cyan")
    ellipse((64, 89, 102, 101), "night")
    cx, cy, radius = 77, 81, 18
    ellipse((cx - radius - 1, cy - radius - 1, cx + radius + 1, cy + radius + 1), "black")
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            nx, ny = (x - cx) / radius, (y - cy) / radius
            rr = nx * nx + ny * ny
            if rr > 1:
                continue
            nz = (1 - rr) ** 0.5
            lit = -0.48 * nx - 0.58 * ny + 0.66 * nz
            # Follow the sphere's lighting across the whole surface. A
            # screen-horizontal dark reflection looked like a cut in the ball.
            colour = "cream" if lit > 0.94 else "silver" if lit > 0.68 else "steel" if lit > 0.25 else "blue"
            if rr > 0.88:
                colour = "silver" if nx + ny < -0.35 else "teal"
            im.putpixel((x, y), pal[colour])
    line([(66, 72), (69, 69), (74, 68)], "cream", 2)
    line([(78, 93), (85, 91), (89, 87)], "cyan")
    # Apron stays dark and empty under the bootloader's progress indicator.
    polygon([(10, 110), (115, 110), (121, 123), (5, 123)], "night")
    line([(12, 122), (115, 122)], "blue")

    pic = ak.Picture(np.array(im, dtype=np.uint8), pal)
    # Original small 5×7 lettering, at its own size.
    small = {
        "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
        "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
        "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
        "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
        "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
        "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
        "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    }
    rows = ["..".join(small[ch][y] for ch in "MIDNIGHT") for y in range(7)]
    mask = np.array([[c == "#" for c in row] for row in rows])
    ak.title(pic, mask, (128 - mask.shape[1]) // 2, 7, fill=["cyan"],
             shadow=dict(dx=1, dy=1, colour="black"), seam_dither=False)
    title = lettering("PINBALL")
    ak.title(pic, title, (128 - title.shape[1]) // 2, 22,
             fill=["gold2", "gold1", "gold0"], hi="cream", lo="gold0",
             extrude=dict(dx=1, dy=1, depth=3, side="wine", bottom="black"),
             shadow=dict(dx=1, dy=2, colour="black"), seam_dither=False)
    ak.sparkle(pic, 68, 69, 3, "cream")
    return pic.image()


if __name__ == "__main__":
    print(boxart.save(draw(), HERE.parent / "docs" / "cart.png"))
