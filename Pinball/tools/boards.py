#!/usr/bin/env python3
"""Compile editable JSON tables to checked PBT1 files; optionally make a test SD image."""
import argparse
import json
from pathlib import Path
import re
import struct
import sys

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
KINDS = {name: i for i, name in enumerate(("wall", "bumper", "target", "lane", "scoop", "flippers",
                                        "ramp", "spinner", "drop_target", "kickback", "gate", "saucer", "rubber"))}


def checksum(data):
    value = 2166136261
    for i, byte in enumerate(data):
        value = ((value ^ (0 if 16 <= i < 20 else byte)) * 16777619) & 0xFFFFFFFF
    return value


def label(value, size):
    data = value.encode("ascii")
    if not data or len(data) >= size or any(n < 32 or n > 126 for n in data):
        raise ValueError(f"expected 1..{size - 1} printable ASCII characters: {value!r}")
    return data.ljust(size, b"\0")


def encode(t):
    if not re.fullmatch(r"[A-Z0-9_]{1,8}", t["file"]):
        raise ValueError("file must be an uppercase 8.3 stem")
    height, gravity, theme = t["height"], t.get("gravity", 14), t["theme"]
    if not 256 <= height <= 480 or not 8 <= gravity <= 44 or not 0 <= theme <= 8:
        raise ValueError("height, gravity or theme out of range")
    flags=t.get("flags",0)
    if flags not in (0,1): raise ValueError("unknown board flags")
    objects = t["objects"]
    if not 0 <= len(objects) <= 72:
        raise ValueError("expected 0..72 objects")
    palette = [int(c, 16) for c in t["palette"]]
    if len(palette) != 16 or any(not 0 <= c <= 0xFFF for c in palette):
        raise ValueError("palette must have 16 RGB444 entries")
    ident = t["id"]
    if not 0 < ident <= 0xFFFFFFFF:
        raise ValueError("id must be a nonzero uint32")
    out = bytearray(struct.pack("<4sBBBBHHII20s24s16H", b"PBT1", 1, theme, len(objects), flags,
                                height, gravity, ident, 0, label(t["title"], 20),
                                label(t["mission"], 24), *palette))
    groups, lanes, scoop = set(), set(), False
    for o in objects:
        kind = KINDS[o["kind"]]
        x, y, u, v = (o.get(k, 0) for k in ("x", "y", "u", "v"))
        group, value = o.get("group", 0), o.get("value", 0)
        if not 5 <= x <= 108 or not 8 <= y <= height - 50 or not 0 <= group <= 2 or not 0 <= value <= 10000:
            raise ValueError(f"object position, group or score out of range: {o}")
        if kind in (KINDS["wall"], KINDS["gate"]):
            if not 5 <= u <= 110 or not 8 <= v <= height - 40 or (x, y) == (u, v):
                raise ValueError(f"invalid wall: {o}")
        elif kind == KINDS["flippers"]:
            if not 20 <= x <= 38 or not 82 <= u <= 100 or not 16 <= v <= 26 or y < 80 or x + 2 * v + 16 > u:
                raise ValueError(f"invalid flippers: {o}")
        elif kind == KINDS["ramp"]:
            if not 8 <= u <= 105 or not 12 <= v <= height - 50 or abs(y - v) < 32:
                raise ValueError(f"invalid ramp: {o}")
        elif kind in (KINDS["target"], KINDS["drop_target"]):
            if not 3 <= u <= 12 or not 3 <= v <= 12:
                raise ValueError(f"invalid target: {o}")
            groups.add(group)
        elif kind == KINDS["rubber"]:
            if not flags & 1 or group > 1 or not 8 <= u <= 24 or not 16 <= v <= 40 or not 8 <= x + (-u if group else u) <= 108 or y + v > height-8:
                raise ValueError(f"invalid rubber slingshot: {o}")
        elif kind == KINDS["spinner"]:
            if not 6 <= u <= 16:
                raise ValueError(f"invalid spinner: {o}")
        else:
            if not 3 <= u <= 12 or not 0 <= v <= 1600:
                raise ValueError(f"invalid circular object: {o}")
            if kind == KINDS["lane"]:
                lanes.add(group)
            scoop |= kind == KINDS["scoop"]
        out.extend(struct.pack("<BBhhhhH", kind, group, x, y, u, v, value))
    struct.pack_into("<I", out, 16, checksum(out))
    return bytes(out)


def image(path, files, fs="fat16", **kwargs):
    sys.path.insert(0, str(ROOT / "CHGame/platform/board/arduino/CHGame/libraries/CHSd/tools"))
    from fatimg import build_image
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return build_image(path, files, fs=fs, **kwargs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=GAME / "boards/tables.json")
    p.add_argument("--out", type=Path, default=GAME / "sd/PINBALL")
    p.add_argument("--image", type=Path)
    p.add_argument("--check", action="store_true", help="verify generated files without changing them")
    a = p.parse_args()
    specs = json.loads(a.source.read_text())
    names, ids = set(), set()
    files = {}
    for t in specs:
        if t["file"] in names or t["id"] in ids:
            raise SystemExit("table filenames and ids must be unique")
        names.add(t["file"])
        ids.add(t["id"])
        files[t["file"] + ".PBT"] = encode(t)
    if not files:
        raise SystemExit("table pack is empty")
    builtin = next(iter(files.values()))
    header = "// Generated by tools/boards.py from boards/tables.json.\n#pragma once\n"
    header += "static const uint8_t BUILTIN[] = {\n"
    header += "\n".join("    " + ",".join(f"0x{n:02x}" for n in builtin[i:i + 16]) + "," for i in range(0, len(builtin), 16))
    header += "\n};\n"
    outputs = {a.out / name: data for name, data in files.items()}
    outputs[GAME / "Builtin.h"] = header.encode()
    for dest, data in outputs.items():
        if a.check:
            if not dest.exists() or dest.read_bytes() != data:
                raise SystemExit(f"stale generated file: {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    if a.image:
        image(a.image, {"PINBALL/" + k: v for k, v in files.items()})
    print(f"{'Verified' if a.check else 'Built'} {len(files)} tables, {sum(map(len, files.values())):,} bytes total")


if __name__ == "__main__":
    main()
