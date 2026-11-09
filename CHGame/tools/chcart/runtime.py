"""Runtime preparation: a cart to the files of a CHGame SD card, as the menu
bootloader v2 reads them (spec/card.md; the bootloader's side is
platform/bootloader/shared/chgame_card.h and src/menu.c).

    GAMES/                 the menu's tree
      MENU.IDX             the folder's entries in the cart's order, folder
                           titles, the launch flag
      MENU.BG              the list menu's background (the cart's, or
                           spec/assets' default at the top; a folder's own if
                           it has one)
      COVER.PIC            the visual menu's cover of the folder (the cart's,
                           or spec/assets' default at the top; a folder's own
                           if it has one)
      SYSTEM.PIC           (top only) the visual menu's screens: the about
                           page (the cart's or the default), then spec/assets'
      <NAME>.CHG           a game (spec/chg.md), with its picture if it has one,
                           and its record (what a backup needs: backup.py)
      <NAME>/              a folder, the same again
    <the games' SD files>  at the paths the games read them from

Every step is deterministic, so two implementations that follow spec/card.md
write the same bytes: the conformance fixtures in spec/fixtures check it.
"""
from __future__ import annotations

import base64
import json
import pathlib
import struct
import sys
import zlib

from . import model
from .model import CartError, Issue

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import chgpack  # noqa: E402

DEFAULT_BACKGROUND = REPO / "spec" / "assets" / "menu-default.png"
DEFAULT_COVER = REPO / "spec" / "assets" / "cover-default.png"
DEFAULT_ABOUT = REPO / "spec" / "assets" / "about-default.png"
# SYSTEM.PIC's screens after the about page, in order (shared/chgame_card.h
# CARD_SYS_*); a cart replaces any of them through menu.systemImages
SYSTEM_SCREENS = list(model.SYSTEM_IMAGES)
SYSTEM_DIR = REPO / "spec" / "assets" / "system"
IDX_MAGIC, BG_MAGIC = b"CHX1", b"CHB1"
IDX_RECORD, IDX_LAUNCH = 32, 0x01
BG_HEADER, BG_BYTES = 512, 512 + 128 * 64
UI_INDEX = {"text": 11, "disabled": 12, "selectedText": 13, "mark": 14}
RAINBOW_INDEX = 15
# Names Windows will not create a file or folder under, whatever the extension
DEVICE_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


def name83(text, taken, ext, fallback):
    """A name for an entry of one folder: the capitals and digits of `text`,
    8 at most (`fallback` if none), made unique within the folder by a number
    in place of its last characters (WORDS, WORDS2, ... BLACKJA2)."""
    base = "".join(c for c in text.upper() if "A" <= c <= "Z" or "0" <= c <= "9")[:8] or fallback
    cand, n = base, 2
    while (cand, ext) in taken or cand in DEVICE_NAMES:
        s = str(n)
        cand, n = base[:8 - len(s)] + s, n + 1
    taken.add((cand, ext))
    return cand


def raw11(base, ext):
    return base.ljust(8).encode("ascii") + ext.ljust(3).encode("ascii")


def rgb565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def menu_background(png, ui, code="bad-background", where="menu"):
    """MENU.BG from a background PNG (spec/card.md): #FF00FF is colour 15 (the
    rainbow, or as painted: its palette entry is #FF00FF); a colour equal to one of
    the menu's own takes its index (11-14, the lowest if several match); every
    other colour gets 0-10 in order of first appearance, row by row."""
    index = {model.RAINBOW_RGB: RAINBOW_INDEX}
    for k in ("text", "disabled", "selectedText", "mark"):
        index.setdefault(model.hex_rgb(ui[k]), UI_INDEX[k])
    pal = [0] * 16
    for k, rgb in enumerate(model.background_colors(png, ui)):
        if k > 10:
            raise CartError([Issue(code, where, "more than 11 colours")])
        index[rgb] = k
        pal[k] = rgb565(*rgb)
    for k, i in UI_INDEX.items():
        pal[i] = rgb565(*model.hex_rgb(ui[k]))
    pal[RAINBOW_INDEX] = rgb565(*model.RAINBOW_RGB)   # what a static-style bootloader shows
    pix = [index[p] for p in model.rgb_pixels(png)]
    head = BG_MAGIC + bytes(4) + struct.pack("<16H", *pal)
    body = bytes(pix[i] << 4 | pix[i + 1] for i in range(0, len(pix), 2))
    return head.ljust(BG_HEADER, b"\0") + body


def menu_picture(png, where="picture"):
    """A picture for the visual menu (a cover, SYSTEM.PIC's screens, a game's
    picture in its CHG file): MENU.BG's encoding, with the menu's colours at
    their defaults whatever the cart's (spec/card.md, the picture rule)."""
    return menu_background(png, model.UI_COLORS, "bad-picture", where)


def rgb888(c):
    """An RGB565 colour as the 8-bit colour that gives it back."""
    return (c >> 11) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31


def picture_png(pic, ui=None):
    """A picture (menu_picture()'s encoding), or a MENU.BG made with the menu
    colours `ui`, back to a PNG that gives the same bytes again: its own
    colours as RGB565 gives them back, the menu's and #FF00FF exactly."""
    import io
    from PIL import Image
    pal = struct.unpack_from("<16H", pic, 8)
    rgb = [rgb888(c) for c in pal]
    for k, i in UI_INDEX.items():           # (the menu's colours and #FF00FF exactly: RGB565 cannot hold them all)
        rgb[i] = model.hex_rgb((ui or model.UI_COLORS)[k])
    rgb[RAINBOW_INDEX] = model.RAINBOW_RGB
    im = Image.new("P", (128, 128))
    im.putpalette([v for c in rgb for v in c])
    px = pic[BG_HEADER:BG_BYTES]
    im.putdata([b >> 4 if i % 2 == 0 else b & 15 for i, b in enumerate(x for x in px for _ in (0, 1))])
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


RECORD_VERSION = 1
RECORD_TEXT = ("version", "author", "description", "genre", "license", "url", "sourceUrl")


def canonical_json(obj):
    """JSON as the record is written (spec/chg.md): keys sorted, no spaces,
    everything above U+007F escaped (Python's ensure_ascii)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def record(game, device="rev0"):
    """The game's record (spec/chg.md): what its cart says of it that the
    CHG file and the card do not hold otherwise, and the SD files it puts on
    the card with their sizes and CRCs, so that a backup of the card can make
    its cart again (backup.py)."""
    g = {"id": game.id, "title": game.title}
    for k in RECORD_TEXT:
        if getattr(game, k):
            g[k] = getattr(game, k)
    if game.buttons:
        g["buttons"] = [{"control": c, "action": a} for c, a in game.buttons]
    r = {"chgRecord": RECORD_VERSION, "game": g, "binaryBytes": len(game.binaries[device])}
    if game.cart_image is not None:
        r["cartImage"] = base64.b64encode(game.cart_image).decode("ascii")
    if game.license_files:
        r["licenseFiles"] = {n: base64.b64encode(d).decode("ascii") for n, d in game.license_files.items()}
    if game.sd:
        r["sdcard"] = [{"path": p, "bytes": len(game.sd[p]), "crc32": f"{zlib.crc32(game.sd[p]) & 0xFFFFFFFF:08x}"}
                       for p in sorted(game.sd)]
    return canonical_json(r)


def chg_file(game, device="rev0"):
    """The game's CHG file (spec/chg.md): its binary for `device` behind the
    header, with the title, and the author and version where they fit; then
    its picture (cartImage) if it follows the picture rule; then its record."""
    pic = menu_picture(game.cart_image) if model.picture_ok(game.cart_image) else None
    rec = record(game, device)
    if len(rec) > chgpack.RECORD_MAX:
        raise CartError([Issue("record-size", f"games[{game.id}]",
                               f"its record is {len(rec)} B (licence files and cart image); {chgpack.RECORD_MAX} at most")])
    return chgpack.pack(game.binaries[device], game.title,
                        model.chg_text(game.author, model.CHG_AUTHOR_MAX),
                        model.chg_text(game.version, model.CHG_VERSION_MAX), picture=pic, record=rec,
                        target=model.DEVICES[device].chg_target)


def system_pic(about=None, images=None):
    """GAMES/SYSTEM.PIC: the about page (the cart's, else the default), then
    the menu's screens in SYSTEM_SCREENS' order: the cart's where it gives
    one (menu.systemImages), else spec/assets' default."""
    images = images or {}
    pngs = [about if about is not None else DEFAULT_ABOUT.read_bytes()]
    pngs += [images.get(n) if images.get(n) is not None else (SYSTEM_DIR / f"{n}.png").read_bytes()
             for n in SYSTEM_SCREENS]
    return b"".join(menu_picture(p, f"menu.systemImages.{n}") for p, n in zip(pngs, ["about"] + SYSTEM_SCREENS))


def levels(cart):
    """{folder path: [("folder", path) | ("game", Game)]}, "" being GAMES/
    itself: each folder's entries in the cart's order, a folder placed where
    its first game is."""
    out = {"": []}
    for g in cart.games:
        parent = ""
        for p in (g.folder.split("/") if g.folder else []):
            child = f"{parent}/{p}" if parent else p
            if child not in out:
                out[child] = []
                out[parent].append(("folder", child))
            parent = child
        out[parent].append(("game", g))
    return out


def prepare(cart, device="rev0"):
    """{card path: bytes} for the cart: GAMES/ and the games' SD files.
    Raises CartError if the cart breaks a rule or a game has no binary for
    `device`. A card is for one board: its CHG files carry that board's
    target id, and another board's menu refuses to install them."""
    errors = [i for i in model.validate(cart) if i.error]
    errors += [Issue("bad-device", f"games[{g.id}].binaries", f"no binary for {device}")
               for g in cart.games if device not in g.binaries]
    if errors:
        raise CartError(errors)
    ui = cart.ui_colors()
    tree = levels(cart)
    where = {"": "GAMES"}                           # folder path -> card path
    launch = set()                                  # entries flagged for launch
    if cart.launch:
        g = cart.game(cart.launch)
        launch.add(("game", g.id))
        parts = g.folder.split("/") if g.folder else []
        launch |= {("folder", "/".join(parts[:k])) for k in range(1, len(parts) + 1)}
    out = {}
    for path, entries in tree.items():
        taken, idx = set(), bytearray(IDX_MAGIC.ljust(IDX_RECORD, b"\0"))
        files = {}
        for kind, e in entries:
            if kind == "folder":
                name = name83(e.rsplit("/", 1)[-1], taken, "", "FOLDER")
                where[e] = f"{where[path]}/{name}"
                title = e.rsplit("/", 1)[-1].encode("ascii")
                rec = raw11(name, "") + bytes([IDX_LAUNCH if ("folder", e) in launch else 0]) + title.ljust(20, b"\0")
            else:
                name = name83(e.title, taken, "CHG", "GAME")
                files[f"{where[path]}/{name}.CHG"] = chg_file(e, device)
                rec = raw11(name, "CHG") + bytes([IDX_LAUNCH if ("game", e.id) in launch else 0]) + bytes(20)
            idx += rec
        out[f"{where[path]}/MENU.IDX"] = bytes(idx)
        png = cart.background if not path else cart.folder_backgrounds.get(path)
        if not path and png is None:
            png = DEFAULT_BACKGROUND.read_bytes()
        if png is not None:
            out[f"{where[path]}/MENU.BG"] = menu_background(png, ui)
        png = cart.cover if not path else cart.folder_covers.get(path)
        if not path and png is None:
            png = DEFAULT_COVER.read_bytes()
        if png is not None:
            out[f"{where[path]}/COVER.PIC"] = menu_picture(png)
        if not path:
            out["GAMES/SYSTEM.PIC"] = system_pic(cart.about, cart.system_images)
        out.update(files)
    sd = {}
    for g in cart.games:
        sd.update(g.sd)
    for p in sorted(sd):
        out[p] = sd[p]
    return out


def flash_image(game, device="rev0"):
    """What the uploader writes for the game: its binary padded with 0xFF to a
    multiple of 4 (the CHG payload; the menu's installed-game check compares
    its length and CRC-32)."""
    return chgpack.pad_image(game.binaries[device])


def write_folder(files, out):
    """The card's files into a folder (replacing its contents)."""
    import shutil
    out = pathlib.Path(out)
    if out.exists():
        shutil.rmtree(out)
    for p, data in files.items():
        f = out / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)


def write_image(files, path, label="CHGAME"):
    """A FAT32 card image holding the files (CHSd's tools/fatimg.py)."""
    sys.path.insert(0, str(REPO / "platform" / "board" / "arduino" / "CHGame" / "libraries" / "CHSd" / "tools"))
    import fatimg  # noqa: E402
    return fatimg.build_image(str(path), files, fs="fat32", label=label)
