#!/usr/bin/env python3
"""Compile hand-editable ASCII sprite frames into CHGame span sprites."""
import argparse
import json
import math
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
INK = {".": 15, "0": 2, "w": 1, "m": 3, "t": 4, "d": 7,
       "c": 8, "i": 5, "o": 9, "g": 10, "b": 12, "p": 13, "s": 14, "r": 6}


def cast_shadow(rows, offset):
    """Bake a board-tinted silhouette behind the art, keeping its anchor."""
    if not offset:
        return rows
    dx, dy = offset
    out = [["."] * (len(rows[0]) + dx) for _ in range(len(rows) + dy)]
    for y, row in enumerate(rows):
        for x, ink in enumerate(row):
            if ink != ".":
                out[y + dy][x + dx] = "0"
    for y, row in enumerate(rows):
        for x, ink in enumerate(row):
            if ink != ".":
                out[y][x] = ink
    return ["".join(row) for row in out]


def pack(rows, limit=32, trim=False):
    width, height = len(rows[0]), len(rows)
    if not 1 <= width <= limit or not 1 <= height <= limit or any(len(row) != width for row in rows):
        raise ValueError("frames must be rectangular and at most 32 by 32")
    result = bytearray((width, height))
    for row in rows:
        runs = []
        x = 0
        while x < width:
            c = INK[row[x]]
            n = 1
            while x + n < width and n < 16 and INK[row[x + n]] == c:
                n += 1
            runs.append(((n - 1) << 4) | c)
            x += n
        # sprite4 treats the unencoded right edge as transparent. Keep full
        # rows for collision-mask extraction; trim only display sprites.
        if trim:
            while runs and runs[-1] & 15 == 15:
                runs.pop()
            restored=[]
            for run in runs:restored.extend([run&15]*((run>>4)+1))
            restored.extend([15]*(width-len(restored)))
            assert restored==[INK[c] for c in row], 'sprite packing must preserve every pixel'
        result.append(len(runs)); result.extend(runs)
    return bytes(result)


def convex_hull(points):
    points = sorted(set(points))
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    halves = []
    for seq in (points, points[::-1]):
        half = []
        for p in seq:
            while len(half) > 1 and cross(half[-2], half[-1], p) <= 0:
                half.pop()
            half.append(p)
        halves.append(half[:-1])
    return halves[0] + halves[1]


def flipper_pose(rows, angle, mirror, shadow, pivot):
    # Prebake the editable bat into span runs. This avoids decoding and
    # rotating every pixel of six flippers on the 48 MHz handheld each frame.
    cs, sn = math.cos(angle * math.tau / 256), math.sin(angle * math.tau / 256)
    pixels = {}
    for y in range(-24, 25):
        for x in range(-32, 33):
            sx = math.floor(cs * x + sn * y + pivot[0] + .5)
            sy = math.floor(-sn * x + cs * y + pivot[1] + .5)
            if 0 <= sy < len(rows) and 0 <= sx < len(rows[0]) and rows[sy][sx] != ".":
                pixels[(-x if mirror else x, y)] = rows[sy][sx]
    x0 = min(x for x, y in pixels); x1 = max(x for x, y in pixels)
    y0 = min(y for x, y in pixels); y1 = max(y for x, y in pixels)
    frame = ["".join(pixels.get((x, y), ".") for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
    # Half-pixel coordinates surround the actual opaque pixel squares;
    # the cast shadow never contributes to the collision outline.
    hull = convex_hull((2*x+i, 2*y+j) for x,y in pixels for i in (-1,1) for j in (-1,1))
    return pack(cast_shadow(frame, shadow), 56, trim=shadow is not None), -x0, -y0, hull


def score_header():
    fonts = json.loads((GAME / "sprites/score_digits.json").read_text())
    if len(fonts) != 9:
        raise ValueError("one digit style per board theme is required")
    header = '// Generated from sprites/score_digits.json by tools/sprites.py.\n#pragma once\n#include "SpriteData.h"\nnamespace pinball {\n'
    used=[{INK[c] for digit in digits for row in digit for c in row} for digits in fonts.values()]
    # Stable transparent/white codes make repeated rows shareable across themes.
    palettes=[[c for c in (15,1) if c in p]+sorted(p-{15,1}) for p in used]
    if any(len(p)>4 for p in palettes):
        raise ValueError("score fonts support at most four inks per theme (including transparency)")
    header += "static const uint8_t SCORE_PALETTES[9][4] PB_SPRITE = {\n"
    header += ''.join('    {'+','.join(map(str,p+[15]*(4-len(p))))+'},\n' for p in palettes)
    row_words=sorted({sum(p.index(INK[c]) << (i*2) for i,c in enumerate(row))
                      for p,digits in zip(palettes,fonts.values()) for digit in digits for row in digit})
    row_coded=len(row_words)<=256 and len(row_words)*2+810<1440
    header += "};\n#define SCORE_ROW_CODED "+str(int(row_coded))+"\n"
    if row_coded:
        header += 'static const uint16_t SCORE_ROWS[] PB_SPRITE = {'+','.join(map(str,row_words))+'};\n'
    header += f"static const uint8_t SCORE_DIGITS[9][10][{9 if row_coded else 16}] PB_SPRITE = {{\n"
    for name, digits in fonts.items():
        if len(digits) != 10 or any(len(d) != 9 or any(len(row) != 7 for row in d) for d in digits):
            raise ValueError(f"{name}: ten 7x9 digits required")
        header += "    {\n"
        palette=palettes[list(fonts).index(name)]
        for rows in digits:
            if row_coded:
                packed=[row_words.index(sum(palette.index(INK[c]) << (i*2) for i,c in enumerate(row))) for row in rows]
                restored=[palette[(row_words[packed[y]] >> (x*2))&3] for y in range(9) for x in range(7)]
            else:
                pixels = [palette.index(INK[c]) for row in rows for c in row] + [0]
                packed = [sum(pixels[i+j] << (j*2) for j in range(4)) for i in range(0,64,4)]
                restored=[palette[(packed[i//4] >> ((i%4)*2)) & 3] for i in range(63)]
            assert restored==[INK[c] for row in rows for c in row], "score packing must preserve every ink"
            header += "        {" + ",".join(map(str, packed)) + "},\n"
        header += "    },\n"
    return header + "};\n}  // namespace pinball\n"


def border_header():
    borders=json.loads((GAME/'sprites/board_borders.json').read_text())
    if len(borders)!=9:raise ValueError('one border skin per theme is required')
    h='// Generated from sprites/board_borders.json by tools/sprites.py.\n#pragma once\n#include "SpriteData.h"\nnamespace pinball {\n'
    shared={};parts={}
    for name,skin in borders.items():
        for part,rows in skin.items():
            expected={'top':(128,34),'side':(11,16),'emblem':(12,8)}[part]
            if (len(rows[0]),len(rows))!=expected:raise ValueError(f'{name} {part}: expected {expected}')
            if part=='top':rows=rows[6:30] # trim empty rows; world anchor is y=6
            data=pack(rows,128,trim=True)
            if data not in shared:
                shared[data]=f'border_{name}_{part}'
                h+=f'static const uint8_t {shared[data]}[] PB_SPRITE = {{'+','.join(map(str,data))+'};\n'
            parts[name,part]=shared[data]
    h+='struct BoardBorder { const uint8_t *top, *side, *emblem; };\nstatic const BoardBorder BOARD_BORDERS[9] PB_SPRITE = {\n'
    for name in borders:h+='    {'+','.join(parts[name,part] for part in ('top','side','emblem'))+'},\n'
    return h+'};\n}  // namespace pinball\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    source = json.loads((GAME / "sprites/element_sprites.json").read_text())
    # Flippers draw from FlipperData's poses, never an upright elementSprite.
    # Keep their editable source for Studio and pose baking, without pinning
    # an unused generic flipper frame in the runtime animation table.
    display = {key:frames for key,frames in source.items() if key != "flipper"}
    shadows = json.loads((GAME / "sprites/shadows.json").read_text())
    flipper = json.loads((GAME / "sprites/flipper.json").read_text())
    header = "// Generated from sprites/element_sprites.json by tools/sprites.py.\n#pragma once\n#include <stdint.h>\n"
    header += "#if defined(__riscv) && !defined(CHSIM)\n#define PB_SPRITE __attribute__((section(\".rodata.pinball.sprites\")))\n#else\n#define PB_SPRITE\n#endif\n"
    header += "namespace pinball {\nenum SpriteId { " + ", ".join("SPR_" + key.upper() for key in display) + ", SPR_COUNT };\n"
    header += "struct SpriteAnimation { const uint8_t *const *frames; uint8_t count, width, height; };\n"
    shared = {}
    for key, frames in display.items():
        dimensions = {(len(f[0]), len(f)) for f in frames}
        if len(dimensions) != 1 or not 1 <= len(frames) <= 8:
            raise ValueError(f"inconsistent animation: {key}")
        names = []
        for i, frame in enumerate(frames):
            shadow=shadows.get(key)
            if isinstance(shadow,dict):shadow=shadow.get(str(i))
            data = pack(cast_shadow(frame, shadow), 40, trim=True)
            if data not in shared:
                shared[data] = f'{key}_{i}'
                header += f"static const uint8_t {shared[data]}[] PB_SPRITE = {{" + ",".join(map(str, data)) + "};\n"
            names.append(shared[data])
        header += f"static const uint8_t *const {key}_frames[] PB_SPRITE = {{" + ",".join(names) + "};\n"
    header += "static const SpriteAnimation SPRITES[] PB_SPRITE = {\n"
    header += "\n".join(f"    {{{key}_frames, {len(frames)}, {len(frames[0][0])}, {len(frames[0])}}}," for key, frames in display.items())
    header += "\n};\n}  // namespace pinball\n"
    bats = '// Generated from the editable flipper art by tools/sprites.py.\n#pragma once\nnamespace pinball {\n'
    poses = []
    canonical_masks = {}
    def mask_rows(mask):
        rows=[];at=0
        while at<len(mask):
            if mask[at]==255:rows.append([]);at+=1;continue
            row=[]
            while True:
                a,b=mask[at:at+2];at+=2;row.append((a,b&127))
                if b&128:break
            rows.append(row)
        return rows
    for side in range(2):
        for level in range(9):
            angle = flipper["rest_angle"] + level * (flipper["raised_angle"] - flipper["rest_angle"]) / 8
            data, ax, ay, hull = flipper_pose(source["flipper"][0], angle, side, shadows["flipper"], flipper["pivot"])
            name = f"flipper_pose_{side}_{level}"
            bats += f"static const uint8_t {name}[] PB_SPRITE = {{" + ",".join(map(str, data)) + "};\n"
            # Bake the exact pixel-corner conversion formerly done on every hit.
            assert all(v&1 for p in hull for v in p)
            bats += f"static const uint8_t {name}_hull[] PB_SPRITE = {{" + ",".join(str((v+1)//2+(ax if axis==0 else ay)) for p in hull for axis,v in enumerate(p)) + "};\n"
            # Store opaque span endpoints, excluding shadows. The end of a
            # row is flagged in its final endpoint; 255 represents an empty
            # row. This removes redundant transparent/color RLE tokens while
            # preserving every opaque pixel, including tiny interior gaps.
            raw,_,_,_=flipper_pose(source["flipper"][0],angle,side,None,flipper["pivot"])
            at=2; mask=[]
            for row in range(raw[1]):
                runs=raw[at];at+=1;pixels=[]
                for run in raw[at:at+runs]:
                    pixels.extend([run&15 != 15]*((run>>4)+1))
                at+=runs;spans=[];x=0
                while x<len(pixels):
                    if not pixels[x]:x+=1;continue
                    start=x
                    while x<len(pixels) and pixels[x]:x+=1
                    spans.extend((start,x))
                if spans:
                    assert max(spans)<128
                    restored=[False]*len(pixels)
                    for lo,hi in zip(spans[::2],spans[1::2]):restored[lo:hi]=[True]*(hi-lo)
                    assert restored==pixels, "flipper mask must preserve every pixel"
                    spans[-1]|=128;mask.extend(spans)
                else:mask.append(255)
            if side:
                width,left_rows=canonical_masks[level]
                assert width==raw[0]
                expected=[[(width-b,width-a) for a,b in reversed(row)] for row in left_rows]
                assert expected==mask_rows(mask), "shared mirrored mask must preserve every opaque span and tie order"
            else:canonical_masks[level]=(raw[0],mask_rows(mask))
            # Prefix the canonical width. Right-hand poses share the left
            # data, with count's high bit selecting exact reverse traversal.
            if not side:bats += f"static const uint8_t {name}_mask[] PB_SPRITE = {{" + ",".join(map(str,[raw[0],*mask])) + "};\n"
            poses.append(f"{{{name},{name}_hull,flipper_pose_0_{level}_mask,{ax},{ay},{len(hull)|(128 if side else 0)},{raw[1]}}}")
    bats += "const FlipperPose FLIPPER_POSES[2][9] PB_SPRITE = {{" + ",".join(poses[:9]) + "},{" + ",".join(poses[9:]) + "}};\n"
    bats += "}  // namespace pinball\n"
    for out, contents in ((GAME / "SpriteData.h", header), (GAME / "FlipperData.h", bats),
                          (GAME / "ScoreData.h", score_header()), (GAME / "BorderData.h", border_header())):
        if a.check:
            if not out.exists() or out.read_text() != contents:
                raise SystemExit(f"{out.name} is stale")
        else:
            out.write_text(contents)
    print(f"{'Verified' if a.check else 'Built'} {sum(map(len, source.values()))} source frames in {len(source)} animations, 18 flipper poses and 90 score digits")


if __name__ == "__main__":
    main()
