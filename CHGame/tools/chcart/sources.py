"""Where games come from: a sketch folder (built, described by its
chgame.json), a raw .bin, an Intel .hex, the build's .elf, a .chg, or
another .chgame.

A sketch's chgame.json describes the one game it makes, with paths relative
to the sketch; every key is optional (an unknown one is an error, so a typo
cannot drop a field):

    {"id": "words", "title": "WORDS", "author": "...", "version": "...",
     "description": "...", "genre": "...", "license": "Apache-2.0",
     "url": "...", "sourceUrl": "...", "folder": "WORD GAMES",
     "licenseFiles": ["LICENSE", "NOTICE"], "sdcard": "sdcard",
     "cartImage": "docs/cart.png",
     "buttons": [{"control": "A", "action": "Lay a tile"}]}

The defaults: id from the folder's name; title the folder's name in capitals
(as the IDE's Export Compiled Binary titles a .chg); version from config.h's
`#define <PFX>_VERSION "x"`; description the README's first paragraph;
license from the LICENSE file's first line; licenseFiles LICENSE and NOTICE
where they exist; sdcard `sdcard/` if it exists; cartImage docs/cart.png
if it exists, else one drawn from the title (tools/boxart.py: the visual
menu shows it) over the first frame of docs/gameplay.gif if the sketch has
one, as for a game from a .bin, .hex or .chg file without a picture. The
GIF itself never goes into the cart: a .chgame carries no gameplay
pictures (spec/chgame.md). A .chg file with a record (spec/chg.md: every one runtime
preparation writes) gives the game as its cart had it, less its SD files
(`chgame cart backup` reads those from the card).
"""
from __future__ import annotations

import json
import pathlib
import re

from . import model, zipio
from .model import CartError, Game, Issue

SKETCH_KEYS = ("id", "title", "author", "version", "description", "genre", "license", "url", "sourceUrl",
               "folder", "licenseFiles", "sdcard", "cartImage", "buttons")
LICENSES = (("Apache License", "Apache-2.0"), ("MIT License", "MIT"),
            ("GNU GENERAL PUBLIC LICENSE", "GPL-3.0"), ("GNU LESSER GENERAL PUBLIC LICENSE", "LGPL-3.0"),
            ("BSD 3-Clause", "BSD-3-Clause"), ("BSD 2-Clause", "BSD-2-Clause"))


# ---- binaries ---------------------------------------------------------------------

def hex_to_bin(text, device="rev0"):
    """An Intel HEX file's bytes from the device's load address, gaps 0xFF."""
    d = model.DEVICES[device]
    mem, base = {}, 0
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if not line.startswith(":"):
            raise ValueError(f"line {n}: not Intel HEX")
        b = bytes.fromhex(line[1:])
        if len(b) < 5 or len(b) != b[0] + 5 or sum(b) & 0xFF:
            raise ValueError(f"line {n}: bad length or checksum")
        count, addr, kind, data = b[0], b[1] << 8 | b[2], b[3], b[4:-1]
        if kind == 0:
            for i, v in enumerate(data):
                mem[base + addr + i] = v
        elif kind == 1:
            break
        elif kind == 2:
            base = int.from_bytes(data, "big") << 4
        elif kind == 4:
            base = int.from_bytes(data, "big") << 16
        elif kind not in (3, 5):
            raise ValueError(f"line {n}: record type {kind}")
    if not mem:
        raise ValueError("no data")
    lo, hi = min(mem), max(mem) + 1
    if lo < d.load_address:
        raise ValueError(f"data at 0x{lo:X}, below {device}'s load address 0x{d.load_address:X}: "
                         "is this a bootloader, or built for another board?")
    if hi - d.load_address > d.max_image:
        raise ValueError(f"data up to 0x{hi:X}: more than {d.max_image} B from 0x{d.load_address:X}")
    return bytes(mem.get(a, 0xFF) for a in range(d.load_address, hi))


def elf_to_bin(data, device="rev0"):
    """An ELF executable's loadable segments as the raw image from the
    device's load address, gaps 0xFF: what `objcopy -O binary` writes from
    the `.elf` the IDE builds beside the `.bin`. Segments are placed at their
    load address (p_paddr: initialised data lives in RAM but is loaded from
    flash), so the image is the one the board package's build gives."""
    import struct
    d = model.DEVICES[device]
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    if data[4] != 1 or data[5] != 1:
        raise ValueError("not a 32-bit little-endian ELF")
    e_type, e_machine = struct.unpack_from("<HH", data, 16)
    if e_type != 2:
        raise ValueError(f"ELF type {e_type}: not an executable")
    if e_machine != 243:
        raise ValueError(f"ELF machine {e_machine}: not RISC-V (243); built for another board?")
    (e_phoff,) = struct.unpack_from("<I", data, 28)
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 42)
    segs = []
    for i in range(e_phnum):
        at = e_phoff + i * e_phentsize
        if at + 32 > len(data):
            raise ValueError("program headers past the end of the file")
        p_type, p_offset, _vaddr, p_paddr, p_filesz = struct.unpack_from("<IIIII", data, at)
        if p_type != 1 or not p_filesz:                # PT_LOAD with bytes in the file
            continue
        if p_offset + p_filesz > len(data):
            raise ValueError(f"segment at 0x{p_paddr:X} past the end of the file")
        segs.append((p_paddr & 0x07FFFFFF, data[p_offset:p_offset + p_filesz]))   # (flash at 0x0 or 0x08000000)
    if not segs:
        raise ValueError("no loadable segment")
    segs.sort()
    lo, hi = segs[0][0], max(a + len(b) for a, b in segs)
    if lo < d.load_address:
        raise ValueError(f"data at 0x{lo:X}, below {device}'s load address 0x{d.load_address:X}: "
                         "is this a bootloader, or built for another board?")
    if hi - d.load_address > d.max_image:
        raise ValueError(f"data up to 0x{hi:X}: more than {d.max_image} B from 0x{d.load_address:X}")
    img = bytearray(b"\xff" * (hi - d.load_address))
    end = 0
    for a, b in segs:
        if a < end:
            raise ValueError(f"segments overlap at 0x{a:X}")
        img[a - d.load_address:a - d.load_address + len(b)] = b
        end = a + len(b)
    return bytes(img)


def placeholder(title, shot=None):
    """The picture a game without one gets (tools/boxart.py)."""
    import boxart                           # (tools/ is on the path: runtime.py)
    return boxart.placeholder(title, shot)


BINARY_SUFFIXES = (".bin", ".hex", ".elf", ".chg")


def image_from_file(path, device="rev0"):
    """The raw program image in a .bin, .hex or .elf file."""
    p = pathlib.Path(path)
    data = p.read_bytes()
    if p.suffix.lower() == ".hex":
        return hex_to_bin(data.decode("ascii", "replace"), device)
    if p.suffix.lower() == ".elf":
        return elf_to_bin(data, device)
    return data


def from_binary(path, title=None, gid=None, device="rev0"):
    """A Game from a .bin, .hex, .elf or .chg file (the .chg header gives its
    title, author and version, and its picture if it has one). `device` is the
    board a .bin, .hex or .elf was built for; a .chg names its own."""
    p = pathlib.Path(path)
    data = p.read_bytes()
    meta = {}
    if p.suffix.lower() in (".hex", ".elf"):
        img = image_from_file(p, device)
    elif p.suffix.lower() == ".chg":
        import chgpack                      # (tools/ is on the path: runtime.py)
        try:
            info = chgpack.parse(data)
        except chgpack.ChgError as e:
            raise CartError([Issue("bad-field", str(p), str(e))])
        device = info["device"]
        from . import backup
        game, sd, _ = backup.game_from_chg(data, device, str(p))
        if sd is not None:                  # its record: the game as its cart had it (not its SD files)
            game.id, game.title = gid or game.id, title or game.title
            return game
        img = data[chgpack.HEADER_BYTES:chgpack.HEADER_BYTES + info["payload_bytes"]]
        meta = {k: info[k] for k in ("author", "version") if info[k]}
        title = title or info["title"]
        try:
            pic = chgpack.read_picture(data)
        except chgpack.ChgError:
            pic = None
        if pic:
            from . import runtime
            meta["cart_image"] = runtime.picture_png(pic)
    else:
        img = data
    stem = p.name.split(".")[0]
    title = title or stem.upper()[:model.TITLE_MAX]
    meta.setdefault("cart_image", placeholder(title))
    return Game(id=gid or model.slug(title), title=title, binaries={device: img}, **meta)


# ---- sketches ---------------------------------------------------------------------

def sketch_meta(d):
    """The sketch's chgame.json, or {}; raises CartError on an unknown key."""
    f = pathlib.Path(d) / "chgame.json"
    if not f.exists():
        return {}
    try:
        meta = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise CartError([Issue("bad-json", str(f), str(e))])
    if not isinstance(meta, dict):
        raise CartError([Issue("bad-json", str(f), "must be a JSON object")])
    bad = [k for k in meta if k not in SKETCH_KEYS]
    if bad:
        raise CartError([Issue("bad-field", str(f), f"unknown key {k!r} (known: {', '.join(SKETCH_KEYS)})")
                         for k in bad])
    return meta


def config_version(d):
    cfg = pathlib.Path(d) / "config.h"
    if cfg.exists():
        m = re.search(r'#define\s+\w+_VERSION\s+"([^"]+)"', cfg.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1)
    return ""


def readme_paragraph(d):
    """The README's first paragraph of prose, as plain text."""
    f = pathlib.Path(d) / "README.md"
    if not f.exists():
        return ""
    para = []
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s:
            if para:
                break
            continue
        if s.startswith(("#", "![", "|", "```", "<", ">")):    # (a blockquote: a note, not the description)
            if para:
                break
            continue
        para.append(s)
    t = " ".join(para)
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)          # links and images: their text
    return re.sub(r"[*_`]", "", t)


def license_id(d):
    f = pathlib.Path(d) / "LICENSE"
    if f.exists():
        head = f.read_text(encoding="utf-8", errors="replace")[:400]
        for words, spdx in LICENSES:
            if words in head:
                return spdx
    return ""


def from_sketch(d, image, device="rev0"):
    """The Game a sketch folder makes, with `image` its release build's .bin."""
    d = pathlib.Path(d)
    meta = sketch_meta(d)
    g = Game(id=meta.get("id") or model.slug(d.name), title=meta.get("title") or d.name.upper()[:model.TITLE_MAX],
             binaries={device: image})
    g.version = meta.get("version") or config_version(d)
    g.description = meta.get("description") or readme_paragraph(d)
    g.license = meta.get("license") or license_id(d)
    for k in ("author", "genre", "url", "sourceUrl", "folder"):
        setattr(g, k, meta.get(k, ""))
    names = meta.get("licenseFiles", [n for n in ("LICENSE", "NOTICE") if (d / n).is_file()])
    for n in names:
        g.license_files[pathlib.PurePosixPath(n).name] = (d / n).read_bytes()
    sd = meta.get("sdcard", "sdcard" if (d / "sdcard").is_dir() else "")
    if sd:
        root = d / sd
        if not root.is_dir():
            raise CartError([Issue("missing-file", f"{d.name}/chgame.json: sdcard", f"no folder {root}")])
        for f in sorted(root.rglob("*")):
            if f.is_file():
                g.sd[f.relative_to(root).as_posix()] = f.read_bytes()
    if meta.get("cartImage"):
        g.cart_image = (d / meta["cartImage"]).read_bytes()
    elif (d / "docs" / "cart.png").is_file():
        g.cart_image = (d / "docs" / "cart.png").read_bytes()
    if g.cart_image is None:
        gif = d / "docs" / "gameplay.gif"
        g.cart_image = placeholder(g.title, gif.read_bytes() if gif.is_file() else None)
    g.buttons = [(b["control"], b["action"]) for b in meta.get("buttons", [])]
    return g


def build_sketch(d, device="rev0"):
    """Compiles the sketch (release) and returns its Game."""
    import device as dev                    # tools/device.py
    out = dev.build(d)
    return from_sketch(d, (out / f"{pathlib.Path(d).name}.ino.bin").read_bytes(), device)


# ---- anything -----------------------------------------------------------------------

def load_item(item, build=True, title=None):
    """[Game] from a path: a .chgame (all its games), a .bin/.hex/.elf/.chg,
    or a sketch folder (built unless build=False, then its build/release
    .bin); or the name of a game or app in this repository (CHFour)."""
    p = pathlib.Path(item)
    if not p.exists() and p.name == str(item) and not p.suffix:
        import paths                        # tools/paths.py
        p = paths.sketch(str(item))
    if p.is_dir():
        if build:
            return [build_sketch(p)]
        b = p / "build" / "release" / f"{p.name}.ino.bin"
        if not b.exists():
            raise CartError([Issue("missing-file", str(p), f"{b} is missing: build it, or drop --no-build")])
        return [from_sketch(p, b.read_bytes())]
    if p.suffix.lower() == ".chgame":
        return zipio.load(p).games
    if p.suffix.lower() in BINARY_SUFFIXES:
        return [from_binary(p, title)]
    raise CartError([Issue("bad-field", str(p), "not a .chgame, .bin, .hex, .elf, .chg or sketch folder")])


def merge(games, new, log=print):
    """Adds `new` games to the list: an identical game already there is
    skipped; a different one with the same id gets -2, -3 ..."""
    out = list(games)
    for g in new:
        same = next((h for h in out if h.id == g.id), None)
        if same is not None and same == g:
            log(f"{g.id}: already in the cart, skipped")
            continue
        if same is not None:
            base, n = g.id, 2
            while any(h.id == f"{base[:29]}-{n}" for h in out):
                n += 1
            g.id = f"{base[:29]}-{n}"
            log(f"{base}: another game has this id; this one is {g.id}")
        out.append(g)
    return out
