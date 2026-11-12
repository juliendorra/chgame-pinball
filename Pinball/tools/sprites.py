#!/usr/bin/env python3
"""Compile hand-editable ASCII sprite frames into CHGame span sprites."""
import argparse
from collections import Counter
import json
import math
import struct
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


def theme_assets():
    borders = json.loads((GAME / "sprites/board_borders.json").read_text())
    fonts = json.loads((GAME / "sprites/score_digits.json").read_text())
    if len(borders) != 9 or len(fonts) != 9:
        raise ValueError("one border skin and score font per theme are required")
    # Both source files are in board theme order. The roof trim is shared.
    top = None
    themes = []
    for (name, skin), digits in zip(borders.items(), fonts.values()):
        for part, (width, height) in {"top": (128, 34), "side": (11, 16), "emblem": (12, 8)}.items():
            rows = skin[part]
            if len(rows) != height or any(len(row) != width for row in rows):
                raise ValueError(f"{name} {part}: expected {width}x{height}")
        roof = pack(skin["top"][6:30], 128, trim=True)
        if top is not None and top != roof:
            raise ValueError(f"{name}: expected the shared roof trim")
        top = roof
        side = pack(skin["side"], trim=True)
        emblem = pack(skin["emblem"], trim=True)
        if len(digits) != 10 or any(len(d) != 9 or any(len(row) != 7 for row in d) for d in digits):
            raise ValueError(f"{name}: ten 7x9 digits required")
        inks = {INK[c] for digit in digits for row in digit for c in row}
        palette = [c for c in (15, 1) if c in inks] + sorted(inks - {15, 1})
        if len(palette) > 4:
            raise ValueError(f"{name}: score fonts support at most four inks")
        packed_digits = []
        for digit in digits:
            rows = [sum(palette.index(INK[c]) << (x*2) for x, c in enumerate(row)) for row in digit]
            packed_digits.append(struct.pack("<9H", *rows))
        themes.append((side, emblem, bytes(palette + [15]*(4-len(palette))), packed_digits))

    # Fixed PBA1 field sizes let regenerated packs work with installed carts.
    side_size, emblem_size = 155, 50
    if any(len(side) > side_size or len(emblem) > emblem_size for side, emblem, _, _ in themes):
        raise ValueError("theme side or emblem exceeds its PBA1 field")
    header = """// Generated from board_borders.json and score_digits.json by tools/sprites.py.
#pragma once
#include "SpriteData.h"

#ifndef PINBALL_SD_THEMES
#if defined(CHSIM)
#define PINBALL_SD_THEMES 0
#else
#define PINBALL_SD_THEMES 1
#endif
#endif

namespace pinball {
struct ThemeArt {
    uint8_t side[%d], emblem[%d], palette[4], digits[10][18];
};
""" % (side_size, emblem_size)

    def array(data):
        return "{" + ",".join(map(str, data)) + "}"

    def initializer(theme):
        side, emblem, palette, digits = theme
        return "    {" + ",\n     ".join((array(side), array(emblem), array(palette),
                                          "{" + ",\n      ".join(map(array, digits)) + "}")) + "},\n"

    header += "static const uint8_t THEME_ROOF[] PB_SPRITE = " + array(top) + ";\n"
    header += "static const ThemeArt THEME_ART[] PB_SPRITE = {\n" + initializer(themes[0])
    header += "#if !PINBALL_SD_THEMES\n" + "".join(map(initializer, themes[1:])) + "#endif\n};\n"
    header += "}  // namespace pinball\n"

    # Theme N (1–8) occupies sector N-1. Each sector is self-contained, so
    # changing boards requires one data read, even on a fragmented FAT card.
    sectors = []
    for index, (side, emblem, palette, digits) in enumerate(themes[1:], 1):
        data = b"PBA1" + bytes([index]) + side.ljust(side_size, b"\0") + emblem.ljust(emblem_size, b"\0")
        data += palette + b"".join(digits)
        if len(data) > 508:
            raise ValueError("theme payload does not fit a single sector")
        data = data.ljust(508, b"\0")
        checksum = 2166136261
        for byte in data:
            checksum = ((checksum ^ byte) * 16777619) & 0xFFFFFFFF
        sectors.append(data + struct.pack("<I", checksum))
    return header, b"".join(sectors)


def sprite_array(name, data):
    return f"static const uint8_t {name}[] PB_SPRITE = {{" + ",".join(map(str, data)) + "};\n"


def compress_sprites(streams):
    # A token is either a literal span byte or a pair of older tokens.
    # Width and height stay at the front for clipping and collision bounds.
    literals = bytes(sorted(set().union(*(set(data[2:]) for data in streams.values()))))
    lookup = {value: index for index, value in enumerate(literals)}
    encoded = {name: bytes(lookup[value] for value in data[2:]) for name, data in streams.items()}
    pairs = bytearray()
    expansions = [bytes((value,)) for value in literals]
    depths = [0] * len(literals)
    for token in range(len(literals), 256):
        counts = Counter(bytes((a, b)) for data in encoded.values() for a, b in zip(data, data[1:]))
        if not counts:
            break
        pair, count = counts.most_common(1)[0]
        if count <= 2:
            break
        pairs.extend(pair)
        left, right = pair
        depths.append(1 + max(depths[left], depths[right]))
        expansions.append(expansions[left] + expansions[right])
        encoded = {name: data.replace(pair, bytes((token,))) for name, data in encoded.items()}
    packed = {}
    for name, data in encoded.items():
        original = streams[name]
        assert len(data) <= 255 and len(original) <= 1024
        assert b"".join(expansions[token] for token in data) == original[2:]
        packed[name] = original[:2] + bytes((len(data),)) + data
    dictionary = sprite_array("SPRITE_LITERALS", literals) + sprite_array("SPRITE_PAIRS", pairs)
    dictionary += f"static constexpr unsigned SPRITE_STACK = {max(depths)};\n"
    return packed, dictionary


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
    compressed = {}
    for key, frames in display.items():
        dimensions = {(len(f[0]), len(f)) for f in frames}
        if len(dimensions) != 1 or not 1 <= len(frames) <= 8:
            raise ValueError(f"inconsistent animation: {key}")
        names = []
        for i, frame in enumerate(frames):
            shadow=shadows.get(key)
            if isinstance(shadow,dict):shadow=shadow.get(str(i))
            data = pack(cast_shadow(frame, shadow), 40, trim=True)
            use_compression = key not in ("ball", "ramp")
            stream = (data, use_compression)
            if stream not in shared:
                name = f"{key}_{i}"
                shared[stream] = name
                header += sprite_array(name, data)
                if use_compression:
                    compressed[name] = data
            names.append(shared[stream])
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
            bats += sprite_array(name, data)
            if level:
                compressed[name] = data
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
    # Ball, ramp arrows and resting flippers keep their direct spans.
    packed, dictionary = compress_sprites(compressed)
    for name, data in packed.items():
        original = sprite_array(name, compressed[name])
        replacement = sprite_array(name, data)
        header = header.replace(original, replacement)
        bats = bats.replace(original, replacement)
    header = header.replace("}  // namespace pinball\n", dictionary + "}  // namespace pinball\n")
    themes, pack_data = theme_assets()
    for path, contents in (("SpriteData.h", header.encode()), ("FlipperData.h", bats.encode()),
                           ("ThemeData.h", themes.encode()), ("sd/PINBALL/THEMES.PBA", pack_data)):
        out = GAME / path
        if a.check:
            if not out.exists() or out.read_bytes() != contents:
                raise SystemExit(f"{path} is stale")
        else:
            out.write_bytes(contents)
    print(f"{'Verified' if a.check else 'Built'} {sum(map(len, source.values()))} source frames in {len(source)} animations, 18 flipper poses and 90 score digits")


if __name__ == "__main__":
    main()
